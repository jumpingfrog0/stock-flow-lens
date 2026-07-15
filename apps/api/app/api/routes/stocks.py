from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.providers.factory import create_provider
from app.schemas.stocks import StockRefreshRequest, StockRefreshResponse, StockResponse
from app.services.stock_service import StockService
from app.utils.errors import AppError, InvalidSourceError, UpstreamError


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
    try:
        refreshed = await StockService(db).refresh_from_provider(
            create_provider(request.source),
            query=request.query,
            limit=request.limit,
        )
        return StockRefreshResponse(refreshed=refreshed)
    except InvalidSourceError as exc:
        raise _http_error(400, exc) from exc
    except UpstreamError as exc:
        raise _http_error(502, exc) from exc


def _http_error(status_code: int, exc: AppError) -> HTTPException:
    return HTTPException(
        status_code=status_code,
        detail={"code": exc.code, "errorCode": exc.error_code, "message": exc.message},
    )
