from __future__ import annotations

from typing import List

from synthtest.plan.dependency_graph import topo_sort
from synthtest.schema.canonical import SchemaSpec


def plan_tables(schema: SchemaSpec) -> List[str]:
    return topo_sort(schema)
