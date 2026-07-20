import asyncio
import json
from typing import Any

import httpx

from app.core.config import settings
from app.utils.errors import UpstreamError


QUOTE_URL = "https://push2.eastmoney.com/api/qt/stock/get"
DELAY_QUOTE_URL = "https://push2delay.eastmoney.com/api/qt/stock/get"
LIST_URL = "https://push2.eastmoney.com/api/qt/clist/get"
DELAY_LIST_URL = "https://push2delay.eastmoney.com/api/qt/clist/get"
FLOW_URL = "https://push2his.eastmoney.com/api/qt/stock/fflow/daykline/get"
DELAY_FLOW_URL = "https://push2delay.eastmoney.com/api/qt/stock/fflow/daykline/get"
INTRADAY_FLOW_URL = "https://push2delay.eastmoney.com/api/qt/stock/fflow/kline/get"
ANNOUNCEMENT_URL = "https://np-anotice-stock.eastmoney.com/api/security/ann"

DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Referer": "https://quote.eastmoney.com/",
}

_force_curl_transport = False


class EastMoneyHttpClient:
    """Shared retry, domain fallback and optional curl transport for EastMoney."""

    def __init__(self, *, allow_curl_fallback: bool = False):
        self.allow_curl_fallback = allow_curl_fallback
        self._client = httpx.AsyncClient(
            timeout=settings.eastmoney_timeout_seconds,
            trust_env=False,
            headers=DEFAULT_HEADERS,
        )

    async def __aenter__(self) -> "EastMoneyHttpClient":
        return self

    async def __aexit__(self, exc_type, exc, traceback) -> bool:
        await self._client.aclose()
        return False

    async def get_json(
        self,
        url: str,
        params: dict[str, str],
        *,
        fallback_urls: tuple[str, ...] = (),
        attempts: int = 3,
    ) -> dict[str, Any]:
        last_error: Exception | None = None
        for candidate_url in (url, *fallback_urls):
            for attempt in range(attempts):
                try:
                    return await self._get_candidate(candidate_url, params)
                except (
                    httpx.HTTPError,
                    ValueError,
                    OSError,
                    asyncio.TimeoutError,
                ) as exc:
                    last_error = exc
                    if attempt < attempts - 1:
                        await asyncio.sleep(0.4 * (attempt + 1))
        raise UpstreamError("东方财富接口请求失败") from last_error

    async def _get_candidate(
        self, url: str, params: dict[str, str]
    ) -> dict[str, Any]:
        global _force_curl_transport
        if self.allow_curl_fallback and _force_curl_transport:
            return await _get_json_with_curl(url, params)

        try:
            response = await self._client.get(url, params=params)
            response.raise_for_status()
            return response.json()
        except (httpx.HTTPError, ValueError):
            if not self.allow_curl_fallback:
                raise

        result = await _get_json_with_curl(url, params)
        _force_curl_transport = True
        return result


async def _get_json_with_curl(
    url: str, params: dict[str, str]
) -> dict[str, Any]:
    command = [
        "curl",
        "-sS",
        "--fail",
        "--compressed",
        "--max-time",
        str(max(3, int(settings.eastmoney_timeout_seconds))),
        "-A",
        DEFAULT_HEADERS["User-Agent"],
        "-e",
        DEFAULT_HEADERS["Referer"],
        "-G",
        url,
    ]
    for key, value in params.items():
        command.extend(("--data-urlencode", f"{key}={value}"))
    process = await asyncio.create_subprocess_exec(
        *command,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    try:
        stdout, stderr = await asyncio.wait_for(
            process.communicate(),
            timeout=settings.eastmoney_timeout_seconds + 2,
        )
    except asyncio.TimeoutError:
        process.kill()
        await process.communicate()
        raise
    if process.returncode != 0:
        message = stderr.decode("utf-8", errors="replace").strip()
        raise OSError(message or f"curl 退出码 {process.returncode}")
    return json.loads(stdout.decode("utf-8"))
