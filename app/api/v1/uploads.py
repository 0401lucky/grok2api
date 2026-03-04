"""
Uploads API (used by the web chat UI)
"""

import uuid
from pathlib import Path

import aiofiles
from fastapi import APIRouter, UploadFile, File, HTTPException

from app.core.config import get_config
from app.services.grok.assets import DownloadService


router = APIRouter(tags=["Uploads"])

BASE_DIR = Path(__file__).parent.parent.parent.parent / "data" / "tmp"
IMAGE_DIR = BASE_DIR / "image"
ALLOWED_IMAGE_MIME = {
    "image/jpeg": "jpg",
    "image/jpg": "jpg",
    "image/png": "png",
    "image/webp": "webp",
    "image/gif": "gif",
}


def _ext_from_mime(mime: str) -> str:
    m = (mime or "").lower()
    return ALLOWED_IMAGE_MIME.get(m, "jpg")


def _detect_magic_mime(chunk: bytes) -> str | None:
    if not chunk:
        return None
    if len(chunk) >= 8 and chunk[:8] == b"\x89PNG\r\n\x1a\n":
        return "image/png"
    if len(chunk) >= 3 and chunk[:3] == b"\xFF\xD8\xFF":
        return "image/jpeg"
    if len(chunk) >= 6 and chunk[:6] in (b"GIF87a", b"GIF89a"):
        return "image/gif"
    if len(chunk) >= 12 and chunk[:4] == b"RIFF" and chunk[8:12] == b"WEBP":
        return "image/webp"
    return None


@router.post("/uploads/image")
async def upload_image(file: UploadFile = File(...)):
    content_type = (file.content_type or "").lower()
    if content_type not in ALLOWED_IMAGE_MIME:
        raise HTTPException(status_code=400, detail=f"Unsupported file type: {file.content_type}")

    IMAGE_DIR.mkdir(parents=True, exist_ok=True)
    ext = _ext_from_mime(content_type)
    name = f"upload-{uuid.uuid4().hex}.{ext}"
    path = IMAGE_DIR / name

    try:
        max_mb = int(get_config("app.upload_max_image_mb", 25) or 25)
    except Exception:
        max_mb = 25
    max_mb = max(1, min(100, max_mb))
    max_bytes = max_mb * 1024 * 1024

    size = 0
    first_chunk = True
    try:
        async with aiofiles.open(path, "wb") as f:
            while True:
                chunk = await file.read(1024 * 1024)
                if not chunk:
                    break
                if first_chunk:
                    first_chunk = False
                    magic_mime = _detect_magic_mime(chunk)
                    if not magic_mime:
                        raise HTTPException(status_code=400, detail="Invalid image content")
                    if _ext_from_mime(magic_mime) != ext:
                        raise HTTPException(status_code=400, detail="Image content-type mismatch")
                size += len(chunk)
                if size > max_bytes:
                    raise HTTPException(
                        status_code=413,
                        detail=f"Image file too large. Maximum is {max_mb}MB.",
                    )
                await f.write(chunk)
        if size <= 0:
            raise HTTPException(status_code=400, detail="Empty image file")
    except Exception:
        try:
            if path.exists():
                path.unlink()
        except Exception:
            pass
        raise
    finally:
        try:
            await file.close()
        except Exception:
            pass

    # Best-effort: reuse existing cache cleanup policy (size-based).
    try:
        dl = DownloadService()
        await dl.check_limit()
        await dl.close()
    except Exception:
        pass

    return {"url": f"/v1/files/image/{name}", "name": name, "size_bytes": size}


__all__ = ["router"]

