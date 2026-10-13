# v5 design schema — moved, and since 0271 named v6

> **2026‑10‑12 (0271):** the packaged schema is now
> `floorplanner/design/design-schema.v6.json` — version 6, the document this
> app writes; a v5 document still validates under it. See
> [`design-schema.v6.md`](design-schema.v6.md). The text below is kept as it
> was written.

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
