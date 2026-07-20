from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.providers.factory import create_provider
from app.modules.money_flow.schemas import (
    MoneyFlowRefreshRecentRequest,
    MoneyFlowRefreshRecentResponse,
    MoneyFlowSummaryRequest,
    MoneyFlowSummaryResponse,
)
from app.modules.money_flow.service import MoneyFlowService
from app.utils.errors import (
    AppError,
    InvalidDateRangeError,
    InvalidSourceError,
    InvalidSymbolError,
    NoDataError,
    SourceDateRangeUnsupportedError,
    UpstreamError,
)


router = APIRouter(prefix="/api/money-flow", tags=["money-flow"])


@router.post("/summary", response_model=MoneyFlowSummaryResponse)
async def get_money_flow_summary(
    request: MoneyFlowSummaryRequest, db: Session = Depends(get_db)
) -> MoneyFlowSummaryResponse:
    try:
        service = MoneyFlowService(db, create_provider(request.source))
        return await service.get_summary(request.symbols, request.startDate, request.endDate)
    except InvalidSourceError as exc:
        raise _http_error(400, exc) from exc
    except InvalidSymbolError as exc:
        raise _http_error(400, exc) from exc
    except InvalidDateRangeError as exc:
        raise _http_error(400, exc) from exc
    except NoDataError as exc:
        raise _http_error(404, exc) from exc
    except SourceDateRangeUnsupportedError as exc:
        raise _http_error(400, exc) from exc
    except UpstreamError as exc:
        raise _http_error(502, exc) from exc
    except AppError as exc:
        raise _http_error(400, exc) from exc


@router.post("/refresh-recent", response_model=MoneyFlowRefreshRecentResponse)
async def refresh_recent_money_flow(
    request: MoneyFlowRefreshRecentRequest, db: Session = Depends(get_db)
) -> MoneyFlowRefreshRecentResponse:
    try:
        service = MoneyFlowService(db, create_provider(request.source))
        return await service.refresh_recent(request.symbols)
    except InvalidSourceError as exc:
        raise _http_error(400, exc) from exc
    except UpstreamError as exc:
        raise _http_error(502, exc) from exc
    except AppError as exc:
        raise _http_error(400, exc) from exc


def _http_error(status_code: int, exc: AppError) -> HTTPException:
    return HTTPException(
        status_code=status_code,
        detail={"code": exc.code, "errorCode": exc.error_code, "message": exc.message},
    )
