from __future__ import annotations

from mc_localize.catalog import CatalogEntry


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
