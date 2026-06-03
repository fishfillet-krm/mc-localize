from __future__ import annotations

import json
from pathlib import Path
import shutil

from mc_localize.catalog import CatalogEntry
from mc_localize.install_guide import write_install_guide
from mc_localize.selection import select_export_entries


def build_resource_pack(
    entries: list[CatalogEntry],
    translations: dict[str, str],
    target_locale: str,
    out_dir: Path,
    pack_format: int,
    resourcepacks_dir: Path | None = None,
) -> dict:
    out_dir.mkdir(parents=True, exist_ok=True)
    lang_by_namespace: dict[str, dict[str, str]] = {}
    unsupported_count = 0

    supported_ids = {entry.id for entry in select_export_entries(entries)}
    unsupported_count = len([entry for entry in entries if entry.output_strategy != "resource_pack_lang"])

    for entry in entries:
        if entry.id not in supported_ids:
            continue
        translated = translations.get(entry.id, "")
        if not translated:
            continue
        lang_by_namespace.setdefault(entry.namespace, {})[entry.key] = translated

    for namespace, lang_values in sorted(lang_by_namespace.items()):
        lang_dir = out_dir / "assets" / namespace / "lang"
        lang_dir.mkdir(parents=True, exist_ok=True)
        lang_path = lang_dir / f"{target_locale}.json"
        lang_path.write_text(
            json.dumps(dict(sorted(lang_values.items())), ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )

    pack_mcmeta = {
        "pack": {
            "pack_format": pack_format,
            "description": "Localization pack generated from extracted instance data",
        }
    }
    (out_dir / "pack.mcmeta").write_text(
        json.dumps(pack_mcmeta, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    zip_base = out_dir.with_suffix("")
    zip_path = Path(shutil.make_archive(str(zip_base), "zip", root_dir=out_dir))
    install_path = out_dir.with_name(f"{out_dir.name}-install.txt")
    write_install_guide(install_path, zip_path, resourcepacks_dir, unsupported_count=unsupported_count)

    return {
        "out_dir": str(out_dir),
        "zip": str(zip_path),
        "install_guide": str(install_path),
        "namespaces": len(lang_by_namespace),
        "translated_entries": sum(len(values) for values in lang_by_namespace.values()),
        "unsupported_entries": unsupported_count,
    }
