from datetime import UTC, date, datetime
import json

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import QueryHistory
from app.schemas.query_history import QueryHistoryResponse


class QueryHistoryService:
    def __init__(self, db: Session):
        self.db = db

    def list_recent(self, limit: int = 50) -> list[QueryHistoryResponse]:
        statement = select(QueryHistory).order_by(QueryHistory.created_at.desc()).limit(limit)
        return [history_to_response(row) for row in self.db.scalars(statement).all()]

    def create(
        self, symbols: list[str], start_date: date, end_date: date, source: str = "akshare"
    ) -> QueryHistoryResponse:
        now = datetime.now(UTC).isoformat()
        row = QueryHistory(
            symbols=json.dumps(symbols, ensure_ascii=False),
            start_date=start_date.isoformat(),
            end_date=end_date.isoformat(),
            source=source,
            created_at=now,
        )
        self.db.add(row)
        self.db.commit()
        self.db.refresh(row)
        return history_to_response(row)

    def recent_symbols(self, limit: int = 50) -> list[str]:
        symbols: list[str] = []
        statement = select(QueryHistory).order_by(QueryHistory.created_at.desc()).limit(limit)
        for row in self.db.scalars(statement).all():
            for symbol in _loads_symbols(row.symbols):
                if symbol not in symbols:
                    symbols.append(symbol)
        return symbols

    def recent_symbol_sources(self, limit: int = 50) -> list[tuple[str, str]]:
        pairs: list[tuple[str, str]] = []
        statement = select(QueryHistory).order_by(QueryHistory.created_at.desc()).limit(limit)
        for row in self.db.scalars(statement).all():
            for symbol in _loads_symbols(row.symbols):
                pair = (symbol, row.source)
                if pair not in pairs:
                    pairs.append(pair)
        return pairs


def history_to_response(row: QueryHistory) -> QueryHistoryResponse:
    return QueryHistoryResponse(
        id=row.id,
        symbols=_loads_symbols(row.symbols),
        startDate=date.fromisoformat(row.start_date),
        endDate=date.fromisoformat(row.end_date),
        source=row.source,
        createdAt=row.created_at,
    )


def _loads_symbols(raw: str) -> list[str]:
    try:
        value = json.loads(raw)
    except json.JSONDecodeError:
        return []
    if not isinstance(value, list):
        return []
    return [str(item) for item in value]
