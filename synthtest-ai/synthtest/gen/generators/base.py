from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional

from synthtest.schema.canonical import ColumnSpec
from synthtest.util.rng import Rng


@dataclass
class GeneratorContext:
    column: ColumnSpec
    rng: Rng
    table: str
    row_index: int
    mode: str
    nullable: bool
    max_attempts: int


def generate_value(ctx: GeneratorContext) -> Any:
    raise NotImplementedError
