from __future__ import annotations

from typing import Any, Tuple

from synthtest.schema.canonical import ColumnSpec
from synthtest.util.rng import Rng
from synthtest.gen.generators import primitives

VALID_BOUNDARY_PROB = 0.15
VALID_NULL_PROB = 0.1
INVALID_PROB = 0.25


def apply_edge_cases(value: Any, column: ColumnSpec, mode: str, rng: Rng) -> tuple[Any, str | None]:
    if mode == "invalid" and rng.random() < INVALID_PROB:
        return _invalid_value(column, rng), "invalid"

    if column.nullable and rng.random() < VALID_NULL_PROB:
        return None, "null"

    if rng.random() < VALID_BOUNDARY_PROB:
        return _boundary_value(value, column, rng), "boundary"

    return value, None


def _boundary_value(value: Any, column: ColumnSpec, rng: Rng) -> Any:
    if column.type in {"int", "decimal"} and column.range and len(column.range) >= 2:
        boundary = column.range[0] if rng.random() < 0.5 else column.range[1]
        return int(boundary) if column.type == "int" else float(boundary)
    if column.type == "date" and column.range and len(column.range) >= 2:
        start, end = primitives.parse_date_range(column.range)
        return start if rng.random() < 0.5 else end
    if column.type == "datetime" and column.range and len(column.range) >= 2:
        start, end = primitives.parse_datetime_range(column.range)
        return start if rng.random() < 0.5 else end
    if column.type == "text" and column.length and len(column.length) >= 2:
        target = column.length[0] if rng.random() < 0.5 else column.length[1]
        text = str(value or "")
        if len(text) >= target:
            return text[:target]
        return text.ljust(target, "x")
    if column.type == "enum" and column.values:
        return column.values[0] if rng.random() < 0.5 else column.values[-1]
    return value


def _invalid_value(column: ColumnSpec, rng: Rng) -> Any:
    if column.type in {"int", "decimal"}:
        if column.range and len(column.range) >= 2:
            return float(column.range[1]) + 9999
        return "not_a_number"
    if column.type in {"date", "datetime"}:
        return "not_a_date"
    if column.type == "bool":
        return "not_bool"
    if column.type == "enum":
        return "INVALID_ENUM"
    if column.type == "uuid":
        return "not-a-uuid"
    if column.type == "email":
        return "invalid-email"
    if column.type == "phone":
        return "invalid-phone"
    if column.type == "country":
        return "Atlantis"
    if column.type == "postcode_uk":
        return "INVALID"
    if column.type == "name":
        return ""
    if column.type == "text" and column.regex:
        return "!!!"
    if column.type == "text" and column.length:
        return ""
    return "invalid"
