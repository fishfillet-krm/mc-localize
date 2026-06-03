from __future__ import annotations

import csv
import json
from pathlib import Path

from mc_localize.catalog import CatalogEntry
from mc_localize.key_classification import inferred_category, key_prefix
from mc_localize.lang_metadata import existing_target_text, notes_without_metadata
from mc_localize.reports import summarize_export
from mc_localize.selection import select_export_entries


CSV_COLUMNS = [
    "id",
    "source_type",
    "namespace",
    "key",
    "key_prefix",
    "inferred_category",
    "source_text",
    "has_existing_target",
    "existing_target_text",
    "target_matches_source",
    "translated_text",
    "source_path",
    "entry_path",
    "context",
    "notes",
]


def export_workfiles(entries: list[CatalogEntry], out_dir: Path, target_locale: str) -> dict:
    out_dir.mkdir(parents=True, exist_ok=True)
    exported = select_export_entries(entries)
    csv_path = out_dir / "strings.csv"
    jsonl_path = out_dir / "strings.jsonl"

    with csv_path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=CSV_COLUMNS)
        writer.writeheader()
        for entry in exported:
            target_text = existing_target_text(entry)
            has_target = bool(target_text)
            writer.writerow(
                {
                    "id": entry.id,
                    "source_type": entry.source_type,
                    "namespace": entry.namespace,
                    "key": entry.key,
                    "key_prefix": key_prefix(entry.key),
                    "inferred_category": inferred_category(entry.key),
                    "source_text": entry.source_text,
                    "has_existing_target": "yes" if has_target else "no",
                    "existing_target_text": target_text,
                    "target_matches_source": "yes" if has_target and target_text == entry.source_text else "no",
                    "translated_text": "",
                    "source_path": entry.source_path,
                    "entry_path": entry.entry_path,
                    "context": f"{entry.source_path}:{entry.entry_path}",
                    "notes": "; ".join(notes_without_metadata(entry)),
                }
            )

    with jsonl_path.open("w", encoding="utf-8", newline="\n") as handle:
        for entry in exported:
            target_text = existing_target_text(entry)
            handle.write(
                json.dumps(
                    {
                        "id": entry.id,
                        "source_text": entry.source_text,
                        "has_existing_target": bool(target_text),
                        "existing_target_text": target_text,
                        "target_matches_source": bool(target_text and target_text == entry.source_text),
                        "translated_text": "",
                        "target_locale": target_locale,
                        "context": {
                            "namespace": entry.namespace,
                            "key": entry.key,
                            "key_prefix": key_prefix(entry.key),
                            "inferred_category": inferred_category(entry.key),
                            "source_type": entry.source_type,
                            "source_path": entry.source_path,
                            "entry_path": entry.entry_path,
                        },
                        "notes": notes_without_metadata(entry),
                    },
                    ensure_ascii=False,
                    sort_keys=True,
                )
            )
            handle.write("\n")

    return {"csv": str(csv_path), "jsonl": str(jsonl_path), "count": len(exported), "summary": summarize_export(entries, len(exported))}
