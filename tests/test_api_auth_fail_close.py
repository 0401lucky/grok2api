import os

from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

from app.core import auth as auth_module


def _build_client() -> TestClient:
    app = FastAPI()

    @app.get("/protected")
    async def protected(_token=Depends(auth_module.verify_api_key)):
        return {"ok": True}

    return TestClient(app)


def test_verify_api_key_fail_close_when_unconfigured(monkeypatch):
    async def _fake_legacy_keys():
        return set()

    monkeypatch.setattr(auth_module, "_load_legacy_api_keys", _fake_legacy_keys)
    monkeypatch.setattr(auth_module, "get_config", lambda key, default=None: "")
    monkeypatch.delenv("ALLOW_ANON_API", raising=False)

    client = _build_client()
    resp = client.get("/protected")
    assert resp.status_code == 401
    assert "not configured" in str(resp.json().get("detail", "")).lower()


def test_verify_api_key_can_allow_bootstrap_with_env(monkeypatch):
    async def _fake_legacy_keys():
        return set()

    monkeypatch.setattr(auth_module, "_load_legacy_api_keys", _fake_legacy_keys)
    monkeypatch.setattr(auth_module, "get_config", lambda key, default=None: "")
    monkeypatch.setenv("ALLOW_ANON_API", "true")

    client = _build_client()
    resp = client.get("/protected")
    assert resp.status_code == 200
    assert resp.json() == {"ok": True}

    # 清理环境变量，避免影响其他测试
    os.environ.pop("ALLOW_ANON_API", None)

