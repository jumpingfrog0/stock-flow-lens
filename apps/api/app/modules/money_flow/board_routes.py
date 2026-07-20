from typing import Annotated

from fastapi import APIRouter, HTTPException, Query

from app.providers.factory import create_provider
from app.modules.money_flow.board_schemas import (
    BoardFlowSummaryRequest,
    BoardFlowSummaryResponse,
    BoardSearchItem,
    BoardType,
)
from app.modules.money_flow.board_service import BoardFlowService
from app.utils.errors import (
    AppError,
    InvalidBoardError,
    InvalidDateRangeError,
    InvalidSourceError,
    NoDataError,
    SourceDateRangeUnsupportedError,
    UpstreamError,
)


boards_router = APIRouter(prefix="/api/boards", tags=["boards"])
board_flow_router = APIRouter(prefix="/api/board-flow", tags=["board-flow"])


@boards_router.get("/search", response_model=list[BoardSearchItem])
async def search_boards(
    type_: Annotated[BoardType, Query(alias="type")],
    q: str = "",
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    source: str = "akshare",
) -> list[BoardSearchItem]:
    try:
        service = BoardFlowService(create_provider(source))
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
    except (InvalidBoardError, InvalidSourceError) as exc:
        raise _http_error(400, exc) from exc
    except UpstreamError as exc:
        raise _http_error(502, exc) from exc


@board_flow_router.post("/summary", response_model=BoardFlowSummaryResponse)
async def get_board_flow_summary(
    request: BoardFlowSummaryRequest,
) -> BoardFlowSummaryResponse:
    try:
        service = BoardFlowService(create_provider(request.source))
        return await service.get_summary(request.boards, request.startDate, request.endDate, request.type)
    except (InvalidBoardError, InvalidSourceError) as exc:
        raise _http_error(400, exc) from exc
    except InvalidDateRangeError as exc:
        raise _http_error(400, exc) from exc
    except NoDataError as exc:
        raise _http_error(404, exc) from exc
    except SourceDateRangeUnsupportedError as exc:
        raise _http_error(400, exc) from exc
    except UpstreamError as exc:
        raise _http_error(502, exc) from exc


def _http_error(status_code: int, exc: AppError) -> HTTPException:
    return HTTPException(
        status_code=status_code,
        detail={"code": exc.code, "errorCode": exc.error_code, "message": exc.message},
    )
