from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from typing import Any


_ALIEN_NUMBER_RE = re.compile(r"\b(\d{6})-(\d{7})\b")
_PASSPORT_RE = re.compile(r"\b([A-Z])(\d{4})(\d{4})\b")
_PHONE_RE = re.compile(r"\b(01[016789])-(\d{3,4})-(\d{4})\b")


def mask(text: str) -> tuple[str, list[dict[str, Any]]]:
    restore_map: list[dict[str, Any]] = []
    masked = text
    offset = 0

    for match, replacement in _find_replacements(text):
        start, end = match.span()
        masked_start = start + offset
        masked_end = end + offset
        masked = masked[:masked_start] + replacement + masked[masked_end:]
        restore_map.append(
            {
                "start": masked_start,
                "end": masked_start + len(replacement),
                "original": match.group(0),
            }
        )
        offset += len(replacement) - (end - start)

    return masked, restore_map


def restore(text: str, restore_map: list[dict[str, Any]]) -> str:
    restored = text
    for entry in sorted(restore_map, key=lambda item: item["start"], reverse=True):
        restored = restored[: entry["start"]] + entry["original"] + restored[entry["end"] :]
    return restored


def mask_text(text: str) -> str:
    masked, _ = mask(text)
    return masked


def mask_payload(payload: Any) -> Any:
    if isinstance(payload, str):
        return mask_text(payload)
    if isinstance(payload, Mapping):
        return {key: mask_payload(value) for key, value in payload.items()}
    if isinstance(payload, tuple):
        return tuple(mask_payload(value) for value in payload)
    if isinstance(payload, list):
        return [mask_payload(value) for value in payload]
    if isinstance(payload, set):
        return {mask_payload(value) for value in payload}
    return payload


def _find_replacements(text: str) -> list[tuple[re.Match[str], str]]:
    replacements: list[tuple[re.Match[str], str]] = []
    replacements.extend((_match, f"{_match.group(1)}-{'▲' * len(_match.group(2))}") for _match in _ALIEN_NUMBER_RE.finditer(text))
    replacements.extend((_match, f"{_match.group(1)}{_match.group(2)}****") for _match in _PASSPORT_RE.finditer(text))
    replacements.extend((_match, f"{_match.group(1)}-****-{_match.group(3)}") for _match in _PHONE_RE.finditer(text))
    replacements.sort(key=lambda item: item[0].start())
    return replacements
