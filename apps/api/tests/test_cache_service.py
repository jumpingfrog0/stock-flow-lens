from datetime import date

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.models import Base, MoneyFlowDaily
from app.providers.base import StockDailyFlow, StockDailyFlowResult
from app.services.cache_service import CacheService


def make_session():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)()


def test_upsert_does_not_duplicate_rows():
    db = make_session()
    service = CacheService(db)
    result = StockDailyFlowResult(
        code="300308",
        name="中际旭创",
        market="sz",
        secid="0.300308",
        source="eastmoney",
        rows=[
            StockDailyFlow(
                trade_date=date(2026, 7, 9),
                main_net_inflow=100.0,
                super_large_inflow=10.0,
                large_inflow=20.0,
                medium_inflow=30.0,
                small_inflow=40.0,
                close_price=1194.9,
                change_pct=5.9,
            )
        ],
    )

    service.upsert_provider_result(result)
    service.upsert_provider_result(result)

    rows = db.query(MoneyFlowDaily).all()
    assert len(rows) == 1
    assert rows[0].main_net_inflow == 100.0
