import asyncio
import logging

from app.core.config import settings
from app.db.session import create_session
from app.providers.eastmoney import EastMoneyProvider
from app.services.money_flow_service import MoneyFlowService
from app.services.query_history_service import QueryHistoryService
from app.services.watchlist_service import WatchlistService


logger = logging.getLogger(__name__)


class AutoRefreshService:
    def __init__(self):
        self._task: asyncio.Task | None = None

    def start(self) -> None:
        if self._task or not settings.auto_refresh_enabled:
            return
        self._task = asyncio.create_task(self._run())

    async def stop(self) -> None:
        if not self._task:
            return
        self._task.cancel()
        try:
            await self._task
        except asyncio.CancelledError:
            pass
        self._task = None

    async def _run(self) -> None:
        while True:
            await asyncio.sleep(settings.auto_refresh_interval_seconds)
            await self.refresh_once()

    async def refresh_once(self) -> None:
        db = create_session()
        try:
            watchlist_codes = WatchlistService(db).all_item_codes()
            history_codes = QueryHistoryService(db).recent_symbols(settings.auto_refresh_history_limit)
            symbols = _unique([*watchlist_codes, *history_codes])
            if not symbols:
                return
            result = await MoneyFlowService(db, EastMoneyProvider()).refresh_recent(symbols)
            if result.errors:
                logger.warning("auto_refresh_partial_failed errors=%s", len(result.errors))
        except Exception:
            logger.exception("auto_refresh_failed")
        finally:
            db.close()


def _unique(values: list[str]) -> list[str]:
    result: list[str] = []
    for value in values:
        if value not in result:
            result.append(value)
    return result


auto_refresh_service = AutoRefreshService()
