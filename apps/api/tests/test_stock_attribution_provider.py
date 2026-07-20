from datetime import date
from unittest.mock import AsyncMock

import pytest

from app.providers.stock_attribution import (
    StockAttributionProvider,
    _match_board,
    _quote_trade_date,
)


def test_match_board_prefers_exact_name():
    items = [
        {"f12": "BK1", "f14": "水产养殖"},
        {"f12": "BK2", "f14": "养殖业"},
        {"f12": "BK3", "f14": "养殖业Ⅱ"},
    ]

    result = _match_board(items, "养殖业")

    assert result["f12"] == "BK2"


def test_quote_trade_date_uses_shanghai_timezone():
    result = _quote_trade_date({"f86": 1784073600})

    assert result == date(2026, 7, 15)


@pytest.mark.asyncio
async def test_quote_main_flow_is_used_when_daily_flow_endpoint_fails(monkeypatch):
    provider = StockAttributionProvider()
    monkeypatch.setattr(
        provider,
        "_fetch_quote",
        AsyncMock(
            return_value={
                "f43": 39.65,
                "f57": "002714",
                "f58": "牧原股份",
                "f62": 167_000_000,
                "f86": 1784073600,
                "f127": "养殖业",
                "f170": 4.12,
            }
        ),
    )
    monkeypatch.setattr(
        provider,
        "_fetch_latest_flow",
        AsyncMock(side_effect=RuntimeError("upstream unavailable")),
    )
    monkeypatch.setattr(provider, "_fetch_indexes", AsyncMock(return_value=[]))
    monkeypatch.setattr(provider, "_fetch_market_breadth", AsyncMock(return_value=None))
    monkeypatch.setattr(provider, "_fetch_announcements", AsyncMock(return_value=[]))
    monkeypatch.setattr(provider, "_fetch_industry", AsyncMock(return_value=None))

    context = await provider.fetch_context("002714")

    assert context.stock.main_net_inflow == 167_000_000
    assert "当日资金流接口暂不可用" not in context.warnings
