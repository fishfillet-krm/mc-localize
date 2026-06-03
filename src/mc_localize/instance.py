from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path


@dataclass(frozen=True, slots=True)
class InstanceInfo:
    instance_root: Path
    game_root: Path
    minecraft_version: str | None
    pack_format: int | None

    @property
    def resourcepacks_dir(self) -> Path:
        return self.game_root / "resourcepacks"


PACK_FORMAT_BY_MAJOR_MINOR: list[tuple[tuple[int, int], tuple[int, int], int]] = [
    ((1, 6), (1, 8), 1),
    ((1, 9), (1, 10), 2),
    ((1, 11), (1, 12), 3),
    ((1, 13), (1, 14), 4),
    ((1, 15), (1, 16), 5),
    ((1, 17), (1, 17), 7),
    ((1, 18), (1, 18), 8),
    ((1, 19), (1, 19), 9),
    ((1, 20), (1, 20), 15),
]


def detect_instance(path: Path, minecraft_version: str | None = None, pack_format: int | None = None) -> InstanceInfo:
    root = path.resolve()
    game_root = root / ".minecraft" if (root / ".minecraft").is_dir() else root
    detected_version = minecraft_version or _read_prism_minecraft_version(root)
    detected_pack_format = pack_format if pack_format is not None else pack_format_for_version(detected_version)
    return InstanceInfo(
        instance_root=root,
        game_root=game_root,
        minecraft_version=detected_version,
        pack_format=detected_pack_format,
    )


def pack_format_for_version(version: str | None) -> int | None:
    if not version:
        return None
    parts = version.split(".")
    if len(parts) < 2:
        return None
    try:
        major_minor = (int(parts[0]), int(parts[1]))
    except ValueError:
        return None
    for minimum, maximum, pack_format in PACK_FORMAT_BY_MAJOR_MINOR:
        if minimum <= major_minor <= maximum:
            return pack_format
    return None


def _read_prism_minecraft_version(instance_root: Path) -> str | None:
    metadata_path = instance_root / "mmc-pack.json"
    if not metadata_path.is_file():
        return None
    try:
        data = json.loads(metadata_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    for component in data.get("components", []):
        if component.get("uid") == "net.minecraft":
            version = component.get("version") or component.get("cachedVersion")
            return str(version) if version else None
    return None
