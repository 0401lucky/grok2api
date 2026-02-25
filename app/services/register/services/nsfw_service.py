from __future__ import annotations

from typing import Optional, Dict, Any
from urllib.parse import unquote

from curl_cffi import requests

from app.core.config import get_config

DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36"
)

NSFW_API = "https://grok.com/auth_mgmt.AuthManagement/UpdateUserFeatureControls"
AGE_VERIFY_API = "https://grok.com/rest/auth/set-birth-date"

# Rust 版本的稳态回退 emulation：chrome_116
NSFW_FALLBACK_IMPERSONATE = "chrome116"

NSFW_FEATURES_PATH = "features"
NSFW_FEATURES_ENABLED_PATH = "features.enabled"

# Legacy protobuf layout kept as compatibility fallback.
NSFW_PROTO_PAYLOAD_LEGACY = b"\x08\x01\x10\x01"

# 历史版本里常见的一种 payload：通过 feature name 字符串开启 always_show_nsfw_content
NSFW_PROTO_PAYLOAD_NAME_BASED = (
    b"\x0a\x02\x10\x01"
    b"\x12\x1a"
    b"\x0a\x18"
    b"always_show_nsfw_content"
)


def _encode_grpc_web_payload(proto_payload: bytes) -> bytes:
    # gRPC-web framing: 1 byte (compressed flag) + 4 bytes big-endian length + payload
    length = len(proto_payload)
    return b"\x00" + length.to_bytes(4, "big") + proto_payload


def _parse_grpc_web_trailers(body: bytes) -> dict[str, str]:
    """
    解析 gRPC-web 响应中的 trailers（通常包含 grpc-status / grpc-message）。

    帧格式：
      - 1 byte flag：0x00 data frame，0x80 trailer frame
      - 4 bytes length（大端）
      - payload
    """
    trailers: dict[str, str] = {}
    i = 0
    n = len(body)
    while i + 5 <= n:
        flag = body[i]
        length = int.from_bytes(body[i + 1:i + 5], "big")
        i += 5
        if length < 0 or i + length > n:
            break
        payload = body[i:i + length]
        i += length

        if flag & 0x80:
            text = payload.decode("utf-8", errors="replace")
            for line in text.split("\r\n"):
                line = line.strip()
                if not line or ":" not in line:
                    continue
                k, v = line.split(":", 1)
                k = k.strip().lower()
                v = v.strip()
                trailers[k] = unquote(v)
            break
    return trailers


def _grpc_code(v: Any) -> int | None:
    try:
        if v is None:
            return None
        return int(v)
    except Exception:
        return None


def _normalize_emulation(value: str) -> str:
    return (
        str(value or "")
        .strip()
        .lower()
        .replace("-", "")
        .replace("_", "")
        .replace(" ", "")
    )


def _emulation_equals(left: str, right: str) -> bool:
    return _normalize_emulation(left) == _normalize_emulation(right)


def _is_auth_related(text: str) -> bool:
    lower = str(text or "").lower()
    return any(k in lower for k in ("unauthorized", "forbidden", "auth", "permission", "token"))


def _is_payload_decode_error(text: str) -> bool:
    lower = str(text or "").lower()
    return any(
        k in lower
        for k in (
            "failed to decode protobuf",
            "invalid wire type",
            "updateuserfeaturecontrolsrequest.features",
        )
    )


def _is_field_mask_missing(text: str) -> bool:
    return "field mask must be provided" in str(text or "").lower()


def _is_invalid_field_mask_path(text: str) -> bool:
    lower = str(text or "").lower()
    return any(k in lower for k in ("invalid field mask", "fieldmask", "cannot find field", "unknown path"))


def _is_rejected_features_field(text: str) -> bool:
    lower = str(text or "").lower()
    return any(
        k in lower
        for k in (
            "invalid field: features",
            "field mask must be provided",
            "invalid field",
        )
    )


def _should_retry_with_alternate_mask_field(result: dict) -> bool:
    if result.get("ok"):
        return False
    if _grpc_code(result.get("grpc_status")) != 3:
        return False
    msg = result.get("grpc_message") or result.get("error") or ""
    return _is_field_mask_missing(msg)


def _should_retry_with_alternate_mask_path(result: dict) -> bool:
    if result.get("ok"):
        return False
    if _grpc_code(result.get("grpc_status")) != 3:
        return False
    msg = result.get("grpc_message") or result.get("error") or ""
    return _is_invalid_field_mask_path(msg)


def _should_retry_with_age_verify(result: dict) -> bool:
    if result.get("ok"):
        return False
    if _grpc_code(result.get("grpc_status")) != 3:
        return False
    msg = result.get("grpc_message") or result.get("error") or ""
    return _is_rejected_features_field(msg)


def _should_retry_with_legacy_payload(result: dict) -> bool:
    if result.get("ok"):
        return False
    if _grpc_code(result.get("grpc_status")) != 13:
        return False
    msg = result.get("grpc_message") or result.get("error") or ""
    return _is_payload_decode_error(msg)


def _should_retry_with_fallback_emulation(result: dict) -> bool:
    if result.get("ok"):
        return False
    status_code = result.get("status_code")
    if status_code in (401, 403):
        return True
    if _grpc_code(result.get("grpc_status")) in (7, 16):
        return True
    msg = result.get("grpc_message") or result.get("error") or ""
    return _is_auth_related(msg)


def _build_proto_payload(mask_field_number: int, mask_path: str) -> bytes:
    """
    Rust 版本的 payload 构造：features + FieldMask(paths=[mask_path])。

    - features: field #1 (length-delimited) => bytes [0x08,0x01,0x10,0x01]
    - field mask: field #2 or #3 (length-delimited) => google.protobuf.FieldMask
    """
    out = bytearray([0x0A, 0x04, 0x08, 0x01, 0x10, 0x01])

    path_bytes = str(mask_path or "").encode("utf-8")
    if not path_bytes or len(path_bytes) > 255:
        return bytes(out)

    # FieldMask.paths (field #1, string)
    field_mask = bytearray([0x0A, len(path_bytes)]) + path_bytes
    if len(field_mask) > 255:
        return bytes(out)

    top_level_tag = (int(mask_field_number) << 3) | 0x02
    out.extend([top_level_tag, len(field_mask)])
    out.extend(field_mask)
    return bytes(out)


class NsfwSettingsService:
    """开启 NSFW 相关设置（线程安全，无全局状态）。"""

    def __init__(self, cf_clearance: str = ""):
        self.cf_clearance = (cf_clearance or "").strip()

    @staticmethod
    def _build_proxies() -> Optional[dict]:
        proxy = str(get_config("grok.base_proxy_url", "") or "").strip()
        return {"http": proxy, "https": proxy} if proxy else None

    def _send_enable_request(
        self,
        *,
        sso: str,
        sso_rw: str,
        proto_payload: bytes,
        impersonate: str,
        user_agent: str,
        cf_clearance: str,
        timeout: int,
    ) -> Dict[str, Any]:
        cookies = {"sso": sso, "sso-rw": sso_rw}
        clearance = (cf_clearance or "").strip()
        if clearance:
            cookies["cf_clearance"] = clearance

        headers = {
            "accept": "*/*",
            "content-type": "application/grpc-web+proto",
            "origin": "https://grok.com",
            "referer": "https://grok.com/",
            "x-grpc-web": "1",
            "x-user-agent": "connect-es/2.1.1",
            "user-agent": user_agent or DEFAULT_USER_AGENT,
        }

        payload = _encode_grpc_web_payload(proto_payload)

        try:
            response = requests.post(
                NSFW_API,
                headers=headers,
                cookies=cookies,
                data=payload,
                impersonate=impersonate,
                timeout=timeout,
                proxies=self._build_proxies(),
            )
        except Exception as e:
            return {
                "ok": False,
                "hex_reply": "",
                "status_code": None,
                "grpc_status": None,
                "grpc_message": None,
                "error": str(e),
            }

        raw = response.content or b""
        trailers = _parse_grpc_web_trailers(raw)

        grpc_status_val = response.headers.get("grpc-status") or trailers.get("grpc-status")
        grpc_message_val = response.headers.get("grpc-message") or trailers.get("grpc-message") or ""
        grpc_message_decoded = unquote(grpc_message_val) if grpc_message_val else ""

        grpc_code = _grpc_code(grpc_status_val)
        status_code = int(getattr(response, "status_code", 0) or 0)
        ok = False
        error = None

        if status_code != 200:
            ok = False
            error = "403 Forbidden" if status_code == 403 else f"HTTP {status_code}"
        else:
            # grpc_code == None 表示未找到 grpc-status（部分 gRPC-web 响应可能不带），按成功处理
            ok = grpc_code in (None, 0)
            if not ok:
                if grpc_code is None:
                    error = "gRPC unknown"
                elif grpc_message_decoded:
                    error = f"gRPC {grpc_code}: {grpc_message_decoded}"
                else:
                    error = f"gRPC {grpc_code}"

        return {
            "ok": bool(ok),
            "hex_reply": raw.hex(),
            "status_code": status_code if status_code else None,
            "grpc_status": grpc_code,
            "grpc_message": grpc_message_decoded or None,
            "error": None if ok else error,
        }

    def _verify_age_via_rest(
        self,
        *,
        sso: str,
        sso_rw: str,
        impersonate: str,
        user_agent: str,
        cf_clearance: str,
        timeout: int,
    ) -> Dict[str, Any]:
        cookies = {"sso": sso, "sso-rw": sso_rw}
        clearance = (cf_clearance or "").strip()
        if clearance:
            cookies["cf_clearance"] = clearance

        headers = {
            "accept": "*/*",
            "content-type": "application/json",
            "origin": "https://grok.com",
            "referer": "https://grok.com/",
            "user-agent": user_agent or DEFAULT_USER_AGENT,
        }

        try:
            response = requests.post(
                AGE_VERIFY_API,
                headers=headers,
                cookies=cookies,
                json={"birthDate": "2001-01-01T16:00:00.000Z"},
                impersonate=impersonate,
                timeout=timeout,
                proxies=self._build_proxies(),
            )
            status_code = int(getattr(response, "status_code", 0) or 0)
            text = (response.text or "") if hasattr(response, "text") else ""
            ok = status_code == 200
            return {
                "ok": ok,
                "hex_reply": (response.content or b"").hex(),
                "status_code": status_code if status_code else None,
                "grpc_status": None,
                "grpc_message": None,
                "error": None if ok else f"HTTP {status_code}",
                "response_text": text[:500],
            }
        except Exception as e:
            return {
                "ok": False,
                "hex_reply": "",
                "status_code": None,
                "grpc_status": None,
                "grpc_message": None,
                "error": str(e),
                "response_text": "",
            }

    def _enable_chain(
        self,
        *,
        sso: str,
        sso_rw: str,
        impersonate: str,
        user_agent: str,
        cf_clearance: str,
        timeout: int,
        allow_age_verify: bool = True,
    ) -> Dict[str, Any]:
        # Prefer request shape with explicit FieldMask (field #2), which upstream may require.
        primary_payload = _build_proto_payload(2, NSFW_FEATURES_PATH)
        result = self._send_enable_request(
            sso=sso,
            sso_rw=sso_rw,
            proto_payload=primary_payload,
            impersonate=impersonate,
            user_agent=user_agent,
            cf_clearance=cf_clearance,
            timeout=timeout,
        )
        if result.get("ok"):
            return result

        if _should_retry_with_alternate_mask_field(result):
            second_payload = _build_proto_payload(3, NSFW_FEATURES_PATH)
            second = self._send_enable_request(
                sso=sso,
                sso_rw=sso_rw,
                proto_payload=second_payload,
                impersonate=impersonate,
                user_agent=user_agent,
                cf_clearance=cf_clearance,
                timeout=timeout,
            )
            if second.get("ok"):
                return second
            second["error"] = (
                f"primary payload failed: {result.get('error')}; "
                f"alternate mask field failed: {second.get('error')}"
            )
            result = second

        if _should_retry_with_alternate_mask_path(result):
            third_payload = _build_proto_payload(2, NSFW_FEATURES_ENABLED_PATH)
            third = self._send_enable_request(
                sso=sso,
                sso_rw=sso_rw,
                proto_payload=third_payload,
                impersonate=impersonate,
                user_agent=user_agent,
                cf_clearance=cf_clearance,
                timeout=timeout,
            )
            if third.get("ok"):
                return third
            third["error"] = (
                f"previous payload failed: {result.get('error')}; "
                f"alternate mask path failed: {third.get('error')}"
            )
            result = third

        if _should_retry_with_legacy_payload(result):
            legacy = self._send_enable_request(
                sso=sso,
                sso_rw=sso_rw,
                proto_payload=NSFW_PROTO_PAYLOAD_LEGACY,
                impersonate=impersonate,
                user_agent=user_agent,
                cf_clearance=cf_clearance,
                timeout=timeout,
            )
            if legacy.get("ok"):
                return legacy
            legacy["error"] = (
                f"previous payload failed: {result.get('error')}; "
                f"legacy payload failed: {legacy.get('error')}"
            )
            result = legacy

        # 补一条“name-based” payload，兼容部分历史行为。
        #
        # 注意：age-verify 触发条件需要基于前面 payload 的错误信息判断，
        # 所以这里不要直接覆盖 `result`，避免把“features 字段被拒绝”等关键信息冲掉。
        name_based = self._send_enable_request(
            sso=sso,
            sso_rw=sso_rw,
            proto_payload=NSFW_PROTO_PAYLOAD_NAME_BASED,
            impersonate=impersonate,
            user_agent=user_agent,
            cf_clearance=cf_clearance,
            timeout=timeout,
        )
        if name_based.get("ok"):
            return name_based
        name_based["error"] = (
            f"previous payload failed: {result.get('error')}; "
            f"name-based payload failed: {name_based.get('error')}"
        )
        if allow_age_verify and (
            _should_retry_with_age_verify(result) or _should_retry_with_age_verify(name_based)
        ):
            age_result = self._verify_age_via_rest(
                sso=sso,
                sso_rw=sso_rw,
                impersonate=impersonate,
                user_agent=user_agent,
                cf_clearance=cf_clearance,
                timeout=timeout,
            )
            if age_result.get("ok"):
                retry = self._enable_chain(
                    sso=sso,
                    sso_rw=sso_rw,
                    impersonate=impersonate,
                    user_agent=user_agent,
                    cf_clearance=cf_clearance,
                    timeout=timeout,
                    allow_age_verify=False,
                )
                if retry.get("ok"):
                    return retry
                retry["error"] = (
                    f"age-verify ok; enable retry failed: {retry.get('error') or 'unknown'}"
                )
                return retry
            failed_msg = name_based.get("error") or result.get("error")
            age_result["error"] = (
                f"gRPC update failed: {failed_msg}; "
                f"age-verify fallback failed: {age_result.get('error')}"
            )
            return age_result

        return name_based

    def enable_nsfw(
        self,
        sso: str,
        sso_rw: str,
        impersonate: str,
        user_agent: Optional[str] = None,
        cf_clearance: Optional[str] = None,
        timeout: int = 15,
    ) -> Dict[str, Any]:
        """
        启用 always_show_nsfw_content。
        返回: {
            ok: bool,
            hex_reply: str,
            status_code: int | None,
            grpc_status: int | None,
            grpc_message: str | None,
            error: str | None
        }
        """
        if not sso:
            return {
                "ok": False,
                "hex_reply": "",
                "status_code": None,
                "grpc_status": None,
                "grpc_message": None,
                "error": "缺少 sso",
            }
        if not sso_rw:
            return {
                "ok": False,
                "hex_reply": "",
                "status_code": None,
                "grpc_status": None,
                "grpc_message": None,
                "error": "缺少 sso-rw",
            }

        preferred_impersonate = str(impersonate or "").strip()
        if not preferred_impersonate:
            preferred_impersonate = str(get_config("grok.wreq_emulation_nsfw", "") or "").strip()
        if not preferred_impersonate:
            preferred_impersonate = "chrome120"

        clearance = (cf_clearance if cf_clearance is not None else self.cf_clearance).strip()
        ua = user_agent or DEFAULT_USER_AGENT

        result = self._enable_chain(
            sso=sso,
            sso_rw=sso_rw,
            impersonate=preferred_impersonate,
            user_agent=ua,
            cf_clearance=clearance,
            timeout=timeout,
        )
        if result.get("ok"):
            return result

        if _should_retry_with_fallback_emulation(result) and not _emulation_equals(
            preferred_impersonate, NSFW_FALLBACK_IMPERSONATE
        ):
            second = self._enable_chain(
                sso=sso,
                sso_rw=sso_rw,
                impersonate=NSFW_FALLBACK_IMPERSONATE,
                user_agent=ua,
                cf_clearance=clearance,
                timeout=timeout,
            )
            if second.get("ok"):
                return second
            second["error"] = (
                f"primary attempt failed: {result.get('error')}; "
                f"fallback attempt failed: {second.get('error')}"
            )
            return second

        return result
