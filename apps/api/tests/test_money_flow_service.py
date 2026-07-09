from datetime import date

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.models import Base
from app.providers.base import MoneyFlowProvider, StockDailyFlow, StockDailyFlowResult
from app.providers.eastmoney import infer_secid
from app.services.money_flow_service import MoneyFlowService, direction_for
from app.utils.errors import InvalidDateRangeError, InvalidSymbolError


class FakeProvider(MoneyFlowProvider):
    source = "eastmoney"

    def __init__(self):
        self.calls = 0

    async def fetch_stock_daily_flow(self, symbol, start_date, end_date):
        self.calls += 1
        return StockDailyFlowResult(
            code=symbol,
            name="测试股票",
            market="sz",
            secid=f"0.{symbol}",
            source=self.source,
            rows=[
                StockDailyFlow(
                    trade_date=date(2026, 7, 8),
                    main_net_inflow=100.0,
                    super_large_inflow=10.0,
                    large_inflow=20.0,
                    medium_inflow=30.0,
                    small_inflow=40.0,
                    close_price=10.0,
                    change_pct=1.0,
                ),
                StockDailyFlow(
                    trade_date=date(2026, 7, 9),
                    main_net_inflow=-50.0,
                    super_large_inflow=-5.0,
                    large_inflow=-10.0,
                    medium_inflow=-15.0,
                    small_inflow=-20.0,
                    close_price=9.8,
                    change_pct=-2.0,
                ),
            ],
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
    assert first.items[0].mainNetInflow == 50.0
    assert second.items[0].daily[1].cumulativeMainNetInflow == 50.0


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
