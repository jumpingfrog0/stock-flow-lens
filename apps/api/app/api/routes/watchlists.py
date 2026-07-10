from fastapi import APIRouter, Depends, Response
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.watchlists import (
    WatchlistCreate,
    WatchlistItemCreate,
    WatchlistResponse,
    WatchlistUpdate,
)
from app.services.watchlist_service import WatchlistService
from app.utils.errors import AppError


router = APIRouter(prefix="/api/watchlists", tags=["watchlists"])


@router.get("", response_model=list[WatchlistResponse])
def list_watchlists(db: Session = Depends(get_db)) -> list[WatchlistResponse]:
    return WatchlistService(db).list_watchlists()


@router.post("", response_model=WatchlistResponse)
def create_watchlist(request: WatchlistCreate, db: Session = Depends(get_db)) -> WatchlistResponse:
    return WatchlistService(db).create_watchlist(request.name)


@router.patch("/{watchlist_id}", response_model=WatchlistResponse)
def update_watchlist(
    watchlist_id: int, request: WatchlistUpdate, db: Session = Depends(get_db)
) -> WatchlistResponse:
    try:
        return WatchlistService(db).update_watchlist(watchlist_id, request.name)
    except AppError as exc:
        raise route_error(exc) from exc


@router.delete("/{watchlist_id}", status_code=204)
def delete_watchlist(watchlist_id: int, db: Session = Depends(get_db)) -> Response:
    try:
        WatchlistService(db).delete_watchlist(watchlist_id)
    except AppError as exc:
        raise route_error(exc) from exc
    return Response(status_code=204)


@router.post("/{watchlist_id}/items", response_model=WatchlistResponse)
def add_watchlist_item(
    watchlist_id: int, request: WatchlistItemCreate, db: Session = Depends(get_db)
) -> WatchlistResponse:
    try:
        return WatchlistService(db).add_item(watchlist_id, request.symbol)
    except AppError as exc:
        raise route_error(exc) from exc


@router.delete("/{watchlist_id}/items/{symbol}", response_model=WatchlistResponse)
def delete_watchlist_item(
    watchlist_id: int, symbol: str, db: Session = Depends(get_db)
) -> WatchlistResponse:
    try:
        return WatchlistService(db).delete_item(watchlist_id, symbol)
    except AppError as exc:
        raise route_error(exc) from exc


def route_error(exc: AppError):
    from fastapi import HTTPException

    status_code = 404 if exc.error_code.endswith("NOT_FOUND") else 400
    return HTTPException(
        status_code=status_code,
        detail={"code": exc.code, "errorCode": exc.error_code, "message": exc.message},
    )
