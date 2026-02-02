from __future__ import annotations

import csv
import datetime as dt
from pathlib import Path
from typing import Any, Dict, List, Tuple

import yaml

from synthtest.validate.pii_guard import detect_pii, is_email, is_phone


def infer_basic(input_path: str | Path, out_path: str | Path) -> None:
    input_path = Path(input_path)
    out_path = Path(out_path)

    with input_path.open("r", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        rows = list(reader)

    if not rows:
        raise ValueError("No rows found in input CSV")

    table_name = input_path.stem
    columns = {}
    for col in reader.fieldnames or []:
        values = [row.get(col) for row in rows]
        col_spec = _infer_column(values)
        columns[col] = col_spec

    config = {
        "dataset": {
            "name": table_name,
            "seed": 42,
            "mode": "valid",
            "size": {table_name: len(rows)},
            "max_attempts": 10,
        },
        "tables": {
            table_name: {
                "primary_key": _pick_primary_key(columns),
                "columns": columns,
            }
        },
        "rules": [],
    }

    out_path.write_text(yaml.safe_dump(config, sort_keys=False), encoding="utf-8")


def _infer_column(values: List[Any]) -> Dict[str, Any]:
    cleaned = [v for v in values if v not in (None, "")]
    nullable = len(cleaned) < len(values)

    if not cleaned:
        return {"type": "text", "nullable": True, "length": [1, 10]}

    pii = detect_pii([str(v) for v in cleaned])

    if pii:
        if all(is_email(str(v)) for v in cleaned):
            return {"type": "email", "nullable": nullable, "pii": True}
        if all(is_phone(str(v)) for v in cleaned):
            return {"type": "phone", "nullable": nullable, "pii": True}

    if _all_int(cleaned):
        min_val, max_val = _min_max(cleaned, int)
        return {"type": "int", "nullable": nullable, "range": [min_val, max_val]}
    if _all_float(cleaned):
        min_val, max_val = _min_max(cleaned, float)
        return {"type": "decimal", "nullable": nullable, "range": [min_val, max_val]}
    if _all_bool(cleaned):
        return {"type": "bool", "nullable": nullable}
    if _all_date(cleaned):
        min_val, max_val = _min_max_date(cleaned)
        return {"type": "date", "nullable": nullable, "range": [min_val, max_val]}
    if _all_datetime(cleaned):
        min_val, max_val = _min_max_datetime(cleaned)
        return {"type": "datetime", "nullable": nullable, "range": [min_val, max_val]}

    unique_vals = list({str(v) for v in cleaned})
    if len(unique_vals) <= 10 and len(cleaned) > 0 and len(unique_vals) / len(cleaned) <= 0.2:
        counts = {val: 0 for val in unique_vals}
        for v in cleaned:
            counts[str(v)] += 1
        values_sorted = list(counts.keys())
        weights = [counts[v] / len(cleaned) for v in values_sorted]
        return {"type": "enum", "nullable": nullable, "values": values_sorted, "weights": weights}

    min_len = min(len(str(v)) for v in cleaned) if cleaned else 1
    max_len = max(len(str(v)) for v in cleaned) if cleaned else 10
    unique = len(unique_vals) == len(cleaned) and len(cleaned) > 0
    return {"type": "text", "nullable": nullable, "length": [min_len, max_len], "unique": unique}


def _pick_primary_key(columns: Dict[str, Dict[str, Any]]) -> str:
    for name, spec in columns.items():
        if spec.get("unique"):
            return name
    return next(iter(columns.keys()))


def _all_int(values: List[Any]) -> bool:
    try:
        return all(str(v).lstrip("-").isdigit() for v in values)
    except Exception:
        return False


def _all_float(values: List[Any]) -> bool:
    try:
        for v in values:
            float(v)
        return True
    except Exception:
        return False


def _all_bool(values: List[Any]) -> bool:
    return all(str(v).lower() in {"true", "false", "1", "0"} for v in values)


def _all_date(values: List[Any]) -> bool:
    try:
        for v in values:
            dt.date.fromisoformat(str(v))
        return True
    except Exception:
        return False


def _all_datetime(values: List[Any]) -> bool:
    try:
        for v in values:
            dt.datetime.fromisoformat(str(v).replace("Z", "+00:00"))
        return True
    except Exception:
        return False


def _min_max(values: List[Any], cast):
    casted = [cast(v) for v in values]
    return min(casted), max(casted)


def _min_max_date(values: List[Any]):
    casted = [dt.date.fromisoformat(str(v)) for v in values]
    casted.sort()
    return casted[0].isoformat(), casted[-1].isoformat()


def _min_max_datetime(values: List[Any]):
    casted = [dt.datetime.fromisoformat(str(v).replace("Z", "+00:00")) for v in values]
    casted.sort()
    return casted[0].isoformat(), casted[-1].isoformat()
