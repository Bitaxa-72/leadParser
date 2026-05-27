from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


SOCIAL_COLUMNS = (
    "telegram",
    "vk",
    "instagram",
    "facebook",
    "whatsapp",
    "youtube",
    "other_social",
)


@dataclass(slots=True)
class BusinessRecord:
    name: str
    business_type: str
    city: str
    source_url: str
    website: str = ""
    email: str = ""
    telegram: str = ""
    vk: str = ""
    instagram: str = ""
    facebook: str = ""
    whatsapp: str = ""
    youtube: str = ""
    other_social: str = ""
    phone: str = ""
    address: str = ""
    source_name: str = ""
    raw: dict[str, Any] = field(default_factory=dict)
    collected_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(timespec="seconds")
    )

    def dedupe_key(self) -> str:
        parts = [
            self.city,
            self.website or self.source_url,
            self.email,
            self.name,
            self.address,
        ]
        return "|".join(normalize_key_part(part) for part in parts if part)

    def to_json(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "business_type": self.business_type,
            "city": self.city,
            "website": self.website,
            "email": self.email,
            "telegram": self.telegram,
            "vk": self.vk,
            "instagram": self.instagram,
            "facebook": self.facebook,
            "whatsapp": self.whatsapp,
            "youtube": self.youtube,
            "other_social": self.other_social,
            "phone": self.phone,
            "address": self.address,
            "source_url": self.source_url,
            "source_name": self.source_name,
            "collected_at": self.collected_at,
            "dedupe_key": self.dedupe_key(),
            "raw": self.raw,
        }

    @classmethod
    def from_json(cls, data: dict[str, Any]) -> "BusinessRecord":
        payload = {key: data.get(key, "") for key in cls.__dataclass_fields__}
        payload["raw"] = data.get("raw") or {}
        return cls(**payload)

    def to_excel_row(self) -> list[str]:
        return [
            self.name,
            self.business_type,
            self.city,
            self.website,
            self.email,
            self.telegram,
            self.vk,
            self.instagram,
            self.facebook,
            self.whatsapp,
            self.youtube,
            self.other_social,
            self.phone,
            self.address,
            self.source_url,
            self.source_name,
            self.collected_at,
        ]


def normalize_key_part(value: str) -> str:
    return " ".join(value.strip().lower().split())
