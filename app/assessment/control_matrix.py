from __future__ import annotations

import csv
from pathlib import Path
from typing import Any


def load_control_matrix(path: str | Path) -> list[dict[str, str]]:
    with Path(path).open("r", encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    if not rows:
        raise ValueError(f"Control matrix is empty: {path}")
    required = {"control_id", "aspect", "source_ids", "required_terms", "recommendation_scope", "suggested_owner"}
    missing = required.difference(rows[0].keys())
    if missing:
        raise ValueError(f"Control matrix missing columns: {sorted(missing)}")
    return rows


def split_semicolon(value: str | None) -> list[str]:
    if not value:
        return []
    return [part.strip() for part in value.split(";") if part.strip()]


def source_ids_for_control(control: dict[str, Any]) -> list[str]:
    return split_semicolon(control.get("source_ids"))


def pasal_numbers_for_control(control: dict[str, Any]) -> list[str]:
    numbers: list[str] = []
    for source_id in source_ids_for_control(control):
        marker = "-P"
        if marker not in source_id:
            continue
        tail = source_id.rsplit(marker, 1)[1]
        number = ""
        for char in tail:
            if char.isdigit():
                number += char
            else:
                break
        if number and number not in numbers:
            numbers.append(number)
    return numbers
