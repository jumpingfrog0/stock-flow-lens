from dataclasses import dataclass


INVALID_SYMBOL = "INVALID_SYMBOL"
INVALID_DATE_RANGE = "INVALID_DATE_RANGE"
NO_DATA = "NO_DATA"
UPSTREAM_FAILED = "UPSTREAM_FAILED"
PARTIAL_FAILED = "PARTIAL_FAILED"


@dataclass
class AppError(Exception):
    error_code: str
    message: str
    code: str | None = None


class InvalidSymbolError(AppError):
    def __init__(self, code: str):
        super().__init__(INVALID_SYMBOL, "不支持的股票代码", code)


class InvalidDateRangeError(AppError):
    def __init__(self, message: str = "日期区间无效"):
        super().__init__(INVALID_DATE_RANGE, message)


class NoDataError(AppError):
    def __init__(self, code: str | None = None):
        super().__init__(NO_DATA, "区间无数据", code)


class UpstreamError(AppError):
    def __init__(self, message: str = "东方财富接口失败", code: str | None = None):
        super().__init__(UPSTREAM_FAILED, message, code)
