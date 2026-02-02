from __future__ import annotations

from pathlib import Path
from typing import Any, List

from .json_exporter import _serialize_value


class SqlExporter:
    def __init__(self, path: Path, table: str, columns: List[str]):
        self.path = path
        self.table = table
        self.columns = columns
        self._file = path.open("w", encoding="utf-8")

    def write_row(self, row: dict[str, Any]) -> None:
        values = [_sql_literal(_serialize_value(row.get(col))) for col in self.columns]
        cols = ", ".join(self.columns)
        vals = ", ".join(values)
        self._file.write(f"INSERT INTO {self.table} ({cols}) VALUES ({vals});\n")

    def close(self) -> None:
        self._file.close()


def _sql_literal(value: Any) -> str:
    if value is None:
        return "NULL"
    if isinstance(value, (int, float)):
        return str(value)
    text = str(value).replace("'", "''")
    return f"'{text}'"
