from __future__ import annotations

import uuid
from pathlib import Path
from typing import Any, Dict, List

from synthtest.config.models import RunMetadata
from synthtest.export.csv_exporter import CsvExporter
from synthtest.export.json_exporter import JsonExporter
from synthtest.export.sql_exporter import SqlExporter
from synthtest.gen.edge_cases import apply_edge_cases
from synthtest.gen.generators import faker_generators, primitives
from synthtest.gen.repair import repair_loop
from synthtest.gen.rules_engine import evaluate_rules
from synthtest.plan.planner import plan_tables
from synthtest.schema.canonical import ColumnSpec, SchemaSpec, TableSpec
from synthtest.util.logging import get_logger, log_event
from synthtest.util.rng import Rng
from synthtest.validate.validator import validate_output

LOGGER = get_logger(__name__)


def generate_dataset(schema: SchemaSpec, config_hash: str, out_dir: str | Path, fmt: str) -> RunMetadata:
    out_path = Path(out_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    dataset_id = str(uuid.uuid4())
    rng = Rng.with_seed(schema.dataset.seed)

    plan = plan_tables(schema)
    row_counts: Dict[str, int] = {}
    pk_pools: Dict[str, List[Any]] = {}
    repair_attempts: Dict[str, int] = {}

    for table_name in plan:
        table = schema.tables[table_name]
        table_seed = rng.derive(table_name)
        row_count = schema.dataset.size.get(table_name, 10)
        row_counts[table_name] = row_count
        pk_pools[table_name] = []
        repair_attempts[table_name] = 0

        exporter = _make_exporter(fmt, out_path, table_name, list(table.columns.keys()))
        unique_sets: Dict[str, set] = {col: set() for col, spec in table.columns.items() if spec.unique}
        pk_set: set = set()

        def generate_row() -> Dict[str, Any]:
            return _generate_row(table, table_seed, pk_pools, schema)

        def validate_row(row: Dict[str, Any]) -> bool:
            return _row_valid(row, table, unique_sets, pk_set, pk_pools, schema)

        for idx in range(row_count):
            if schema.dataset.mode == "valid":
                result = repair_loop(generate_row, validate_row, schema.dataset.max_attempts)
                row = result.row
                success = result.success
                repair_attempts[table_name] += result.attempts
                if not success:
                    log_event(LOGGER, "row_generation_failed", table=table_name, row_index=idx)
            else:
                row = generate_row()

            _register_uniques(row, table, unique_sets, pk_set, pk_pools)
            exporter.write_row(row)

        exporter.close()

    metadata = RunMetadata(
        dataset_id=dataset_id,
        dataset_name=schema.dataset.name,
        seed=schema.dataset.seed,
        mode=schema.dataset.mode,
        timestamp=_timestamp(),
        config_hash=config_hash,
        format=fmt,
        row_counts=row_counts,
        tables=list(row_counts.keys()),
        max_attempts=schema.dataset.max_attempts,
    )

    metadata_path = out_path / "run_metadata.json"
    metadata_path.write_text(metadata.model_dump_json(indent=2), encoding="utf-8")

    report = validate_output(schema, out_path, fmt)
    for table_name, attempts in repair_attempts.items():
        if table_name in report.tables:
            report.tables[table_name].repair_attempts = attempts
    report_path = out_path / "validation_report.json"
    report_path.write_text(report.model_dump_json(indent=2), encoding="utf-8")

    return metadata


def _make_exporter(fmt: str, out_dir: Path, table: str, columns: List[str]):
    if fmt == "csv":
        return CsvExporter(out_dir / f"{table}.csv", columns)
    if fmt == "json":
        return JsonExporter(out_dir / f"{table}.jsonl", columns)
    if fmt == "sql":
        return SqlExporter(out_dir / f"{table}.sql", table, columns)
    raise ValueError(f"Unsupported format: {fmt}")


def _generate_row(table: TableSpec, rng: Rng, pk_pools: Dict[str, List[Any]], schema: SchemaSpec) -> Dict[str, Any]:
    row: Dict[str, Any] = {}
    for col_name, column in table.columns.items():
        value = _generate_value(table, column, rng, pk_pools, schema)
        value, _ = apply_edge_cases(value, column, schema.dataset.mode, rng)
        row[col_name] = value

    return row


def _generate_value(
    table: TableSpec,
    column: ColumnSpec,
    rng: Rng,
    pk_pools: Dict[str, List[Any]],
    schema: SchemaSpec,
) -> Any:
    fk = next((fk for fk in table.foreign_keys if fk.column == column.name), None)
    if fk:
        parent_pool = pk_pools.get(fk.ref_table, [])
        if schema.dataset.mode == "invalid" and rng.random() < 0.2:
            return "invalid_fk"
        if parent_pool:
            return rng.choice(parent_pool)
        return None

    if column.type == "uuid":
        return primitives.generate_uuid(rng)
    if column.type == "int":
        min_val, max_val = _range_to_float(column.range)
        return primitives.generate_int(rng, min_val, max_val, column.distribution)
    if column.type == "decimal":
        min_val, max_val = _range_to_float(column.range)
        return primitives.generate_decimal(rng, min_val, max_val, column.distribution)
    if column.type == "bool":
        return primitives.generate_bool(rng)
    if column.type == "datetime":
        start, end = primitives.parse_datetime_range(column.range)
        return primitives.generate_datetime(rng, start, end)
    if column.type == "date":
        start, end = primitives.parse_date_range(column.range)
        return primitives.generate_date(rng, start, end)
    if column.type == "enum":
        return primitives.generate_enum(rng, column.values or [], column.weights)
    if column.type == "text":
        min_len, max_len = _length_pair(column.length)
        if column.regex:
            return primitives.generate_text_from_regex(rng, column.regex)
        return primitives.generate_text(rng, min_len, max_len)
    if column.type == "email":
        return faker_generators.generate_email(rng)
    if column.type == "phone":
        return faker_generators.generate_phone(rng)
    if column.type == "country":
        return faker_generators.generate_country(rng)
    if column.type == "postcode_uk":
        return faker_generators.generate_postcode_uk(rng)
    if column.type == "name":
        return faker_generators.generate_name(rng)
    return None


def _range_to_float(raw):
    if not raw or len(raw) < 2:
        return None, None
    return float(raw[0]), float(raw[1])


def _length_pair(raw):
    if not raw or len(raw) < 2:
        return None, None
    return int(raw[0]), int(raw[1])


def _row_valid(
    row: Dict[str, Any],
    table: TableSpec,
    unique_sets: Dict[str, set],
    pk_set: set,
    pk_pools: Dict[str, List[Any]],
    schema: SchemaSpec,
) -> bool:
    for col_name, column in table.columns.items():
        value = row.get(col_name)
        if value is None:
            if not column.nullable:
                return False
            continue
        if column.unique and value in unique_sets.get(col_name, set()):
            return False
        if col_name == table.primary_key and value in pk_set:
            return False
        if column.type == "enum" and column.values and value not in column.values:
            return False
        if column.type in {"int", "decimal"} and column.range and len(column.range) >= 2:
            min_val, max_val = float(column.range[0]), float(column.range[1])
            try:
                numeric = float(value)
            except (TypeError, ValueError):
                return False
            if numeric < min_val or numeric > max_val:
                return False
        if column.type == "text" and column.regex:
            import re

            if not re.fullmatch(column.regex, str(value)):
                return False
        fk = next((fk for fk in table.foreign_keys if fk.column == col_name), None)
        if fk:
            if value not in pk_pools.get(fk.ref_table, []):
                return False
    context = {table.name: row}
    if evaluate_rules(schema.rules, context):
        return False
    return True


def _register_uniques(row: Dict[str, Any], table: TableSpec, unique_sets: Dict[str, set], pk_set: set, pk_pools: Dict[str, List[Any]]):
    pk_value = row.get(table.primary_key)
    if pk_value is not None:
        pk_set.add(pk_value)
        pk_pools[table.name].append(pk_value)
    for col_name, values in unique_sets.items():
        value = row.get(col_name)
        if value is not None:
            values.add(value)


def _timestamp() -> str:
    from datetime import datetime

    return datetime.utcnow().isoformat() + "Z"
