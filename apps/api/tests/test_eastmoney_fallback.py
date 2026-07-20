from unittest.mock import AsyncMock

import httpx
import pytest

from app.infrastructure.eastmoney import client as client_module


class FakeClient:
    def __init__(self):
        self.urls: list[str] = []

    async def get(self, url, **kwargs):
        self.urls.append(url)
        if url == client_module.FLOW_URL:
            raise httpx.RemoteProtocolError("server disconnected")
        return FakeResponse()

    async def aclose(self):
        return None


class FakeResponse:
    def raise_for_status(self):
        return None

    def json(self):
        return {"data": {"klines": ["2026-07-15,1"]}}


@pytest.mark.asyncio
async def test_eastmoney_request_falls_back_to_delay_domain(monkeypatch):
    client = FakeClient()
    monkeypatch.setattr(
        client_module.httpx,
        "AsyncClient",
        lambda **kwargs: client,
    )
    monkeypatch.setattr(client_module.asyncio, "sleep", AsyncMock())

    async with client_module.EastMoneyHttpClient() as eastmoney_client:
        result = await eastmoney_client.get_json(
            client_module.FLOW_URL,
            {"secid": "0.002714"},
            fallback_urls=(client_module.DELAY_FLOW_URL,),
        )

    assert result["data"]["klines"]
    assert client.urls == [
        client_module.FLOW_URL,
        client_module.FLOW_URL,
        client_module.FLOW_URL,
        client_module.DELAY_FLOW_URL,
    ]
