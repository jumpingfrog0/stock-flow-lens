from app.providers.base import MoneyFlowProvider
from app.providers.eastmoney import EastMoneyProvider
from app.utils.errors import InvalidSourceError


SUPPORTED_SOURCES = ("akshare", "eastmoney")


def validate_source(source: str) -> str:
    if source not in SUPPORTED_SOURCES:
        raise InvalidSourceError(source)
    return source


def create_provider(source: str) -> MoneyFlowProvider:
    validate_source(source)
    if source == "akshare":
        from app.providers.akshare import AkShareProvider

        return AkShareProvider()
    return EastMoneyProvider()
