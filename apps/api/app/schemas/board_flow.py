from datetime import date
from typing import Literal

from pydantic import BaseModel, Field, field_validator

from app.schemas.money_flow import MoneyFlowSummaryResponse


BoardType = Literal["industry", "concept"]


class BoardSearchItem(BaseModel):
    code: str
    name: str
    type: BoardType
    market: str
    secid: str
    source: str


class BoardFlowSummaryRequest(BaseModel):
    boards: list[str] = Field(min_length=1)
    startDate: date
    endDate: date
    type: BoardType
    source: str = "eastmoney"

    @field_validator("boards")
    @classmethod
    def clean_boards(cls, value: list[str]) -> list[str]:
        cleaned: list[str] = []
        for board in value:
            stripped = board.strip().upper()
            if stripped and stripped not in cleaned:
                cleaned.append(stripped)
        return cleaned


class BoardFlowSummaryResponse(MoneyFlowSummaryResponse):
    pass
