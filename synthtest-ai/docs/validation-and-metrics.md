# Validation and Metrics

SynthTest AI validates generated outputs against the schema and rules.

## Report structure
```json
{
  "dataset": "ecommerce",
  "mode": "valid",
  "total_violations": 0,
  "constraint_coverage": {
    "type": 1200,
    "nullable": 1200,
    "range": 600,
    "regex": 200,
    "enum": 300,
    "unique": 100,
    "foreign_key": 800
  },
  "tables": {
    "orders": {
      "table": "orders",
      "row_count": 300,
      "violations": {},
      "rule_violations": 0,
      "failed_rows": 0,
      "constraint_coverage": {"type": 1200},
      "repair_attempts": 320
    }
  }
}
```

## Constraint coverage
Coverage counts how many times each constraint category was evaluated across rows.

## Repair attempts
In valid mode, SynthTest AI retries failed rows up to `max_attempts`. The report includes total repair attempts per table.
