from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.providers.stock_attribution import StockAttributionProvider
from app.schemas.stock_analysis import StockMoveAnalysisRequest, StockMoveAnalysisResponse
from app.services.stock_analysis_service import StockAnalysisService
from app.utils.errors import AppError, InvalidSymbolError, NoDataError, StockNotFoundError, UpstreamError


router = APIRouter(prefix="/api/stock-analysis", tags=["stock-analysis"])


@router.post("/attribution", response_model=StockMoveAnalysisResponse)
async def analyze_stock_move(
    request: StockMoveAnalysisRequest,
    db: Session = Depends(get_db),
) -> StockMoveAnalysisResponse:
    try:
        service = StockAnalysisService(db, StockAttributionProvider())
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
