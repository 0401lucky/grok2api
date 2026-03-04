from pathlib import Path

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.v1 import uploads as uploads_api


def _build_client(monkeypatch, tmp_path: Path) -> TestClient:
    monkeypatch.setattr(uploads_api, "IMAGE_DIR", tmp_path)
    monkeypatch.setattr(uploads_api, "get_config", lambda key, default=None: 1 if key == "app.upload_max_image_mb" else default)
    app = FastAPI()
    app.include_router(uploads_api.router, prefix="/v1")
    return TestClient(app)


def test_upload_image_respects_size_limit(monkeypatch, tmp_path: Path):
    client = _build_client(monkeypatch, tmp_path)

    payload = b"\x89PNG\r\n\x1a\n" + b"x" * (1024 * 1024 + 1)
    resp = client.post(
        "/v1/uploads/image",
        files={"file": ("large.png", payload, "image/png")},
    )

    assert resp.status_code == 413
    assert list(tmp_path.iterdir()) == []


def test_upload_image_small_file_ok(monkeypatch, tmp_path: Path):
    client = _build_client(monkeypatch, tmp_path)

    payload = b"\x89PNG\r\n\x1a\n" + (b"ok" * 1024)
    resp = client.post(
        "/v1/uploads/image",
        files={"file": ("small.png", payload, "image/png")},
    )

    assert resp.status_code == 200
    data = resp.json()
    assert str(data.get("url") or "").startswith("/v1/files/image/upload-")
    assert len(list(tmp_path.iterdir())) == 1
