from __future__ import annotations

import csv
from dataclasses import dataclass, field
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


@dataclass(frozen=True, slots=True)
class ExportOptions:
    namespaces: set[str] = field(default_factory=set)
    categories: set[str] = field(default_factory=set)
    missing_target_only: bool = False
    target_matches_source_only: bool = False
    split_by: str | None = None


def export_workfiles(
    entries: list[CatalogEntry],
    out_dir: Path,
    target_locale: str,
    options: ExportOptions | None = None,
) -> dict:
    options = options or ExportOptions()
    out_dir.mkdir(parents=True, exist_ok=True)
    active_entries = select_export_entries(entries)
    exported = _filter_entries(active_entries, options)
    csv_path = out_dir / "strings.csv"
    jsonl_path = out_dir / "strings.jsonl"

    _write_csv(csv_path, exported)
    _write_jsonl(jsonl_path, exported, target_locale)

    split_outputs = []
    if options.split_by == "namespace":
        split_dir = out_dir / "by-namespace"
        for namespace in sorted({entry.namespace for entry in exported}):
            namespace_entries = [entry for entry in exported if entry.namespace == namespace]
            namespace_dir = split_dir / _safe_filename(namespace)
            namespace_dir.mkdir(parents=True, exist_ok=True)
            namespace_csv = namespace_dir / "strings.csv"
            namespace_jsonl = namespace_dir / "strings.jsonl"
            _write_csv(namespace_csv, namespace_entries)
            _write_jsonl(namespace_jsonl, namespace_entries, target_locale)
            split_outputs.append(
                {
                    "namespace": namespace,
                    "csv": str(namespace_csv),
                    "jsonl": str(namespace_jsonl),
                    "count": len(namespace_entries),
                }
            )

    return {
        "csv": str(csv_path),
        "jsonl": str(jsonl_path),
        "count": len(exported),
        "summary": summarize_export(entries, len(exported)),
        "filters": _options_summary(options),
        "split_outputs": split_outputs,
    }


def _filter_entries(entries: list[CatalogEntry], options: ExportOptions) -> list[CatalogEntry]:
    filtered = []
    for entry in entries:
        target_text = existing_target_text(entry)
        target_matches_source = bool(target_text and target_text == entry.source_text)
        if options.namespaces and entry.namespace not in options.namespaces:
            continue
        if options.categories and inferred_category(entry.key) not in options.categories:
            continue
        if options.missing_target_only and target_text:
            continue
        if options.target_matches_source_only and not target_matches_source:
            continue
        filtered.append(entry)
    return filtered


def _write_csv(path: Path, entries: list[CatalogEntry]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=CSV_COLUMNS)
        writer.writeheader()
        for entry in entries:
            writer.writerow(_csv_row(entry))


def _write_jsonl(path: Path, entries: list[CatalogEntry], target_locale: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for entry in entries:
            handle.write(json.dumps(_jsonl_row(entry, target_locale), ensure_ascii=False, sort_keys=True))
            handle.write("\n")


def _csv_row(entry: CatalogEntry) -> dict[str, str]:
    target_text = existing_target_text(entry)
    has_target = bool(target_text)
    return {
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


def _jsonl_row(entry: CatalogEntry, target_locale: str) -> dict:
    target_text = existing_target_text(entry)
    return {
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
    }


def _options_summary(options: ExportOptions) -> dict:
    return {
        "namespaces": sorted(options.namespaces),
        "categories": sorted(options.categories),
        "missing_target_only": options.missing_target_only,
        "target_matches_source_only": options.target_matches_source_only,
        "split_by": options.split_by,
    }


def _safe_filename(value: str) -> str:
    safe = "".join(char if char.isalnum() or char in "._-" else "_" for char in value)
    return safe or "_"
