from __future__ import annotations

import json
from pathlib import Path
from typing import Any, List


class JsonExporter:
    def __init__(self, path: Path, columns: List[str]):
        self.path = path
        self.columns = columns
        self._file = path.open("w", encoding="utf-8")

    def write_row(self, row: dict[str, Any]) -> None:
        payload = {col: _serialize_value(row.get(col)) for col in self.columns}
        self._file.write(json.dumps(payload, ensure_ascii=True) + "\n")

    def close(self) -> None:
        self._file.close()


def _serialize_value(value: Any) -> Any:
    if value is None:
        return None
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return value
