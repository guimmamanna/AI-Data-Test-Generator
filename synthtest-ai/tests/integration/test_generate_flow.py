from pathlib import Path

from synthtest.gen.core import generate_dataset
from synthtest.schema.dsl import parse_schema
from synthtest.util.hashing import hash_config


def test_generate_and_validate(tmp_path: Path):
    raw = {
        "dataset": {"name": "demo", "seed": 7, "mode": "valid", "size": {"customers": 5, "orders": 10}},
        "tables": {
            "customers": {
                "primary_key": "customer_id",
                "columns": {
                    "customer_id": {"type": "uuid"},
                    "email": {"type": "email", "unique": True},
                },
            },
            "orders": {
                "primary_key": "order_id",
                "foreign_keys": [{"column": "customer_id", "ref_table": "customers", "ref_column": "customer_id"}],
                "columns": {
                    "order_id": {"type": "uuid"},
                    "customer_id": {"type": "uuid"},
                    "status": {"type": "enum", "values": ["PAID", "FAILED"]},
                    "total": {"type": "decimal", "range": [0, 1000]},
                },
            },
        },
        "rules": [
            {"if": "orders.status == 'FAILED'", "then": ["orders.total <= 500.0"]}
        ],
    }
    schema = parse_schema(raw)
    metadata = generate_dataset(schema, hash_config(raw), tmp_path, "csv")
    report_path = tmp_path / "validation_report.json"
    assert report_path.exists()
    assert metadata.dataset_name == "demo"
