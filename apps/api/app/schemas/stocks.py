from pydantic import BaseModel, Field


class StockResponse(BaseModel):
    code: str
    name: str
    market: str
    secid: str
    industry: str | None = None
    updatedAt: str


class StockRefreshRequest(BaseModel):
    query: str = ""
    limit: int = Field(default=500, ge=1, le=5000)


class StockRefreshResponse(BaseModel):
    refreshed: int
