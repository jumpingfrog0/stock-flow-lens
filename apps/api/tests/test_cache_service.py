from datetime import date

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.models import Base, MoneyFlowDaily, Stock
from app.providers.base import StockDailyFlow, StockDailyFlowResult, StockInfo
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


def test_cache_is_isolated_by_source():
    db = make_session()
    service = CacheService(db)
    for source, amount in (("eastmoney", 100.0), ("akshare", 250.0)):
        service.upsert_provider_result(
            StockDailyFlowResult(
                code="300308",
                name="中际旭创",
                market="sz",
                secid="0.300308",
                source=source,
                rows=[
                    StockDailyFlow(
                        trade_date=date(2026, 7, 9),
                        main_net_inflow=amount,
                        super_large_inflow=None,
                        large_inflow=None,
                        medium_inflow=None,
                        small_inflow=None,
                        close_price=10.0,
                        change_pct=1.0,
                    )
                ],
            )
        )

    rows = db.query(MoneyFlowDaily).all()
    eastmoney_rows = service.get_daily_rows(
        "300308", "2026-07-09", "2026-07-09", "eastmoney"
    )
    akshare_rows = service.get_daily_rows(
        "300308", "2026-07-09", "2026-07-09", "akshare"
    )

    assert len(rows) == 2
    assert eastmoney_rows[0].main_net_inflow == 100.0
    assert akshare_rows[0].main_net_inflow == 250.0


def test_placeholder_metadata_does_not_overwrite_existing_stock():
    db = make_session()
    service = CacheService(db)
    service.upsert_stocks(
        [
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

    service.upsert_provider_result(
        StockDailyFlowResult(
            code="300308",
            name="300308",
            market="sz",
            secid="0.300308",
            source="akshare",
            industry=None,
            rows=[
                StockDailyFlow(
                    trade_date=date(2026, 7, 9),
                    main_net_inflow=100.0,
                    super_large_inflow=None,
                    large_inflow=None,
                    medium_inflow=None,
                    small_inflow=None,
                    close_price=10.0,
                    change_pct=1.0,
                )
            ],
        )
    )
    service.upsert_stocks(
        [
            StockInfo(
                code="300308",
                name="中际旭创",
                market="sz",
                secid="0.300308",
                source="akshare",
                industry=None,
            )
        ]
    )

    stock = service.db.get(Stock, "300308")
    assert stock.name == "中际旭创"
    assert stock.industry == "通信设备"
