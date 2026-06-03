from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from mc_localize.build_resource_pack import build_resource_pack
from mc_localize.catalog import read_jsonl, write_jsonl
from mc_localize.export_workfiles import export_workfiles
from mc_localize.instance import detect_instance
from mc_localize.scan import scan_instance
from mc_localize.translations import read_translations
from mc_localize.validate import validate_translations


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except Exception as exc:  # noqa: BLE001 - CLI boundary
        print(f"error: {exc}", file=sys.stderr)
        return 1


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="mc-localize")
    subcommands = parser.add_subparsers(required=True)

    scan = subcommands.add_parser("scan", help="scan an instance and write catalog.jsonl")
    scan.add_argument("--instance", required=True, type=Path)
    scan.add_argument("--out", required=True, type=Path)
    scan.add_argument("--source-locale", default="en_us")
    scan.add_argument("--minecraft-version")
    scan.add_argument("--pack-format", type=int)
    scan.set_defaults(func=_cmd_scan)

    export = subcommands.add_parser("export", help="export translation work files")
    export.add_argument("--catalog", required=True, type=Path)
    export.add_argument("--target-locale", required=True)
    export.add_argument("--out", required=True, type=Path)
    export.set_defaults(func=_cmd_export)

    validate = subcommands.add_parser("validate", help="validate translated work files")
    validate.add_argument("--catalog", required=True, type=Path)
    validate.add_argument("--translations", required=True, type=Path)
    validate.add_argument("--target-locale", required=True)
    validate.set_defaults(func=_cmd_validate)

    build = subcommands.add_parser("build", help="build a resource pack from translations")
    build.add_argument("--catalog", required=True, type=Path)
    build.add_argument("--translations", required=True, type=Path)
    build.add_argument("--target-locale", required=True)
    build.add_argument("--out", required=True, type=Path)
    build.add_argument("--instance", type=Path)
    build.add_argument("--minecraft-version")
    build.add_argument("--pack-format", type=int)
    build.set_defaults(func=_cmd_build)

    return parser


def _cmd_scan(args: argparse.Namespace) -> int:
    entries, metadata = scan_instance(
        args.instance,
        source_locale=args.source_locale,
        minecraft_version=args.minecraft_version,
        pack_format=args.pack_format,
    )
    count = write_jsonl(args.out, entries)
    print(json.dumps({"catalog": str(args.out), "rows": count, **metadata}, ensure_ascii=False, indent=2))
    return 0


def _cmd_export(args: argparse.Namespace) -> int:
    entries = read_jsonl(args.catalog)
    result = export_workfiles(entries, args.out, args.target_locale)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


def _cmd_validate(args: argparse.Namespace) -> int:
    entries = read_jsonl(args.catalog)
    translations = read_translations(args.translations)
    result = validate_translations(entries, translations)
    print(json.dumps({"ok": result.ok, "errors": result.errors, "warnings": result.warnings}, ensure_ascii=False, indent=2))
    return 0 if result.ok else 1


def _cmd_build(args: argparse.Namespace) -> int:
    entries = read_jsonl(args.catalog)
    translations = read_translations(args.translations)

    pack_format = args.pack_format
    resourcepacks_dir = None
    if args.instance:
        instance = detect_instance(args.instance, minecraft_version=args.minecraft_version, pack_format=args.pack_format)
        pack_format = pack_format or instance.pack_format
        resourcepacks_dir = instance.resourcepacks_dir
    if pack_format is None:
        raise ValueError("pack_format could not be detected; pass --instance or --pack-format")

    validation = validate_translations(entries, translations)
    if not validation.ok:
        print(json.dumps({"ok": False, "errors": validation.errors, "warnings": validation.warnings}, ensure_ascii=False, indent=2))
        return 1

    result = build_resource_pack(
        entries=entries,
        translations=translations,
        target_locale=args.target_locale,
        out_dir=args.out,
        pack_format=pack_format,
        resourcepacks_dir=resourcepacks_dir,
    )
    result["warnings"] = validation.warnings
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0
