from unittest.mock import AsyncMock

import httpx
import pytest

from app.providers import eastmoney as eastmoney_module


class FakeClient:
    def __init__(self):
        self.urls: list[str] = []

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, traceback):
        return False

    async def get(self, url, **kwargs):
        self.urls.append(url)
        if url == eastmoney_module.EASTMONEY_FLOW_URL:
            raise httpx.RemoteProtocolError("server disconnected")
        return FakeResponse()


class FakeResponse:
    def raise_for_status(self):
        return None

    def json(self):
        return {"data": {"klines": ["2026-07-15,1"]}}


@pytest.mark.asyncio
async def test_eastmoney_request_falls_back_to_delay_domain(monkeypatch):
    client = FakeClient()
    monkeypatch.setattr(
        eastmoney_module.httpx,
        "AsyncClient",
        lambda **kwargs: client,
    )
    monkeypatch.setattr(eastmoney_module.asyncio, "sleep", AsyncMock())

    result = await eastmoney_module._get_json_with_retry(
        eastmoney_module.EASTMONEY_FLOW_URL,
        {"secid": "0.002714"},
        {"User-Agent": "Mozilla/5.0"},
    )

    assert result["data"]["klines"]
    assert client.urls == [
        eastmoney_module.EASTMONEY_FLOW_URL,
        eastmoney_module.EASTMONEY_FLOW_URL,
        eastmoney_module.EASTMONEY_FLOW_URL,
        eastmoney_module.EASTMONEY_DELAY_FLOW_URL,
    ]
