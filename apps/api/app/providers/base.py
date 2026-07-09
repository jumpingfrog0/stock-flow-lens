from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class StockDailyFlow:
    trade_date: date
    main_net_inflow: float
    super_large_inflow: float | None
    large_inflow: float | None
    medium_inflow: float | None
    small_inflow: float | None
    close_price: float | None
    change_pct: float | None


@dataclass(frozen=True)
class StockDailyFlowResult:
    code: str
    name: str
    market: str
    secid: str
    source: str
    rows: list[StockDailyFlow]


class MoneyFlowProvider(ABC):
    source = "eastmoney"

    @abstractmethod
    async def fetch_stock_daily_flow(
        self, symbol: str, start_date: date, end_date: date
    ) -> StockDailyFlowResult:
        raise NotImplementedError
