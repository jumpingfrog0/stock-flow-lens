from datetime import date

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.modules.money_flow import board_routes as board_flow
from app.providers.base import (
    BoardDailyFlow,
    BoardDailyFlowResult,
    BoardSearchResult,
    MoneyFlowProvider,
)
from app.utils.errors import InvalidSourceError


class FakeRouteBoardProvider(MoneyFlowProvider):
    def __init__(self, source="eastmoney"):
        self.source = source

    async def fetch_stock_daily_flow(self, symbol, start_date, end_date):
        raise NotImplementedError

    async def search_boards(self, board_type, query, limit):
        return [
            BoardSearchResult(
                code="BK0475",
                name="半导体",
                type=board_type,
                market="board",
                secid="90.BK0475",
                source=self.source,
            )
        ][:limit]

    async def fetch_board_daily_flow(self, board, board_type, start_date, end_date):
        return BoardDailyFlowResult(
            code=board,
            name="半导体",
            type=board_type,
            market="board",
            secid=f"90.{board}",
            source=self.source,
            rows=[
                BoardDailyFlow(
                    trade_date=date(2026, 7, 9),
                    main_net_inflow=100.0,
                    super_large_inflow=10.0,
                    large_inflow=20.0,
                    medium_inflow=30.0,
                    small_inflow=40.0,
                    close_price=None,
                    change_pct=1.0,
                )
            ],
        )


def make_client(monkeypatch):
    def fake_factory(source):
        if source not in {"akshare", "eastmoney"}:
            raise InvalidSourceError(source)
        return FakeRouteBoardProvider(source)

    monkeypatch.setattr(
        board_flow,
        "create_provider",
        fake_factory,
    )
    app = FastAPI()
    app.include_router(board_flow.boards_router)
    app.include_router(board_flow.board_flow_router)
    return TestClient(app)


def test_search_boards_route(monkeypatch):
    client = make_client(monkeypatch)

    response = client.get("/api/boards/search", params={"type": "industry", "q": "半导体"})

    assert response.status_code == 200
    assert response.json()[0]["code"] == "BK0475"
    assert response.json()[0]["source"] == "akshare"


def test_board_flow_summary_route(monkeypatch):
    client = make_client(monkeypatch)

    response = client.post(
        "/api/board-flow/summary",
        json={
            "boards": ["BK0475"],
            "startDate": "2026-07-09",
            "endDate": "2026-07-09",
            "type": "industry",
            "source": "eastmoney",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["items"][0]["mainNetInflow"] == 100.0
    assert body["totalDirection"] == "inflow"
    assert body["source"] == "eastmoney"


def test_board_flow_rejects_invalid_source(monkeypatch):
    client = make_client(monkeypatch)

    response = client.post(
        "/api/board-flow/summary",
        json={
            "boards": ["BK0475"],
            "startDate": "2026-07-09",
            "endDate": "2026-07-09",
            "type": "industry",
            "source": "unknown",
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"]["errorCode"] == "INVALID_SOURCE"
