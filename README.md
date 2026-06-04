# mc-localize

`mc-localize` is a local-first tool for Minecraft Java Edition modded instances.

It scans a modded instance, extracts strings needed for localization work, exports translation-friendly files, validates edited translations, and builds a resource pack that can be installed manually.

The tool does not translate text by itself. Translation is expected to happen outside the tool, either manually or with AI/MT workflows chosen by the user.

## Current Scope

Phase 1 focuses on:

- Detecting an instance root or `.minecraft` game root.
- Detecting Minecraft version and resource-pack `pack_format` when launcher metadata is available.
- Extracting language JSON files from `mods/*.jar`.
- Extracting language JSON files from `kubejs/assets/**/lang`.
- Exporting `strings.csv` and `strings.jsonl`.
- Building `assets/<namespace>/lang/<target-locale>.json` files from edited work files.
- Generating `pack.mcmeta`, a zip file, and manual installation instructions.

## Example

```powershell
python -m mc_localize scan --instance "D:\Document\Prism\instances\FTB StoneBlock 3" --out work/catalog.jsonl --target-locale ja_jp
python -m mc_localize export --catalog work/catalog.jsonl --target-locale ja_jp --out work/export/ja_jp
python -m mc_localize validate --catalog work/catalog.jsonl --translations work/export/ja_jp/strings.csv --target-locale ja_jp
python -m mc_localize build --catalog work/catalog.jsonl --translations work/export/ja_jp/strings.csv --target-locale ja_jp --out dist/ftb-stoneblock-3-ja_jp
```

After `build`, copy the generated zip into the instance's `resourcepacks` directory and enable it in Minecraft or your launcher.

## Scan Reports

Use report outputs when you want to keep a record of what was extracted:

```powershell
python -m mc_localize scan --instance "D:\Document\Prism\instances\FTB StoneBlock 3" --out work/before-launch.jsonl --target-locale ja_jp --report-out work/reports/before-launch.json --text-report-out work/reports/before-launch.txt
```

To compare two scans, for example before and after launching Minecraft once:

```powershell
python -m mc_localize compare --before work/before-launch.jsonl --after work/after-launch.jsonl --report-out work/reports/launch-diff.json --text-report-out work/reports/launch-diff.txt
```

## Export Context

Exported work files include columns for filtering and review:

- `namespace`: the mod/resource namespace.
- `key`: the original language key.
- `key_prefix`: the first two key segments, useful for grouping.
- `inferred_category`: a best-effort category such as `item`, `block`, `entity`, `gui`, or `tooltip`.
- `source_path` and `entry_path`: where the source text came from.
- `existing_target_text`: existing target-locale text when `scan --target-locale` found one.

Existing target text is exported as reference data. It is not copied into `translated_text` automatically.

You can filter or split exports to keep translation batches manageable:

```powershell
python -m mc_localize export --catalog work/catalog.jsonl --target-locale ja_jp --out work/export/missing-blocks --category block --missing-target-only
python -m mc_localize export --catalog work/catalog.jsonl --target-locale ja_jp --out work/export/chipped --namespace chipped
python -m mc_localize export --catalog work/catalog.jsonl --target-locale ja_jp --out work/export/by-namespace --missing-target-only --split-by namespace
```

## Development

```powershell
python -m unittest discover -s tests
```

This project intentionally avoids committing real mod jars, generated catalogs, generated translation work files, or built resource packs.
