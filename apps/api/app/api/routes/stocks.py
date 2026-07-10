from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.providers.eastmoney import EastMoneyProvider
from app.schemas.stocks import StockRefreshRequest, StockRefreshResponse, StockResponse
from app.services.stock_service import StockService


router = APIRouter(prefix="/api/stocks", tags=["stocks"])


@router.get("/search", response_model=list[StockResponse])
def search_stocks(
    q: str = "",
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
) -> list[StockResponse]:
    return StockService(db).search_local(q, limit)


@router.post("/refresh", response_model=StockRefreshResponse)
async def refresh_stocks(
    request: StockRefreshRequest | None = None, db: Session = Depends(get_db)
) -> StockRefreshResponse:
    request = request or StockRefreshRequest()
    refreshed = await StockService(db).refresh_from_provider(
        EastMoneyProvider(),
        query=request.query,
        limit=request.limit,
    )
    return StockRefreshResponse(refreshed=refreshed)
