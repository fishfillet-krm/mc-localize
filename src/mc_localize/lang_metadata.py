from __future__ import annotations

from pathlib import Path

from mc_localize.catalog import CatalogEntry
from mc_localize.extractors.lang_json import extract_from_kubejs, extract_from_mod_jars

EXISTING_TARGET_PREFIX = "existing_target_text="


def collect_existing_targets(game_root: Path, target_locale: str | None) -> dict[tuple[str, str], str]:
    if not target_locale:
        return {}
    entries: list[CatalogEntry] = []
    entries.extend(extract_from_mod_jars(game_root, target_locale))
    entries.extend(extract_from_kubejs(game_root, target_locale))
    targets: dict[tuple[str, str], str] = {}
    for entry in entries:
        if entry.output_strategy != "resource_pack_lang":
            continue
        targets[(entry.namespace, entry.key)] = entry.source_text
    return targets


def attach_existing_targets(entries: list[CatalogEntry], existing_targets: dict[tuple[str, str], str]) -> None:
    if not existing_targets:
        return
    for entry in entries:
        target_text = existing_targets.get((entry.namespace, entry.key))
        if target_text is not None:
            entry.notes.append(f"{EXISTING_TARGET_PREFIX}{target_text}")


def existing_target_text(entry: CatalogEntry) -> str:
    for note in entry.notes:
        if note.startswith(EXISTING_TARGET_PREFIX):
            return note.removeprefix(EXISTING_TARGET_PREFIX)
    return ""


def notes_without_metadata(entry: CatalogEntry) -> list[str]:
    return [note for note in entry.notes if not note.startswith(EXISTING_TARGET_PREFIX)]
