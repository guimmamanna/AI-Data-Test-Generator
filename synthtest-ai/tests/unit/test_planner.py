from synthtest.schema.dsl import parse_schema
from synthtest.plan.planner import plan_tables


def test_planner_topo_order():
    raw = {
        "dataset": {"name": "demo", "seed": 1, "mode": "valid", "size": {"a": 1, "b": 1, "c": 1}},
        "tables": {
            "a": {"primary_key": "id", "columns": {"id": {"type": "uuid"}}},
            "b": {
                "primary_key": "id",
                "foreign_keys": [{"column": "a_id", "ref_table": "a", "ref_column": "id"}],
                "columns": {"id": {"type": "uuid"}, "a_id": {"type": "uuid"}},
            },
            "c": {
                "primary_key": "id",
                "foreign_keys": [{"column": "b_id", "ref_table": "b", "ref_column": "id"}],
                "columns": {"id": {"type": "uuid"}, "b_id": {"type": "uuid"}},
            },
        },
    }
    schema = parse_schema(raw)
    order = plan_tables(schema)
    assert order.index("a") < order.index("b") < order.index("c")
