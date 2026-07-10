from dataclasses import dataclass


INVALID_SYMBOL = "INVALID_SYMBOL"
INVALID_BOARD = "INVALID_BOARD"
INVALID_DATE_RANGE = "INVALID_DATE_RANGE"
NO_DATA = "NO_DATA"
UPSTREAM_FAILED = "UPSTREAM_FAILED"
PARTIAL_FAILED = "PARTIAL_FAILED"
AMBIGUOUS_SYMBOL = "AMBIGUOUS_SYMBOL"
STOCK_NOT_FOUND = "STOCK_NOT_FOUND"
WATCHLIST_NOT_FOUND = "WATCHLIST_NOT_FOUND"


@dataclass
class AppError(Exception):
    error_code: str
    message: str
    code: str | None = None


class InvalidSymbolError(AppError):
    def __init__(self, code: str):
        super().__init__(INVALID_SYMBOL, "不支持的股票代码", code)


class InvalidBoardError(AppError):
    def __init__(self, code: str):
        super().__init__(INVALID_BOARD, "不支持的板块代码", code)


class StockNotFoundError(AppError):
    def __init__(self, code: str):
        super().__init__(STOCK_NOT_FOUND, "未找到匹配股票", code)


class AmbiguousSymbolError(AppError):
    def __init__(self, code: str, matches: list[str]):
        message = f"股票名称匹配多个结果：{', '.join(matches[:10])}"
        super().__init__(AMBIGUOUS_SYMBOL, message, code)


class WatchlistNotFoundError(AppError):
    def __init__(self, watchlist_id: int):
        super().__init__(WATCHLIST_NOT_FOUND, "自选股分组不存在", str(watchlist_id))


class InvalidDateRangeError(AppError):
    def __init__(self, message: str = "日期区间无效"):
        super().__init__(INVALID_DATE_RANGE, message)


class NoDataError(AppError):
    def __init__(self, code: str | None = None):
        super().__init__(NO_DATA, "区间无数据", code)


class UpstreamError(AppError):
    def __init__(self, message: str = "东方财富接口失败", code: str | None = None):
        super().__init__(UPSTREAM_FAILED, message, code)
