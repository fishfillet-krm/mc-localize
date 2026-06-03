from __future__ import annotations

import csv
import json
from pathlib import Path

from mc_localize.catalog import CatalogEntry


CSV_COLUMNS = ["id", "source_type", "namespace", "key", "source_text", "translated_text", "context", "notes"]


def export_workfiles(entries: list[CatalogEntry], out_dir: Path, target_locale: str) -> dict:
    out_dir.mkdir(parents=True, exist_ok=True)
    exported = select_export_entries(entries)
    csv_path = out_dir / "strings.csv"
    jsonl_path = out_dir / "strings.jsonl"

    with csv_path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=CSV_COLUMNS)
        writer.writeheader()
        for entry in exported:
            writer.writerow(
                {
                    "id": entry.id,
                    "source_type": entry.source_type,
                    "namespace": entry.namespace,
                    "key": entry.key,
                    "source_text": entry.source_text,
                    "translated_text": "",
                    "context": f"{entry.source_path}:{entry.entry_path}",
                    "notes": "; ".join(entry.notes),
                }
            )

    with jsonl_path.open("w", encoding="utf-8", newline="\n") as handle:
        for entry in exported:
            handle.write(
                json.dumps(
                    {
                        "id": entry.id,
                        "source_text": entry.source_text,
                        "translated_text": "",
                        "target_locale": target_locale,
                        "context": {
                            "namespace": entry.namespace,
                            "key": entry.key,
                            "source_type": entry.source_type,
                            "source_path": entry.source_path,
                            "entry_path": entry.entry_path,
                        },
                        "notes": entry.notes,
                    },
                    ensure_ascii=False,
                    sort_keys=True,
                )
            )
            handle.write("\n")

    return {"csv": str(csv_path), "jsonl": str(jsonl_path), "count": len(exported)}


def select_export_entries(entries: list[CatalogEntry]) -> list[CatalogEntry]:
    by_output_key: dict[tuple[str, str, str], CatalogEntry] = {}
    for entry in entries:
        if entry.output_strategy != "resource_pack_lang":
            continue
        output_key = (entry.output_strategy, entry.namespace, entry.key)
        current = by_output_key.get(output_key)
        if current is None or entry.priority > current.priority:
            by_output_key[output_key] = entry
    return sorted(by_output_key.values(), key=lambda entry: (entry.namespace, entry.key, entry.id))
