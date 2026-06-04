from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from mc_localize.build_resource_pack import BuildOptions, build_resource_pack
from mc_localize.catalog import read_jsonl, write_jsonl
from mc_localize.export_workfiles import ExportOptions, export_workfiles
from mc_localize.instance import detect_instance
from mc_localize.reports import compare_catalogs, write_json_report, write_text_report
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
    scan.add_argument("--target-locale", help="also collect existing target-locale text as export metadata")
    scan.add_argument("--minecraft-version")
    scan.add_argument("--pack-format", type=int)
    scan.add_argument("--report-out", type=Path, help="write a JSON scan report")
    scan.add_argument("--text-report-out", type=Path, help="write a human-readable scan report")
    scan.set_defaults(func=_cmd_scan)

    export = subcommands.add_parser("export", help="export translation work files")
    export.add_argument("--catalog", required=True, type=Path)
    export.add_argument("--target-locale", required=True)
    export.add_argument("--out", required=True, type=Path)
    export.add_argument("--namespace", action="append", default=[], help="only export a namespace; may be repeated")
    export.add_argument("--category", action="append", default=[], help="only export an inferred category; may be repeated")
    export.add_argument("--missing-target-only", action="store_true", help="only export rows without existing target text")
    export.add_argument(
        "--target-matches-source-only",
        action="store_true",
        help="only export rows where existing target text equals source text",
    )
    export.add_argument("--split-by", choices=["namespace"], help="also write split work files")
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
    build.add_argument(
        "--untranslated",
        choices=["skip", "existing-target", "source"],
        default="skip",
        help="how to handle rows without translated_text",
    )
    build.set_defaults(func=_cmd_build)

    compare = subcommands.add_parser("compare", help="compare two catalog.jsonl files")
    compare.add_argument("--before", required=True, type=Path)
    compare.add_argument("--after", required=True, type=Path)
    compare.add_argument("--report-out", type=Path, help="write a JSON compare report")
    compare.add_argument("--text-report-out", type=Path, help="write a human-readable compare report")
    compare.set_defaults(func=_cmd_compare)

    return parser


def _cmd_scan(args: argparse.Namespace) -> int:
    entries, metadata = scan_instance(
        args.instance,
        source_locale=args.source_locale,
        target_locale=args.target_locale,
        minecraft_version=args.minecraft_version,
        pack_format=args.pack_format,
    )
    count = write_jsonl(args.out, entries)
    result = {"catalog": str(args.out), "rows": count, **metadata}
    if args.report_out:
        write_json_report(args.report_out, result)
        result["report"] = str(args.report_out)
    if args.text_report_out:
        write_text_report(args.text_report_out, "Scan Report", result)
        result["text_report"] = str(args.text_report_out)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


def _cmd_export(args: argparse.Namespace) -> int:
    entries = read_jsonl(args.catalog)
    options = ExportOptions(
        namespaces=set(args.namespace),
        categories=set(args.category),
        missing_target_only=args.missing_target_only,
        target_matches_source_only=args.target_matches_source_only,
        split_by=args.split_by,
    )
    result = export_workfiles(entries, args.out, args.target_locale, options=options)
    output = dict(result)
    if output.get("split_outputs"):
        output["split_output_count"] = len(output["split_outputs"])
        output["split_outputs"] = output["split_outputs"][:20]
        output["split_outputs_truncated"] = output["split_output_count"] > 20
    print(json.dumps(output, ensure_ascii=False, indent=2))
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
        options=BuildOptions(untranslated=args.untranslated),
    )
    result["validation_warning_count"] = len(validation.warnings)
    result["warnings"] = validation.warnings[:20]
    result["warnings_truncated"] = len(validation.warnings) > 20
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


def _cmd_compare(args: argparse.Namespace) -> int:
    before = read_jsonl(args.before)
    after = read_jsonl(args.after)
    result = compare_catalogs(before, after)
    if args.report_out:
        write_json_report(args.report_out, result)
        result["report"] = str(args.report_out)
    if args.text_report_out:
        write_text_report(args.text_report_out, "Catalog Compare Report", result)
        result["text_report"] = str(args.text_report_out)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0
