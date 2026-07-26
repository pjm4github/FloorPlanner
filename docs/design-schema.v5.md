# v5 design schema — moved

The v5 JSON Schema (`format: "floorplanner-design"`, Draft 2020-12) was vendored
into the package at **P0.7**. It now lives at:

    floorplanner/design/design-schema.v5.json    (packaged data)

Load and use it from Python:

```python
from floorplanner.design.validate import load_schema, schema_errors, check

errs = schema_errors(doc) + check(doc)   # [] means valid
```

Or from the CLI (schema defaults to the packaged one):

```
python tools/validate_design.py yourfile.json
```

This pointer remains in `docs/` so references to the old location resolve.
