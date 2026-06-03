from __future__ import annotations

from collections import Counter

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


def _count_by(entries: list[CatalogEntry], attribute: str) -> dict[str, int]:
    counter = Counter(str(getattr(entry, attribute)) for entry in entries)
    return dict(sorted(counter.items()))


def _top_counts(entries: list[CatalogEntry], attribute: str, limit: int) -> dict[str, int]:
    counter = Counter(str(getattr(entry, attribute)) for entry in entries)
    return dict(counter.most_common(limit))
