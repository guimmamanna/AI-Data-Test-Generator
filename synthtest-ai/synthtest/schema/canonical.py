from __future__ import annotations

from typing import Dict, List, Literal, Optional

from pydantic import BaseModel, Field


ColumnType = Literal[
    "uuid",
    "int",
    "decimal",
    "datetime",
    "date",
    "bool",
    "enum",
    "text",
    "email",
    "phone",
    "country",
    "postcode_uk",
    "name",
]

DistributionType = Literal["uniform", "normal", "lognormal", "categorical"]


class ColumnSpec(BaseModel):
    name: str
    type: ColumnType
    nullable: bool = False
    unique: bool = False
    range: Optional[List[str | int | float]] = None
    regex: Optional[str] = None
    values: Optional[List[str]] = None
    weights: Optional[List[float]] = None
    distribution: Optional[DistributionType] = None
    length: Optional[List[int]] = None
    pii: bool = False


class ForeignKeySpec(BaseModel):
    column: str
    ref_table: str
    ref_column: str


class TableSpec(BaseModel):
    name: str
    primary_key: str
    foreign_keys: List[ForeignKeySpec] = Field(default_factory=list)
    columns: Dict[str, ColumnSpec]


class RuleSpec(BaseModel):
    if_expr: str = Field(alias="if")
    then: List[str]


class DatasetSpec(BaseModel):
    name: str
    seed: int
    mode: Literal["valid", "invalid"] = "valid"
    size: Dict[str, int] = Field(default_factory=dict)
    max_attempts: int = 10


class SchemaSpec(BaseModel):
    dataset: DatasetSpec
    tables: Dict[str, TableSpec]
    rules: List[RuleSpec] = Field(default_factory=list)
