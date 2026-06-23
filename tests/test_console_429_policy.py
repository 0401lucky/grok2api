import tempfile
import unittest
from pathlib import Path

from app.control.account.backends.local import LocalAccountRepository
from app.control.account.commands import AccountPatch, AccountUpsert
from app.control.account.enums import AccountStatus, QuotaSource
from app.control.account.models import QuotaWindow
from app.control.account.quota_defaults import normalize_quota_window
from app.control.account.refresh import AccountRefreshService
from app.platform.errors import UpstreamError
from app.platform.runtime.clock import now_ms


class Console429PolicyTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.repo = LocalAccountRepository(Path(self._tmp.name) / "accounts.db")
        await self.repo.initialize()
        await self.repo.upsert_accounts([AccountUpsert(token="token-console")])
        self.service = AccountRefreshService(self.repo)

    async def asyncTearDown(self) -> None:
        await self.repo.close()
        self._tmp.cleanup()

    async def _record(self):
        return (await self.repo.get_accounts(["token-console"]))[0]

    async def test_console_429_expires_only_after_three_windowed_hits(self) -> None:
        exc = UpstreamError("rate limited", status=429)

        await self.service.record_failure_async("token-console", 5, exc)
        first = await self._record()

        self.assertEqual(first.status, AccountStatus.ACTIVE)
        self.assertEqual(first.ext["console_429_count"], 1)
        self.assertEqual(first.quota_set().console.remaining, 0)
        self.assertIsNotNone(first.quota_set().console.reset_at)

        await self.service.record_failure_async("token-console", 5, exc)
        second = await self._record()
        self.assertEqual(second.status, AccountStatus.ACTIVE)
        self.assertEqual(second.ext["console_429_count"], 2)

        await self.service.record_failure_async("token-console", 5, exc)
        third = await self._record()
        self.assertEqual(third.status, AccountStatus.EXPIRED)
        self.assertEqual(third.state_reason, "console_429_threshold_exceeded")
        self.assertEqual(third.ext["console_429_count"], 3)
        self.assertEqual(third.ext["expired_reason"], "console_429_threshold_exceeded")

    async def test_clear_failures_clears_console_429_metadata(self) -> None:
        now = now_ms()
        await self.repo.patch_accounts(
            [
                AccountPatch(
                    token="token-console",
                    status=AccountStatus.EXPIRED,
                    state_reason="console_429_threshold_exceeded",
                    ext_merge={
                        "expired_at": now,
                        "expired_reason": "console_429_threshold_exceeded",
                        "console_429_count": 3,
                        "console_429_last_at": now,
                    },
                )
            ]
        )

        await self.repo.patch_accounts(
            [AccountPatch(token="token-console", clear_failures=True)]
        )
        record = await self._record()

        self.assertEqual(record.status, AccountStatus.ACTIVE)
        self.assertIsNone(record.state_reason)
        self.assertNotIn("console_429_count", record.ext)
        self.assertNotIn("console_429_last_at", record.ext)
        self.assertNotIn("expired_reason", record.ext)

    async def test_recover_console_expired_accounts_restores_healthy_history(self) -> None:
        old_expired_at = now_ms() - 2 * 3600 * 1000
        await self.repo.patch_accounts(
            [
                AccountPatch(
                    token="token-console",
                    status=AccountStatus.EXPIRED,
                    state_reason="console_429_threshold_exceeded",
                    usage_use_delta=6,
                    usage_fail_delta=3,
                    last_fail_at=old_expired_at,
                    last_fail_reason="rate_limited",
                    ext_merge={
                        "expired_at": old_expired_at,
                        "expired_reason": "console_429_threshold_exceeded",
                        "console_429_count": 3,
                        "console_429_last_at": old_expired_at,
                    },
                )
            ]
        )

        recovered = await self.service.recover_console_expired_accounts()
        record = await self._record()

        self.assertEqual(recovered, 1)
        self.assertEqual(record.status, AccountStatus.ACTIVE)
        self.assertIsNone(record.state_reason)
        self.assertEqual(record.usage_fail_count, 0)
        self.assertNotIn("console_429_count", record.ext)
        self.assertNotIn("console_429_last_at", record.ext)

    async def test_reset_expired_console_windows_recovers_stuck_zero_without_reset_at(self) -> None:
        now = now_ms()
        await self.repo.patch_accounts(
            [
                AccountPatch(
                    token="token-console",
                    quota_console={
                        "remaining": 0,
                        "total": 30,
                        "window_seconds": 900,
                        "reset_at": None,
                        "synced_at": now,
                        "source": 2,
                    },
                )
            ]
        )

        reset = await self.service.reset_expired_console_windows()
        record = await self._record()

        self.assertEqual(reset, 1)
        self.assertEqual(record.quota_set().console.remaining, 30)
        self.assertIsNone(record.quota_set().console.reset_at)

    async def test_reset_expired_console_windows_clears_expired_reset_even_with_remaining(self) -> None:
        now = now_ms()
        await self.repo.patch_accounts(
            [
                AccountPatch(
                    token="token-console",
                    quota_console={
                        "remaining": 12,
                        "total": 30,
                        "window_seconds": 900,
                        "reset_at": now - 1,
                        "synced_at": now,
                        "source": 2,
                    },
                )
            ]
        )

        reset = await self.service.reset_expired_console_windows()
        record = await self._record()

        self.assertEqual(reset, 1)
        self.assertEqual(record.quota_set().console.remaining, 30)
        self.assertIsNone(record.quota_set().console.reset_at)


class ConsoleQuotaNormalizationTests(unittest.TestCase):
    def test_normalize_console_quota_clamps_historical_values(self) -> None:
        normalized = normalize_quota_window(
            "basic",
            5,
            QuotaWindow(
                remaining=200,
                total=200,
                window_seconds=86_400,
                reset_at=None,
                synced_at=123,
                source=QuotaSource.ESTIMATED,
            ),
        )

        self.assertIsNotNone(normalized)
        assert normalized is not None
        self.assertEqual(normalized.remaining, 30)
        self.assertEqual(normalized.total, 30)
        self.assertEqual(normalized.window_seconds, 900)
