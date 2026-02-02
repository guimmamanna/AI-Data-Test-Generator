# Config Spec

SynthTest AI supports YAML and JSON. Core structure:

```yaml
dataset:
  name: ecommerce
  seed: 123
  mode: valid   # valid|invalid
  size:
    customers: 100
    orders: 300
  max_attempts: 20

tables:
  customers:
    primary_key: customer_id
    foreign_keys: []
    columns:
      customer_id:
        type: uuid
      email:
        type: email
        unique: true
      created_at:
        type: datetime
        range: ["2023-01-01T00:00:00", "2025-01-01T00:00:00"]

rules:
  - if: "orders.status == 'FAILED'"
    then:
      - "orders.total_amount <= 500.0"
```

## Column fields
- `type`: uuid|int|decimal|datetime|date|bool|enum|text|email|phone|country|postcode_uk|name
- `nullable`: bool
- `unique`: bool
- `range`: [min, max] for numeric/date/datetime
- `regex`: regex string for text
- `values` + `weights`: enum values and categorical weights
- `distribution`: uniform|normal|lognormal|categorical
- `length`: [min, max] for text
- `pii`: bool (for inference and safety)

## Rules
Rules are evaluated per-row with a safe expression evaluator:
- `if`: condition expression
- `then`: list of constraint expressions

Example:
```
if: "orders.status == 'FAILED'"
then:
  - "orders.total_amount <= 500.0"
```
