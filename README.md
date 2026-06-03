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
python -m mc_localize scan --instance "D:\Document\Prism\instances\FTB StoneBlock 3" --out work/catalog.jsonl
python -m mc_localize export --catalog work/catalog.jsonl --target-locale ja_jp --out work/export/ja_jp
python -m mc_localize validate --catalog work/catalog.jsonl --translations work/export/ja_jp/strings.csv --target-locale ja_jp
python -m mc_localize build --catalog work/catalog.jsonl --translations work/export/ja_jp/strings.csv --target-locale ja_jp --out dist/ftb-stoneblock-3-ja_jp
```

After `build`, copy the generated zip into the instance's `resourcepacks` directory and enable it in Minecraft or your launcher.

## Development

```powershell
python -m unittest discover -s tests
```

This project intentionally avoids committing real mod jars, generated catalogs, generated translation work files, or built resource packs.
