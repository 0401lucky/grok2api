"""console.x.ai Responses protocol adapter."""

from typing import Any, AsyncGenerator

import orjson

from app.control.proxy.models import ProxyFeedback, ProxyFeedbackKind
from app.dataplane.reverse.protocol.tool_parser import ParsedToolCall
from app.dataplane.reverse.runtime.endpoint_table import CONSOLE_RESPONSES
from app.dataplane.reverse.transport._proxy_feedback import upstream_feedback
from app.platform.errors import UpstreamError
from app.platform.logging.logger import logger


# 对外模型名到 console.x.ai 实际模型名的映射。
CONSOLE_MODELS: dict[str, str] = {
    "grok-4.3-console": "grok-4.3",
    "grok-4.3-low": "grok-4.3",
    "grok-4.3-medium": "grok-4.3",
    "grok-4.3-high": "grok-4.3",
    "grok-4.20-0309-reasoning-console": "grok-4.20-0309-reasoning",
    "grok-4.20-0309-console": "grok-4.20-0309",
    "grok-4.20-0309-non-reasoning-console": "grok-4.20-0309-non-reasoning",
    "grok-4.20-multi-agent-console": "grok-4.20-multi-agent-0309",
    "grok-4.20-multi-agent-low": "grok-4.20-multi-agent-0309",
    "grok-4.20-multi-agent-medium": "grok-4.20-multi-agent-0309",
    "grok-4.20-multi-agent-high": "grok-4.20-multi-agent-0309",
    "grok-4.20-multi-agent-xhigh": "grok-4.20-multi-agent-0309",
    "grok-build-console": "grok-build-0.1",
}

_MODELS_WITH_REASONING_FIELD = frozenset(
    {
        "grok-4.3",
        "grok-4.20-multi-agent-0309",
    }
)

_MODEL_FIXED_EFFORT: dict[str, str] = {
    "grok-4.3-low": "low",
    "grok-4.3-medium": "medium",
    "grok-4.3-high": "high",
    "grok-4.20-multi-agent-low": "low",
    "grok-4.20-multi-agent-medium": "medium",
    "grok-4.20-multi-agent-high": "high",
    "grok-4.20-multi-agent-xhigh": "xhigh",
}

_MODEL_MAX_OUTPUT_TOKENS: dict[str, int] = {
    "grok-4.20-multi-agent-0309": 2_000_000,
    "grok-build-0.1": 256_000,
}

_MODELS_WITH_SEARCH_TOOLS = frozenset(
    {
        "grok-4.3",
        "grok-4.20-multi-agent-0309",
        "grok-4.20-0309",
        "grok-4.20-0309-reasoning",
        "grok-4.20-0309-non-reasoning",
        "grok-build-0.1",
    }
)

_EFFORT_MAP: dict[str, str] = {
    "none": "none",
    "minimal": "low",
    "low": "low",
    "medium": "medium",
    "high": "high",
    "xhigh": "xhigh",
}

_WEB_SEARCH_ALIASES = frozenset({"web_search", "web_search_preview"})
_X_SEARCH_ALIASES = frozenset({"x_search", "x_keyword_search", "x_semantic_search"})

# Grok/xAI 内部工具名。它们可能以 function_call/tool card 形式出现在上游流里，
# 但对 OpenAI 客户端必须保持“内部工具”语义，不能转成客户端 tool_calls。
# 参考 xAI Tool Usage Details 的 server-side function names，并保留旧 grok.com
# parser 已观测到的 alias。故意不含泛名 search，避免误伤用户自定义工具。
_CONSOLE_INTERNAL_TOOL_NAMES: frozenset[str] = frozenset({
    # 公开工具类型 / 别名
    "web_search",
    "x_search",
    "code_interpreter",
    "file_search",
    # SERVER_SIDE_TOOL_WEB_SEARCH function names
    "web_search_with_snippets",
    "browse_page",
    "open_page",
    "open_page_with_find",
    # SERVER_SIDE_TOOL_IMAGE_SEARCH function names / 观测别名
    "search_images",
    "image_search",
    "view_image",
    # SERVER_SIDE_TOOL_X_SEARCH function names
    "x_user_search",
    "x_keyword_search",
    "x_semantic_search",
    "x_thread_fetch",
    "view_x_video",
    # 其它服务端 / 内部 helper
    "chatroom_send",
    "code_execution",
    "collections_search",
})


def _api_role(role: str) -> str:
    if role in {"system", "developer", "assistant"}:
        return role if role != "developer" else "system"
    return "user"


def _image_url_from_block(block: dict[str, Any]) -> str:
    src = block.get("image_url") or block.get("source") or block.get("url") or ""
    if isinstance(src, dict):
        return str(src.get("url") or "")
    return str(src or "")


def _content_blocks(msg: dict[str, Any], *, include_tool_calls: bool = True) -> list[dict[str, Any]]:
    content = msg.get("content")
    blocks: list[dict[str, Any]] = []

    if isinstance(content, str):
        if content:
            blocks.append({"type": "input_text", "text": content})
    elif isinstance(content, list):
        for block in content:
            if not isinstance(block, dict):
                continue
            btype = block.get("type", "")
            if btype in {"text", "input_text", "output_text"}:
                text = block.get("text") or ""
                if text:
                    blocks.append({"type": "input_text", "text": text})
            elif btype in {"image_url", "input_image", "image"}:
                url = _image_url_from_block(block)
                if url:
                    blocks.append({"type": "input_image", "image_url": url})
            elif btype == "tool_result":
                text = block.get("content") or block.get("text") or ""
                if text:
                    blocks.append({"type": "input_text", "text": str(text)})
            else:
                text = block.get("text")
                if text is None:
                    text = str(block)
                blocks.append({"type": "input_text", "text": str(text)})
    elif content is not None:
        blocks.append({"type": "input_text", "text": str(content)})

    tool_calls = msg.get("tool_calls")
    if include_tool_calls and tool_calls:
        try:
            tool_text = orjson.dumps(tool_calls).decode()
        except Exception:
            tool_text = str(tool_calls)
        blocks.append({"type": "input_text", "text": f"[tool_calls]\n{tool_text}"})

    return blocks


def _default_console_tools(console_model: str) -> list[dict[str, Any]]:
    """模型支持搜索时下发的默认 console 工具。"""
    if console_model not in _MODELS_WITH_SEARCH_TOOLS:
        return []
    return [
        {"type": "web_search", "enable_image_understanding": True},
        {"type": "x_search", "enable_video_understanding": True},
    ]


def _normalize_user_console_tool(tool: dict[str, Any]) -> dict[str, Any] | None:
    """把客户端声明的非 function 工具规范化为 console 形态。

    仅统一搜索工具的 type 别名（web_search_preview→web_search 等），其余配置原样保留、
    不补默认开关，以便客户端显式配置覆盖默认；其它内置工具（code_interpreter、
    collections_search、file_search…）原样透传。function 工具由
    ``_to_console_function_tools`` 处理，这里返回 None 跳过。
    """
    tool_type = str(tool.get("type") or "").strip()
    if not tool_type or tool_type == "function":
        return None
    normalized = dict(tool)
    if tool_type in _WEB_SEARCH_ALIASES:
        normalized["type"] = "web_search"
    elif tool_type in _X_SEARCH_ALIASES:
        normalized["type"] = "x_search"
    return normalized


def _tool_identity(tool: dict[str, Any]) -> tuple[str, str]:
    """工具去重标识：function 以名称区分，其余以 type 区分。"""
    tool_type = str(tool.get("type") or "").strip()
    if tool_type == "function":
        return (tool_type, str(tool.get("name") or "").strip())
    return (tool_type, "")


def _merge_console_tools(
    default_tools: list[dict[str, Any]],
    user_tools: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """合并默认工具与客户端工具，客户端显式配置覆盖同类默认工具。"""
    result: list[dict[str, Any]] = []
    positions: dict[tuple[str, str], int] = {}
    for tool in default_tools:
        ident = _tool_identity(tool)
        positions[ident] = len(result)
        result.append(tool)
    for tool in user_tools:
        ident = _tool_identity(tool)
        pos = positions.get(ident)
        if pos is None:
            positions[ident] = len(result)
            result.append(tool)
        else:
            result[pos] = tool
    return result


def _is_console_internal_tool_name(name: str) -> bool:
    return name.strip() in _CONSOLE_INTERNAL_TOOL_NAMES


def client_function_tool_names(tools: list[dict[str, Any]] | None) -> set[str]:
    """返回客户端声明的 function 工具名集合。

    console 模型可能为内置工具（搜索、浏览、看图、代码执行等）发出内部工具事件，
    只有客户端 function 工具才应转成 OpenAI tool_calls。
    """
    names: set[str] = set()
    for tool in tools or []:
        if not isinstance(tool, dict):
            continue
        if tool.get("type") != "function":
            continue
        fn = tool.get("function")
        src = fn if isinstance(fn, dict) else tool
        name = str(src.get("name") or "").strip()
        if name and not _is_console_internal_tool_name(name):
            names.add(name)
    return names


def _to_console_function_tools(tools: list[dict[str, Any]] | None) -> list[dict[str, Any]]:
    """把 OpenAI function 工具转成 console Responses 形态。

    仅处理 ``type == "function"`` 的客户端工具；搜索类工具仍由 ``_console_tools``
    负责，内部工具名一律跳过，避免暴露成客户端可调用工具。
    """
    converted: list[dict[str, Any]] = []
    for tool in tools or []:
        if not isinstance(tool, dict):
            continue
        if tool.get("type") != "function":
            continue
        fn = tool.get("function")
        src = fn if isinstance(fn, dict) else tool
        name = str(src.get("name") or "").strip()
        if not name or _is_console_internal_tool_name(name):
            continue
        item: dict[str, Any] = {"type": "function", "name": name}
        description = src.get("description")
        if description is not None:
            item["description"] = description
        parameters = src.get("parameters")
        if parameters is not None:
            item["parameters"] = parameters
        # 客户端若提供 strict 严格模式标志则透传
        for key in ("strict",):
            if key in src:
                item[key] = src[key]
            elif key in tool:
                item[key] = tool[key]
        converted.append(item)
    return converted


def _to_console_tool_choice(tool_choice: Any) -> Any:
    """把 OpenAI tool_choice 映射为 console Responses 的 tool_choice。"""
    if tool_choice is None:
        return None
    if isinstance(tool_choice, str):
        return tool_choice
    if not isinstance(tool_choice, dict):
        return tool_choice

    if tool_choice.get("type") != "function":
        return dict(tool_choice)

    fn = tool_choice.get("function")
    if isinstance(fn, dict):
        name = str(fn.get("name") or "").strip()
    else:
        name = str(tool_choice.get("name") or "").strip()
    if not name:
        return dict(tool_choice)
    if _is_console_internal_tool_name(name):
        return "auto"
    return {"type": "function", "name": name}


def _content_to_text(content: Any) -> str:
    if content is None:
        return ""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts: list[str] = []
        for block in content:
            if isinstance(block, dict):
                text = block.get("text")
                if text is None:
                    text = block.get("content")
                parts.append(str(text if text is not None else block))
            else:
                parts.append(str(block))
        return "\n".join(part for part in parts if part)
    return str(content)


def _assistant_tool_calls_to_console(tool_calls: Any) -> list[dict[str, Any]]:
    """把 assistant 历史消息里的 tool_calls 转成 console function_call input items。"""
    if not isinstance(tool_calls, list):
        return []

    items: list[dict[str, Any]] = []
    for tool_call in tool_calls:
        if not isinstance(tool_call, dict):
            continue
        if tool_call.get("type") not in (None, "function"):
            continue
        fn = tool_call.get("function")
        if not isinstance(fn, dict):
            continue
        name = str(fn.get("name") or "").strip()
        if not name:
            continue
        call_id = str(tool_call.get("id") or tool_call.get("call_id") or "").strip()
        if not call_id:
            continue
        arguments = fn.get("arguments")
        if arguments is None:
            arguments = "{}"
        elif not isinstance(arguments, str):
            arguments = orjson.dumps(arguments).decode()
        items.append({
            "type": "function_call",
            "call_id": call_id,
            "name": name,
            "arguments": arguments,
            "status": "completed",
        })
    return items


def _tool_message_to_console_output(msg: dict[str, Any]) -> dict[str, Any] | None:
    """把 OpenAI ``role == "tool"`` 消息转成 console function_call_output input item。"""
    call_id = str(msg.get("tool_call_id") or msg.get("call_id") or "").strip()
    if not call_id:
        return None
    return {
        "type": "function_call_output",
        "call_id": call_id,
        "output": _content_to_text(msg.get("content", "")),
    }


def _normalize_response_format(response_format: Any) -> dict[str, Any] | None:
    if response_format is None:
        return None
    if isinstance(response_format, str):
        fmt_type = response_format.strip()
        return {"type": fmt_type} if fmt_type else None
    if not isinstance(response_format, dict):
        return None

    if "format" in response_format and isinstance(response_format.get("format"), dict):
        return _normalize_response_format(response_format.get("format"))

    fmt_type = str(response_format.get("type") or "").strip()
    if not fmt_type:
        return None

    if fmt_type == "json_schema":
        json_schema = response_format.get("json_schema")
        source = json_schema if isinstance(json_schema, dict) else response_format
        normalized: dict[str, Any] = {"type": "json_schema"}
        normalized["name"] = str(source.get("name") or "response")
        if source.get("description") is not None:
            normalized["description"] = source.get("description")
        normalized["schema"] = source.get("schema") or {}
        if source.get("strict") is not None:
            normalized["strict"] = bool(source.get("strict"))
        return normalized

    normalized = dict(response_format)
    normalized["type"] = fmt_type
    normalized.pop("json_schema", None)
    return normalized


def _console_text_config(
    *,
    response_format: Any = None,
    text: dict[str, Any] | None = None,
) -> dict[str, Any] | None:
    if isinstance(text, dict):
        config = dict(text)
        normalized = _normalize_response_format(config.get("format"))
        if normalized:
            config["format"] = normalized
        if config:
            return config

    normalized = _normalize_response_format(response_format)
    if normalized:
        return {"format": normalized}
    return None


def build_console_payload(
    *,
    messages: list[dict[str, Any]],
    model: str,
    temperature: float = 0.7,
    top_p: float = 0.95,
    reasoning_effort: str | None = None,
    stream: bool = True,
    tools: list[dict[str, Any]] | None = None,
    tool_choice: Any = None,
    response_format: Any = None,
    text: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build the JSON payload for ``POST console.x.ai/v1/responses``."""
    input_items: list[dict[str, Any]] = []
    for msg in messages:
        if not isinstance(msg, dict):
            continue
        role = str(msg.get("role") or "user")
        # role == "tool" 走原生 function_call_output，不再塞进文本
        if role == "tool":
            tool_output = _tool_message_to_console_output(msg)
            if tool_output:
                input_items.append(tool_output)
            continue
        # 历史 assistant 的 tool_calls 走原生 function_call，故此处不并入文本
        blocks = _content_blocks(msg, include_tool_calls=False)
        if blocks:
            input_items.append({"role": _api_role(role), "content": blocks})
        if role == "assistant":
            input_items.extend(_assistant_tool_calls_to_console(msg.get("tool_calls")))

    console_model = CONSOLE_MODELS.get(model, model)
    effort = _MODEL_FIXED_EFFORT.get(model) or _EFFORT_MAP.get(
        reasoning_effort or "medium", "medium"
    )

    payload: dict[str, Any] = {
        "model": console_model,
        "input": input_items,
        "max_output_tokens": _MODEL_MAX_OUTPUT_TOKENS.get(console_model, 1_000_000),
        "temperature": temperature,
        "top_p": top_p,
        "store": False,
        "include": ["reasoning.encrypted_content"],
        "stream": stream,
    }

    if console_model in _MODELS_WITH_REASONING_FIELD:
        payload["reasoning"] = {"effort": effort}

    # 客户端工具：非 function 内置工具规范化后原样透传，function 工具转 console 形态
    user_tools: list[dict[str, Any]] = []
    for tool in tools or []:
        if not isinstance(tool, dict):
            continue
        normalized = _normalize_user_console_tool(tool)
        if normalized is not None:
            user_tools.append(normalized)
    user_tools.extend(_to_console_function_tools(tools))

    # tool_choice="none" 表示不希望调用工具：不下发默认搜索工具
    default_tools = [] if tool_choice == "none" else _default_console_tools(console_model)
    payload_tools = _merge_console_tools(default_tools, user_tools)
    if payload_tools:
        payload["tools"] = payload_tools
        normalized_tool_choice = _to_console_tool_choice(tool_choice)
        payload["tool_choice"] = (
            normalized_tool_choice if normalized_tool_choice is not None else "auto"
        )

    text_config = _console_text_config(response_format=response_format, text=text)
    if text_config:
        payload["text"] = text_config

    logger.debug(
        "console payload built: model={} console_model={} input_items={} has_reasoning={} tool_count={} has_text_format={}",
        model,
        console_model,
        len(input_items),
        console_model in _MODELS_WITH_REASONING_FIELD,
        len(payload.get("tools", [])),
        bool(text_config),
    )
    return payload


class ConsoleStreamAdapter:
    """Parse console.x.ai Responses SSE events into text tokens.

    console Responses 流可能包含两类工具活动：
    - console 内部工具（搜索、浏览、看图、代码执行等），由 Grok 自用以生成最终答案；
    - 客户端声明的 function 工具，必须作为 tool_calls/function_call 暴露给客户端。

    仅第二类会被导出。内部工具事件被忽略且不影响文本增量，从而避免“内置搜索调用
    被误判为客户端 function 调用”导致的空响应回归。
    """

    __slots__ = (
        "text_buf",
        "usage",
        "_done",
        "_function_calls",
        "_function_order",
        "_allowed_function_names",
        "_ignored_function_keys",
        "_function_keys_by_output_index",
    )

    def __init__(
        self,
        function_tool_names: set[str] | list[str] | tuple[str, ...] | None = None,
    ) -> None:
        self.text_buf: list[str] = []
        self.usage: dict[str, Any] | None = None
        self._done = False
        self._function_calls: dict[str, dict[str, Any]] = {}
        self._function_order: list[str] = []
        self._allowed_function_names = {
            str(name).strip()
            for name in (function_tool_names or ())
            if str(name).strip() and not _is_console_internal_tool_name(str(name).strip())
        }
        self._ignored_function_keys: set[str] = set()
        self._function_keys_by_output_index: dict[str, str] = {}

    def _apply_final_text(self, text: Any) -> list[str]:
        if not isinstance(text, str) or not text:
            return []
        current = self.full_text
        if not current:
            self.text_buf = [text]
            return [text]
        if len(text) > len(current):
            emitted = [text[len(current):]] if text.startswith(current) else []
            self.text_buf = [text]
            return [part for part in emitted if part]
        return []

    @staticmethod
    def _content_text(content: Any) -> str:
        if not isinstance(content, list):
            return ""
        parts: list[str] = []
        for block in content:
            if not isinstance(block, dict):
                continue
            block_type = str(block.get("type") or "")
            if block_type not in {"output_text", "text"}:
                continue
            text = block.get("text")
            if isinstance(text, str) and text:
                parts.append(text)
        return "".join(parts)

    @classmethod
    def _output_text(cls, output: Any) -> str:
        if not isinstance(output, list):
            return ""
        parts: list[str] = []
        for item in output:
            if not isinstance(item, dict):
                continue
            direct = item.get("output_text")
            if isinstance(direct, str) and direct:
                parts.append(direct)
            content_text = cls._content_text(item.get("content"))
            if content_text:
                parts.append(content_text)
        return "".join(parts)

    def feed(self, event_type: str, data: str) -> list[str]:
        if self._done:
            return []
        try:
            obj = orjson.loads(data)
        except (orjson.JSONDecodeError, ValueError):
            return []

        if not event_type:
            event_type = str(obj.get("type") or "")

        if event_type == "response.output_text.delta":
            delta = obj.get("delta") or ""
            if delta:
                self.text_buf.append(delta)
                return [str(delta)]
        elif event_type == "response.output_text.done":
            return self._apply_final_text(obj.get("text"))
        elif event_type == "response.content_part.done":
            part = obj.get("part") if isinstance(obj.get("part"), dict) else {}
            return self._apply_final_text(part.get("text"))
        elif event_type == "response.output_item.added":
            item = obj.get("item")
            if isinstance(item, dict) and item.get("type") == "function_call":
                self._upsert_function_call(item, obj)
        elif event_type == "response.function_call_arguments.delta":
            key = self._function_key(obj)
            if self._should_ignore_function_event(key, obj):
                return []
            delta = obj.get("delta", "")
            if key and isinstance(delta, str):
                info = self._ensure_function_call(key, obj)
                info["arguments"] = str(info.get("arguments") or "") + delta
        elif event_type == "response.function_call_arguments.done":
            key = self._function_key(obj)
            if self._should_ignore_function_event(key, obj):
                return []
            args = obj.get("arguments")
            if key and isinstance(args, str):
                info = self._ensure_function_call(key, obj)
                info["arguments"] = args
        elif event_type == "response.output_item.done":
            item = obj.get("item") if isinstance(obj.get("item"), dict) else {}
            if item.get("type") == "function_call":
                self._upsert_function_call(item, obj, completed=True)
            else:
                return self._apply_final_text(self._content_text(item.get("content")))
        elif event_type == "response.completed":
            emitted: list[str] = []
            response = obj.get("response") or {}
            if isinstance(response, dict):
                self.usage = response.get("usage")
                output = response.get("output")
                if isinstance(output, list):
                    for out_item in output:
                        if isinstance(out_item, dict) and out_item.get("type") == "function_call":
                            self._upsert_function_call(out_item, {}, completed=True)
                emitted.extend(self._apply_final_text(response.get("output_text")))
                emitted.extend(self._apply_final_text(self._output_text(output)))
            self._done = True
            return emitted
        elif event_type == "error":
            msg = obj.get("message") or obj.get("error") or str(obj)
            raise UpstreamError(f"Console API error: {msg}", status=502)

        return []

    def _function_key(self, obj: dict[str, Any]) -> str:
        raw = obj.get("item_id")
        if raw:
            return str(raw)
        raw = obj.get("output_index")
        if raw is None:
            return ""
        idx_key = str(raw)
        return self._function_keys_by_output_index.get(idx_key) or f"output:{idx_key}"

    def _allows_function_name(self, name: str) -> bool:
        name = name.strip()
        return bool(name) and name in self._allowed_function_names

    def _forget_output_index_for_key(self, key: str) -> None:
        for idx, mapped_key in list(self._function_keys_by_output_index.items()):
            if mapped_key == key:
                self._function_keys_by_output_index.pop(idx, None)

    def _ignore_function_key(self, key: str) -> None:
        if not key:
            return
        self._ignored_function_keys.add(key)
        self._function_calls.pop(key, None)
        self._forget_output_index_for_key(key)
        if key in self._function_order:
            self._function_order = [item for item in self._function_order if item != key]

    def _should_ignore_function_event(self, key: str, obj: dict[str, Any]) -> bool:
        if not self._allowed_function_names:
            self._ignore_function_key(key)
            return True
        if key and key in self._ignored_function_keys:
            return True
        name = str(obj.get("name") or "").strip()
        if name and not self._allows_function_name(name):
            self._ignore_function_key(key)
            return True
        return False

    def _ensure_function_call(self, key: str, obj: dict[str, Any]) -> dict[str, Any]:
        info = self._function_calls.get(key)
        if info is None:
            info = {
                "id": key,
                "type": "function_call",
                "call_id": "",
                "name": "",
                "arguments": "",
                "status": "in_progress",
            }
            self._function_calls[key] = info
            self._function_order.append(key)
        output_index = obj.get("output_index")
        if output_index is not None:
            idx_key = str(output_index)
            info["output_index"] = output_index
            self._function_keys_by_output_index[idx_key] = key
        return info

    def _merge_function_keys(self, source_key: str, target_key: str) -> None:
        if not source_key or source_key == target_key:
            return
        source = self._function_calls.pop(source_key, None)
        if source is not None:
            target = self._function_calls.get(target_key)
            if target is None:
                self._function_calls[target_key] = source
                for i, key in enumerate(self._function_order):
                    if key == source_key:
                        self._function_order[i] = target_key
                        break
                if target_key not in self._function_order:
                    self._function_order.append(target_key)
            else:
                for field, value in source.items():
                    if field == "arguments":
                        if not target.get("arguments"):
                            target[field] = value
                    elif value and not target.get(field):
                        target[field] = value
                self._function_order = [
                    key for key in self._function_order if key != source_key
                ]
        for idx, mapped_key in list(self._function_keys_by_output_index.items()):
            if mapped_key == source_key:
                self._function_keys_by_output_index[idx] = target_key
        if source_key in self._ignored_function_keys:
            self._ignored_function_keys.add(target_key)

    def _upsert_function_call(
        self,
        item: dict[str, Any],
        event_obj: dict[str, Any],
        *,
        completed: bool = False,
    ) -> None:
        event_key = self._function_key(event_obj)
        item_key = str(item.get("id") or item.get("call_id") or "")
        key = item_key or event_key
        if not key:
            return
        if event_key and item_key and event_key != item_key:
            self._merge_function_keys(event_key, item_key)
            key = item_key
        if key in self._ignored_function_keys:
            return

        name = str(item.get("name") or "").strip()
        if name and not self._allows_function_name(name):
            self._ignore_function_key(key)
            return

        info = self._ensure_function_call(key, event_obj)
        for field in ("id", "call_id", "name"):
            if item.get(field):
                info[field] = item[field]
        item_args = item.get("arguments")
        if isinstance(item_args, str) and (item_args or not info.get("arguments")):
            info["arguments"] = item_args
        if completed or item.get("status") == "completed":
            info["status"] = "completed"

    @property
    def full_text(self) -> str:
        return "".join(self.text_buf)

    @property
    def function_call_items(self) -> list[dict[str, Any]]:
        items: list[dict[str, Any]] = []
        for key in self._function_order:
            info = self._function_calls.get(key) or {}
            name = str(info.get("name") or "").strip()
            if not self._allows_function_name(name):
                continue
            items.append({
                "id": str(info.get("id") or key),
                "type": "function_call",
                "call_id": str(info.get("call_id") or key),
                "name": name,
                "arguments": str(info.get("arguments") or "{}"),
                "status": str(info.get("status") or "completed"),
            })
        return items

    @property
    def parsed_tool_calls(self) -> list[ParsedToolCall]:
        return [
            ParsedToolCall(
                call_id=str(item.get("call_id") or item.get("id")),
                name=str(item["name"]),
                arguments=str(item.get("arguments") or "{}"),
            )
            for item in self.function_call_items
        ]


def raise_empty_console_response(model: str) -> None:
    raise UpstreamError(
        "Console API completed without output text",
        status=503,
        body=f"reason=empty_output model={model}",
    )


def classify_console_line(line: str) -> tuple[str, str]:
    stripped = line.strip()
    if not stripped:
        return "skip", ""
    if stripped.startswith("event:"):
        return "event", stripped[6:].strip()
    if stripped.startswith("data:"):
        data = stripped[5:].strip()
        if data == "[DONE]":
            return "done", ""
        return "data", data
    return "skip", ""


def _transport_feedback() -> ProxyFeedback:
    return ProxyFeedback(kind=ProxyFeedbackKind.TRANSPORT_ERROR)


def _success_feedback() -> ProxyFeedback:
    return ProxyFeedback(kind=ProxyFeedbackKind.SUCCESS, status_code=200)


async def stream_console_chat(
    token: str,
    payload: dict[str, Any],
    *,
    timeout_s: float = 120.0,
) -> AsyncGenerator[tuple[str, str], None]:
    """POST to console.x.ai/v1/responses and yield ``(event_type, data)``."""
    from app.dataplane.proxy import get_proxy_runtime
    from app.dataplane.proxy.adapters.headers import build_console_headers
    from app.dataplane.proxy.adapters.session import ResettableSession, build_session_kwargs

    proxy = await get_proxy_runtime()
    # console.x.ai 与 grok.com 共用 SSO/CF 访问态。这里沿用默认 grok.com
    # clearance，与参考项目保持一致，避免单独按 console.x.ai 生成无效 clearance。
    lease = await proxy.acquire()
    headers = build_console_headers(token, lease=lease)
    session_kwargs = build_session_kwargs(lease=lease)

    async with ResettableSession(**session_kwargs) as session:
        try:
            response = await session.post(
                CONSOLE_RESPONSES,
                headers=headers,
                data=orjson.dumps(payload),
                timeout=timeout_s,
                stream=True,
            )
        except UpstreamError as exc:
            await proxy.feedback(lease, upstream_feedback(exc))
            raise
        except Exception as exc:
            await proxy.feedback(lease, _transport_feedback())
            raise UpstreamError(
                f"Console transport failed: {exc}",
                status=502,
                body=str(exc).replace("\n", "\\n")[:400],
            ) from exc

        if response.status_code != 200:
            try:
                body = response.content.decode("utf-8", "replace")[:400]
            except Exception:
                body = ""
            err = UpstreamError(
                f"Console API returned {response.status_code}",
                status=response.status_code,
                body=body,
            )
            await proxy.feedback(lease, upstream_feedback(err))
            raise err

        # 上游已经接受请求，proxy/clearance 已完成它们该完成的部分。
        # high/xhigh 这类长 SSE 流后续可能因平台或客户端中断，不应误伤代理池。
        await proxy.feedback(lease, _success_feedback())

        current_event = ""
        try:
            async for raw_line in response.aiter_lines():
                if isinstance(raw_line, bytes):
                    raw_line = raw_line.decode("utf-8", "replace")
                kind, value = classify_console_line(str(raw_line))
                if kind == "event":
                    current_event = value
                elif kind == "data":
                    yield current_event, value
                    current_event = ""
                elif kind == "done":
                    return
        except UpstreamError:
            raise
        except Exception as exc:
            raise UpstreamError(
                f"Console stream read failed: {exc}",
                status=502,
                body=str(exc).replace("\n", "\\n")[:400],
            ) from exc


__all__ = [
    "CONSOLE_MODELS",
    "build_console_payload",
    "client_function_tool_names",
    "ConsoleStreamAdapter",
    "raise_empty_console_response",
    "classify_console_line",
    "stream_console_chat",
]
