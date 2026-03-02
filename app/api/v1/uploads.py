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


def _ext_from_mime(mime: str) -> str:
    m = (mime or "").lower()
    if m == "image/png":
        return "png"
    if m == "image/webp":
        return "webp"
    if m == "image/gif":
        return "gif"
    if m in ("image/jpeg", "image/jpg"):
        return "jpg"
    return "jpg"


@router.post("/uploads/image")
async def upload_image(file: UploadFile = File(...)):
    content_type = (file.content_type or "").lower()
    if not content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail=f"Unsupported file type: {file.content_type}")

    IMAGE_DIR.mkdir(parents=True, exist_ok=True)
    name = f"upload-{uuid.uuid4().hex}.{_ext_from_mime(content_type)}"
    path = IMAGE_DIR / name

    try:
        max_mb = int(get_config("app.upload_max_image_mb", 25) or 25)
    except Exception:
        max_mb = 25
    max_mb = max(1, min(100, max_mb))
    max_bytes = max_mb * 1024 * 1024

    size = 0
    try:
        async with aiofiles.open(path, "wb") as f:
            while True:
                chunk = await file.read(1024 * 1024)
                if not chunk:
                    break
                size += len(chunk)
                if size > max_bytes:
                    raise HTTPException(
                        status_code=413,
                        detail=f"Image file too large. Maximum is {max_mb}MB.",
                    )
                await f.write(chunk)
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

