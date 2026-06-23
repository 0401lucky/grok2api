import tempfile
import unittest
from pathlib import Path

from app.control.account.backends.local import LocalAccountRepository
from app.control.account.commands import AccountUpsert
from app.dataplane.account.selector import select, set_strategy
from app.dataplane.account.sync import apply_changes
from app.dataplane.account.table import AccountRuntimeTable
from app.dataplane.shared.enums import ModeId, PoolId, StatusId


def _append_basic_slot(
    table: AccountRuntimeTable,
    token: str,
    *,
    quota_fast: int = 30,
    health: float = 1.0,
    fail_count: int = 0,
) -> int:
    return table._append_slot(
        token=token,
        pool_id=int(PoolId.BASIC),
        status_id=int(StatusId.ACTIVE),
        quota_auto=-1,
        quota_fast=quota_fast,
        quota_expert=-1,
        quota_heavy=-1,
        quota_grok_4_3=-1,
        quota_console=30,
        total_auto=0,
        total_fast=30,
        total_expert=0,
        total_heavy=0,
        total_grok_4_3=0,
        total_console=30,
        window_auto=0,
        window_fast=86_400,
        window_expert=0,
        window_heavy=0,
        window_grok_4_3=0,
        window_console=900,
        reset_auto=0,
        reset_fast=0,
        reset_expert=0,
        reset_heavy=0,
        reset_grok_4_3=0,
        reset_console=0,
        health=health,
        last_use_s=0,
        last_fail_s=0,
        fail_count=fail_count,
        tags=[],
    )


class AccountIncrementalSyncTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.repo = LocalAccountRepository(Path(self._tmp.name) / "accounts.db")
        await self.repo.initialize()

    async def asyncTearDown(self) -> None:
        await self.repo.close()
        self._tmp.cleanup()

    async def test_local_bulk_upsert_returns_rows_and_preserves_tokens(self) -> None:
        result = await self.repo.upsert_accounts(
            [
                AccountUpsert(token="sso=token-a"),
                AccountUpsert(token="token-b", pool="super"),
                AccountUpsert(token="token-c", pool="heavy"),
            ]
        )

        records = await self.repo.get_accounts(["token-a", "token-b", "token-c"])

        self.assertEqual(result.upserted, 3)
        self.assertEqual({record.token for record in records}, {"token-a", "token-b", "token-c"})
        self.assertEqual({record.pool for record in records}, {"basic", "super", "heavy"})

    async def test_apply_changes_advances_by_batch_revision_without_skipping(self) -> None:
        for token in ("token-one", "token-two", "token-three"):
            await self.repo.upsert_accounts([AccountUpsert(token=token)])

        table = AccountRuntimeTable()
        changed = await apply_changes(table, self.repo, batch_limit=1)

        self.assertTrue(changed)
        self.assertEqual(
            set(table.idx_by_token),
            {"token-one", "token-two", "token-three"},
        )
        self.assertEqual(table.revision, await self.repo.get_revision())


class AccountSelectionPolicyTests(unittest.TestCase):
    def tearDown(self) -> None:
        set_strategy("random")

    def test_quota_strategy_filters_accounts_at_inflight_cap(self) -> None:
        table = AccountRuntimeTable()
        capped = _append_basic_slot(table, "token-capped", quota_fast=30, health=1.0)
        available = _append_basic_slot(
            table, "token-available", quota_fast=1, health=0.1
        )
        table.inflight_by_idx[capped] = 12

        set_strategy("quota")
        selected = select(
            table,
            int(PoolId.BASIC),
            int(ModeId.FAST),
            now_s=1_000,
        )

        self.assertEqual(selected, available)

    def test_random_strategy_filters_high_failure_accounts(self) -> None:
        table = AccountRuntimeTable()
        _append_basic_slot(table, "token-failed", fail_count=5)
        available = _append_basic_slot(table, "token-available", fail_count=0)

        set_strategy("random")
        selected = select(
            table,
            int(PoolId.BASIC),
            int(ModeId.FAST),
            now_s=1_000,
        )

        self.assertEqual(selected, available)
