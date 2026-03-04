from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.v1 import admin as admin_api
from app.core import admin_session as admin_session_module


def _mock_get_config(key: str, default=None):
    values = {
        "app.admin_username": "admin",
        "app.app_key": "unit-test-secret",
        "app.admin_session_ttl_hours": 8,
    }
    return values.get(key, default)


def _build_client(monkeypatch) -> TestClient:
    monkeypatch.setattr(admin_api, "get_config", _mock_get_config)
    monkeypatch.setattr(admin_session_module, "get_config", _mock_get_config)
    app = FastAPI()
    app.include_router(admin_api.router)
    return TestClient(app)


def test_admin_login_rejects_weak_default_password(monkeypatch):
    def _weak_get_config(key: str, default=None):
        values = {
            "app.admin_username": "admin",
            "app.app_key": "admin",
            "app.admin_session_ttl_hours": 8,
        }
        return values.get(key, default)

    monkeypatch.setattr(admin_api, "get_config", _weak_get_config)
    monkeypatch.setattr(admin_session_module, "get_config", _weak_get_config)

    app = FastAPI()
    app.include_router(admin_api.router)
    client = TestClient(app)

    login = client.post(
        "/api/v1/admin/login",
        json={"username": "admin", "password": "admin"},
    )
    assert login.status_code == 503


def test_admin_login_returns_session_token_and_can_access_admin_api(monkeypatch):
    client = _build_client(monkeypatch)

    login = client.post(
        "/api/v1/admin/login",
        json={"username": "admin", "password": "unit-test-secret"},
    )
    assert login.status_code == 200
    data = login.json()
    token = str(data.get("api_key") or "")
    assert token.startswith("g2a.")

    protected = client.get(
        "/api/v1/admin/storage",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert protected.status_code == 200

    unauthorized = client.get("/api/v1/admin/storage")
    assert unauthorized.status_code == 401


def test_tampered_admin_session_token_is_rejected(monkeypatch):
    client = _build_client(monkeypatch)

    login = client.post(
        "/api/v1/admin/login",
        json={"username": "admin", "password": "unit-test-secret"},
    )
    token = str(login.json().get("api_key") or "")
    assert token

    tail = token[-1]
    bad_tail = "a" if tail != "a" else "b"
    tampered = token[:-1] + bad_tail

    rejected = client.get(
        "/api/v1/admin/storage",
        headers={"Authorization": f"Bearer {tampered}"},
    )
    assert rejected.status_code == 401


def test_admin_logout_revokes_session_token(monkeypatch):
    client = _build_client(monkeypatch)

    login = client.post(
        "/api/v1/admin/login",
        json={"username": "admin", "password": "unit-test-secret"},
    )
    token = str(login.json().get("api_key") or "")
    assert token

    logout = client.post(
        "/api/v1/admin/logout",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert logout.status_code == 200

    rejected = client.get(
        "/api/v1/admin/storage",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert rejected.status_code == 401
