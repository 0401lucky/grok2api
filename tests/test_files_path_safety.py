from pathlib import Path

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.v1 import files as files_api


def _build_client(monkeypatch, tmp_path: Path) -> TestClient:
    image_dir = tmp_path / "image"
    video_dir = tmp_path / "video"
    image_dir.mkdir(parents=True, exist_ok=True)
    video_dir.mkdir(parents=True, exist_ok=True)

    monkeypatch.setattr(files_api, "IMAGE_DIR", image_dir)
    monkeypatch.setattr(files_api, "VIDEO_DIR", video_dir)

    app = FastAPI()
    app.include_router(files_api.router, prefix="/v1/files")
    return TestClient(app)


def test_files_reject_path_traversal_backslash(monkeypatch, tmp_path: Path):
    client = _build_client(monkeypatch, tmp_path)
    # Use percent-encoding for backslashes to mimic an attacker payload.
    resp = client.get("/v1/files/image/%5c..%5c..%5cconfig.toml")
    assert resp.status_code == 400


def test_files_reject_path_traversal_dots(monkeypatch, tmp_path: Path):
    client = _build_client(monkeypatch, tmp_path)
    # NOTE: literal ".." may be normalized by the HTTP client; use encoding to ensure it reaches the app.
    resp = client.get("/v1/files/image/%2e%2e")
    assert resp.status_code == 400


def test_files_can_serve_known_file(monkeypatch, tmp_path: Path):
    client = _build_client(monkeypatch, tmp_path)
    (tmp_path / "image" / "ok.png").write_bytes(b"\x89PNG\r\n\x1a\n")
    resp = client.get("/v1/files/image/ok.png")
    assert resp.status_code == 200
