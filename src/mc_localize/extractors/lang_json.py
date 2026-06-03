from __future__ import annotations

import json
from pathlib import Path
import re
from zipfile import BadZipFile, ZipFile

from mc_localize.catalog import CatalogEntry, sha256_text, stable_lang_id

LANG_JSON_RE = re.compile(r"^assets/([^/]+)/lang/([^/]+)\.json$")


def extract_from_mod_jars(game_root: Path, source_locale: str) -> list[CatalogEntry]:
    mods_dir = game_root / "mods"
    if not mods_dir.is_dir():
        return []

    entries: list[CatalogEntry] = []
    for jar_path in sorted(mods_dir.glob("*.jar")):
        try:
            entries.extend(_extract_from_zip(jar_path, jar_path.name, source_locale, priority=300))
        except BadZipFile:
            entries.append(
                CatalogEntry(
                    id=sha256_text(f"bad_zip\0{jar_path.name}"),
                    source_type="error",
                    source_path=f"mods/{jar_path.name}",
                    entry_path="",
                    namespace="",
                    locale=source_locale,
                    key="",
                    source_text="",
                    source_hash="",
                    output_strategy="none",
                    priority=0,
                    notes=["Jar could not be read as a zip archive."],
                )
            )
    return entries


def extract_from_kubejs(game_root: Path, source_locale: str) -> list[CatalogEntry]:
    kubejs_assets = game_root / "kubejs" / "assets"
    if not kubejs_assets.is_dir():
        return []

    entries: list[CatalogEntry] = []
    pattern = f"*/lang/{source_locale}.json"
    for lang_path in sorted(kubejs_assets.glob(pattern)):
        namespace = lang_path.parts[-3]
        entry_path = f"assets/{namespace}/lang/{source_locale}.json"
        source_path = _relative_or_absolute(lang_path, game_root)
        entries.extend(
            _entries_from_json_text(
                text=lang_path.read_text(encoding="utf-8"),
                source_type="kubejs_lang_json",
                source_path=source_path,
                entry_path=entry_path,
                namespace=namespace,
                locale=source_locale,
                priority=1000,
            )
        )
    return entries


def _extract_from_zip(zip_path: Path, zip_name: str, source_locale: str, priority: int) -> list[CatalogEntry]:
    entries: list[CatalogEntry] = []
    with ZipFile(zip_path) as archive:
        for member in sorted(archive.namelist()):
            match = LANG_JSON_RE.match(member)
            if not match:
                continue
            namespace, locale = match.groups()
            if locale != source_locale:
                continue
            raw = archive.read(member).decode("utf-8-sig")
            entries.extend(
                _entries_from_json_text(
                    text=raw,
                    source_type="lang_json",
                    source_path=f"mods/{zip_name}",
                    entry_path=member,
                    namespace=namespace,
                    locale=locale,
                    priority=priority,
                )
            )
    return entries


def _entries_from_json_text(
    text: str,
    source_type: str,
    source_path: str,
    entry_path: str,
    namespace: str,
    locale: str,
    priority: int,
) -> list[CatalogEntry]:
    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        return [
            CatalogEntry(
                id=sha256_text(f"invalid_json\0{source_path}\0{entry_path}"),
                source_type="error",
                source_path=source_path,
                entry_path=entry_path,
                namespace=namespace,
                locale=locale,
                key="",
                source_text="",
                source_hash="",
                output_strategy="none",
                priority=0,
                notes=[f"Language JSON could not be parsed: {exc}"],
            )
        ]
    if not isinstance(data, dict):
        return []

    entries: list[CatalogEntry] = []
    for key, value in sorted(data.items()):
        if not isinstance(value, str):
            continue
        entries.append(
            CatalogEntry(
                id=stable_lang_id(source_type, namespace, key, locale),
                source_type=source_type,
                source_path=source_path,
                entry_path=entry_path,
                namespace=namespace,
                locale=locale,
                key=key,
                source_text=value,
                source_hash=sha256_text(value),
                output_strategy="resource_pack_lang",
                priority=priority,
                notes=[],
            )
        )
    return entries


def _relative_or_absolute(path: Path, base: Path) -> str:
    try:
        return path.relative_to(base).as_posix()
    except ValueError:
        return str(path)
