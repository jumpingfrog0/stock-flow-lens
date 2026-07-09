from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.providers.eastmoney import EastMoneyProvider
from app.schemas.money_flow import MoneyFlowSummaryRequest, MoneyFlowSummaryResponse
from app.services.money_flow_service import MoneyFlowService
from app.utils.errors import AppError, InvalidDateRangeError, InvalidSymbolError, NoDataError, UpstreamError


router = APIRouter(prefix="/api/money-flow", tags=["money-flow"])


@router.post("/summary", response_model=MoneyFlowSummaryResponse)
async def get_money_flow_summary(
    request: MoneyFlowSummaryRequest, db: Session = Depends(get_db)
) -> MoneyFlowSummaryResponse:
    if request.source != "eastmoney":
        raise HTTPException(
            status_code=400,
            detail={"errorCode": "INVALID_SOURCE", "message": "1A 仅支持 eastmoney 数据源"},
        )

    service = MoneyFlowService(db, EastMoneyProvider())
    try:
        return await service.get_summary(request.symbols, request.startDate, request.endDate)
    except InvalidSymbolError as exc:
        raise _http_error(400, exc) from exc
    except InvalidDateRangeError as exc:
        raise _http_error(400, exc) from exc
    except NoDataError as exc:
        raise _http_error(404, exc) from exc
    except UpstreamError as exc:
        raise _http_error(502, exc) from exc


def _http_error(status_code: int, exc: AppError) -> HTTPException:
    return HTTPException(
        status_code=status_code,
        detail={"code": exc.code, "errorCode": exc.error_code, "message": exc.message},
    )
