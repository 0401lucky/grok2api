import asyncio
from types import SimpleNamespace

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect

from app.api.v1 import admin as admin_api
from app.core import admin_session as admin_session_module


def _mock_get_config(key: str, default=None):
    values = {
        "app.admin_username": "admin",
        "app.app_key": "unit-test-secret",
        "app.admin_session_ttl_hours": 8,
    }
    return values.get(key, default)


def _build_client(monkeypatch: pytest.MonkeyPatch) -> TestClient:
    monkeypatch.setattr(admin_api, "get_config", _mock_get_config)
    monkeypatch.setattr(admin_session_module, "get_config", _mock_get_config)

    app = FastAPI()
    app.include_router(admin_api.router)
    return TestClient(app)


def _ws_headers(token: str) -> dict[str, str]:
    return {
        "Authorization": f"Bearer {token}",
        "Origin": "http://localhost:8000",
    }


def _recv_until(ws, predicate, max_messages: int = 80):
    for _ in range(max_messages):
        msg = ws.receive_json()
        if predicate(msg):
            return msg
    pytest.fail("Did not receive expected websocket message in time")


def test_imagine_ws_rejects_invalid_api_key(monkeypatch: pytest.MonkeyPatch):
    client = _build_client(monkeypatch)
    with pytest.raises(WebSocketDisconnect) as exc:
        with client.websocket_connect(
            "/api/v1/admin/imagine/ws",
            headers=_ws_headers("wrong-key"),
        ):
            pass
    assert exc.value.code == 1008


def test_imagine_ws_ping_pong(monkeypatch: pytest.MonkeyPatch):
    client = _build_client(monkeypatch)
    token = admin_session_module.create_admin_session_token("admin")
    with client.websocket_connect("/api/v1/admin/imagine/ws", headers=_ws_headers(token)) as ws:
        ws.send_json({"type": "ping"})
        msg = ws.receive_json()
    assert msg == {"type": "pong"}


def test_imagine_ws_rejects_untrusted_origin(monkeypatch: pytest.MonkeyPatch):
    client = _build_client(monkeypatch)
    token = admin_session_module.create_admin_session_token("admin")
    headers = _ws_headers(token)
    headers["Origin"] = "https://evil.example.com"
    with pytest.raises(WebSocketDisconnect) as exc:
        with client.websocket_connect("/api/v1/admin/imagine/ws", headers=headers):
            pass
    assert exc.value.code == 1008


def test_imagine_ws_rejects_non_admin_session_token(monkeypatch: pytest.MonkeyPatch):
    client = _build_client(monkeypatch)
    with pytest.raises(WebSocketDisconnect) as exc:
        with client.websocket_connect(
            "/api/v1/admin/imagine/ws",
            headers=_ws_headers("managed-key"),
        ):
            pass
    assert exc.value.code == 1008


def test_imagine_ws_empty_prompt_error(monkeypatch: pytest.MonkeyPatch):
    client = _build_client(monkeypatch)
    token = admin_session_module.create_admin_session_token("admin")
    with client.websocket_connect("/api/v1/admin/imagine/ws", headers=_ws_headers(token)) as ws:
        ws.send_json({"type": "start", "prompt": "   "})
        msg = ws.receive_json()

    assert msg.get("type") == "error"
    assert msg.get("code") == "empty_prompt"


def test_imagine_ws_start_stop_message_flow(monkeypatch: pytest.MonkeyPatch):
    client = _build_client(monkeypatch)

    class _DummyTokenManager:
        def __init__(self):
            self.sync_calls = 0

        async def reload_if_stale(self):
            return None

        def get_token_for_model(self, _model_id: str):
            return "token-demo"

        async def sync_usage(self, *_args, **_kwargs):
            self.sync_calls += 1
            return True

    token_mgr = _DummyTokenManager()

    async def _fake_get_token_manager():
        return token_mgr

    async def _fake_collect_imagine_batch(_token: str, _prompt: str, _aspect_ratio: str):
        await asyncio.sleep(0.01)
        return ["ZmFrZV9pbWFnZQ=="]

    monkeypatch.setattr(admin_api, "get_token_manager", _fake_get_token_manager)
    monkeypatch.setattr(
        admin_api.ModelService,
        "get",
        lambda model_id: SimpleNamespace(model_id=model_id, is_image=True),
    )
    monkeypatch.setattr(admin_api, "_collect_imagine_batch", _fake_collect_imagine_batch)

    token = admin_session_module.create_admin_session_token("admin")
    with client.websocket_connect("/api/v1/admin/imagine/ws", headers=_ws_headers(token)) as ws:
        ws.send_json({"type": "start", "prompt": "a cat", "aspect_ratio": "1:1"})
        running = _recv_until(
            ws,
            lambda m: m.get("type") == "status" and m.get("status") == "running",
        )
        image = _recv_until(ws, lambda m: m.get("type") == "image")

        ws.send_json({"type": "ping"})
        pong = _recv_until(ws, lambda m: m.get("type") == "pong")

        ws.send_json({"type": "stop"})
        stopped = _recv_until(
            ws,
            lambda m: m.get("type") == "status" and m.get("status") == "stopped",
        )

    assert running.get("aspect_ratio") == "1:1"
    assert isinstance(running.get("run_id"), str) and running.get("run_id")
    assert image.get("b64_json") == "ZmFrZV9pbWFnZQ=="
    assert image.get("aspect_ratio") == "1:1"
    assert int(image.get("sequence") or 0) >= 1
    assert pong == {"type": "pong"}
    assert stopped.get("run_id") == running.get("run_id")
    assert token_mgr.sync_calls >= 1


def test_imagine_ws_stop_immediately_remains_healthy(monkeypatch: pytest.MonkeyPatch):
    client = _build_client(monkeypatch)

    class _DummyTokenManager:
        async def reload_if_stale(self):
            return None

        def get_token_for_model(self, _model_id: str):
            return "token-demo"

        async def sync_usage(self, *_args, **_kwargs):
            return True

    token_mgr = _DummyTokenManager()

    async def _fake_get_token_manager():
        return token_mgr

    async def _slow_collect_imagine_batch(_token: str, _prompt: str, _aspect_ratio: str):
        await asyncio.sleep(0.5)
        return ["ZmFrZV9pbWFnZQ=="]

    monkeypatch.setattr(admin_api, "get_token_manager", _fake_get_token_manager)
    monkeypatch.setattr(
        admin_api.ModelService,
        "get",
        lambda model_id: SimpleNamespace(model_id=model_id, is_image=True),
    )
    monkeypatch.setattr(admin_api, "_collect_imagine_batch", _slow_collect_imagine_batch)

    token = admin_session_module.create_admin_session_token("admin")
    with client.websocket_connect("/api/v1/admin/imagine/ws", headers=_ws_headers(token)) as ws:
        ws.send_json({"type": "start", "prompt": "a fox", "aspect_ratio": "1:1"})
        running = _recv_until(
            ws,
            lambda m: m.get("type") == "status" and m.get("status") == "running",
        )

        ws.send_json({"type": "stop"})
        stopped = _recv_until(
            ws,
            lambda m: m.get("type") == "status" and m.get("status") == "stopped",
            max_messages=120,
        )

        ws.send_json({"type": "ping"})
        pong = _recv_until(ws, lambda m: m.get("type") == "pong")

    assert running.get("run_id")
    assert stopped.get("run_id") == running.get("run_id")
    assert pong == {"type": "pong"}
