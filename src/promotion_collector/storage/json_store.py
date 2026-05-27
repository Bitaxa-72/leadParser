from __future__ import annotations

import json
from pathlib import Path

from promotion_collector.models import BusinessRecord


class JsonStore:
    def __init__(self, path: Path) -> None:
        self.path = path

    def load_keys(self) -> set[str]:
        return {record.dedupe_key() for record in self.load_records()}

    def load_records(self) -> list[BusinessRecord]:
        if not self.path.exists():
            return []
        with self.path.open("r", encoding="utf-8") as file:
            payload = json.load(file)
        return [BusinessRecord.from_json(item) for item in payload.get("records", [])]

    def append_unique(self, records: list[BusinessRecord]) -> list[BusinessRecord]:
        existing_records = self.load_records()
        existing_keys = {record.dedupe_key() for record in existing_records}
        unique_records: list[BusinessRecord] = []

        for record in records:
            key = record.dedupe_key()
            if key in existing_keys:
                continue
            existing_keys.add(key)
            unique_records.append(record)

        if unique_records:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            all_records = existing_records + unique_records
            payload = {
                "version": 1,
                "count": len(all_records),
                "records": [record.to_json() for record in all_records],
            }
            with self.path.open("w", encoding="utf-8") as file:
                json.dump(payload, file, ensure_ascii=False, indent=2)

        return unique_records
