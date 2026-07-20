from datetime import date

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from app.db.models import Base, QueryHistory, Stock
from app.providers.base import MoneyFlowProvider, StockDailyFlow, StockDailyFlowResult, StockInfo
from app.services.cache_service import CacheService
from app.modules.money_flow.service import MoneyFlowService
from app.services.query_history_service import QueryHistoryService
from app.services.stock_service import StockService
from app.services.watchlist_service import WatchlistService
from app.utils.errors import AmbiguousSymbolError


class FakeProvider(MoneyFlowProvider):
    source = "eastmoney"

    def __init__(self, rows=None, stocks=None):
        self.calls = 0
        self.search_calls = 0
        self.rows = rows or [make_flow_row(date(2026, 7, 9), 100.0)]
        self.stocks = stocks or []

    async def fetch_stock_daily_flow(self, symbol, start_date, end_date):
        self.calls += 1
        return StockDailyFlowResult(
            code=symbol,
            name="中际旭创",
            market="sz",
            secid=f"0.{symbol}",
            source=self.source,
            rows=[row for row in self.rows if start_date <= row.trade_date <= end_date],
            industry="通信设备",
        )

    async def search_stocks(self, query="", limit=500):
        self.search_calls += 1
        return self.stocks[:limit]


def make_flow_row(trade_date, main_net_inflow):
    return StockDailyFlow(
        trade_date=trade_date,
        main_net_inflow=main_net_inflow,
        super_large_inflow=None,
        large_inflow=None,
        medium_inflow=None,
        small_inflow=None,
        close_price=10.0,
        change_pct=1.0,
    )


def make_session():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)()


def seed_stock(db, code, name, industry=None):
    db.add(
        Stock(
            code=code,
            name=name,
            market="sz" if code.startswith("3") else "sh",
            secid=f"0.{code}",
            industry=industry,
            updated_at="2026-07-09T00:00:00+00:00",
        )
    )
    db.commit()


def test_resolve_symbol_exact_name_before_fuzzy_and_code_direct():
    db = make_session()
    seed_stock(db, "300308", "中际旭创")
    seed_stock(db, "300999", "中际旭创新")
    service = StockService(db)

    assert service.resolve_symbol("300308") == "300308"
    assert service.resolve_symbol("中际旭创") == "300308"
    assert service.resolve_symbol("旭创新") == "300999"


def test_resolve_symbol_ambiguous_fuzzy_match():
    db = make_session()
    seed_stock(db, "300308", "中际旭创")
    seed_stock(db, "300999", "旭创测试")

    with pytest.raises(AmbiguousSymbolError):
        StockService(db).resolve_symbol("旭创")


@pytest.mark.asyncio
async def test_stock_refresh_upserts_provider_results():
    db = make_session()
    provider = FakeProvider(
        stocks=[
            StockInfo(
                code="300308",
                name="中际旭创",
                market="sz",
                secid="0.300308",
                source="eastmoney",
                industry="通信设备",
            )
        ]
    )

    refreshed = await StockService(db).refresh_from_provider(provider)

    stock = db.get(Stock, "300308")
    assert refreshed == 1
    assert provider.search_calls == 1
    assert stock.name == "中际旭创"
    assert stock.industry == "通信设备"


@pytest.mark.asyncio
async def test_summary_resolves_name_and_writes_history():
    db = make_session()
    seed_stock(db, "300308", "中际旭创")

    result = await MoneyFlowService(db, FakeProvider()).get_summary(
        ["中际旭创"], date(2026, 7, 9), date(2026, 7, 9)
    )

    histories = db.scalars(select(QueryHistory)).all()
    assert result.items[0].code == "300308"
    assert len(histories) == 1
    assert QueryHistoryService(db).list_recent()[0].symbols == ["300308"]


def test_watchlists_create_update_items_and_delete():
    db = make_session()
    seed_stock(db, "300308", "中际旭创")
    service = WatchlistService(db)

    created = service.create_watchlist("重点观察")
    with_item = service.add_item(created.id, "中际旭创")
    updated = service.update_watchlist(created.id, "短线观察")
    after_delete_item = service.delete_item(created.id, "300308")
    service.delete_watchlist(created.id)

    assert with_item.items[0].stock.code == "300308"
    assert updated.name == "短线观察"
    assert after_delete_item.items == []
    assert service.list_watchlists() == []


@pytest.mark.asyncio
async def test_refresh_recent_bypasses_cache_and_overwrites_rows():
    db = make_session()
    first_provider = FakeProvider([make_flow_row(date(2026, 7, 9), 100.0)])
    await MoneyFlowService(db, first_provider).get_summary(
        ["300308"], date(2026, 7, 9), date(2026, 7, 9)
    )

    refresh_provider = FakeProvider([make_flow_row(date(2026, 7, 9), 250.0)])
    refresh_result = await MoneyFlowService(db, refresh_provider).refresh_recent(
        ["300308"], end_date=date(2026, 7, 10)
    )
    cached_rows = CacheService(db).get_daily_rows("300308", "2026-07-09", "2026-07-09")

    assert refresh_provider.calls == 1
    assert refresh_result.items[0].refreshedRows == 1
    assert cached_rows[0].main_net_inflow == 250.0
