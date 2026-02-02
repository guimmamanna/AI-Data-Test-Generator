# Security and PII

- SynthTest AI generates synthetic values and never copies source values for columns marked `pii: true`.
- The `infer-basic` command uses basic detectors for email and phone and flags those columns as PII.
- Rules are evaluated via a safe expression evaluator with a restricted grammar (no eval).
- Invalid mode intentionally generates violations to test downstream validators.
