from types import SimpleNamespace

import pytest

from app.services import auto_refresh_service as auto_refresh_module
from app.services.auto_refresh_service import AutoRefreshService
from app.utils.errors import InvalidSourceError


@pytest.mark.asyncio
async def test_auto_refresh_groups_symbols_by_history_source(monkeypatch):
    calls: list[tuple[str, list[str]]] = []

    class FakeDb:
        closed = False

        def close(self):
            self.closed = True

    db = FakeDb()

    class FakeWatchlistService:
        def __init__(self, value):
            pass

        def all_item_codes(self):
            return ["300308"]

    class FakeQueryHistoryService:
        def __init__(self, value):
            pass

        def recent_symbol_sources(self, limit):
            return [
                ("300308", "eastmoney"),
                ("300502", "akshare"),
                ("300999", "legacy"),
            ]

    class FakeMoneyFlowService:
        def __init__(self, value, provider):
            self.provider = provider

        async def refresh_recent(self, symbols):
            calls.append((self.provider.source, symbols))
            return SimpleNamespace(errors=[])

    def fake_provider(source):
        if source == "legacy":
            raise InvalidSourceError(source)
        return SimpleNamespace(source=source)

    monkeypatch.setattr(auto_refresh_module, "create_session", lambda: db)
    monkeypatch.setattr(auto_refresh_module, "WatchlistService", FakeWatchlistService)
    monkeypatch.setattr(auto_refresh_module, "QueryHistoryService", FakeQueryHistoryService)
    monkeypatch.setattr(auto_refresh_module, "MoneyFlowService", FakeMoneyFlowService)
    monkeypatch.setattr(auto_refresh_module, "create_provider", fake_provider)
    monkeypatch.setattr(auto_refresh_module.settings, "default_source", "akshare")

    await AutoRefreshService().refresh_once()

    assert calls == [
        ("akshare", ["300308", "300502"]),
        ("eastmoney", ["300308"]),
    ]
    assert db.closed is True
