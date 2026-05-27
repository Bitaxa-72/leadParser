from __future__ import annotations

import time
from dataclasses import dataclass
from urllib.parse import urlparse

import httpx


DEFAULT_USER_AGENT = (
    "promotion-collector/0.1 "
    "(public business contact research; respectful low-rate crawler)"
)


@dataclass(slots=True)
class FetchResult:
    url: str
    status_code: int
    text: str
    final_url: str


class HttpClient:
    def __init__(self, timeout: float = 20.0, delay_seconds: float = 1.0) -> None:
        self.delay_seconds = delay_seconds
        self._last_request_at: dict[str, float] = {}
        self._client = httpx.Client(
            follow_redirects=True,
            timeout=timeout,
            headers={"User-Agent": DEFAULT_USER_AGENT},
        )

    def get_text(self, url: str) -> FetchResult:
        self._respect_domain_delay(url)
        response = self._client.get(url)
        content_type = response.headers.get("content-type", "")
        text = response.text if "text" in content_type or "html" in content_type else ""
        return FetchResult(
            url=url,
            status_code=response.status_code,
            text=text,
            final_url=str(response.url),
        )

    def post_json(self, url: str, payload: dict[str, object]) -> dict[str, object]:
        self._respect_domain_delay(url)
        response = self._client.post(url, json=payload)
        response.raise_for_status()
        return response.json()

    def post_form(self, url: str, data: dict[str, str]) -> dict[str, object]:
        self._respect_domain_delay(url)
        response = self._client.post(url, data=data)
        response.raise_for_status()
        return response.json()

    def close(self) -> None:
        self._client.close()

    def _respect_domain_delay(self, url: str) -> None:
        domain = urlparse(url).netloc
        last_request = self._last_request_at.get(domain)
        if last_request is not None:
            wait_for = self.delay_seconds - (time.monotonic() - last_request)
            if wait_for > 0:
                time.sleep(wait_for)
        self._last_request_at[domain] = time.monotonic()


def is_http_url(value: str) -> bool:
    parsed = urlparse(value)
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)
