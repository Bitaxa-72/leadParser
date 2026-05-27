from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONFIG_DIR = PROJECT_ROOT / "config" / "cities"
DEFAULT_DATA_DIR = PROJECT_ROOT / "data"

RUSSIA_MILLION_PLUS_CITIES = (
    "moscow",
    "saint-petersburg",
    "novosibirsk",
    "yekaterinburg",
    "kazan",
    "nizhny-novgorod",
    "chelyabinsk",
    "krasnoyarsk",
    "samara",
    "ufa",
    "rostov-on-don",
    "omsk",
    "krasnodar",
    "voronezh",
    "perm",
    "volgograd",
)

CITY_GROUPS = {
    "russia-million-plus": RUSSIA_MILLION_PLUS_CITIES,
}


@dataclass(frozen=True, slots=True)
class CityConfig:
    slug: str
    name: str
    country: str
    bbox: tuple[float, float, float, float]
    language_keywords: tuple[str, ...] = field(default_factory=tuple)
    business_type_keywords: dict[str, tuple[str, ...]] = field(default_factory=dict)
    seed_urls: tuple[str, ...] = field(default_factory=tuple)
    overpass_extra_filters: tuple[dict[str, str], ...] = field(default_factory=tuple)

    @property
    def data_dir(self) -> Path:
        return DEFAULT_DATA_DIR / self.slug

    @property
    def json_path(self) -> Path:
        return self.data_dir / "records.json"

    @property
    def xlsx_path(self) -> Path:
        return self.data_dir / f"{self.slug}_contacts.xlsx"


def load_city_config(slug: str, config_dir: Path = DEFAULT_CONFIG_DIR) -> CityConfig:
    path = config_dir / f"{slug}.json"
    if not path.exists():
        available = ", ".join(sorted(item.stem for item in config_dir.glob("*.json")))
        raise FileNotFoundError(
            f"City config '{slug}' not found in {config_dir}. Available: {available or 'none'}"
        )

    with path.open("r", encoding="utf-8") as file:
        data: dict[str, Any] = json.load(file)

    bbox = data["bbox"]
    if len(bbox) != 4:
        raise ValueError("bbox must contain [south, west, north, east]")

    return CityConfig(
        slug=data["slug"],
        name=data["name"],
        country=data["country"],
        bbox=tuple(float(value) for value in bbox),  # type: ignore[arg-type]
        language_keywords=tuple(data.get("language_keywords", [])),
        business_type_keywords={
            str(name): tuple(values)
            for name, values in data.get("business_type_keywords", {}).items()
        },
        seed_urls=tuple(data.get("seed_urls", [])),
        overpass_extra_filters=tuple(data.get("overpass_extra_filters", [])),
    )


def list_city_configs(config_dir: Path = DEFAULT_CONFIG_DIR) -> list[str]:
    return sorted(path.stem for path in config_dir.glob("*.json"))


def list_city_groups() -> list[str]:
    return sorted(CITY_GROUPS)


def get_city_group(name: str) -> tuple[str, ...]:
    if name not in CITY_GROUPS:
        available = ", ".join(list_city_groups())
        raise KeyError(f"City group '{name}' not found. Available: {available or 'none'}")
    return CITY_GROUPS[name]
