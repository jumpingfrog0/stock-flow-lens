from datetime import date

from app.providers.base import BoardSearchResult, MoneyFlowProvider
from app.schemas.board_flow import BoardFlowSummaryResponse
from app.schemas.money_flow import (
    DailyMoneyFlow,
    MoneyFlowError,
    MoneyFlowItem,
    MoneyFlowRange,
)
from app.services.money_flow_service import direction_for, validate_date_range
from app.utils.errors import AppError, NoDataError


class BoardFlowService:
    def __init__(self, provider: MoneyFlowProvider):
        self.provider = provider

    async def search_boards(
        self, board_type: str, query: str, limit: int
    ) -> list[BoardSearchResult]:
        return await self.provider.search_boards(board_type, query, limit)

    async def get_summary(
        self, boards: list[str], start_date: date, end_date: date, board_type: str
    ) -> BoardFlowSummaryResponse:
        validate_date_range(start_date, end_date)
        items: list[MoneyFlowItem] = []
        errors: list[MoneyFlowError] = []
        app_errors: list[AppError] = []

        for board in boards:
            try:
                items.append(await self._get_board_summary(board, board_type, start_date, end_date))
            except AppError as exc:
                app_errors.append(exc)
                errors.append(
                    MoneyFlowError(code=exc.code or board, errorCode=exc.error_code, message=exc.message)
                )

        if not items:
            if app_errors:
                raise app_errors[0]
            raise NoDataError()

        total = sum(item.mainNetInflow for item in items)
        return BoardFlowSummaryResponse(
            range=MoneyFlowRange(startDate=start_date, endDate=end_date),
            items=items,
            totalMainNetInflow=total,
            totalDirection=direction_for(total),
            totalDirectionAmount=abs(total) if total < 0 else total,
            errors=errors,
        )

    async def _get_board_summary(
        self, board: str, board_type: str, start_date: date, end_date: date
    ) -> MoneyFlowItem:
        result = await self.provider.fetch_board_daily_flow(board, board_type, start_date, end_date)
        if not result.rows:
            raise NoDataError(board)

        total = sum(row.main_net_inflow for row in result.rows)
        cumulative = 0.0
        daily: list[DailyMoneyFlow] = []
        for row in result.rows:
            cumulative += row.main_net_inflow
            daily.append(
                DailyMoneyFlow(
                    tradeDate=row.trade_date,
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
            code=result.code,
            name=result.name,
            mainNetInflow=total,
            direction=direction_for(total),
            directionAmount=abs(total) if total < 0 else total,
            tradeDays=len(result.rows),
            daily=daily,
        )
