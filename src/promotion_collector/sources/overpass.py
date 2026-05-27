from __future__ import annotations

from collections.abc import Iterable
from typing import Any

import httpx

from promotion_collector.classifier import classify_business_type, has_russian_orientation
from promotion_collector.config import CityConfig
from promotion_collector.contact_extractor import extract_contacts
from promotion_collector.http_client import HttpClient, is_http_url
from promotion_collector.models import BusinessRecord
from promotion_collector.sources.base import Source


OVERPASS_ENDPOINT = "https://overpass-api.de/api/interpreter"


class OverpassSource(Source):
    name = "OpenStreetMap Overpass"

    def __init__(self, http: HttpClient | None = None, enrich_websites: bool = True) -> None:
        self.http = http or HttpClient(delay_seconds=1.2)
        self.enrich_websites = enrich_websites

    def collect(self, config: CityConfig, limit: int) -> Iterable[BusinessRecord]:
        query = build_overpass_query(config)
        try:
            payload = self.http.post_form(OVERPASS_ENDPOINT, {"data": query})
        except httpx.HTTPError:
            return

        count = 0
        for element in payload.get("elements", []):
            if not isinstance(element, dict):
                continue
            record = self._record_from_element(element, config)
            if record is None:
                continue
            yield record
            count += 1
            if count >= limit:
                break

    def _record_from_element(
        self, element: dict[str, Any], config: CityConfig
    ) -> BusinessRecord | None:
        tags = element.get("tags") or {}
        if not isinstance(tags, dict):
            return None

        name = _first(tags, "name", "name:ru", "brand", "operator")
        text_for_matching = " ".join(str(value) for value in tags.values())
        if not name or not has_russian_orientation(f"{name} {text_for_matching}", config):
            return None

        website = _first(tags, "website", "contact:website", "url")
        email = _first(tags, "email", "contact:email")
        social = {
            "telegram": _first(tags, "contact:telegram", "telegram"),
            "vk": _first(tags, "contact:vk", "vk"),
            "instagram": _first(tags, "contact:instagram", "instagram"),
            "facebook": _first(tags, "contact:facebook", "facebook"),
            "whatsapp": _first(tags, "contact:whatsapp", "whatsapp"),
            "youtube": _first(tags, "contact:youtube", "youtube"),
        }

        source_url = osm_source_url(element)
        extracted_text = ""
        if self.enrich_websites and website and is_http_url(website):
            try:
                page = self.http.get_text(website)
            except httpx.HTTPError:
                page = None
            if page and page.status_code < 400 and page.text:
                contacts = extract_contacts(page.text, page.final_url)
                email = email or contacts.first_email()
                for network in social:
                    social[network] = social[network] or contacts.first_social(network)
                extracted_text = contacts.text_excerpt

        business_type = classify_business_type(
            f"{name} {text_for_matching} {extracted_text}",
            config,
        )
        return BusinessRecord(
            name=name,
            business_type=business_type,
            city=config.name,
            website=website,
            email=email,
            telegram=social["telegram"],
            vk=social["vk"],
            instagram=social["instagram"],
            facebook=social["facebook"],
            whatsapp=social["whatsapp"],
            youtube=social["youtube"],
            phone=_first(tags, "phone", "contact:phone"),
            address=_address_from_tags(tags),
            source_url=source_url,
            source_name=self.name,
            raw={"osm": element},
        )


def build_overpass_query(config: CityConfig) -> str:
    south, west, north, east = config.bbox
    bbox = f"{south},{west},{north},{east}"
    filters = list(config.overpass_extra_filters)
    if not filters:
        pattern = "|".join(config.language_keywords)
        filters = [{"tag": "name", "pattern": pattern}]

    statements = [
        f'nwr["{item["tag"]}"~"{item["pattern"]}",i]({bbox});'
        for item in filters
        if item.get("tag") and item.get("pattern")
    ]
    return "[out:json][timeout:35];(" + "".join(statements) + ");out center tags;"


def osm_source_url(element: dict[str, Any]) -> str:
    element_type = str(element.get("type", "node"))
    element_id = str(element.get("id", ""))
    return f"https://www.openstreetmap.org/{element_type}/{element_id}"


def _first(tags: dict[str, Any], *keys: str) -> str:
    for key in keys:
        value = tags.get(key)
        if value:
            return str(value).strip()
    return ""


def _address_from_tags(tags: dict[str, Any]) -> str:
    parts = [
        _first(tags, "addr:housenumber"),
        _first(tags, "addr:street"),
        _first(tags, "addr:city"),
    ]
    return ", ".join(part for part in parts if part)
