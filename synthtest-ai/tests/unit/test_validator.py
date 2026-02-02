from pathlib import Path

from synthtest.schema.dsl import parse_schema
from synthtest.validate.validator import validate_output


def test_validator_valid_csv(tmp_path: Path):
    raw = {
        "dataset": {"name": "demo", "seed": 1, "mode": "valid", "size": {"users": 1}},
        "tables": {
            "users": {
                "primary_key": "id",
                "columns": {
                    "id": {"type": "uuid"},
                    "age": {"type": "int", "range": [0, 120]},
                    "status": {"type": "enum", "values": ["ACTIVE", "INACTIVE"]},
                },
            }
        },
        "rules": [],
    }
    schema = parse_schema(raw)
    data_path = tmp_path / "users.csv"
    data_path.write_text("id,age,status\n123e4567-e89b-12d3-a456-426614174000,30,ACTIVE\n", encoding="utf-8")

    report = validate_output(schema, tmp_path, "csv")
    assert report.total_violations == 0
