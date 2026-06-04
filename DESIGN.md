# Minecraft Modded Instance Localization Pack Builder - Design

## Purpose

This project is a generic tool for Minecraft Java Edition modded instances. Given an instance directory, it mechanically extracts data needed to translate that exact launch configuration, organizes the extracted strings into translation-friendly files, and later converts the completed translations into files Minecraft can apply.

The tool does not translate text by itself. Translation is performed outside the tool, either manually or with AI/MT tools chosen by the user.

## Core Scope

The tool is responsible for:

- Scanning a Minecraft instance or `.minecraft` directory.
- Detecting Minecraft version, loader metadata, mods, resource packs, KubeJS files, quests, books, and other supported localization sources.
- Extracting user-visible strings and stable metadata.
- Producing translation work files that are easy to edit manually or pass to external AI/translation workflows.
- Validating edited translation files.
- Building a Minecraft-applicable resource pack and, where resource packs alone are insufficient, optional overlay files.
- Packaging the generated result and producing clear manual installation guidance.

The tool is not responsible for:

- Machine translation.
- Translation quality review.
- Hosting or distributing translated packs.
- Managing one specific modpack as a product.
- Modifying original mod jars.
- Editing the original instance in place by default.
- Enabling generated packs in launcher or Minecraft options files.

## Example Reference Instance

The initial test instance is:

- `D:\Document\Prism\instances\FTB StoneBlock 3`
- Minecraft `1.18.2`
- Forge `40.2.34`
- Resource pack `pack_format`: `8`

This instance is a fixture for design and testing, not the identity of the project. The tool must remain usable with other PrismLauncher, vanilla launcher, CurseForge, Modrinth, and server-style directories where the file layout is compatible.

## Basic Workflow

1. `scan`
   - Read an instance directory.
   - Detect supported sources.
   - Produce an extraction catalog.

2. `export`
   - Convert the catalog into editable translation work files.
   - Keep enough metadata to rebuild Minecraft paths after translation.

3. External translation
   - The user edits the exported files manually or with external AI/translation tools.
   - This step is outside the tool.

4. `validate`
   - Check translated files for missing entries, invalid placeholders, broken JSON, duplicate keys, and unsupported output cases.

5. `build`
   - Generate a resource pack from the translated files.
   - Generate optional overlay files for formats that cannot be represented by a resource pack alone.

6. Manual installation
   - The user copies the generated pack into the target instance's `resourcepacks` directory or otherwise installs it using their launcher.
   - The tool may print exact destination paths and checklist-style instructions, but should not write into the instance unless a future explicit install command is added.

## Input Directory Detection

The user may pass either:

- A launcher instance root such as `...\Prism\instances\Pack Name`.
- A direct `.minecraft` root.
- A server or unpacked modpack root containing `mods`, `config`, or `kubejs`.

Detection rules:

- If `.minecraft` exists, treat it as the game root.
- Otherwise, if `mods`, `config`, `resourcepacks`, `kubejs`, or `versions` exists, treat the provided path as the game root.
- Read launcher metadata when available:
  - PrismLauncher/MultiMC: `mmc-pack.json`, `instance.cfg`.
  - CurseForge/Modrinth exports can be supported later through manifest files.
- Determine `pack_format` from Minecraft version.
- If the Minecraft version cannot be detected, require `--minecraft-version` or `--pack-format`.

## Supported Source Types

### Mod Jar Language Files

Paths inside jar files:

- `assets/<namespace>/lang/en_us.json`
- `assets/<namespace>/lang/*.json`
- Legacy: `assets/<namespace>/lang/*.lang`

Extraction behavior:

- Read jar files as zip archives.
- Parse language JSON as key-value maps.
- Keep string values only.
- Record source jar, namespace, language file path, key, source text, and source hash.
- Do not write back to jars.

### Existing Resource Packs

Paths:

- `resourcepacks/*.zip`
- `resourcepacks/<folder>/assets/<namespace>/lang/*.json`

Extraction behavior:

- Treat enabled and bundled packs as higher-priority sources than jars when possible.
- For the first version, scan all packs and report conflicts; enable-state detection can be added later.

### KubeJS Assets

Paths:

- `kubejs/assets/<namespace>/lang/*.json`
- `kubejs/assets/<namespace>/patchouli_books/**`
- `kubejs/assets/<namespace>/tips/**`

Extraction behavior:

- Treat KubeJS assets like resource-pack assets.
- KubeJS can intentionally override mod-provided text, so it should outrank jar language files.

### FTB Quests

Common paths:

- `config/ftbquests/quests/**/*.snbt`

Extraction behavior:

- Extract visible literal strings from chapters, quests, tasks, rewards, descriptions, and groups.
- Mark whether each item can be represented in a resource pack.
- Initially use report/work-file mode only.
- If a later build mode rewrites quest files, output to a generated overlay directory and never mutate the source instance directly.

### Patchouli Books

Common paths:

- `assets/<namespace>/patchouli_books/**`

Extraction behavior:

- Extract book names, category names, entry names, page text, landing text, and tooltips.
- Preserve page structure metadata so translated files can be rebuilt.
- Some books already support language files; others require copied book JSON. The extractor must mark output strategy per entry.

### Candidate Text Sources

These should be optional because they may contain IDs, comments, or non-visible data:

- `config/**/*.toml`
- `config/**/*.json`
- `config/**/*.json5`
- `config/**/*.snbt`
- `config/**/*.yaml`
- `kubejs/**/*.{js,ts}`

Candidate extraction should default to report-only until a format-specific extractor is implemented.

## Normalized Catalog

The catalog is the tool's internal source of truth.

Recommended path:

- `work/catalog.jsonl`

Example row:

```json
{
  "id": "sha256 stable id",
  "source_type": "lang_json",
  "source_path": "mods/create-1.18.2-0.5.1.f.jar",
  "entry_path": "assets/create/lang/en_us.json",
  "namespace": "create",
  "locale": "en_us",
  "key": "block.create.shaft",
  "source_text": "Shaft",
  "source_hash": "sha256 normalized text hash",
  "output_strategy": "resource_pack_lang",
  "priority": 300,
  "notes": []
}
```

Stable ID rules:

- For language keys: hash of `source_type`, `namespace`, `key`, and source locale.
- For literal structured text: hash of `source_type`, source file path, structural path, and nearby stable IDs when available.
- Do not include source text in the stable ID; use `source_hash` to detect changed text.

## Translation Work Files

The exported files are meant for humans and external tools.

Recommended default:

- `work/export/<target-locale>/strings.csv`
- `work/export/<target-locale>/strings.jsonl`

CSV columns:

```text
id,source_type,namespace,key,key_prefix,inferred_category,source_text,has_existing_target,existing_target_text,target_matches_source,translated_text,source_path,entry_path,context,notes
```

JSONL row:

```json
{
  "id": "same id as catalog",
  "source_text": "Shaft",
  "has_existing_target": true,
  "existing_target_text": "シャフト",
  "target_matches_source": false,
  "translated_text": "",
  "context": {
    "namespace": "create",
    "key": "block.create.shaft",
    "key_prefix": "block.create",
    "inferred_category": "block",
    "source_type": "lang_json"
  },
  "notes": []
}
```

The tool should preserve unknown columns in CSV where practical, so users can add review notes without losing them during round trips.

Exports should support common batching filters:

- Include only selected namespaces.
- Include only selected inferred categories.
- Include only rows without existing target-locale text.
- Include only rows where the existing target-locale text is identical to the source text.
- Optionally split output files by namespace.

## Build Inputs

The build command consumes:

- A catalog.
- One or more translated work files.
- Target locale such as `ja_jp`.
- Output options.

The build command should not require a translation memory or any machine translation provider.

## Generated Outputs

### Resource Pack

Recommended output:

- `dist/<instance-name>-<target-locale>/`
- `dist/<instance-name>-<target-locale>.zip`
- `dist/<instance-name>-<target-locale>-install.txt`

Required files:

- `pack.mcmeta`
- `assets/<namespace>/lang/<target-locale>.json`

For Minecraft `1.18.2`:

```json
{
  "pack": {
    "pack_format": 8,
    "description": "Localization pack generated from extracted instance data"
  }
}
```

### Overlay Output

Some sources cannot be applied through language files alone. Examples:

- FTB Quests literal SNBT text.
- Patchouli books that do not use lang keys.
- Config-defined display text.

For these, generate an optional overlay directory:

- `dist/<instance-name>-<target-locale>-overlay/`

The overlay must be explicitly enabled by command flags such as `--include-overlays`.

The first version can build only resource-pack language files and report overlay-required entries as unsupported.

### Installation Guidance

The default output should include a short generated instruction file instead of modifying the user's instance.

For a normal resource pack, the instruction file should include:

- The generated zip path.
- The detected instance resource pack directory, if known.
- The manual copy destination.
- A reminder to enable the pack in Minecraft's resource pack screen or through the user's launcher.
- Any unsupported overlay-required entries found during build or validation.

For overlay outputs, the instruction file must clearly distinguish resource-pack installation from any extra manual file replacement or launcher-specific steps.

## Validation Rules

Validate before building:

- Every translated row references a known catalog ID.
- Required translated rows are present.
- JSON syntax is valid.
- Placeholders are preserved:
  - `%s`, `%1$s`, `%d`, `%f`
  - `{0}`, `{1}`
  - Minecraft formatting codes such as `§a`
  - escaped newlines where required
- No duplicate output keys with conflicting translated values.
- Output files use UTF-8.
- `pack_format` is known for the detected Minecraft version.

Validation should emit:

- Human-readable summary.
- Machine-readable report, e.g. `work/reports/validate.json`.

## Conflict Handling

Multiple sources can define the same language key.

Default priority:

1. KubeJS assets.
2. Existing resource packs.
3. Mod jars.

When conflicts occur:

- Keep all source records in the catalog.
- Choose the highest-priority record for the default export.
- Report lower-priority records as overridden.
- If same key and same priority conflict, require user decision or emit a warning and choose deterministic path order.

## CLI Shape

```powershell
mc-localize scan --instance "D:\Document\Prism\instances\FTB StoneBlock 3" --out work/catalog.jsonl
mc-localize export --catalog work/catalog.jsonl --target-locale ja_jp --out work/export/ja_jp
mc-localize validate --catalog work/catalog.jsonl --translations work/export/ja_jp/strings.csv --target-locale ja_jp
mc-localize build --catalog work/catalog.jsonl --translations work/export/ja_jp/strings.csv --target-locale ja_jp --out dist/ftb-stoneblock-3-ja_jp
```

The command names are provisional. The important distinctions are:

- There is no `translate` command in the core scope.
- There is no default `apply` command. Applying the generated pack is a manual user step unless a future explicit install feature is designed separately.

## Suggested Project Structure

```text
.
├─ README.md
├─ DESIGN.md
├─ pyproject.toml
├─ src/
│  └─ mc_localize/
│     ├─ cli.py
│     ├─ instance.py
│     ├─ pack_format.py
│     ├─ catalog.py
│     ├─ export_workfiles.py
│     ├─ build_resource_pack.py
│     ├─ validate.py
│     ├─ install_guide.py
│     └─ extractors/
│        ├─ lang_json.py
│        ├─ legacy_lang.py
│        ├─ resourcepacks.py
│        ├─ kubejs.py
│        ├─ ftbquests.py
│        └─ patchouli.py
├─ tests/
│  └─ fixtures/
└─ work/
```

Python is a good initial implementation language because jar files are zip files, JSON/CSV handling is built in, and cross-platform filesystem handling is straightforward.

## Implementation Phases

### Phase 1: Minimum Useful Tool

- Detect instance root and game root.
- Detect Minecraft version and `pack_format`.
- Extract `en_us.json` from `mods/*.jar`.
- Extract language JSON from `kubejs/assets/**/lang`.
- Export `strings.csv` and `strings.jsonl`.
- Build `assets/<namespace>/lang/<target-locale>.json` from edited work files.
- Generate `pack.mcmeta`.
- Zip output pack.
- Generate manual installation instructions.

### Phase 2: Safety and Ergonomics

- Validate placeholders.
- Report duplicate and overridden keys.
- Detect existing target-locale files.
- Improve generated installation guidance with exact detected paths.
- Add summary reports.

### Phase 3: More Source Formats

- Legacy `.lang` support.
- Existing resource pack extraction.
- FTB Quests report-only extraction.
- Patchouli extraction.
- Candidate-text reports for configs and KubeJS scripts.

### Phase 4: Overlay Generation

- Generate copied overlay files for formats that cannot be represented by resource-pack language files.
- Keep original instance read-only.
- Provide clear install instructions.
- Consider an explicit install command only after the manual workflow is stable.

### Phase 5: Project Hardening

- Add unit tests with tiny fixture jars and KubeJS directories.
- Add CLI snapshot tests for catalog/export/build output.
- Add GitHub Actions after moving development to GitHub.
- Keep generated `work/` and `dist/` out of version control by default.

## Open Questions

- Should the default source locale always be `en_us`, or should it scan all available source locales?
- Should existing Japanese translations in mods be exported as prefilled translations or treated as references?
- Should CSV or JSONL be the primary editable format?
- Should a later explicit install command exist, or should all installation remain manual?
- Should overlay generation be part of version 1, or should version 1 only report overlay-required text?

## Current Assessment

For the initial reference instance, a Minecraft launch is not required to build Phase 1. The existing directory already contains mod jars and KubeJS language files. Later launches may generate additional files, but the tool should handle that by rescanning rather than depending on a first launch.
