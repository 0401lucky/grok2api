"""
文件服务 API 路由
"""

import aiofiles.os
from pathlib import Path
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from app.core.logger import logger

router = APIRouter(tags=["Files"])

# 缓存根目录
BASE_DIR = Path(__file__).parent.parent.parent.parent / "data" / "tmp"
IMAGE_DIR = BASE_DIR / "image"
VIDEO_DIR = BASE_DIR / "video"

def _safe_filename(raw: str) -> str:
    name = str(raw or "").strip()
    if not name:
        raise HTTPException(status_code=404, detail="File not found")
    # Disallow path traversal / separators (including Windows backslashes).
    if "/" in name or "\\" in name or ".." in name:
        raise HTTPException(status_code=400, detail="Invalid file name")
    return name


@router.get("/image/{filename:path}")
async def get_image(filename: str):
    """
    获取图片文件
    """
    safe = _safe_filename(filename)
    file_path = IMAGE_DIR / safe
    
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
                    "Cache-Control": "public, max-age=31536000, immutable"
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
    file_path = VIDEO_DIR / safe
    
    if await aiofiles.os.path.exists(file_path):
        if await aiofiles.os.path.isfile(file_path):
            return FileResponse(
                file_path, 
                media_type="video/mp4",
                headers={
                    "Cache-Control": "public, max-age=31536000, immutable"
                }
            )

    logger.warning(f"Video not found: {safe}")
    raise HTTPException(status_code=404, detail="Video not found")
