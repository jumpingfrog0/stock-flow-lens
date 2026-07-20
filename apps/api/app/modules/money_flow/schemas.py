from datetime import date

from pydantic import BaseModel, Field, field_validator


class MoneyFlowSummaryRequest(BaseModel):
    symbols: list[str] = Field(min_length=1)
    startDate: date
    endDate: date
    source: str = "akshare"

    @field_validator("symbols")
    @classmethod
    def clean_symbols(cls, value: list[str]) -> list[str]:
        cleaned: list[str] = []
        for symbol in value:
            stripped = symbol.strip()
            if stripped and stripped not in cleaned:
                cleaned.append(stripped)
        return cleaned


class DailyMoneyFlow(BaseModel):
    tradeDate: date
    mainNetInflow: float
    superLargeInflow: float | None = None
    largeInflow: float | None = None
    mediumInflow: float | None = None
    smallInflow: float | None = None
    closePrice: float | None = None
    changePct: float | None = None
    cumulativeMainNetInflow: float


class MoneyFlowItem(BaseModel):
    code: str
    name: str
    mainNetInflow: float
    direction: str
    directionAmount: float
    tradeDays: int
    daily: list[DailyMoneyFlow]


class MoneyFlowError(BaseModel):
    code: str | None = None
    errorCode: str
    message: str


class MoneyFlowRange(BaseModel):
    startDate: date
    endDate: date


class MoneyFlowSummaryResponse(BaseModel):
    source: str
    range: MoneyFlowRange
    items: list[MoneyFlowItem]
    totalMainNetInflow: float
    totalDirection: str
    totalDirectionAmount: float
    errors: list[MoneyFlowError] = []


class MoneyFlowRefreshRecentRequest(BaseModel):
    symbols: list[str] = Field(min_length=1)
    source: str = "akshare"

    @field_validator("symbols")
    @classmethod
    def clean_symbols(cls, value: list[str]) -> list[str]:
        cleaned: list[str] = []
        for symbol in value:
            stripped = symbol.strip()
            if stripped and stripped not in cleaned:
                cleaned.append(stripped)
        return cleaned


class MoneyFlowRefreshRecentItem(BaseModel):
    code: str
    name: str
    refreshedRows: int


class MoneyFlowRefreshRecentResponse(BaseModel):
    source: str
    range: MoneyFlowRange
    items: list[MoneyFlowRefreshRecentItem]
    errors: list[MoneyFlowError] = []
