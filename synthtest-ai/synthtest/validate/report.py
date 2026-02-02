from __future__ import annotations

from typing import Dict, Optional

from pydantic import BaseModel, Field


class TableReport(BaseModel):
    table: str
    row_count: int
    violations: Dict[str, int] = Field(default_factory=dict)
    rule_violations: int = 0
    failed_rows: int = 0
    constraint_coverage: Dict[str, int] = Field(default_factory=dict)
    repair_attempts: Optional[int] = None


class ValidationReport(BaseModel):
    dataset: str
    mode: str
    total_violations: int
    tables: Dict[str, TableReport]
    constraint_coverage: Dict[str, int] = Field(default_factory=dict)
