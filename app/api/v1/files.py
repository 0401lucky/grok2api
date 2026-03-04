"""
文件服务 API 路由
"""

import aiofiles.os
import re
from pathlib import Path
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from app.core.logger import logger

router = APIRouter(tags=["Files"])

# 缓存根目录
BASE_DIR = Path(__file__).parent.parent.parent.parent / "data" / "tmp"
IMAGE_DIR = BASE_DIR / "image"
VIDEO_DIR = BASE_DIR / "video"

_SAFE_FILE_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,254}$")
_WINDOWS_RESERVED_NAMES = {
    "con",
    "prn",
    "aux",
    "nul",
    "com1",
    "com2",
    "com3",
    "com4",
    "com5",
    "com6",
    "com7",
    "com8",
    "com9",
    "lpt1",
    "lpt2",
    "lpt3",
    "lpt4",
    "lpt5",
    "lpt6",
    "lpt7",
    "lpt8",
    "lpt9",
}


def _safe_filename(raw: str) -> str:
    name = str(raw or "").strip()
    if not name:
        raise HTTPException(status_code=404, detail="File not found")
    # Reject traversal, separators, control chars, drive letters and ADS-like names.
    if (
        "/" in name
        or "\\" in name
        or ".." in name
        or ":" in name
        or any(ord(ch) < 32 for ch in name)
        or not _SAFE_FILE_RE.fullmatch(name)
    ):
        raise HTTPException(status_code=400, detail="Invalid file name")
    stem = Path(name).stem.lower()
    if stem in _WINDOWS_RESERVED_NAMES:
        raise HTTPException(status_code=400, detail="Invalid file name")
    return name


def _safe_child_path(base_dir: Path, filename: str) -> Path:
    safe = _safe_filename(filename)
    p = (base_dir / safe).resolve()
    try:
        p.relative_to(base_dir.resolve())
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid file path")
    return p


@router.get("/image/{filename:path}")
async def get_image(filename: str):
    """
    获取图片文件
    """
    safe = _safe_filename(filename)
    file_path = _safe_child_path(IMAGE_DIR, safe)
    
    if await aiofiles.os.path.exists(file_path):
        if await aiofiles.os.path.isfile(file_path):
            content_type = "image/jpeg"
            if file_path.suffix.lower() == ".png":
                content_type = "image/png"
            elif file_path.suffix.lower() == ".webp":
                content_type = "image/webp"
            
            # 增加缓存头，支持高并发场景下的浏览器/CDN缓存
            return FileResponse(
                file_path, 
                media_type=content_type,
                headers={
                    "Cache-Control": "public, max-age=31536000, immutable",
                    "X-Content-Type-Options": "nosniff",
                }
            )

    logger.warning(f"Image not found: {safe}")
    raise HTTPException(status_code=404, detail="Image not found")


@router.get("/video/{filename:path}")
async def get_video(filename: str):
    """
    获取视频文件
    """
    safe = _safe_filename(filename)
    file_path = _safe_child_path(VIDEO_DIR, safe)
    
    if await aiofiles.os.path.exists(file_path):
        if await aiofiles.os.path.isfile(file_path):
            return FileResponse(
                file_path, 
                media_type="video/mp4",
                headers={
                    "Cache-Control": "public, max-age=31536000, immutable",
                    "X-Content-Type-Options": "nosniff",
                }
            )

    logger.warning(f"Video not found: {safe}")
    raise HTTPException(status_code=404, detail="Video not found")
