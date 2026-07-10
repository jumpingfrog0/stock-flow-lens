from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.query_history import QueryHistoryCreate, QueryHistoryResponse
from app.services.query_history_service import QueryHistoryService


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
    return QueryHistoryService(db).create(
        request.symbols,
        request.startDate,
        request.endDate,
        request.source,
    )
