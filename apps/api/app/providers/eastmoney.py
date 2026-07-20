import asyncio
from datetime import date

import httpx

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
from app.utils.errors import InvalidBoardError, NoDataError, UpstreamError


EASTMONEY_FLOW_URL = "https://push2his.eastmoney.com/api/qt/stock/fflow/daykline/get"
EASTMONEY_DELAY_FLOW_URL = (
    "https://push2delay.eastmoney.com/api/qt/stock/fflow/daykline/get"
)
EASTMONEY_BOARD_LIST_URL = "https://push2.eastmoney.com/api/qt/clist/get"
EASTMONEY_DELAY_BOARD_LIST_URL = "https://push2delay.eastmoney.com/api/qt/clist/get"
EASTMONEY_FALLBACK_URLS = {
    EASTMONEY_FLOW_URL: EASTMONEY_DELAY_FLOW_URL,
    EASTMONEY_BOARD_LIST_URL: EASTMONEY_DELAY_BOARD_LIST_URL,
}
BOARD_TYPE_FS = {
    "industry": "m:90+t:2",
    "concept": "m:90+t:3",
}


class EastMoneyProvider(MoneyFlowProvider):
    source = "eastmoney"

    async def fetch_stock_daily_flow(
        self, symbol: str, start_date: date, end_date: date
    ) -> StockDailyFlowResult:
        secid, market = infer_secid(symbol)
        params = {
            "secid": secid,
            "lmt": "0",
            "klt": "101",
            "fields1": "f1,f2,f3,f7",
            "fields2": "f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61,f62,f63",
        }
        headers = {
            "User-Agent": "Mozilla/5.0",
            "Referer": "https://quote.eastmoney.com/",
        }

        try:
            payload = await _get_json_with_retry(EASTMONEY_FLOW_URL, params, headers)
        except (httpx.HTTPError, ValueError) as exc:
            raise UpstreamError("东方财富接口请求失败", symbol) from exc

        data = payload.get("data")
        if not data:
            raise NoDataError(symbol)

        klines = data.get("klines") or []
        rows = [
            row
            for row in (_parse_kline(kline) for kline in klines)
            if start_date <= row.trade_date <= end_date
        ]
        if not rows:
            raise NoDataError(symbol)

        return StockDailyFlowResult(
            code=str(data.get("code") or symbol),
            name=str(data.get("name") or symbol),
            market=market,
            secid=secid,
            source=self.source,
            rows=rows,
        )

    async def search_stocks(self, query: str = "", limit: int = 500) -> list[StockInfo]:
        return []

    async def search_boards(
        self, board_type: str, query: str, limit: int
    ) -> list[BoardSearchResult]:
        fs = _board_fs(board_type)
        params = {
            "pn": "1",
            "pz": "500",
            "po": "1",
            "np": "1",
            "ut": "bd1d9ddb04089700cf9c27f6f7426281",
            "fltt": "2",
            "invt": "2",
            "fid": "f62",
            "fs": fs,
            "fields": "f12,f14",
        }
        headers = {
            "User-Agent": "Mozilla/5.0",
            "Referer": "https://quote.eastmoney.com/",
        }

        try:
            payload = await _get_json_with_retry(EASTMONEY_BOARD_LIST_URL, params, headers)
        except (httpx.HTTPError, ValueError) as exc:
            raise UpstreamError("东方财富板块搜索失败") from exc

        diff = (payload.get("data") or {}).get("diff")
        if diff is None:
            raise UpstreamError("东方财富板块搜索字段异常")

        keyword = query.strip().upper()
        results: list[BoardSearchResult] = []
        for item in diff:
            code = str(item.get("f12") or "").strip().upper()
            name = str(item.get("f14") or "").strip()
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
        _board_fs(board_type)
        secid, code = infer_board_secid(board)
        params = {
            "secid": secid,
            "lmt": "0",
            "klt": "101",
            "fields1": "f1,f2,f3,f7",
            "fields2": "f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61,f62,f63",
        }
        headers = {
            "User-Agent": "Mozilla/5.0",
            "Referer": "https://quote.eastmoney.com/",
        }

        try:
            payload = await _get_json_with_retry(EASTMONEY_FLOW_URL, params, headers)
        except (httpx.HTTPError, ValueError) as exc:
            raise UpstreamError("东方财富板块资金流接口请求失败", code) from exc

        data = payload.get("data")
        if not data:
            raise NoDataError(code)

        klines = data.get("klines") or []
        rows = [
            row
            for row in (_parse_board_kline(kline) for kline in klines)
            if start_date <= row.trade_date <= end_date
        ]
        if not rows:
            raise NoDataError(code)

        return BoardDailyFlowResult(
            code=str(data.get("code") or code),
            name=str(data.get("name") or code),
            type=board_type,
            market="board",
            secid=secid,
            source=self.source,
            rows=rows,
        )


def _board_fs(board_type: str) -> str:
    try:
        return BOARD_TYPE_FS[board_type]
    except KeyError as exc:
        raise InvalidBoardError(board_type) from exc


async def _get_json_with_retry(
    url: str, params: dict[str, str], headers: dict[str, str]
) -> dict:
    last_error: Exception | None = None
    async with httpx.AsyncClient(
        timeout=settings.eastmoney_timeout_seconds,
        trust_env=False,
    ) as client:
        candidate_urls = (
            (url, EASTMONEY_FALLBACK_URLS[url])
            if url in EASTMONEY_FALLBACK_URLS
            else (url,)
        )
        for candidate_url in candidate_urls:
            for attempt in range(3):
                try:
                    response = await client.get(
                        candidate_url,
                        params=params,
                        headers=headers,
                    )
                    response.raise_for_status()
                    return response.json()
                except (httpx.HTTPError, ValueError) as exc:
                    last_error = exc
                    if attempt < 2:
                        await asyncio.sleep(0.4 * (attempt + 1))
    if last_error:
        raise last_error
    raise UpstreamError("东方财富接口请求失败")


def _to_float(value: str) -> float | None:
    if value in {"", "-", "None", "null"}:
        return None
    return float(value)


def _parse_kline(kline: str) -> StockDailyFlow:
    return _parse_daily_flow(kline, StockDailyFlow)


def _parse_board_kline(kline: str) -> BoardDailyFlow:
    return _parse_daily_flow(kline, BoardDailyFlow)


def _parse_daily_flow(
    kline: str, row_class: type[StockDailyFlow] | type[BoardDailyFlow]
) -> StockDailyFlow | BoardDailyFlow:
    parts = kline.split(",")
    if len(parts) < 13:
        raise UpstreamError("东方财富资金流字段数量异常")

    try:
        return row_class(
            trade_date=date.fromisoformat(parts[0]),
            main_net_inflow=float(parts[1]),
            small_inflow=_to_float(parts[2]),
            super_large_inflow=_to_float(parts[3]),
            large_inflow=_to_float(parts[4]),
            medium_inflow=_to_float(parts[5]),
            close_price=_to_float(parts[11]),
            change_pct=_to_float(parts[12]),
        )
    except (TypeError, ValueError) as exc:
        raise UpstreamError("东方财富资金流字段解析失败") from exc
