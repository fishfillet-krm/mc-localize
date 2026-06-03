from __future__ import annotations

from dataclasses import asdict, dataclass, field
import hashlib
import json
from pathlib import Path
from typing import Iterable


@dataclass(slots=True)
class CatalogEntry:
    id: str
    source_type: str
    source_path: str
    entry_path: str
    namespace: str
    locale: str
    key: str
    source_text: str
    source_hash: str
    output_strategy: str
    priority: int
    notes: list[str] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict) -> "CatalogEntry":
        return cls(
            id=str(data["id"]),
            source_type=str(data["source_type"]),
            source_path=str(data["source_path"]),
            entry_path=str(data["entry_path"]),
            namespace=str(data["namespace"]),
            locale=str(data["locale"]),
            key=str(data["key"]),
            source_text=str(data["source_text"]),
            source_hash=str(data["source_hash"]),
            output_strategy=str(data["output_strategy"]),
            priority=int(data["priority"]),
            notes=list(data.get("notes", [])),
        )

    def to_dict(self) -> dict:
        return asdict(self)


def stable_lang_id(source_type: str, namespace: str, key: str, locale: str) -> str:
    return sha256_text("\0".join([source_type, namespace, key, locale]))


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def write_jsonl(path: Path, entries: Iterable[CatalogEntry]) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for entry in entries:
            handle.write(json.dumps(entry.to_dict(), ensure_ascii=False, sort_keys=True))
            handle.write("\n")
            count += 1
    return count


def read_jsonl(path: Path) -> list[CatalogEntry]:
    entries: list[CatalogEntry] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, 1):
            line = line.strip()
            if not line:
                continue
            try:
                entries.append(CatalogEntry.from_dict(json.loads(line)))
            except (KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
                raise ValueError(f"Invalid catalog row at {path}:{line_no}: {exc}") from exc
    return entries
