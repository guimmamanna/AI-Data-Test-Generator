from __future__ import annotations

import csv
import datetime as dt
import json
import re
import uuid
from pathlib import Path
from typing import Any, Dict, List, Tuple

from synthtest.gen.rules_engine import evaluate_rules
from synthtest.schema.canonical import ColumnSpec, SchemaSpec, TableSpec
from synthtest.validate.report import TableReport, ValidationReport


def validate_output(schema: SchemaSpec, out_dir: Path, fmt: str) -> ValidationReport:
    table_rows: Dict[str, List[Dict[str, Any]]] = {}
    for table_name in schema.tables.keys():
        path = _table_path(out_dir, table_name, fmt)
        table_rows[table_name] = _load_rows(path, fmt)

    pk_sets = {name: _collect_pk(schema.tables[name], rows) for name, rows in table_rows.items()}

    table_reports: Dict[str, TableReport] = {}
    total_violations = 0
    aggregate_coverage: Dict[str, int] = {}

    for table_name, rows in table_rows.items():
        table = schema.tables[table_name]
        report = _validate_table(table, rows, pk_sets, schema)
        table_reports[table_name] = report
        total_violations += sum(report.violations.values()) + report.rule_violations
        for key, count in report.constraint_coverage.items():
            aggregate_coverage[key] = aggregate_coverage.get(key, 0) + count

    return ValidationReport(
        dataset=schema.dataset.name,
        mode=schema.dataset.mode,
        total_violations=total_violations,
        tables=table_reports,
        constraint_coverage=aggregate_coverage,
    )


def _table_path(out_dir: Path, table: str, fmt: str) -> Path:
    if fmt == "csv":
        return out_dir / f"{table}.csv"
    if fmt == "json":
        return out_dir / f"{table}.jsonl"
    if fmt == "sql":
        return out_dir / f"{table}.sql"
    raise ValueError(f"Unsupported format: {fmt}")


def _load_rows(path: Path, fmt: str) -> List[Dict[str, Any]]:
    if not path.exists():
        return []
    if fmt == "csv":
        with path.open("r", encoding="utf-8") as handle:
            reader = csv.DictReader(handle)
            return [dict(row) for row in reader]
    if fmt == "json":
        rows: List[Dict[str, Any]] = []
        with path.open("r", encoding="utf-8") as handle:
            for line in handle:
                line = line.strip()
                if not line:
                    continue
                rows.append(json.loads(line))
        return rows
    if fmt == "sql":
        rows = []
        with path.open("r", encoding="utf-8") as handle:
            for line in handle:
                line = line.strip()
                if not line:
                    continue
                row = _parse_sql_insert(line)
                if row:
                    rows.append(row)
        return rows
    raise ValueError(f"Unsupported format: {fmt}")


def _collect_pk(table: TableSpec, rows: List[Dict[str, Any]]) -> set:
    values = set()
    for row in rows:
        raw = row.get(table.primary_key)
        column = table.columns.get(table.primary_key)
        if column is None:
            continue
        value, type_error = _coerce_value(raw, column)
        if value is not None and not type_error:
            values.add(value)
    return values


def _validate_table(
    table: TableSpec,
    rows: List[Dict[str, Any]],
    pk_sets: Dict[str, set],
    schema: SchemaSpec,
) -> TableReport:
    violations: Dict[str, int] = {}
    coverage: Dict[str, int] = {}
    unique_sets: Dict[str, set] = {name: set() for name, col in table.columns.items() if col.unique}
    failed_rows = 0
    rule_violations = 0

    for row in rows:
        row_failed = False
        parsed_row: Dict[str, Any] = {}
        for col_name, column in table.columns.items():
            raw_value = row.get(col_name)
            coverage = _increment(coverage, "type")
            value, type_error = _coerce_value(raw_value, column)
            parsed_row[col_name] = value
            if value is None:
                coverage = _increment(coverage, "nullable")
                if not column.nullable:
                    violations = _increment(violations, "nullability")
                    row_failed = True
                continue
            if type_error:
                violations = _increment(violations, "type")
                row_failed = True
                continue

            if column.range and column.type in {"int", "decimal", "date", "datetime"}:
                coverage = _increment(coverage, "range")
                if not _check_range(value, column):
                    violations = _increment(violations, "range")
                    row_failed = True

            if column.regex and column.type in {"text", "email", "phone", "postcode_uk", "name"}:
                coverage = _increment(coverage, "regex")
                if not re.fullmatch(column.regex, str(value)):
                    violations = _increment(violations, "regex")
                    row_failed = True

            if column.values and column.type == "enum":
                coverage = _increment(coverage, "enum")
                if value not in column.values:
                    violations = _increment(violations, "enum")
                    row_failed = True

            if column.unique:
                coverage = _increment(coverage, "unique")
                if value in unique_sets[col_name]:
                    violations = _increment(violations, "unique")
                    row_failed = True
                unique_sets[col_name].add(value)

            fk = next((fk for fk in table.foreign_keys if fk.column == col_name), None)
            if fk:
                coverage = _increment(coverage, "foreign_key")
                if value not in pk_sets.get(fk.ref_table, set()):
                    violations = _increment(violations, "foreign_key")
                    row_failed = True

        coverage = _increment(coverage, "rules")
        context = {table.name: parsed_row}
        if evaluate_rules(schema.rules, context):
            rule_violations += 1
            row_failed = True

        if row_failed:
            failed_rows += 1

    return TableReport(
        table=table.name,
        row_count=len(rows),
        violations=violations,
        rule_violations=rule_violations,
        failed_rows=failed_rows,
        constraint_coverage=coverage,
    )


def _increment(counter: Dict[str, int], key: str) -> Dict[str, int]:
    counter[key] = counter.get(key, 0) + 1
    return counter


def _coerce_value(raw_value: Any, column: ColumnSpec) -> Tuple[Any, bool]:
    if raw_value is None:
        return None, False
    if isinstance(raw_value, str) and raw_value.strip() in {"", "NULL", "null"}:
        return None, False

    try:
        if column.type == "uuid":
            if isinstance(raw_value, uuid.UUID):
                return str(raw_value), False
            uuid.UUID(str(raw_value))
            return str(raw_value), False
        if column.type == "int":
            return int(raw_value), False
        if column.type == "decimal":
            return float(raw_value), False
        if column.type == "bool":
            if isinstance(raw_value, bool):
                return raw_value, False
            if str(raw_value).lower() in {"true", "1"}:
                return True, False
            if str(raw_value).lower() in {"false", "0"}:
                return False, False
            return raw_value, True
        if column.type == "datetime":
            if isinstance(raw_value, dt.datetime):
                return raw_value, False
            text = str(raw_value)
            try:
                return dt.datetime.fromisoformat(text), False
            except ValueError:
                return dt.datetime.fromisoformat(text.replace("Z", "+00:00")), False
        if column.type == "date":
            if isinstance(raw_value, dt.date) and not isinstance(raw_value, dt.datetime):
                return raw_value, False
            return dt.date.fromisoformat(str(raw_value)), False
        if column.type in {"enum", "text", "email", "phone", "country", "postcode_uk", "name"}:
            return str(raw_value), False
    except Exception:
        return raw_value, True
    return raw_value, False


def _check_range(value: Any, column: ColumnSpec) -> bool:
    if not column.range or len(column.range) < 2:
        return True
    min_val, max_val = column.range[0], column.range[1]
    if column.type in {"int", "decimal"}:
        return float(min_val) <= float(value) <= float(max_val)
    if column.type == "date":
        start = dt.date.fromisoformat(str(min_val))
        end = dt.date.fromisoformat(str(max_val))
        return start <= value <= end
    if column.type == "datetime":
        start = dt.datetime.fromisoformat(str(min_val).replace("Z", "+00:00"))
        end = dt.datetime.fromisoformat(str(max_val).replace("Z", "+00:00"))
        if isinstance(value, dt.datetime) and value.tzinfo is not None:
            value = value.replace(tzinfo=None)
        if start.tzinfo is not None:
            start = start.replace(tzinfo=None)
        if end.tzinfo is not None:
            end = end.replace(tzinfo=None)
        return start <= value <= end
    return True


def _parse_sql_insert(line: str) -> Dict[str, Any] | None:
    match = re.match(r"INSERT INTO\s+(\w+)\s*\(([^\)]+)\)\s*VALUES\s*\((.*)\);", line)
    if not match:
        return None
    columns = [c.strip() for c in match.group(2).split(",")]
    values = _split_sql_values(match.group(3))
    return {col: _parse_sql_value(val) for col, val in zip(columns, values)}


def _split_sql_values(blob: str) -> List[str]:
    values = []
    current = ""
    in_string = False
    i = 0
    while i < len(blob):
        char = blob[i]
        if char == "'":
            in_string = not in_string
            current += char
        elif char == "," and not in_string:
            values.append(current.strip())
            current = ""
        else:
            current += char
        i += 1
    if current:
        values.append(current.strip())
    return values


def _parse_sql_value(value: str) -> Any:
    if value.upper() == "NULL":
        return None
    if value.startswith("'") and value.endswith("'"):
        return value[1:-1].replace("''", "'")
    return value
