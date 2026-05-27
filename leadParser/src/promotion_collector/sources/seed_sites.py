from __future__ import annotations

from collections.abc import Iterable
from urllib.parse import urlparse

import httpx

from promotion_collector.classifier import classify_business_type, has_russian_orientation
from promotion_collector.config import CityConfig
from promotion_collector.contact_extractor import extract_contacts
from promotion_collector.http_client import HttpClient, is_http_url
from promotion_collector.models import BusinessRecord
from promotion_collector.sources.base import Source


class SeedSiteSource(Source):
    name = "Seed websites"

    def __init__(self, http: HttpClient | None = None, max_pages_per_site: int = 3) -> None:
        self.http = http or HttpClient(delay_seconds=1.0)
        self.max_pages_per_site = max_pages_per_site

    def collect(self, config: CityConfig, limit: int) -> Iterable[BusinessRecord]:
        count = 0
        visited: set[str] = set()
        for seed_url in config.seed_urls:
            if not is_http_url(seed_url):
                continue
            for record in self._collect_from_site(seed_url, config, visited):
                yield record
                count += 1
                if count >= limit:
                    return

    def _collect_from_site(
        self, seed_url: str, config: CityConfig, visited: set[str]
    ) -> Iterable[BusinessRecord]:
        queue = [seed_url]
        pages_seen_for_site = 0
        while queue and pages_seen_for_site < self.max_pages_per_site:
            url = queue.pop(0)
            if url in visited:
                continue
            visited.add(url)
            pages_seen_for_site += 1

            try:
                page = self.http.get_text(url)
            except httpx.HTTPError:
                continue
            if page.status_code >= 400 or not page.text:
                continue

            contacts = extract_contacts(page.text, page.final_url)
            text = f"{contacts.title} {contacts.text_excerpt}"
            if has_russian_orientation(text, config):
                yield BusinessRecord(
                    name=contacts.title or _domain_name(page.final_url),
                    business_type=classify_business_type(text, config),
                    city=config.name,
                    website=page.final_url,
                    email=contacts.first_email(),
                    telegram=contacts.first_social("telegram"),
                    vk=contacts.first_social("vk"),
                    instagram=contacts.first_social("instagram"),
                    facebook=contacts.first_social("facebook"),
                    whatsapp=contacts.first_social("whatsapp"),
                    youtube=contacts.first_social("youtube"),
                    other_social=contacts.other_social(),
                    source_url=page.final_url,
                    source_name=self.name,
                    raw={"title": contacts.title, "text_excerpt": contacts.text_excerpt},
                )

            queue.extend(link for link in contacts.internal_links if link not in visited)


def _domain_name(url: str) -> str:
    return urlparse(url).netloc.removeprefix("www.")
