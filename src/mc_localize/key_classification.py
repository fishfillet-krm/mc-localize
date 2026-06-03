from __future__ import annotations


def key_prefix(key: str) -> str:
    parts = key.split(".")
    if len(parts) >= 2:
        return ".".join(parts[:2])
    return key


def inferred_category(key: str) -> str:
    lower = key.lower()
    first = lower.split(".", 1)[0]
    aliases = {
        "advancements": "advancement",
        "attributes": "attribute",
        "biomes": "biome",
        "blocks": "block",
        "effects": "effect",
        "enchantments": "enchantment",
        "entities": "entity",
        "fluids": "fluid",
        "items": "item",
        "itemgroups": "itemgroup",
        "keys": "key",
        "messages": "message",
        "screens": "screen",
        "subtitles": "subtitle",
        "tooltips": "tooltip",
    }
    if first in aliases:
        return aliases[first]
    if first in {
        "advancement",
        "attribute",
        "biome",
        "block",
        "container",
        "death",
        "effect",
        "enchantment",
        "entity",
        "fluid",
        "gui",
        "item",
        "itemgroup",
        "key",
        "menu",
        "message",
        "screen",
        "stat",
        "subtitle",
        "tooltip",
    }:
        return first
    if lower.startswith("block."):
        return "block"
    if lower.startswith("item."):
        return "item"
    if ".tooltip" in lower or lower.startswith("tooltip."):
        return "tooltip"
    if ".advancement" in lower or lower.startswith("advancements."):
        return "advancement"
    if ".jei." in lower or lower.startswith("jei."):
        return "jei"
    if ".config." in lower or lower.startswith("config."):
        return "config"
    if ".gui." in lower or lower.startswith("gui."):
        return "gui"
    return "other"
