from datetime import UTC, datetime
import re

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.db.models import Stock
from app.providers.base import MoneyFlowProvider, StockInfo
from app.providers.eastmoney import infer_secid
from app.schemas.stocks import StockResponse
from app.services.cache_service import CacheService
from app.utils.errors import AmbiguousSymbolError, InvalidSymbolError, StockNotFoundError


STOCK_CODE_PATTERN = re.compile(r"^\d{6}$")


class StockService:
    def __init__(self, db: Session):
        self.db = db

    def search_local(self, query: str, limit: int = 20) -> list[StockResponse]:
        cleaned = query.strip()
        statement = select(Stock).order_by(Stock.code.asc()).limit(limit)
        if cleaned:
            pattern = f"%{cleaned}%"
            statement = (
                select(Stock)
                .where(or_(Stock.code.like(pattern), Stock.name.like(pattern)))
                .order_by(Stock.code.asc())
                .limit(limit)
            )
        return [stock_to_response(stock) for stock in self.db.scalars(statement).all()]

    async def refresh_from_provider(
        self, provider: MoneyFlowProvider, query: str = "", limit: int = 500
    ) -> int:
        try:
            stocks = await provider.search_stocks(query, limit)
        except NotImplementedError:
            stocks = []
        return CacheService(self.db).upsert_stocks(stocks)

    def resolve_symbol(self, symbol: str) -> str:
        cleaned = symbol.strip()
        if not cleaned:
            raise InvalidSymbolError(symbol)
        if STOCK_CODE_PATTERN.fullmatch(cleaned):
            return cleaned

        exact_matches = list(self.db.scalars(select(Stock).where(Stock.name == cleaned)).all())
        if len(exact_matches) == 1:
            return exact_matches[0].code
        if len(exact_matches) > 1:
            raise AmbiguousSymbolError(cleaned, [_format_match(stock) for stock in exact_matches])

        pattern = f"%{cleaned}%"
        fuzzy_matches = list(
            self.db.scalars(
                select(Stock)
                .where(or_(Stock.name.like(pattern), Stock.code.like(pattern)))
                .order_by(Stock.code.asc())
                .limit(11)
            ).all()
        )
        if len(fuzzy_matches) == 1:
            return fuzzy_matches[0].code
        if len(fuzzy_matches) > 1:
            raise AmbiguousSymbolError(cleaned, [_format_match(stock) for stock in fuzzy_matches])
        raise StockNotFoundError(cleaned)

    def get_or_create_stock_for_symbol(self, symbol: str) -> Stock:
        code = self.resolve_symbol(symbol)
        stock = self.db.get(Stock, code)
        if stock:
            return stock

        secid, market = infer_secid(code)
        stock = Stock(
            code=code,
            name=code,
            market=market,
            secid=secid,
            industry=None,
            updated_at=datetime.now(UTC).isoformat(),
        )
        self.db.add(stock)
        self.db.commit()
        self.db.refresh(stock)
        return stock

    def get_recent_history_symbols(self, limit: int = 50) -> list[str]:
        from app.services.query_history_service import QueryHistoryService

        return QueryHistoryService(self.db).recent_symbols(limit)


def stock_to_response(stock: Stock) -> StockResponse:
    return StockResponse(
        code=stock.code,
        name=stock.name,
        market=stock.market,
        secid=stock.secid,
        industry=stock.industry,
        updatedAt=stock.updated_at,
    )


def stock_info_from_row(stock: Stock) -> StockInfo:
    return StockInfo(
        code=stock.code,
        name=stock.name,
        market=stock.market,
        secid=stock.secid,
        source="local",
        industry=stock.industry,
    )


def _format_match(stock: Stock) -> str:
    return f"{stock.code} {stock.name}"
