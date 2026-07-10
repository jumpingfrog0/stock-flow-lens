from pydantic import BaseModel, Field

from app.schemas.stocks import StockResponse


class WatchlistCreate(BaseModel):
    name: str = Field(min_length=1, max_length=80)


class WatchlistUpdate(BaseModel):
    name: str = Field(min_length=1, max_length=80)


class WatchlistItemCreate(BaseModel):
    symbol: str = Field(min_length=1)


class WatchlistItemResponse(BaseModel):
    id: int
    stock: StockResponse
    createdAt: str


class WatchlistResponse(BaseModel):
    id: int
    name: str
    createdAt: str
    updatedAt: str
    items: list[WatchlistItemResponse] = []
