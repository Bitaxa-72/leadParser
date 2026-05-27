from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Iterable

from promotion_collector.config import CityConfig
from promotion_collector.models import BusinessRecord


class Source(ABC):
    name: str

    @abstractmethod
    def collect(self, config: CityConfig, limit: int) -> Iterable[BusinessRecord]:
        """Yield records for a city, stopping after approximately limit records."""
