from datetime import date

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.models import Base
from app.db.session import get_db
from app.modules.stock_move_attribution import routes as stock_move_attribution
from app.modules.stock_move_attribution.engine import (
    METHODOLOGY_VERSION,
    _rotation_relevant,
)
from app.modules.stock_move_attribution.evidence import (
    AnnouncementSnapshot,
    IndexSnapshot,
    IndustrySnapshot,
    MarketBreadthSnapshot,
    StockAttributionContext,
    StockSnapshot,
)
from app.modules.stock_move_attribution.service import StockMoveAttributionService


class FakeAttributionProvider:
    source = "eastmoney"

    def __init__(self, context):
        self.context = context

    async def fetch_context(self, symbol):
        assert symbol == "002714"
        return self.context


def make_session():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)()


def make_indexes(*, growth=(-1.21, -4.25), value=(-0.2, 0.2)):
    return [
        IndexSnapshot("shanghai", "上证指数", "market", -0.29),
        IndexSnapshot("shenzhen", "深证成指", "market", -0.97),
        IndexSnapshot("chinext", "创业板指", "growth", growth[0]),
        IndexSnapshot("star50", "科创50", "growth", growth[1]),
        IndexSnapshot("csi300", "沪深300", "value", value[0]),
        IndexSnapshot("sse50", "上证50", "value", value[1]),
    ]


def make_context(*, same_day_announcement=False, industry_change=2.0):
    trade_date = date(2026, 7, 15)
    announcement_date = trade_date if same_day_announcement else date(2026, 7, 11)
    return StockAttributionContext(
        source="eastmoney",
        stock=StockSnapshot(
            code="002714",
            name="牧原股份",
            secid="0.002714",
            trade_date=trade_date,
            industry="养殖业",
            close_price=39.65,
            change_pct=4.12,
            open_price=37.71,
            high_price=40.10,
            low_price=37.68,
            previous_close=38.08,
            amount=3_336_653_065.89,
            turnover_rate=2.58,
            volume_ratio=1.17,
            main_net_inflow=225_774_032.0,
        ),
        indexes=make_indexes(),
        breadth=MarketBreadthSnapshot(total=5000, advancing=3300, declining=1600, flat=100),
        industry=IndustrySnapshot(
            code="BK0001",
            name="养殖业",
            change_pct=industry_change,
            main_net_inflow=680_000_000.0,
            peer_count=20,
            advancing=15,
            declining=4,
            flat=1,
            median_change_pct=1.5,
        ),
        announcements=[
            AnnouncementSnapshot(
                title="牧原股份:2026年半年度业绩预告",
                notice_date=announcement_date,
                art_code="AN1",
            )
        ],
        warnings=[],
    )


@pytest.mark.asyncio
async def test_analysis_identifies_high_to_low_rotation_as_primary_driver():
    service = StockMoveAttributionService(make_session(), FakeAttributionProvider(make_context()))

    result = await service.analyze("002714")

    assert result.primaryDriver == "market_rotation"
    assert result.methodologyVersion == METHODOLOGY_VERSION
    assert result.confidence == "high"
    assert result.style.rotation == "high_to_low"
    assert result.stock.marketRelativePct == pytest.approx(5.09)
    assert result.stock.industryRelativePct == pytest.approx(2.12)
    assert result.drivers[0].code == "market_rotation"
    assert result.counterfactuals[0].result == "supports"
    assert result.counterfactuals[2].result == "weakens"


@pytest.mark.asyncio
async def test_analysis_prefers_stock_specific_when_industry_and_style_do_not_explain_move():
    context = make_context(same_day_announcement=True, industry_change=0.2)
    context = StockAttributionContext(
        source="eastmoney",
        stock=context.stock,
        indexes=make_indexes(growth=(0.2, -0.1), value=(0.1, 0.0)),
        breadth=MarketBreadthSnapshot(total=5000, advancing=2450, declining=2450, flat=100),
        industry=IndustrySnapshot(
            code="BK0001",
            name="养殖业",
            change_pct=0.2,
            main_net_inflow=-10_000_000.0,
            peer_count=20,
            advancing=6,
            declining=13,
            flat=1,
            median_change_pct=-0.4,
        ),
        announcements=context.announcements,
        warnings=[],
    )
    service = StockMoveAttributionService(make_session(), FakeAttributionProvider(context))

    result = await service.analyze("002714")

    assert result.primaryDriver == "stock_specific"
    assert result.drivers[0].code == "stock_specific"
    assert result.counterfactuals[0].result == "weakens"
    assert result.counterfactuals[2].result == "supports"


def test_stock_move_attribution_route(monkeypatch):
    context = make_context()
    monkeypatch.setattr(
        stock_move_attribution,
        "StockMoveEvidenceProvider",
        lambda: FakeAttributionProvider(context),
    )
    db = make_session()
    app = FastAPI()
    app.include_router(stock_move_attribution.router)
    app.dependency_overrides[get_db] = lambda: db
    client = TestClient(app)

    response = client.post("/api/stock-move/attribution", json={"symbol": "002714"})

    assert response.status_code == 200
    assert response.json()["methodologyVersion"] == METHODOLOGY_VERSION
    assert response.json()["primaryDriver"] == "market_rotation"
    assert response.json()["stock"]["name"] == "牧原股份"

    old_response = client.post("/api/stock-analysis/attribution", json={"symbol": "002714"})
    assert old_response.status_code == 404


@pytest.mark.parametrize(
    ("rotation", "style_bucket", "move_positive", "expected"),
    [
        ("high_to_low", "defensive_value", True, True),
        ("high_to_low", "defensive_value", False, False),
        ("high_to_low", "growth", False, True),
        ("low_to_high", "growth", True, True),
        ("low_to_high", "defensive_value", False, True),
        ("balanced", "growth", True, False),
    ],
)
def test_rotation_relevance_uses_style_and_move_direction(
    rotation,
    style_bucket,
    move_positive,
    expected,
):
    assert _rotation_relevant(rotation, style_bucket, move_positive) is expected
