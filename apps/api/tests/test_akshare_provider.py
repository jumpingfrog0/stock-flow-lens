from datetime import date

import pandas as pd
import pytest

from app.providers import akshare as akshare_module
from app.providers.akshare import AkShareProvider
from app.providers.factory import create_provider
from app.schemas.board_flow import BoardFlowSummaryRequest
from app.schemas.money_flow import MoneyFlowSummaryRequest
from app.schemas.stocks import StockRefreshRequest
from app.utils.errors import (
    InvalidSourceError,
    SourceDateRangeUnsupportedError,
    UpstreamError,
)


def stock_flow_frame() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "日期": date(2026, 7, 8),
                "收盘价": 100.5,
                "涨跌幅": 1.2,
                "主力净流入-净额": 100.0,
                "超大单净流入-净额": 10.0,
                "大单净流入-净额": 20.0,
                "中单净流入-净额": 30.0,
                "小单净流入-净额": 40.0,
            },
            {
                "日期": date(2026, 7, 9),
                "收盘价": 101.0,
                "涨跌幅": float("nan"),
                "主力净流入-净额": -50.0,
                "超大单净流入-净额": float("nan"),
                "大单净流入-净额": -20.0,
                "中单净流入-净额": -30.0,
                "小单净流入-净额": 100.0,
            },
        ]
    )


def info_frame() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {"item": "股票简称", "value": "中际旭创"},
            {"item": "行业", "value": "通信设备"},
        ]
    )


@pytest.mark.asyncio
async def test_stock_flow_maps_fields_and_metadata(monkeypatch):
    monkeypatch.setattr(
        akshare_module.ak,
        "stock_individual_fund_flow",
        lambda **kwargs: stock_flow_frame(),
    )
    monkeypatch.setattr(
        akshare_module.ak,
        "stock_individual_info_em",
        lambda **kwargs: info_frame(),
    )

    result = await AkShareProvider().fetch_stock_daily_flow(
        "300308", date(2026, 7, 8), date(2026, 7, 9)
    )

    assert result.source == "akshare"
    assert result.market == "sz"
    assert result.name == "中际旭创"
    assert result.industry == "通信设备"
    assert result.rows[0].main_net_inflow == 100.0
    assert result.rows[1].super_large_inflow is None
    assert result.rows[1].change_pct is None


@pytest.mark.asyncio
async def test_stock_flow_succeeds_when_optional_info_fails(monkeypatch):
    provider = AkShareProvider()

    async def fake_call(function, message, **kwargs):
        if "个股信息" in message:
            raise UpstreamError("AKShare 个股信息接口请求失败")
        return stock_flow_frame()

    monkeypatch.setattr(provider, "_call", fake_call)

    result = await provider.fetch_stock_daily_flow(
        "300308", date(2026, 7, 8), date(2026, 7, 9)
    )

    assert result.name == "300308"
    assert result.industry is None
    assert len(result.rows) == 2


@pytest.mark.asyncio
async def test_stock_flow_error_takes_priority_when_both_calls_fail(monkeypatch):
    provider = AkShareProvider()

    async def fake_call(function, message, **kwargs):
        raise UpstreamError(message)

    monkeypatch.setattr(provider, "_call", fake_call)

    with pytest.raises(UpstreamError) as exc_info:
        await provider.fetch_stock_daily_flow(
            "300308", date(2026, 7, 8), date(2026, 7, 9)
        )

    assert exc_info.value.message == "AKShare 个股资金流接口请求失败"


@pytest.mark.asyncio
async def test_stock_flow_rejects_date_before_available_start(monkeypatch):
    monkeypatch.setattr(
        akshare_module.ak,
        "stock_individual_fund_flow",
        lambda **kwargs: stock_flow_frame(),
    )
    monkeypatch.setattr(
        akshare_module.ak,
        "stock_individual_info_em",
        lambda **kwargs: info_frame(),
    )

    with pytest.raises(SourceDateRangeUnsupportedError) as exc_info:
        await AkShareProvider().fetch_stock_daily_flow(
            "300308", date(2026, 7, 7), date(2026, 7, 9)
        )

    assert "2026-07-08" in exc_info.value.message


@pytest.mark.asyncio
async def test_stock_search_filters_unsupported_markets(monkeypatch):
    frame = pd.DataFrame(
        [
            {"code": "300308", "name": "中际旭创"},
            {"code": "603986", "name": "兆易创新"},
            {"code": "430047", "name": "诺思兰德"},
        ]
    )
    monkeypatch.setattr(
        akshare_module.ak,
        "stock_info_a_code_name",
        lambda: frame,
    )

    results = await AkShareProvider().search_stocks("创", limit=10)

    assert [(item.code, item.market) for item in results] == [
        ("300308", "sz"),
        ("603986", "sh"),
    ]


@pytest.mark.asyncio
async def test_board_search_and_flow_merge_price_history(monkeypatch):
    board_list = pd.DataFrame(
        [{"板块代码": "BK0475", "板块名称": "半导体"}]
    )
    flow = pd.DataFrame(
        [
            {
                "日期": date(2026, 7, 8),
                "主力净流入-净额": 100.0,
                "超大单净流入-净额": 10.0,
                "大单净流入-净额": 20.0,
                "中单净流入-净额": 30.0,
                "小单净流入-净额": 40.0,
            },
            {
                "日期": date(2026, 7, 9),
                "主力净流入-净额": -20.0,
                "超大单净流入-净额": -2.0,
                "大单净流入-净额": -4.0,
                "中单净流入-净额": -6.0,
                "小单净流入-净额": 12.0,
            },
        ]
    )
    prices = pd.DataFrame(
        [
            {"日期": date(2026, 7, 8), "收盘": 1200.0, "涨跌幅": 1.5},
        ]
    )
    monkeypatch.setattr(
        akshare_module.ak,
        "stock_board_industry_name_em",
        lambda: board_list,
    )
    monkeypatch.setattr(
        akshare_module.ak,
        "stock_sector_fund_flow_hist",
        lambda **kwargs: flow,
    )
    monkeypatch.setattr(
        akshare_module.ak,
        "stock_board_industry_hist_em",
        lambda **kwargs: prices,
    )

    provider = AkShareProvider()
    search_results = await provider.search_boards("industry", "半导体", 10)
    result = await provider.fetch_board_daily_flow(
        "BK0475", "industry", date(2026, 7, 8), date(2026, 7, 9)
    )

    assert search_results[0].source == "akshare"
    assert result.name == "半导体"
    assert result.rows[0].close_price == 1200.0
    assert result.rows[0].change_pct == 1.5
    assert result.rows[1].close_price is None
    assert result.rows[1].change_pct is None


def test_akshare_is_default_and_factory_rejects_unknown_source():
    summary = MoneyFlowSummaryRequest(
        symbols=["300308"],
        startDate=date(2026, 7, 8),
        endDate=date(2026, 7, 9),
    )
    board = BoardFlowSummaryRequest(
        boards=["BK0475"],
        startDate=date(2026, 7, 8),
        endDate=date(2026, 7, 9),
        type="industry",
    )

    assert summary.source == "akshare"
    assert board.source == "akshare"
    assert StockRefreshRequest().source == "akshare"
    assert create_provider("akshare").source == "akshare"
    assert create_provider("eastmoney").source == "eastmoney"
    with pytest.raises(InvalidSourceError):
        create_provider("unknown")
