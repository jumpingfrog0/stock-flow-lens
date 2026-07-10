from typing import Annotated

from fastapi import APIRouter, HTTPException, Query

from app.providers.eastmoney import EastMoneyProvider
from app.schemas.board_flow import (
    BoardFlowSummaryRequest,
    BoardFlowSummaryResponse,
    BoardSearchItem,
    BoardType,
)
from app.services.board_flow_service import BoardFlowService
from app.utils.errors import AppError, InvalidBoardError, InvalidDateRangeError, NoDataError, UpstreamError


boards_router = APIRouter(prefix="/api/boards", tags=["boards"])
board_flow_router = APIRouter(prefix="/api/board-flow", tags=["board-flow"])


@boards_router.get("/search", response_model=list[BoardSearchItem])
async def search_boards(
    type_: Annotated[BoardType, Query(alias="type")],
    q: str = "",
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
) -> list[BoardSearchItem]:
    service = BoardFlowService(EastMoneyProvider())
    try:
        results = await service.search_boards(type_, q, limit)
        return [
            BoardSearchItem(
                code=item.code,
                name=item.name,
                type=item.type,
                market=item.market,
                secid=item.secid,
                source=item.source,
            )
            for item in results
        ]
    except InvalidBoardError as exc:
        raise _http_error(400, exc) from exc
    except UpstreamError as exc:
        raise _http_error(502, exc) from exc


@board_flow_router.post("/summary", response_model=BoardFlowSummaryResponse)
async def get_board_flow_summary(
    request: BoardFlowSummaryRequest,
) -> BoardFlowSummaryResponse:
    if request.source != "eastmoney":
        raise HTTPException(
            status_code=400,
            detail={"errorCode": "INVALID_SOURCE", "message": "1B 仅支持 eastmoney 数据源"},
        )

    service = BoardFlowService(EastMoneyProvider())
    try:
        return await service.get_summary(request.boards, request.startDate, request.endDate, request.type)
    except InvalidBoardError as exc:
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
