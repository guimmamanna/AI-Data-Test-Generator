# CLI

## Initialize
```
synthtest init
```

## Generate
```
synthtest generate --config examples/ecommerce.yml --out ./out --format csv
```

## Validate
```
synthtest validate --config examples/ecommerce.yml --data ./out --format csv
```

## Infer basic schema
```
synthtest infer-basic --input sample.csv --out schema.yml
```
