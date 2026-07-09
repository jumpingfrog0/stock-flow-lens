import logging
from datetime import date

from sqlalchemy.orm import Session

from app.providers.base import MoneyFlowProvider
from app.providers.eastmoney import infer_secid
from app.schemas.money_flow import (
    DailyMoneyFlow,
    MoneyFlowError,
    MoneyFlowItem,
    MoneyFlowRange,
    MoneyFlowSummaryResponse,
)
from app.services.cache_service import CacheService
from app.utils.errors import AppError, InvalidDateRangeError, NoDataError


logger = logging.getLogger(__name__)


class MoneyFlowService:
    def __init__(self, db: Session, provider: MoneyFlowProvider):
        self.cache = CacheService(db)
        self.provider = provider

    async def get_summary(
        self, symbols: list[str], start_date: date, end_date: date
    ) -> MoneyFlowSummaryResponse:
        validate_date_range(start_date, end_date)
        items: list[MoneyFlowItem] = []
        errors: list[MoneyFlowError] = []
        app_errors: list[AppError] = []

        for symbol in symbols:
            try:
                item = await self._get_symbol_summary(symbol, start_date, end_date)
                items.append(item)
            except AppError as exc:
                app_errors.append(exc)
                errors.append(
                    MoneyFlowError(code=exc.code or symbol, errorCode=exc.error_code, message=exc.message)
                )

        if not items:
            if app_errors:
                raise app_errors[0]
            raise NoDataError()

        total = sum(item.mainNetInflow for item in items)
        return MoneyFlowSummaryResponse(
            range=MoneyFlowRange(startDate=start_date, endDate=end_date),
            items=items,
            totalMainNetInflow=total,
            totalDirection=direction_for(total),
            totalDirectionAmount=abs(total) if total < 0 else total,
            errors=errors,
        )

    async def _get_symbol_summary(
        self, symbol: str, start_date: date, end_date: date
    ) -> MoneyFlowItem:
        infer_secid(symbol)
        start_key = start_date.isoformat()
        end_key = end_date.isoformat()
        cached_rows = self.cache.get_daily_rows(symbol, start_key, end_key, self.provider.source)
        cache_hit = len(cached_rows) > 0
        logger.info(
            "money_flow_query cache_hit=%s symbol=%s startDate=%s endDate=%s",
            str(cache_hit).lower(),
            symbol,
            start_key,
            end_key,
        )

        if not cache_hit:
            result = await self.provider.fetch_stock_daily_flow(symbol, start_date, end_date)
            self.cache.upsert_provider_result(result)
            cached_rows = self.cache.get_daily_rows(symbol, start_key, end_key, self.provider.source)

        if not cached_rows:
            raise NoDataError(symbol)

        name = self.cache.get_stock_name(symbol)
        total = sum(row.main_net_inflow for row in cached_rows)
        cumulative = 0.0
        daily: list[DailyMoneyFlow] = []
        for row in cached_rows:
            cumulative += row.main_net_inflow
            daily.append(
                DailyMoneyFlow(
                    tradeDate=date.fromisoformat(row.trade_date),
                    mainNetInflow=row.main_net_inflow,
                    superLargeInflow=row.super_large_inflow,
                    largeInflow=row.large_inflow,
                    mediumInflow=row.medium_inflow,
                    smallInflow=row.small_inflow,
                    closePrice=row.close_price,
                    changePct=row.change_pct,
                    cumulativeMainNetInflow=cumulative,
                )
            )

        return MoneyFlowItem(
            code=symbol,
            name=name,
            mainNetInflow=total,
            direction=direction_for(total),
            directionAmount=abs(total) if total < 0 else total,
            tradeDays=len(cached_rows),
            daily=daily,
        )


def validate_date_range(start_date: date, end_date: date) -> None:
    if start_date > end_date:
        raise InvalidDateRangeError("开始日期不能晚于结束日期")
    if (end_date - start_date).days > 366:
        raise InvalidDateRangeError("日期区间不能超过 366 天")


def direction_for(value: float) -> str:
    if value > 0:
        return "inflow"
    if value < 0:
        return "outflow"
    return "flat"
