from __future__ import annotations

import csv
import json
from pathlib import Path


def read_translations(path: Path) -> dict[str, str]:
    if path.suffix.lower() == ".jsonl":
        return _read_jsonl_translations(path)
    return _read_csv_translations(path)


def _read_csv_translations(path: Path) -> dict[str, str]:
    translations: dict[str, str] = {}
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        for row_no, row in enumerate(reader, 2):
            entry_id = (row.get("id") or "").strip()
            if not entry_id:
                raise ValueError(f"Missing id at {path}:{row_no}")
            translations[entry_id] = row.get("translated_text") or ""
    return translations


def _read_jsonl_translations(path: Path) -> dict[str, str]:
    translations: dict[str, str] = {}
    with path.open("r", encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, 1):
            line = line.strip()
            if not line:
                continue
            data = json.loads(line)
            entry_id = str(data.get("id") or "").strip()
            if not entry_id:
                raise ValueError(f"Missing id at {path}:{line_no}")
            translations[entry_id] = str(data.get("translated_text") or "")
    return translations
