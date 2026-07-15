from datetime import date

from pydantic import BaseModel, Field, field_validator


class QueryHistoryCreate(BaseModel):
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


class QueryHistoryResponse(BaseModel):
    id: int
    symbols: list[str]
    startDate: date
    endDate: date
    source: str
    createdAt: str
