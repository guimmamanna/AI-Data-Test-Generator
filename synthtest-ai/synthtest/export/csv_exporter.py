from __future__ import annotations

import csv
from pathlib import Path
from typing import Any, Iterable, List

from .json_exporter import _serialize_value


class CsvExporter:
    def __init__(self, path: Path, columns: List[str]):
        self.path = path
        self.columns = columns
        self._file = path.open("w", newline="", encoding="utf-8")
        self._writer = csv.DictWriter(self._file, fieldnames=columns)
        self._writer.writeheader()

    def write_row(self, row: dict[str, Any]) -> None:
        serialized = {col: _serialize_value(row.get(col)) for col in self.columns}
        self._writer.writerow(serialized)

    def close(self) -> None:
        self._file.close()
