from datetime import date

import pytest

from app.providers.base import (
    BoardDailyFlow,
    BoardDailyFlowResult,
    BoardSearchResult,
    MoneyFlowProvider,
)
from app.providers.eastmoney import infer_board_secid
from app.services.board_flow_service import BoardFlowService
from app.utils.errors import InvalidBoardError, NoDataError, UpstreamError


class FakeBoardProvider(MoneyFlowProvider):
    source = "eastmoney"

    def __init__(self, rows_by_board=None, failures=None):
        self.rows_by_board = rows_by_board or {}
        self.failures = set(failures or [])
        self.calls = []

    async def fetch_stock_daily_flow(self, symbol, start_date, end_date):
        raise NotImplementedError

    async def search_boards(self, board_type, query, limit):
        boards = [
            BoardSearchResult(
                code="BK0475",
                name="半导体",
                type=board_type,
                market="board",
                secid="90.BK0475",
                source=self.source,
            ),
            BoardSearchResult(
                code="BK0815",
                name="机器人概念",
                type=board_type,
                market="board",
                secid="90.BK0815",
                source=self.source,
            ),
        ]
        keyword = query.strip().upper()
        matched = [
            board
            for board in boards
            if not keyword or keyword in board.code or keyword in board.name.upper()
        ]
        return matched[:limit]

    async def fetch_board_daily_flow(self, board, board_type, start_date, end_date):
        self.calls.append((board, board_type, start_date, end_date))
        if board in self.failures:
            raise UpstreamError("上游失败", board)
        rows = [
            row
            for row in self.rows_by_board.get(board, [])
            if start_date <= row.trade_date <= end_date
        ]
        return BoardDailyFlowResult(
            code=board,
            name=f"{board_type}-{board}",
            type=board_type,
            market="board",
            secid=f"90.{board}",
            source=self.source,
            rows=rows,
        )


def make_flow_row(trade_date, main_net_inflow):
    return BoardDailyFlow(
        trade_date=trade_date,
        main_net_inflow=main_net_inflow,
        super_large_inflow=main_net_inflow * 0.1,
        large_inflow=main_net_inflow * 0.2,
        medium_inflow=main_net_inflow * 0.3,
        small_inflow=main_net_inflow * 0.4,
        close_price=None,
        change_pct=1.0,
    )


def test_infer_board_secid():
    assert infer_board_secid("BK0475") == ("90.BK0475", "BK0475")
    assert infer_board_secid("90.BK0815") == ("90.BK0815", "BK0815")
    with pytest.raises(InvalidBoardError):
        infer_board_secid("300308")


@pytest.mark.asyncio
async def test_search_boards_uses_provider():
    service = BoardFlowService(FakeBoardProvider())

    results = await service.search_boards("industry", "半导体", 20)

    assert [item.code for item in results] == ["BK0475"]
    assert results[0].type == "industry"


@pytest.mark.asyncio
async def test_industry_summary():
    provider = FakeBoardProvider(
        {
            "BK0475": [
                make_flow_row(date(2026, 7, 8), 100.0),
                make_flow_row(date(2026, 7, 9), -30.0),
            ]
        }
    )
    service = BoardFlowService(provider)

    summary = await service.get_summary(["BK0475"], date(2026, 7, 8), date(2026, 7, 9), "industry")

    assert summary.items[0].code == "BK0475"
    assert summary.items[0].mainNetInflow == 70.0
    assert summary.items[0].daily[1].cumulativeMainNetInflow == 70.0
    assert summary.totalDirection == "inflow"


@pytest.mark.asyncio
async def test_concept_summary_with_partial_failure():
    provider = FakeBoardProvider(
        {
            "BK0815": [
                make_flow_row(date(2026, 7, 8), -50.0),
                make_flow_row(date(2026, 7, 9), -25.0),
            ]
        },
        failures={"BK9999"},
    )
    service = BoardFlowService(provider)

    summary = await service.get_summary(
        ["BK0815", "BK9999"], date(2026, 7, 8), date(2026, 7, 9), "concept"
    )

    assert summary.items[0].name == "concept-BK0815"
    assert summary.items[0].direction == "outflow"
    assert summary.totalMainNetInflow == -75.0
    assert summary.errors[0].code == "BK9999"
    assert summary.errors[0].errorCode == "UPSTREAM_FAILED"


@pytest.mark.asyncio
async def test_empty_board_data_raises_no_data():
    service = BoardFlowService(FakeBoardProvider({"BK0475": []}))

    with pytest.raises(NoDataError):
        await service.get_summary(["BK0475"], date(2026, 7, 8), date(2026, 7, 9), "industry")


@pytest.mark.asyncio
async def test_all_upstream_failures_preserve_first_error():
    service = BoardFlowService(FakeBoardProvider(failures={"BK0815"}))

    with pytest.raises(UpstreamError):
        await service.get_summary(["BK0815"], date(2026, 7, 8), date(2026, 7, 9), "concept")
