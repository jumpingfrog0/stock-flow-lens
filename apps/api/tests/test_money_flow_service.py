from datetime import date

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.models import Base
from app.providers.base import MoneyFlowProvider, StockDailyFlow, StockDailyFlowResult
from app.providers.eastmoney import infer_secid
from app.services.cache_service import CacheService
from app.modules.money_flow.service import MoneyFlowService, direction_for
from app.utils.errors import InvalidDateRangeError, InvalidSymbolError


class FakeProvider(MoneyFlowProvider):
    source = "eastmoney"

    def __init__(self, rows=None):
        self.calls = 0
        self.rows = rows or [
            make_flow_row(date(2026, 7, 8), 100.0),
            make_flow_row(date(2026, 7, 9), -50.0),
        ]

    async def fetch_stock_daily_flow(self, symbol, start_date, end_date):
        self.calls += 1
        return StockDailyFlowResult(
            code=symbol,
            name="测试股票",
            market="sz",
            secid=f"0.{symbol}",
            source=self.source,
            rows=[row for row in self.rows if start_date <= row.trade_date <= end_date],
        )

    async def search_boards(self, board_type, query, limit):
        raise NotImplementedError

    async def fetch_board_daily_flow(self, board, board_type, start_date, end_date):
        raise NotImplementedError


def make_flow_row(trade_date, main_net_inflow):
    return StockDailyFlow(
        trade_date=trade_date,
        main_net_inflow=main_net_inflow,
        super_large_inflow=main_net_inflow * 0.1,
        large_inflow=main_net_inflow * 0.2,
        medium_inflow=main_net_inflow * 0.3,
        small_inflow=main_net_inflow * 0.4,
        close_price=10.0,
        change_pct=1.0,
    )


def make_session():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)()


def test_infer_secid():
    assert infer_secid("300308") == ("0.300308", "sz")
    assert infer_secid("603986") == ("1.603986", "sh")
    with pytest.raises(InvalidSymbolError):
        infer_secid("123456")


def test_direction_for():
    assert direction_for(1) == "inflow"
    assert direction_for(-1) == "outflow"
    assert direction_for(0) == "flat"


@pytest.mark.asyncio
async def test_summary_fetches_then_uses_cache():
    db = make_session()
    provider = FakeProvider()
    service = MoneyFlowService(db, provider)

    first = await service.get_summary(["300308"], date(2026, 7, 8), date(2026, 7, 9))
    second = await service.get_summary(["300308"], date(2026, 7, 8), date(2026, 7, 9))

    assert provider.calls == 1
    assert first.source == "eastmoney"
    assert first.items[0].mainNetInflow == 50.0
    assert second.items[0].daily[1].cumulativeMainNetInflow == 50.0


@pytest.mark.asyncio
async def test_partial_cache_fetches_full_requested_range():
    db = make_session()
    provider = FakeProvider(
        [
            make_flow_row(date(2026, 7, 7), 25.0),
            make_flow_row(date(2026, 7, 8), 100.0),
            make_flow_row(date(2026, 7, 9), -50.0),
        ]
    )
    service = MoneyFlowService(db, provider)

    await service.get_summary(["300308"], date(2026, 7, 8), date(2026, 7, 9))
    expanded = await service.get_summary(["300308"], date(2026, 7, 7), date(2026, 7, 9))

    assert provider.calls == 2
    assert expanded.items[0].tradeDays == 3
    assert [row.tradeDate for row in expanded.items[0].daily] == [
        date(2026, 7, 7),
        date(2026, 7, 8),
        date(2026, 7, 9),
    ]


@pytest.mark.asyncio
async def test_invalid_date_range():
    service = MoneyFlowService(make_session(), FakeProvider())
    with pytest.raises(InvalidDateRangeError):
        await service.get_summary(["300308"], date(2026, 7, 9), date(2026, 7, 8))


@pytest.mark.asyncio
async def test_all_failed_symbols_preserve_first_error_type():
    service = MoneyFlowService(make_session(), FakeProvider())
    with pytest.raises(InvalidSymbolError):
        await service.get_summary(["123456"], date(2026, 7, 8), date(2026, 7, 9))


@pytest.mark.asyncio
async def test_complete_akshare_cache_does_not_call_provider():
    db = make_session()
    cached_result = StockDailyFlowResult(
        code="300308",
        name="中际旭创",
        market="sz",
        secid="0.300308",
        source="akshare",
        rows=[
            make_flow_row(date(2026, 7, 8), 100.0),
            make_flow_row(date(2026, 7, 9), -50.0),
        ],
    )
    CacheService(db).upsert_provider_result(cached_result)
    provider = FakeProvider()
    provider.source = "akshare"

    result = await MoneyFlowService(db, provider).get_summary(
        ["300308"], date(2026, 7, 8), date(2026, 7, 9)
    )

    assert provider.calls == 0
    assert result.source == "akshare"
    assert result.items[0].mainNetInflow == 50.0
