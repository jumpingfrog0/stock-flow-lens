import asyncio
import logging

from app.core.config import settings
from app.db.session import create_session
from app.providers.factory import create_provider
from app.services.money_flow_service import MoneyFlowService
from app.services.query_history_service import QueryHistoryService
from app.services.watchlist_service import WatchlistService
from app.utils.errors import InvalidSourceError


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
            history_pairs = QueryHistoryService(db).recent_symbol_sources(
                settings.auto_refresh_history_limit
            )
            pairs = _unique_pairs(
                [
                    *((code, settings.default_source) for code in watchlist_codes),
                    *history_pairs,
                ]
            )
            if not pairs:
                return
            grouped: dict[str, list[str]] = {}
            for symbol, source in pairs:
                grouped.setdefault(source, []).append(symbol)
            for source, symbols in grouped.items():
                try:
                    provider = create_provider(source)
                except InvalidSourceError:
                    logger.warning("auto_refresh_unknown_source source=%s", source)
                    continue
                result = await MoneyFlowService(db, provider).refresh_recent(symbols)
                if result.errors:
                    logger.warning(
                        "auto_refresh_partial_failed source=%s errors=%s",
                        source,
                        len(result.errors),
                    )
        except Exception:
            logger.exception("auto_refresh_failed")
        finally:
            db.close()


def _unique_pairs(values: list[tuple[str, str]]) -> list[tuple[str, str]]:
    result: list[tuple[str, str]] = []
    for value in values:
        if value not in result:
            result.append(value)
    return result


auto_refresh_service = AutoRefreshService()
