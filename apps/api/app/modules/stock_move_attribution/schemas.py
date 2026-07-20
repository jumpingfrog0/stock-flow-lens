from datetime import date
from typing import Literal

from pydantic import BaseModel, field_validator


PrimaryDriver = Literal["market_rotation", "industry_move", "stock_specific", "mixed", "insufficient"]
Confidence = Literal["high", "medium", "low"]
RotationDirection = Literal["high_to_low", "low_to_high", "balanced"]
StyleBucket = Literal["growth", "defensive_value", "unclassified"]


class StockMoveAttributionRequest(BaseModel):
    symbol: str

    @field_validator("symbol")
    @classmethod
    def clean_symbol(cls, value: str) -> str:
        return value.strip()


class StockMoveSnapshot(BaseModel):
    code: str
    name: str
    tradeDate: date
    industry: str | None
    styleBucket: StyleBucket
    closePrice: float
    changePct: float
    openPrice: float | None
    highPrice: float | None
    lowPrice: float | None
    previousClose: float | None
    amount: float | None
    turnoverRate: float | None
    volumeRatio: float | None
    mainNetInflow: float | None
    marketRelativePct: float | None
    industryRelativePct: float | None


class MarketBenchmark(BaseModel):
    key: str
    name: str
    group: str
    changePct: float


class MarketBreadth(BaseModel):
    total: int
    advancing: int
    declining: int
    flat: int
    advancingRatio: float


class MarketContext(BaseModel):
    benchmarkKey: str
    benchmarkName: str
    benchmarkChangePct: float
    benchmarks: list[MarketBenchmark]
    breadth: MarketBreadth | None


class StyleContext(BaseModel):
    rotation: RotationDirection
    growthProxyChangePct: float | None
    valueProxyChangePct: float | None
    valueMinusGrowthPct: float | None
    note: str


class IndustryContext(BaseModel):
    code: str
    name: str
    changePct: float | None
    mainNetInflow: float | None
    peerCount: int
    advancing: int
    declining: int
    flat: int
    advancingRatio: float | None
    medianChangePct: float | None


class AnnouncementItem(BaseModel):
    title: str
    noticeDate: date
    artCode: str
    sameDay: bool


class DriverEvidence(BaseModel):
    code: Literal["market_rotation", "industry_move", "stock_specific"]
    label: str
    score: int
    evidence: list[str]
    limitations: list[str]


class CounterfactualCheck(BaseModel):
    code: Literal["peers_move_together", "style_rotation", "same_day_announcement"]
    result: Literal["supports", "weakens", "unknown"]
    conclusion: str


class StockMoveAttributionResponse(BaseModel):
    methodologyVersion: str
    source: str
    asOf: date
    primaryDriver: PrimaryDriver
    confidence: Confidence
    summary: str
    stock: StockMoveSnapshot
    market: MarketContext
    style: StyleContext
    industry: IndustryContext | None
    announcements: list[AnnouncementItem]
    drivers: list[DriverEvidence]
    counterfactuals: list[CounterfactualCheck]
    warnings: list[str]
