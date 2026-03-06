from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.v1 import admin as admin_api
from app.core import admin_session as admin_session_module
from app.core import config as config_module


def _mock_get_config(key: str, default=None):
    values = {
        "app.admin_username": "admin",
        "app.app_key": "unit-test-secret",
        "app.app_key_hash": "",
        "app.admin_session_ttl_hours": 8,
    }
    return values.get(key, default)


def _build_client(monkeypatch) -> TestClient:
    monkeypatch.setattr(admin_api, "get_config", _mock_get_config)
    monkeypatch.setattr(admin_session_module, "get_config", _mock_get_config)
    monkeypatch.setattr(config_module, "get_config", _mock_get_config)
    app = FastAPI()
    app.include_router(admin_api.router)
    return TestClient(app)


def test_admin_login_rejects_weak_default_password(monkeypatch):
    def _weak_get_config(key: str, default=None):
        values = {
            "app.admin_username": "admin",
            "app.app_key": "admin",
            "app.app_key_hash": "",
            "app.admin_session_ttl_hours": 8,
        }
        return values.get(key, default)

    monkeypatch.setattr(admin_api, "get_config", _weak_get_config)
    monkeypatch.setattr(admin_session_module, "get_config", _weak_get_config)
    monkeypatch.setattr(config_module, "get_config", _weak_get_config)

    app = FastAPI()
    app.include_router(admin_api.router)
    client = TestClient(app)

    login = client.post(
        "/api/v1/admin/login",
        json={"username": "admin", "password": "admin"},
    )
    assert login.status_code == 503


def test_admin_login_sets_cookie_and_can_access_admin_api(monkeypatch):
    client = _build_client(monkeypatch)

    login = client.post(
        "/api/v1/admin/login",
        json={"username": "admin", "password": "unit-test-secret"},
    )
    assert login.status_code == 200
    assert login.json()["status"] == "success"
    assert login.json()["password_reset_required"] is False
    assert client.cookies.get(admin_session_module.ADMIN_SESSION_COOKIE)

    protected = client.get("/api/v1/admin/storage")
    assert protected.status_code == 200

    fresh = _build_client(monkeypatch)
    unauthorized = fresh.get("/api/v1/admin/storage")
    assert unauthorized.status_code == 401


def test_tampered_admin_session_cookie_is_rejected(monkeypatch):
    client = _build_client(monkeypatch)

    login = client.post(
        "/api/v1/admin/login",
        json={"username": "admin", "password": "unit-test-secret"},
    )
    assert login.status_code == 200
    token = str(client.cookies.get(admin_session_module.ADMIN_SESSION_COOKIE) or "")
    assert token

    tail = token[-1]
    bad_tail = "a" if tail != "a" else "b"
    tampered = token[:-1] + bad_tail
    client.cookies.set(admin_session_module.ADMIN_SESSION_COOKIE, tampered)

    rejected = client.get("/api/v1/admin/storage")
    assert rejected.status_code == 401


def test_admin_logout_revokes_session_cookie(monkeypatch):
    client = _build_client(monkeypatch)

    login = client.post(
        "/api/v1/admin/login",
        json={"username": "admin", "password": "unit-test-secret"},
    )
    assert login.status_code == 200
    assert client.cookies.get(admin_session_module.ADMIN_SESSION_COOKIE)

    logout = client.post("/api/v1/admin/logout")
    assert logout.status_code == 200

    rejected = client.get("/api/v1/admin/storage")
    assert rejected.status_code == 401


def test_admin_config_masks_sensitive_fields(monkeypatch):
    client = _build_client(monkeypatch)
    client.post(
        "/api/v1/admin/login",
        json={"username": "admin", "password": "unit-test-secret"},
    )

    monkeypatch.setattr(
        admin_api.config,
        "_config",
        {
            "app": {"admin_username": "admin", "app_key": "unit-test-secret", "api_key": "sk-live"},
            "grok": {"cf_clearance": "cf-secret", "wreq_emulation_nsfw": "chrome120"},
            "register": {"admin_password": "worker-secret", "yescaptcha_key": "yc-secret"},
        },
        raising=False,
    )

    resp = client.get("/api/v1/admin/config")
    assert resp.status_code == 200
    data = resp.json()
    assert data["app"]["app_key"] == "__KEEP_EXISTING__"
    assert data["app"]["api_key"] == "__KEEP_EXISTING__"
    assert data["grok"]["cf_clearance"] == "__KEEP_EXISTING__"
    assert data["register"]["yescaptcha_key"] == "__KEEP_EXISTING__"


def test_admin_login_rate_limit(monkeypatch):
    client = _build_client(monkeypatch)
    for _ in range(5):
        resp = client.post(
            "/api/v1/admin/login",
            json={"username": "admin", "password": "bad-secret"},
        )
        assert resp.status_code in {401, 429}

    final_resp = client.post(
        "/api/v1/admin/login",
        json={"username": "admin", "password": "bad-secret"},
    )
    assert final_resp.status_code == 429
