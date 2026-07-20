from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.modules.stock_move_attribution.evidence import StockMoveEvidenceProvider
from app.modules.stock_move_attribution.schemas import (
    StockMoveAttributionRequest,
    StockMoveAttributionResponse,
)
from app.modules.stock_move_attribution.service import StockMoveAttributionService
from app.utils.errors import AppError, InvalidSymbolError, NoDataError, StockNotFoundError, UpstreamError


router = APIRouter(prefix="/api/stock-move", tags=["stock-move-attribution"])


@router.post("/attribution", response_model=StockMoveAttributionResponse)
async def analyze_stock_move(
    request: StockMoveAttributionRequest,
    db: Session = Depends(get_db),
) -> StockMoveAttributionResponse:
    try:
        service = StockMoveAttributionService(db, StockMoveEvidenceProvider())
        return await service.analyze(request.symbol)
    except (InvalidSymbolError, StockNotFoundError) as exc:
        raise _http_error(400, exc) from exc
    except NoDataError as exc:
        raise _http_error(404, exc) from exc
    except UpstreamError as exc:
        raise _http_error(502, exc) from exc
    except AppError as exc:
        raise _http_error(400, exc) from exc


def _http_error(status_code: int, exc: AppError) -> HTTPException:
    return HTTPException(
        status_code=status_code,
        detail={"code": exc.code, "errorCode": exc.error_code, "message": exc.message},
    )
