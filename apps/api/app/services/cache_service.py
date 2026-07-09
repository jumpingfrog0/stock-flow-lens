from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.dialects.sqlite import insert
from sqlalchemy.orm import Session

from app.db.models import MoneyFlowDaily, Stock
from app.providers.base import StockDailyFlowResult


class CacheService:
    def __init__(self, db: Session):
        self.db = db

    def get_daily_rows(
        self, symbol: str, start_date: str, end_date: str, source: str = "eastmoney"
    ) -> list[MoneyFlowDaily]:
        statement = (
            select(MoneyFlowDaily)
            .where(
                MoneyFlowDaily.stock_code == symbol,
                MoneyFlowDaily.source == source,
                MoneyFlowDaily.trade_date >= start_date,
                MoneyFlowDaily.trade_date <= end_date,
            )
            .order_by(MoneyFlowDaily.trade_date.asc())
        )
        return list(self.db.scalars(statement).all())

    def get_stock_name(self, symbol: str) -> str:
        stock = self.db.get(Stock, symbol)
        return stock.name if stock else symbol

    def upsert_provider_result(self, result: StockDailyFlowResult) -> None:
        now = datetime.now(UTC).isoformat()
        self._upsert_stock(result, now)
        for row in result.rows:
            payload = {
                "stock_code": result.code,
                "trade_date": row.trade_date.isoformat(),
                "main_net_inflow": row.main_net_inflow,
                "super_large_inflow": row.super_large_inflow,
                "large_inflow": row.large_inflow,
                "medium_inflow": row.medium_inflow,
                "small_inflow": row.small_inflow,
                "close_price": row.close_price,
                "change_pct": row.change_pct,
                "source": result.source,
                "created_at": now,
                "updated_at": now,
            }
            statement = insert(MoneyFlowDaily).values(**payload)
            update_payload = payload.copy()
            update_payload.pop("created_at")
            statement = statement.on_conflict_do_update(
                index_elements=["stock_code", "trade_date", "source"],
                set_=update_payload,
            )
            self.db.execute(statement)
        self.db.commit()

    def _upsert_stock(self, result: StockDailyFlowResult, now: str) -> None:
        statement = insert(Stock).values(
            code=result.code,
            name=result.name,
            market=result.market,
            secid=result.secid,
            updated_at=now,
        )
        statement = statement.on_conflict_do_update(
            index_elements=["code"],
            set_={
                "name": result.name,
                "market": result.market,
                "secid": result.secid,
                "updated_at": now,
            },
        )
        self.db.execute(statement)
