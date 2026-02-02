from __future__ import annotations

from typing import Any, Dict

from pydantic import ValidationError

from .canonical import ColumnSpec, DatasetSpec, ForeignKeySpec, RuleSpec, SchemaSpec, TableSpec


class DSLParseError(ValueError):
    pass


def parse_schema(raw: Dict[str, Any]) -> SchemaSpec:
    try:
        dataset_raw = raw.get("dataset", {})
        size_raw = dataset_raw.get("size", {})
        if isinstance(size_raw, int):
            size_raw = {name: size_raw for name in raw.get("tables", {}).keys()}
        dataset = DatasetSpec(**{**dataset_raw, "size": size_raw})

        tables: Dict[str, TableSpec] = {}
        for table_name, table_raw in raw.get("tables", {}).items():
            columns: Dict[str, ColumnSpec] = {}
            for col_name, col_raw in (table_raw.get("columns", {}) or {}).items():
                columns[col_name] = ColumnSpec(name=col_name, **col_raw)
            foreign_keys = [ForeignKeySpec(**fk) for fk in table_raw.get("foreign_keys", [])]
            tables[table_name] = TableSpec(
                name=table_name,
                primary_key=table_raw.get("primary_key"),
                foreign_keys=foreign_keys,
                columns=columns,
            )
        rules = [RuleSpec(**rule) for rule in raw.get("rules", [])]
        return SchemaSpec(dataset=dataset, tables=tables, rules=rules)
    except ValidationError as exc:
        raise DSLParseError(str(exc)) from exc
