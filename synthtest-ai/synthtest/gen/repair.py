from __future__ import annotations

from typing import Callable, Dict, Tuple


class RepairResult:
    def __init__(self, row: Dict[str, object], attempts: int, success: bool):
        self.row = row
        self.attempts = attempts
        self.success = success


def repair_loop(
    generate_row: Callable[[], Dict[str, object]],
    validate_row: Callable[[Dict[str, object]], bool],
    max_attempts: int,
) -> RepairResult:
    attempts = 0
    last_row: Dict[str, object] = {}
    while attempts < max_attempts:
        attempts += 1
        row = generate_row()
        last_row = row
        if validate_row(row):
            return RepairResult(row=row, attempts=attempts, success=True)
    return RepairResult(row=last_row, attempts=attempts, success=False)
