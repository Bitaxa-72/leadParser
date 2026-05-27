from __future__ import annotations

from promotion_collector.config import CityConfig


def has_russian_orientation(text: str, config: CityConfig) -> bool:
    normalized = text.casefold()
    return any(keyword.casefold() in normalized for keyword in config.language_keywords)


def classify_business_type(text: str, config: CityConfig) -> str:
    normalized = text.casefold()
    for business_type, keywords in config.business_type_keywords.items():
        if any(keyword.casefold() in normalized for keyword in keywords):
            return business_type
    return "Другое"
