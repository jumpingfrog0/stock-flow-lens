import asyncio
from dataclasses import dataclass
from datetime import date, datetime
from statistics import median
from typing import Any
from zoneinfo import ZoneInfo

from app.infrastructure.eastmoney.client import (
    ANNOUNCEMENT_URL,
    DELAY_FLOW_URL,
    DELAY_LIST_URL,
    DELAY_QUOTE_URL,
    FLOW_URL,
    INTRADAY_FLOW_URL,
    LIST_URL,
    QUOTE_URL,
    EastMoneyHttpClient,
)
from app.providers.symbols import infer_secid
from app.utils.errors import NoDataError, UpstreamError


EASTMONEY_TOKEN = "bd1d9ddb04089700cf9c27f6f7426281"
SHANGHAI_TZ = ZoneInfo("Asia/Shanghai")
PAGE_SIZE = 100
ALL_A_SHARE_FILTER = "m:0+t:6,m:0+t:80,m:1+t:2,m:1+t:23"

INDEX_DEFINITIONS = (
    ("shanghai", "1.000001", "上证指数", "market"),
    ("shenzhen", "0.399001", "深证成指", "market"),
    ("chinext", "0.399006", "创业板指", "growth"),
    ("star50", "1.000688", "科创50", "growth"),
    ("csi300", "1.000300", "沪深300", "value"),
    ("sse50", "1.000016", "上证50", "value"),
)


@dataclass(frozen=True)
class StockSnapshot:
    code: str
    name: str
    secid: str
    trade_date: date
    industry: str | None
    close_price: float
    change_pct: float
    open_price: float | None
    high_price: float | None
    low_price: float | None
    previous_close: float | None
    amount: float | None
    turnover_rate: float | None
    volume_ratio: float | None
    main_net_inflow: float | None


@dataclass(frozen=True)
class IndexSnapshot:
    key: str
    name: str
    group: str
    change_pct: float


@dataclass(frozen=True)
class MarketBreadthSnapshot:
    total: int
    advancing: int
    declining: int
    flat: int


@dataclass(frozen=True)
class IndustrySnapshot:
    code: str
    name: str
    change_pct: float | None
    main_net_inflow: float | None
    peer_count: int
    advancing: int
    declining: int
    flat: int
    median_change_pct: float | None


@dataclass(frozen=True)
class AnnouncementSnapshot:
    title: str
    notice_date: date
    art_code: str


@dataclass(frozen=True)
class StockAttributionContext:
    source: str
    stock: StockSnapshot
    indexes: list[IndexSnapshot]
    breadth: MarketBreadthSnapshot | None
    industry: IndustrySnapshot | None
    announcements: list[AnnouncementSnapshot]
    warnings: list[str]


class StockMoveEvidenceProvider:
    source = "eastmoney"

    async def fetch_context(self, symbol: str) -> StockAttributionContext:
        secid, _ = infer_secid(symbol)
        async with EastMoneyHttpClient(allow_curl_fallback=True) as client:
            # 先请求关键行情，同时确定当前环境应使用 httpx 还是系统 curl。
            # 东方财富偶尔会按 TLS 客户端特征主动断开 Python HTTP 连接。
            quote = await self._fetch_quote(client, secid)
            flow_task = asyncio.create_task(self._fetch_latest_flow(client, secid))
            indexes_task = asyncio.create_task(self._fetch_indexes(client))
            breadth_task = asyncio.create_task(self._fetch_market_breadth(client))
            announcements_task = asyncio.create_task(self._fetch_announcements(client, symbol))

            results = await asyncio.gather(
                flow_task,
                indexes_task,
                breadth_task,
                announcements_task,
                return_exceptions=True,
            )
            (
                latest_flow_result,
                indexes_result,
                breadth_result,
                announcements_result,
            ) = results

            warnings: list[str] = []
            quote_main_net_inflow = _optional_money_flow(quote.get("f62"))
            if isinstance(latest_flow_result, Exception):
                latest_flow = None
            else:
                latest_flow = latest_flow_result
            if isinstance(indexes_result, Exception):
                indexes = []
                warnings.append("市场指数接口暂不可用")
            else:
                indexes = indexes_result
            if isinstance(breadth_result, Exception):
                breadth = None
                warnings.append("全市场涨跌家数接口暂不可用")
            else:
                breadth = breadth_result
                if breadth is None:
                    warnings.append("全市场涨跌家数接口暂不可用")
            if isinstance(announcements_result, Exception):
                announcements = []
                warnings.append("公司公告接口暂不可用")
            else:
                announcements = announcements_result

            trade_date = _quote_trade_date(quote) or (
                latest_flow[0] if latest_flow is not None else date.today()
            )
            main_net_inflow: float | None = None
            if latest_flow is not None:
                flow_date, flow_amount = latest_flow
                if flow_date == trade_date:
                    main_net_inflow = flow_amount
            if main_net_inflow is None:
                main_net_inflow = quote_main_net_inflow
            if main_net_inflow is None:
                if latest_flow is not None:
                    warnings.append(
                        "当日资金流尚未更新，未将上一交易日资金流用于当日归因"
                    )
                else:
                    warnings.append("当日资金流接口暂不可用")

            industry_name = _optional_text(quote.get("f127"))
            industry: IndustrySnapshot | None = None
            if industry_name:
                try:
                    industry = await self._fetch_industry(client, industry_name)
                    if industry is None:
                        warnings.append(f"未找到与“{industry_name}”匹配的行业板块")
                except UpstreamError:
                    warnings.append("行业板块接口暂不可用")
            else:
                warnings.append("上游未返回股票所属行业")

            stock = StockSnapshot(
                code=str(quote.get("f57") or symbol),
                name=str(quote.get("f58") or symbol),
                secid=secid,
                trade_date=trade_date,
                industry=industry_name,
                close_price=_required_float(quote.get("f43"), symbol),
                change_pct=_required_float(quote.get("f170"), symbol),
                open_price=_optional_float(quote.get("f46")),
                high_price=_optional_float(quote.get("f44")),
                low_price=_optional_float(quote.get("f45")),
                previous_close=_optional_float(quote.get("f60")),
                amount=_optional_float(quote.get("f48")),
                turnover_rate=_optional_float(quote.get("f168")),
                volume_ratio=_optional_float(quote.get("f50")),
                main_net_inflow=main_net_inflow,
            )
            return StockAttributionContext(
                source=self.source,
                stock=stock,
                indexes=indexes,
                breadth=breadth,
                industry=industry,
                announcements=announcements,
                warnings=warnings,
            )

    async def _fetch_quote(self, client: EastMoneyHttpClient, secid: str) -> dict[str, Any]:
        payload = await client.get_json(
            QUOTE_URL,
            {
                "fltt": "2",
                "secid": secid,
                "fields": (
                    "f43,f44,f45,f46,f48,f50,f57,f58,f60,f62,f86,f127,f168,f170"
                ),
            },
            fallback_urls=(DELAY_QUOTE_URL,),
        )
        data = payload.get("data")
        if not data:
            raise NoDataError(secid.split(".")[-1])
        return data

    async def _fetch_latest_flow(
        self, client: EastMoneyHttpClient, secid: str
    ) -> tuple[date, float] | None:
        params = {
            "secid": secid,
            "lmt": "1",
            "klt": "1",
            "fields1": "f1,f2,f3,f7",
            "fields2": "f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61,f62,f63",
        }
        try:
            payload = await client.get_json(
                INTRADAY_FLOW_URL,
                params,
            )
        except UpstreamError:
            payload = await client.get_json(
                FLOW_URL,
                {**params, "klt": "101"},
                fallback_urls=(DELAY_FLOW_URL,),
            )
        klines = (payload.get("data") or {}).get("klines") or []
        if not klines:
            return None
        parts = str(klines[-1]).split(",")
        if len(parts) < 2:
            return None
        try:
            return date.fromisoformat(parts[0][:10]), float(parts[1])
        except (TypeError, ValueError):
            return None

    async def _fetch_indexes(self, client: EastMoneyHttpClient) -> list[IndexSnapshot]:
        payloads = await asyncio.gather(
            *(self._fetch_quote(client, secid) for _, secid, _, _ in INDEX_DEFINITIONS),
            return_exceptions=True,
        )
        results: list[IndexSnapshot] = []
        for definition, payload in zip(INDEX_DEFINITIONS, payloads, strict=True):
            key, _, fallback_name, group = definition
            if isinstance(payload, Exception):
                continue
            change_pct = _optional_float(payload.get("f170"))
            if change_pct is None:
                continue
            results.append(
                IndexSnapshot(
                    key=key,
                    name=str(payload.get("f58") or fallback_name),
                    group=group,
                    change_pct=change_pct,
                )
            )
        if not results:
            raise UpstreamError("东方财富市场指数接口返回为空")
        return results

    async def _fetch_market_breadth(
        self, client: EastMoneyHttpClient
    ) -> MarketBreadthSnapshot | None:
        try:
            items = await _fetch_all_list_items(
                client,
                fs=ALL_A_SHARE_FILTER,
                fields="f3",
            )
        except UpstreamError:
            return None
        changes = [value for item in items if (value := _optional_float(item.get("f3"))) is not None]
        if not changes:
            return None
        advancing = sum(value > 0 for value in changes)
        declining = sum(value < 0 for value in changes)
        return MarketBreadthSnapshot(
            total=len(changes),
            advancing=advancing,
            declining=declining,
            flat=len(changes) - advancing - declining,
        )

    async def _fetch_industry(
        self, client: EastMoneyHttpClient, industry_name: str
    ) -> IndustrySnapshot | None:
        items = await _fetch_all_list_items(
            client,
            fs="m:90+t:2",
            fields="f12,f14,f3,f62",
        )
        board = _match_board(items, industry_name)
        if board is None:
            return None
        code = str(board.get("f12") or "")
        peers = await _fetch_all_list_items(
            client,
            fs=f"b:{code}",
            fields="f12,f14,f3,f62",
        )
        changes = [value for peer in peers if (value := _optional_float(peer.get("f3"))) is not None]
        advancing = sum(value > 0 for value in changes)
        declining = sum(value < 0 for value in changes)
        return IndustrySnapshot(
            code=code,
            name=str(board.get("f14") or industry_name),
            change_pct=_optional_float(board.get("f3")),
            main_net_inflow=_optional_float(board.get("f62")),
            peer_count=len(changes),
            advancing=advancing,
            declining=declining,
            flat=len(changes) - advancing - declining,
            median_change_pct=median(changes) if changes else None,
        )

    async def _fetch_announcements(
        self, client: EastMoneyHttpClient, symbol: str
    ) -> list[AnnouncementSnapshot]:
        try:
            payload = await client.get_json(
                ANNOUNCEMENT_URL,
                {
                    "sr": "-1",
                    "page_size": "10",
                    "page_index": "1",
                    "ann_type": "A",
                    "client_source": "web",
                    "stock_list": symbol,
                },
            )
        except UpstreamError:
            return []
        results: list[AnnouncementSnapshot] = []
        for item in (payload.get("data") or {}).get("list") or []:
            notice_date = _parse_date(item.get("notice_date"))
            title = str(item.get("title_ch") or item.get("title") or "").strip()
            if notice_date is None or not title:
                continue
            results.append(
                AnnouncementSnapshot(
                    title=title,
                    notice_date=notice_date,
                    art_code=str(item.get("art_code") or ""),
                )
            )
        return results


async def _fetch_all_list_items(
    client: EastMoneyHttpClient, fs: str, fields: str
) -> list[dict[str, Any]]:
    first_payload = await _fetch_list_page(client, fs, fields, 1)
    data = first_payload.get("data") or {}
    items = list(data.get("diff") or [])
    total = int(data.get("total") or len(items))
    page_count = max(1, (total + PAGE_SIZE - 1) // PAGE_SIZE)
    if page_count == 1:
        return items

    semaphore = asyncio.Semaphore(8)

    async def fetch_page(page: int) -> list[dict[str, Any]]:
        async with semaphore:
            payload = await _fetch_list_page(client, fs, fields, page)
            return list((payload.get("data") or {}).get("diff") or [])

    pages = await asyncio.gather(*(fetch_page(page) for page in range(2, page_count + 1)))
    for page_items in pages:
        items.extend(page_items)
    return items


async def _fetch_list_page(
    client: EastMoneyHttpClient, fs: str, fields: str, page: int
) -> dict[str, Any]:
    return await client.get_json(
        LIST_URL,
        {
            "pn": str(page),
            "pz": str(PAGE_SIZE),
            "po": "1",
            "np": "1",
            "ut": EASTMONEY_TOKEN,
            "fltt": "2",
            "invt": "2",
            "fid": "f3",
            "fs": fs,
            "fields": fields,
        },
        fallback_urls=(DELAY_LIST_URL,),
    )


def _match_board(items: list[dict[str, Any]], industry_name: str) -> dict[str, Any] | None:
    exact = [item for item in items if str(item.get("f14") or "").strip() == industry_name]
    if exact:
        return exact[0]
    candidates = [
        item
        for item in items
        if industry_name in str(item.get("f14") or "")
        or str(item.get("f14") or "") in industry_name
    ]
    if not candidates:
        return None
    return min(candidates, key=lambda item: len(str(item.get("f14") or "")))


def _quote_trade_date(quote: dict[str, Any]) -> date | None:
    timestamp = _optional_float(quote.get("f86"))
    if not timestamp or timestamp <= 0:
        return None
    try:
        return datetime.fromtimestamp(timestamp, tz=SHANGHAI_TZ).date()
    except (OSError, OverflowError, ValueError):
        return None


def _parse_date(value: Any) -> date | None:
    if value is None:
        return None
    text = str(value).strip()[:10]
    try:
        return date.fromisoformat(text)
    except ValueError:
        return None


def _required_float(value: Any, code: str) -> float:
    parsed = _optional_float(value)
    if parsed is None:
        raise UpstreamError("东方财富股票行情字段缺失", code)
    return parsed


def _optional_float(value: Any) -> float | None:
    if value in {None, "", "-", "None", "null"}:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _optional_money_flow(value: Any) -> float | None:
    parsed = _optional_float(value)
    if parsed is None or abs(parsed) <= 1:
        return None
    return parsed


def _optional_text(value: Any) -> str | None:
    if value in {None, "", "-", "None", "null"}:
        return None
    text = str(value).strip()
    return text or None
