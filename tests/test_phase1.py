from __future__ import annotations

import csv
import json
import tempfile
import unittest
from pathlib import Path
from zipfile import ZipFile

from mc_localize.build_resource_pack import build_resource_pack
from mc_localize.catalog import read_jsonl, write_jsonl
from mc_localize.export_workfiles import export_workfiles
from mc_localize.scan import scan_instance


class Phase1Tests(unittest.TestCase):
    def test_scan_export_and_build_resource_pack(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            game_root = root / ".minecraft"
            mods = game_root / "mods"
            mods.mkdir(parents=True)
            (root / "mmc-pack.json").write_text(
                json.dumps({"components": [{"uid": "net.minecraft", "version": "1.18.2"}]}),
                encoding="utf-8",
            )
            with ZipFile(mods / "example.jar", "w") as archive:
                archive.writestr(
                    "assets/example/lang/en_us.json",
                    json.dumps({"item.example.widget": "Widget %s"}),
                )

            entries, metadata = scan_instance(root)
            self.assertEqual(metadata["pack_format"], 8)
            self.assertEqual(len(entries), 1)
            self.assertEqual(metadata["summary"]["translatable_entries"], 1)
            self.assertEqual(metadata["summary"]["error_entries"], 0)

            catalog_path = root / "work" / "catalog.jsonl"
            write_jsonl(catalog_path, entries)
            loaded_entries = read_jsonl(catalog_path)
            export_dir = root / "work" / "export" / "ja_jp"
            export_workfiles(loaded_entries, export_dir, "ja_jp")

            csv_path = export_dir / "strings.csv"
            with csv_path.open("r", encoding="utf-8-sig", newline="") as handle:
                rows = list(csv.DictReader(handle))
            rows[0]["translated_text"] = "ウィジェット %s"
            with csv_path.open("w", encoding="utf-8-sig", newline="") as handle:
                writer = csv.DictWriter(handle, fieldnames=rows[0].keys())
                writer.writeheader()
                writer.writerows(rows)

            translations = {rows[0]["id"]: rows[0]["translated_text"]}
            result = build_resource_pack(loaded_entries, translations, "ja_jp", root / "dist" / "example-ja_jp", 8)

            lang_path = root / "dist" / "example-ja_jp" / "assets" / "example" / "lang" / "ja_jp.json"
            self.assertTrue(lang_path.is_file())
            self.assertTrue(Path(result["zip"]).is_file())
            self.assertTrue(Path(result["install_guide"]).is_file())

    def test_scan_reports_invalid_language_json_without_stopping(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            mods = root / ".minecraft" / "mods"
            mods.mkdir(parents=True)
            with ZipFile(mods / "broken.jar", "w") as archive:
                archive.writestr("assets/broken/lang/en_us.json", "{\n// nope\n}")
            with ZipFile(mods / "good.jar", "w") as archive:
                archive.writestr("assets/good/lang/en_us.json", json.dumps({"item.good.thing": "Thing"}))

            entries, metadata = scan_instance(root, minecraft_version="1.18.2")

            self.assertEqual(metadata["summary"]["translatable_entries"], 1)
            self.assertEqual(metadata["summary"]["error_entries"], 1)
            self.assertEqual(metadata["summary"]["source_types"]["error"], 1)
            self.assertEqual(metadata["summary"]["source_types"]["lang_json"], 1)
            error = next(entry for entry in entries if entry.source_type == "error")
            self.assertIn("could not be parsed", error.notes[0])


if __name__ == "__main__":
    unittest.main()
