"""Token 刷新调度器"""

import asyncio
from contextlib import asynccontextmanager
from typing import Optional

from app.core.logger import logger
from app.core.storage import get_storage, StorageError
from app.services.token.manager import get_token_manager


@asynccontextmanager
async def _acquire_refresh_lock(storage, interval_seconds: int):
    """统一使用 storage.acquire_lock 获取分布式/本地锁。"""
    try_timeout = max(1, min(30, int(interval_seconds // 120)))
    try:
        async with storage.acquire_lock("token_refresh", timeout=try_timeout):
            yield True
    except StorageError:
        yield False
    except Exception as e:
        logger.warning(f"Scheduler: lock acquire error - {e}")
        yield False


class TokenRefreshScheduler:
    """Token 自动刷新调度器"""

    def __init__(self, interval_hours: int = 8):
        self.interval_hours = interval_hours
        self.interval_seconds = interval_hours * 3600
        self._task: Optional[asyncio.Task] = None
        self._running = False

    async def _refresh_loop(self):
        """刷新循环"""
        logger.info(f"Scheduler: started (interval: {self.interval_hours}h)")

        while self._running:
            try:
                await asyncio.sleep(self.interval_seconds)
                storage = get_storage()

                async with _acquire_refresh_lock(storage, self.interval_seconds) as got_lock:
                    if not got_lock:
                        logger.info("Scheduler: skipped (lock not acquired)")
                        continue

                    logger.info("Scheduler: starting token refresh...")
                    manager = await get_token_manager()
                    result = await manager.refresh_cooling_tokens()

                    logger.info(
                        f"Scheduler: refresh completed - "
                        f"checked={result['checked']}, "
                        f"refreshed={result['refreshed']}, "
                        f"recovered={result['recovered']}, "
                        f"expired={result['expired']}"
                    )

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Scheduler: refresh error - {e}")

    def start(self):
        """启动调度器"""
        if self._running:
            logger.warning("Scheduler: already running")
            return

        self._running = True
        self._task = asyncio.create_task(self._refresh_loop())
        logger.info("Scheduler: enabled")

    def stop(self):
        """停止调度器"""
        if not self._running:
            return

        self._running = False
        if self._task:
            self._task.cancel()
        logger.info("Scheduler: stopped")


# 全局单例
_scheduler: Optional[TokenRefreshScheduler] = None


def get_scheduler(interval_hours: int = 8) -> TokenRefreshScheduler:
    """获取调度器单例"""
    global _scheduler
    if _scheduler is None:
        _scheduler = TokenRefreshScheduler(interval_hours)
    return _scheduler


__all__ = ["TokenRefreshScheduler", "get_scheduler"]
