# Architecture

## High-level architecture

```
+------------------+         +-----------------+         +------------------+
|  Schema DSL      | ----->  |  Planner (DAG)  | ----->  |  Generator Core  |
|  (YAML/JSON)     |         |  Topo Sort      |         |  Column Gens     |
+------------------+         +-----------------+         +------------------+
            |                                             |         |
            |                                             |         v
            |                                             |  Edge Cases + Rules
            |                                             v         |
            |                                      +------------------+
            |                                      |  Exporters        |
            |                                      |  CSV / JSON / SQL |
            |                                      +------------------+
            v
+------------------+         +-----------------+
|  Validator       | <-----  |  Output Files   |
|  Reports + Stats |         |  + metadata     |
+------------------+         +-----------------+
```

## Data generation flow

```
Load schema -> Build dependency graph -> For each table in topo order:
  - seed RNG for table
  - generate PK pool
  - generate columns (types, distributions)
  - apply edge-case profile
  - enforce rules (valid mode)
  - repair loop for violations
  - stream rows to exporter
Validate outputs -> write report + metadata
```

## Dependency graph planning

```
customers (PK)
   |
   v
orders (FK customers.customer_id)
   |
   v
order_items (FK orders.order_id)
```
