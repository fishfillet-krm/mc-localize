from __future__ import annotations

from collections import Counter
import json
from pathlib import Path

from mc_localize.catalog import CatalogEntry
from mc_localize.selection import select_export_entries


def summarize_catalog(entries: list[CatalogEntry]) -> dict:
    active_entries = select_export_entries(entries)
    errors = [entry for entry in entries if entry.source_type == "error"]
    supported = [entry for entry in entries if entry.output_strategy == "resource_pack_lang"]
    overridden = len(supported) - len(active_entries)

    return {
        "rows": len(entries),
        "translatable_entries": len(supported),
        "exportable_entries": len(active_entries),
        "overridden_entries": overridden,
        "error_entries": len(errors),
        "source_types": _count_by(entries, "source_type"),
        "namespace_count": len({entry.namespace for entry in supported}),
        "top_namespaces": _top_counts(supported, "namespace", limit=20),
        "errors": [
            {
                "source_path": entry.source_path,
                "entry_path": entry.entry_path,
                "notes": entry.notes,
            }
            for entry in errors
        ],
    }


def summarize_export(entries: list[CatalogEntry], exported_count: int) -> dict:
    catalog = summarize_catalog(entries)
    return {
        "catalog_rows": catalog["rows"],
        "exported_entries": exported_count,
        "overridden_entries": catalog["overridden_entries"],
        "error_entries": catalog["error_entries"],
    }


def compare_catalogs(before: list[CatalogEntry], after: list[CatalogEntry]) -> dict:
    before_by_id = {entry.id: entry for entry in before}
    after_by_id = {entry.id: entry for entry in after}
    before_ids = set(before_by_id)
    after_ids = set(after_by_id)
    common_ids = before_ids & after_ids
    changed_ids = sorted(
        entry_id
        for entry_id in common_ids
        if before_by_id[entry_id].source_hash != after_by_id[entry_id].source_hash
    )

    return {
        "before": summarize_catalog(before),
        "after": summarize_catalog(after),
        "added_entries": len(after_ids - before_ids),
        "removed_entries": len(before_ids - after_ids),
        "changed_entries": len(changed_ids),
        "added": _entry_refs(after_by_id[entry_id] for entry_id in sorted(after_ids - before_ids)[:50]),
        "removed": _entry_refs(before_by_id[entry_id] for entry_id in sorted(before_ids - after_ids)[:50]),
        "changed": [
            {
                "id": entry_id,
                "namespace": after_by_id[entry_id].namespace,
                "key": after_by_id[entry_id].key,
                "before_source_text": before_by_id[entry_id].source_text,
                "after_source_text": after_by_id[entry_id].source_text,
            }
            for entry_id in changed_ids[:50]
        ],
    }


def write_json_report(path: Path, report: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_text_report(path: Path, title: str, report: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(format_text_report(title, report), encoding="utf-8")


def format_text_report(title: str, report: dict) -> str:
    lines = [title, "=" * len(title), ""]
    if "summary" in report:
        _append_summary(lines, report["summary"])
    elif {"before", "after", "added_entries", "removed_entries", "changed_entries"} <= set(report):
        lines.extend(
            [
                "Before:",
            ]
        )
        _append_summary(lines, report["before"], indent="  ")
        lines.extend(
            [
                "After:",
            ]
        )
        _append_summary(lines, report["after"], indent="  ")
        lines.extend(
            [
                "Diff:",
                f"  added_entries: {report['added_entries']}",
                f"  removed_entries: {report['removed_entries']}",
                f"  changed_entries: {report['changed_entries']}",
                "",
            ]
        )
    else:
        for key, value in report.items():
            lines.append(f"{key}: {value}")
    return "\n".join(lines).rstrip() + "\n"


def _count_by(entries: list[CatalogEntry], attribute: str) -> dict[str, int]:
    counter = Counter(str(getattr(entry, attribute)) for entry in entries)
    return dict(sorted(counter.items()))


def _top_counts(entries: list[CatalogEntry], attribute: str, limit: int) -> dict[str, int]:
    counter = Counter(str(getattr(entry, attribute)) for entry in entries)
    return dict(counter.most_common(limit))


def _entry_refs(entries) -> list[dict]:
    return [
        {
            "id": entry.id,
            "source_type": entry.source_type,
            "source_path": entry.source_path,
            "entry_path": entry.entry_path,
            "namespace": entry.namespace,
            "key": entry.key,
        }
        for entry in entries
    ]


def _append_summary(lines: list[str], summary: dict, indent: str = "") -> None:
    for key in [
        "rows",
        "translatable_entries",
        "exportable_entries",
        "overridden_entries",
        "error_entries",
        "namespace_count",
    ]:
        if key in summary:
            lines.append(f"{indent}{key}: {summary[key]}")
    if summary.get("source_types"):
        lines.append(f"{indent}source_types:")
        for source_type, count in summary["source_types"].items():
            lines.append(f"{indent}  {source_type}: {count}")
    if summary.get("top_namespaces"):
        lines.append(f"{indent}top_namespaces:")
        for namespace, count in summary["top_namespaces"].items():
            lines.append(f"{indent}  {namespace}: {count}")
    if summary.get("errors"):
        lines.append(f"{indent}errors:")
        for error in summary["errors"][:20]:
            notes = "; ".join(error.get("notes", []))
            lines.append(f"{indent}  {error.get('source_path', '')}:{error.get('entry_path', '')} - {notes}")
    lines.append("")
