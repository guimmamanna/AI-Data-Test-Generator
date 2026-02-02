from __future__ import annotations

from collections import defaultdict, deque
from typing import Dict, Iterable, List, Set

from synthtest.schema.canonical import SchemaSpec


class DependencyError(ValueError):
    pass


def build_graph(schema: SchemaSpec) -> Dict[str, Set[str]]:
    graph: Dict[str, Set[str]] = {name: set() for name in schema.tables.keys()}
    for table in schema.tables.values():
        for fk in table.foreign_keys:
            if fk.ref_table not in graph:
                raise DependencyError(f"Unknown referenced table: {fk.ref_table}")
            graph[fk.ref_table].add(table.name)
    return graph


def topo_sort(schema: SchemaSpec) -> List[str]:
    graph = build_graph(schema)
    indegree = {name: 0 for name in graph}
    for parent, children in graph.items():
        for child in children:
            indegree[child] += 1

    queue = deque([name for name, deg in indegree.items() if deg == 0])
    order: List[str] = []
    while queue:
        node = queue.popleft()
        order.append(node)
        for child in graph[node]:
            indegree[child] -= 1
            if indegree[child] == 0:
                queue.append(child)

    if len(order) != len(graph):
        raise DependencyError("Cycle detected in foreign key dependencies")
    return order
