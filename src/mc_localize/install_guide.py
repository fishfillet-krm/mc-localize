from __future__ import annotations

from pathlib import Path


def write_install_guide(
    path: Path,
    zip_path: Path,
    resourcepacks_dir: Path | None,
    unsupported_count: int = 0,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "Manual installation",
        "===================",
        "",
        f"Generated resource pack: {zip_path}",
        "",
        "Install steps:",
        "1. Copy the generated resource pack zip.",
    ]
    if resourcepacks_dir is not None:
        lines.append(f"2. Paste it into: {resourcepacks_dir}")
    else:
        lines.append("2. Paste it into the target instance's resourcepacks directory.")
    lines.extend(
        [
            "3. Start Minecraft.",
            "4. Enable the resource pack in the Resource Packs screen or through your launcher.",
            "",
        ]
    )
    if unsupported_count:
        lines.extend(
            [
                "Notes:",
                f"- {unsupported_count} extracted entries could not be represented by a resource-pack language file.",
                "- Check validation/build reports before expecting full coverage.",
                "",
            ]
        )
    path.write_text("\n".join(lines), encoding="utf-8")
