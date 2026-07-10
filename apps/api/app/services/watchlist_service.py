from datetime import UTC, datetime

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.db.models import Stock, Watchlist, WatchlistItem
from app.schemas.watchlists import WatchlistItemResponse, WatchlistResponse
from app.services.stock_service import StockService, stock_to_response
from app.utils.errors import WatchlistNotFoundError


class WatchlistService:
    def __init__(self, db: Session):
        self.db = db
        self.stocks = StockService(db)

    def list_watchlists(self) -> list[WatchlistResponse]:
        rows = self.db.scalars(select(Watchlist).order_by(Watchlist.id.asc())).all()
        return [self._to_response(row) for row in rows]

    def create_watchlist(self, name: str) -> WatchlistResponse:
        now = datetime.now(UTC).isoformat()
        row = Watchlist(name=name.strip(), created_at=now, updated_at=now)
        self.db.add(row)
        self.db.commit()
        self.db.refresh(row)
        return self._to_response(row)

    def update_watchlist(self, watchlist_id: int, name: str) -> WatchlistResponse:
        row = self._get_watchlist(watchlist_id)
        row.name = name.strip()
        row.updated_at = datetime.now(UTC).isoformat()
        self.db.commit()
        self.db.refresh(row)
        return self._to_response(row)

    def delete_watchlist(self, watchlist_id: int) -> None:
        row = self._get_watchlist(watchlist_id)
        self.db.execute(delete(WatchlistItem).where(WatchlistItem.watchlist_id == watchlist_id))
        self.db.delete(row)
        self.db.commit()

    def add_item(self, watchlist_id: int, symbol: str) -> WatchlistResponse:
        watchlist = self._get_watchlist(watchlist_id)
        stock = self.stocks.get_or_create_stock_for_symbol(symbol)
        existing = self.db.scalar(
            select(WatchlistItem).where(
                WatchlistItem.watchlist_id == watchlist_id,
                WatchlistItem.stock_code == stock.code,
            )
        )
        if not existing:
            self.db.add(
                WatchlistItem(
                    watchlist_id=watchlist_id,
                    stock_code=stock.code,
                    created_at=datetime.now(UTC).isoformat(),
                )
            )
            watchlist.updated_at = datetime.now(UTC).isoformat()
            self.db.commit()
            self.db.refresh(watchlist)
        return self._to_response(watchlist)

    def delete_item(self, watchlist_id: int, stock_code: str) -> WatchlistResponse:
        watchlist = self._get_watchlist(watchlist_id)
        code = self.stocks.resolve_symbol(stock_code)
        self.db.execute(
            delete(WatchlistItem).where(
                WatchlistItem.watchlist_id == watchlist_id,
                WatchlistItem.stock_code == code,
            )
        )
        watchlist.updated_at = datetime.now(UTC).isoformat()
        self.db.commit()
        self.db.refresh(watchlist)
        return self._to_response(watchlist)

    def all_item_codes(self) -> list[str]:
        codes: list[str] = []
        for code in self.db.scalars(select(WatchlistItem.stock_code).order_by(WatchlistItem.id.asc())).all():
            if code not in codes:
                codes.append(code)
        return codes

    def _get_watchlist(self, watchlist_id: int) -> Watchlist:
        row = self.db.get(Watchlist, watchlist_id)
        if not row:
            raise WatchlistNotFoundError(watchlist_id)
        return row

    def _to_response(self, watchlist: Watchlist) -> WatchlistResponse:
        items = self.db.scalars(
            select(WatchlistItem)
            .where(WatchlistItem.watchlist_id == watchlist.id)
            .order_by(WatchlistItem.id.asc())
        ).all()
        stock_map = {
            stock.code: stock
            for stock in self.db.scalars(
                select(Stock).where(Stock.code.in_([item.stock_code for item in items]))
            ).all()
        }
        return WatchlistResponse(
            id=watchlist.id,
            name=watchlist.name,
            createdAt=watchlist.created_at,
            updatedAt=watchlist.updated_at,
            items=[
                WatchlistItemResponse(
                    id=item.id,
                    stock=stock_to_response(stock_map[item.stock_code]),
                    createdAt=item.created_at,
                )
                for item in items
                if item.stock_code in stock_map
            ],
        )
