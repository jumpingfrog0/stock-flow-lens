import asyncio
import logging
import math
from collections.abc import Callable
from datetime import date, datetime
from typing import Any

import akshare as ak

from app.core.config import settings
from app.providers.base import (
    BoardDailyFlow,
    BoardDailyFlowResult,
    BoardSearchResult,
    MoneyFlowProvider,
    StockDailyFlow,
    StockDailyFlowResult,
    StockInfo,
)
from app.providers.symbols import infer_board_secid, infer_secid
from app.utils.errors import (
    InvalidBoardError,
    InvalidSymbolError,
    NoDataError,
    SourceDateRangeUnsupportedError,
    UpstreamError,
)


logger = logging.getLogger(__name__)


class AkShareProvider(MoneyFlowProvider):
    source = "akshare"

    async def fetch_stock_daily_flow(
        self, symbol: str, start_date: date, end_date: date
    ) -> StockDailyFlowResult:
        secid, market = infer_secid(symbol)
        flow_frame, info_frame = await asyncio.gather(
            self._call(
                ak.stock_individual_fund_flow,
                "AKShare 个股资金流接口请求失败",
                stock=symbol,
                market=market,
            ),
            self._call(
                ak.stock_individual_info_em,
                "AKShare 个股信息接口请求失败",
                symbol=symbol,
                timeout=settings.akshare_timeout_seconds,
            ),
            return_exceptions=True,
        )

        if isinstance(flow_frame, Exception):
            raise flow_frame
        if isinstance(info_frame, Exception):
            logger.warning(
                "akshare_stock_info_failed symbol=%s error=%s",
                symbol,
                info_frame,
            )
            info_frame = None

        rows = self._parse_stock_rows(flow_frame, symbol)
        self._validate_available_start(rows, start_date, symbol)
        rows = [row for row in rows if start_date <= row.trade_date <= end_date]
        if not rows:
            raise NoDataError(symbol)

        metadata = _item_value_map(info_frame)
        name = str(metadata.get("股票简称") or symbol).strip()
        industry = _optional_text(metadata.get("行业"))
        return StockDailyFlowResult(
            code=symbol,
            name=name,
            market=market,
            secid=secid,
            source=self.source,
            rows=rows,
            industry=industry,
        )

    async def search_stocks(self, query: str = "", limit: int = 500) -> list[StockInfo]:
        frame = await self._call(
            ak.stock_info_a_code_name,
            "AKShare 股票列表接口请求失败",
        )
        records = _records(frame)
        if not records:
            raise UpstreamError("AKShare 股票列表返回为空")

        keyword = query.strip().upper()
        results: list[StockInfo] = []
        for record in records:
            code = str(_value(record, "code", "代码", "股票代码") or "").strip().zfill(6)
            name = str(_value(record, "name", "名称", "股票简称") or "").strip()
            if not code or not name:
                continue
            try:
                secid, market = infer_secid(code)
            except InvalidSymbolError:
                continue
            if keyword and keyword not in code and keyword not in name.upper():
                continue
            results.append(
                StockInfo(
                    code=code,
                    name=name,
                    market=market,
                    secid=secid,
                    source=self.source,
                )
            )
            if len(results) >= limit:
                break
        return results

    async def search_boards(
        self, board_type: str, query: str, limit: int
    ) -> list[BoardSearchResult]:
        frame = await self._fetch_board_list(board_type)
        keyword = query.strip().upper()
        results: list[BoardSearchResult] = []
        for record in _records(frame):
            code = str(_value(record, "板块代码") or "").strip().upper()
            name = str(_value(record, "板块名称") or "").strip()
            if not code or not name:
                continue
            if keyword and keyword not in code and keyword not in name.upper():
                continue
            results.append(
                BoardSearchResult(
                    code=code,
                    name=name,
                    type=board_type,
                    market="board",
                    secid=f"90.{code}",
                    source=self.source,
                )
            )
            if len(results) >= limit:
                break
        return results

    async def fetch_board_daily_flow(
        self, board: str, board_type: str, start_date: date, end_date: date
    ) -> BoardDailyFlowResult:
        secid, code = infer_board_secid(board)
        board_name = await self._resolve_board_name(code, board_type)
        flow_function, price_function, price_period = _board_functions(board_type)
        date_params = {
            "symbol": board_name,
            "start_date": start_date.strftime("%Y%m%d"),
            "end_date": end_date.strftime("%Y%m%d"),
            "period": price_period,
            "adjust": "",
        }
        flow_frame, price_frame = await asyncio.gather(
            self._call(
                flow_function,
                f"AKShare {board_type}板块资金流接口请求失败",
                symbol=board_name,
            ),
            self._call(
                price_function,
                f"AKShare {board_type}板块行情接口请求失败",
                **date_params,
            ),
        )

        flow_records = _records(flow_frame)
        if not flow_records:
            raise NoDataError(code)
        price_records = _records(price_frame)
        if not price_records:
            raise UpstreamError("AKShare 板块行情返回为空", code)

        try:
            prices = {
                _to_date(_value(record, "日期")): record
                for record in price_records
            }
            rows = [self._parse_board_row(record, prices) for record in flow_records]
        except (TypeError, ValueError) as exc:
            raise UpstreamError("AKShare 板块行情字段解析失败", code) from exc
        rows.sort(key=lambda row: row.trade_date)
        self._validate_available_start(rows, start_date, code)
        rows = [row for row in rows if start_date <= row.trade_date <= end_date]
        if not rows:
            raise NoDataError(code)

        return BoardDailyFlowResult(
            code=code,
            name=board_name,
            type=board_type,
            market="board",
            secid=secid,
            source=self.source,
            rows=rows,
        )

    async def _fetch_board_list(self, board_type: str) -> Any:
        if board_type == "industry":
            function = ak.stock_board_industry_name_em
        elif board_type == "concept":
            function = ak.stock_board_concept_name_em
        else:
            raise InvalidBoardError(board_type)
        frame = await self._call(function, f"AKShare {board_type}板块列表接口请求失败")
        if not _records(frame):
            raise UpstreamError("AKShare 板块列表返回为空")
        return frame

    async def _resolve_board_name(self, code: str, board_type: str) -> str:
        frame = await self._fetch_board_list(board_type)
        for record in _records(frame):
            item_code = str(_value(record, "板块代码") or "").strip().upper()
            if item_code == code:
                name = str(_value(record, "板块名称") or "").strip()
                if name:
                    return name
        raise InvalidBoardError(code)

    async def _call(self, function: Callable[..., Any], message: str, **kwargs: Any) -> Any:
        last_error: Exception | None = None
        for attempt in range(3):
            try:
                return await asyncio.wait_for(
                    asyncio.to_thread(function, **kwargs),
                    timeout=settings.akshare_timeout_seconds,
                )
            except Exception as exc:
                last_error = exc
                if attempt < 2:
                    await asyncio.sleep(0.4 * (attempt + 1))
        raise UpstreamError(message) from last_error

    def _parse_stock_rows(self, frame: Any, symbol: str) -> list[StockDailyFlow]:
        records = _records(frame)
        if not records:
            raise NoDataError(symbol)
        try:
            rows = [
                StockDailyFlow(
                    trade_date=_to_date(_value(record, "日期")),
                    main_net_inflow=_required_float(_value(record, "主力净流入-净额")),
                    super_large_inflow=_optional_float(_value(record, "超大单净流入-净额")),
                    large_inflow=_optional_float(_value(record, "大单净流入-净额")),
                    medium_inflow=_optional_float(_value(record, "中单净流入-净额")),
                    small_inflow=_optional_float(_value(record, "小单净流入-净额")),
                    close_price=_optional_float(_value(record, "收盘价")),
                    change_pct=_optional_float(_value(record, "涨跌幅")),
                )
                for record in records
            ]
        except (TypeError, ValueError) as exc:
            raise UpstreamError("AKShare 个股资金流字段解析失败", symbol) from exc
        rows.sort(key=lambda row: row.trade_date)
        return rows

    def _parse_board_row(
        self, record: dict[str, Any], prices: dict[date, dict[str, Any]]
    ) -> BoardDailyFlow:
        try:
            trade_date = _to_date(_value(record, "日期"))
            price = prices.get(trade_date, {})
            return BoardDailyFlow(
                trade_date=trade_date,
                main_net_inflow=_required_float(_value(record, "主力净流入-净额")),
                super_large_inflow=_optional_float(_value(record, "超大单净流入-净额")),
                large_inflow=_optional_float(_value(record, "大单净流入-净额")),
                medium_inflow=_optional_float(_value(record, "中单净流入-净额")),
                small_inflow=_optional_float(_value(record, "小单净流入-净额")),
                close_price=_optional_float(_value(price, "收盘")),
                change_pct=_optional_float(_value(price, "涨跌幅")),
            )
        except (TypeError, ValueError) as exc:
            raise UpstreamError("AKShare 板块资金流字段解析失败") from exc

    def _validate_available_start(
        self,
        rows: list[StockDailyFlow] | list[BoardDailyFlow],
        start_date: date,
        code: str,
    ) -> None:
        if rows and start_date < rows[0].trade_date:
            raise SourceDateRangeUnsupportedError(
                self.source,
                rows[0].trade_date.isoformat(),
                code,
            )


def _board_functions(board_type: str) -> tuple[Callable[..., Any], Callable[..., Any], str]:
    if board_type == "industry":
        return (
            ak.stock_sector_fund_flow_hist,
            ak.stock_board_industry_hist_em,
            "日k",
        )
    if board_type == "concept":
        return (
            ak.stock_concept_fund_flow_hist,
            ak.stock_board_concept_hist_em,
            "daily",
        )
    raise InvalidBoardError(board_type)


def _records(frame: Any) -> list[dict[str, Any]]:
    if frame is None or getattr(frame, "empty", True):
        return []
    return list(frame.to_dict(orient="records"))


def _item_value_map(frame: Any) -> dict[str, Any]:
    return {
        str(_value(record, "item") or "").strip(): _value(record, "value")
        for record in _records(frame)
    }


def _value(record: dict[str, Any], *keys: str) -> Any:
    for key in keys:
        if key in record:
            return record[key]
    return None


def _to_date(value: Any) -> date:
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    return date.fromisoformat(str(value).strip()[:10])


def _optional_float(value: Any) -> float | None:
    if value is None or value == "" or value == "-" or value == "--":
        return None
    result = float(value)
    return result if math.isfinite(result) else None


def _required_float(value: Any) -> float:
    result = _optional_float(value)
    if result is None:
        raise ValueError("required numeric field is empty")
    return result


def _optional_text(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, float) and not math.isfinite(value):
        return None
    text = str(value).strip()
    return text or None
