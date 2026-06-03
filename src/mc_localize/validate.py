from __future__ import annotations

from dataclasses import dataclass
import re

from mc_localize.catalog import CatalogEntry
from mc_localize.selection import select_export_entries


PLACEHOLDER_RE = re.compile(r"(%(?:\d+\$)?[sdif])|(\{\d+\})|(§.)")


@dataclass(frozen=True, slots=True)
class ValidationResult:
    errors: list[str]
    warnings: list[str]

    @property
    def ok(self) -> bool:
        return not self.errors


def validate_translations(entries: list[CatalogEntry], translations: dict[str, str]) -> ValidationResult:
    errors: list[str] = []
    warnings: list[str] = []
    active_entries = select_export_entries(entries)
    known = {entry.id: entry for entry in entries}

    for entry_id in sorted(translations):
        if entry_id not in known:
            errors.append(f"Unknown translation id: {entry_id}")

    for entry in active_entries:
        translated = translations.get(entry.id, "")
        if not translated:
            warnings.append(f"Missing translation for {entry.namespace}:{entry.key}")
            continue
        source_tokens = _placeholder_tokens(entry.source_text)
        target_tokens = _placeholder_tokens(translated)
        if source_tokens != target_tokens:
            errors.append(
                "Placeholder mismatch for "
                f"{entry.namespace}:{entry.key}: source={source_tokens!r} translated={target_tokens!r}"
            )

    return ValidationResult(errors=errors, warnings=warnings)


def _placeholder_tokens(value: str) -> list[str]:
    return [match.group(0) for match in PLACEHOLDER_RE.finditer(value)]
