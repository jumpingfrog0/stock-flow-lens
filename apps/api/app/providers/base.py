from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class MoneyFlowDailyRow:
    trade_date: date
    main_net_inflow: float
    super_large_inflow: float | None
    large_inflow: float | None
    medium_inflow: float | None
    small_inflow: float | None
    close_price: float | None
    change_pct: float | None


@dataclass(frozen=True)
class StockDailyFlow(MoneyFlowDailyRow):
    pass


@dataclass(frozen=True)
class BoardDailyFlow(MoneyFlowDailyRow):
    pass


@dataclass(frozen=True)
class StockDailyFlowResult:
    code: str
    name: str
    market: str
    secid: str
    source: str
    rows: list[StockDailyFlow]
    industry: str | None = None


@dataclass(frozen=True)
class StockInfo:
    code: str
    name: str
    market: str
    secid: str
    source: str
    industry: str | None = None


@dataclass(frozen=True)
class BoardSearchResult:
    code: str
    name: str
    type: str
    market: str
    secid: str
    source: str


@dataclass(frozen=True)
class BoardDailyFlowResult:
    code: str
    name: str
    type: str
    market: str
    secid: str
    source: str
    rows: list[BoardDailyFlow]


class MoneyFlowProvider(ABC):
    source = "eastmoney"

    @abstractmethod
    async def fetch_stock_daily_flow(
        self, symbol: str, start_date: date, end_date: date
    ) -> StockDailyFlowResult:
        raise NotImplementedError

    async def search_stocks(self, query: str = "", limit: int = 500) -> list[StockInfo]:
        raise NotImplementedError

    async def search_boards(
        self, board_type: str, query: str, limit: int
    ) -> list[BoardSearchResult]:
        raise NotImplementedError

    async def fetch_board_daily_flow(
        self, board: str, board_type: str, start_date: date, end_date: date
    ) -> BoardDailyFlowResult:
        raise NotImplementedError
