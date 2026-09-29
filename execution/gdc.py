from __future__ import annotations

import json
from dataclasses import dataclass
from time import perf_counter
from typing import Any
from urllib.parse import urlencode
from urllib.request import Request, urlopen


@dataclass(frozen=True, slots=True)
class GdcResponse:
    url: str
    payload: dict[str, Any]
    response_bytes: int
    latency_ms: float


class GdcClient:
    """Small read-only adapter for public GDC metadata and aggregate queries."""

    def __init__(
        self, *, base_url: str = "https://api.gdc.cancer.gov", timeout: float = 30
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def get(self, path: str, params: dict[str, str | int] | None = None) -> GdcResponse:
        query = urlencode(params or {})
        url = f"{self.base_url}/{path.lstrip('/')}"
        if query:
            url = f"{url}?{query}"
        request = Request(url, headers={"User-Agent": "OncoJev-architecture-experiment/0.1"})
        started = perf_counter()
        with urlopen(request, timeout=self.timeout) as response:  # noqa: S310
            raw = response.read()
        latency_ms = (perf_counter() - started) * 1000
        payload = json.loads(raw)
        if not isinstance(payload, dict):
            raise ValueError("GDC response must be a JSON object")
        return GdcResponse(
            url=url,
            payload=payload,
            response_bytes=len(raw),
            latency_ms=latency_ms,
        )
