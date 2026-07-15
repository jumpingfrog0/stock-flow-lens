from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.providers.factory import validate_source
from app.schemas.query_history import QueryHistoryCreate, QueryHistoryResponse
from app.services.query_history_service import QueryHistoryService
from app.utils.errors import AppError, InvalidSourceError


router = APIRouter(prefix="/api/query-history", tags=["query-history"])


@router.get("", response_model=list[QueryHistoryResponse])
def list_query_history(
    limit: int = Query(default=50, ge=1, le=200), db: Session = Depends(get_db)
) -> list[QueryHistoryResponse]:
    return QueryHistoryService(db).list_recent(limit)


@router.post("", response_model=QueryHistoryResponse)
def create_query_history(
    request: QueryHistoryCreate, db: Session = Depends(get_db)
) -> QueryHistoryResponse:
    try:
        validate_source(request.source)
    except InvalidSourceError as exc:
        raise _http_error(400, exc) from exc
    return QueryHistoryService(db).create(
        request.symbols,
        request.startDate,
        request.endDate,
        request.source,
    )


def _http_error(status_code: int, exc: AppError) -> HTTPException:
    return HTTPException(
        status_code=status_code,
        detail={"code": exc.code, "errorCode": exc.error_code, "message": exc.message},
    )
