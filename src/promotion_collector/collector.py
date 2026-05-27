from __future__ import annotations

from dataclasses import dataclass

from promotion_collector.config import CityConfig
from promotion_collector.models import BusinessRecord
from promotion_collector.sources import Source
from promotion_collector.storage import ExcelStore, JsonStore


@dataclass(slots=True)
class CollectionResult:
    scanned: int
    unique: int
    json_path: str
    xlsx_path: str
    sheet_name: str | None
    records: list[BusinessRecord]


class Collector:
    def __init__(self, sources: list[Source]) -> None:
        self.sources = sources

    def collect(self, config: CityConfig, limit: int) -> CollectionResult:
        json_store = JsonStore(config.json_path)
        excel_store = ExcelStore(config.xlsx_path)
        existing_keys = json_store.load_keys()

        scanned = 0
        candidates: list[BusinessRecord] = []
        seen_this_run: set[str] = set()

        for source in self.sources:
            remaining = limit - len(candidates)
            if remaining <= 0:
                break
            for record in source.collect(config, remaining):
                scanned += 1
                key = record.dedupe_key()
                if key in existing_keys or key in seen_this_run:
                    continue
                seen_this_run.add(key)
                candidates.append(record)
                if len(candidates) >= limit:
                    break

        unique_records = json_store.append_unique(candidates)
        sheet_name = excel_store.append_iteration_sheet(unique_records)
        return CollectionResult(
            scanned=scanned,
            unique=len(unique_records),
            json_path=str(config.json_path),
            xlsx_path=str(config.xlsx_path),
            sheet_name=sheet_name,
            records=unique_records,
        )
