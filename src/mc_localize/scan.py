from __future__ import annotations

from pathlib import Path

from mc_localize.catalog import CatalogEntry
from mc_localize.extractors.lang_json import extract_from_kubejs, extract_from_mod_jars
from mc_localize.instance import detect_instance
from mc_localize.reports import summarize_catalog


def scan_instance(
    instance_path: Path,
    source_locale: str = "en_us",
    minecraft_version: str | None = None,
    pack_format: int | None = None,
) -> tuple[list[CatalogEntry], dict]:
    info = detect_instance(instance_path, minecraft_version=minecraft_version, pack_format=pack_format)
    entries = []
    entries.extend(extract_from_mod_jars(info.game_root, source_locale))
    entries.extend(extract_from_kubejs(info.game_root, source_locale))
    summary = summarize_catalog(entries)
    metadata = {
        "instance_root": str(info.instance_root),
        "game_root": str(info.game_root),
        "minecraft_version": info.minecraft_version,
        "pack_format": info.pack_format,
        "source_locale": source_locale,
        "summary": summary,
    }
    return entries, metadata
