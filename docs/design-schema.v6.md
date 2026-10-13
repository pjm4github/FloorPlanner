# v6 design schema — a pointer

The JSON Schema for a FloorPlanner design document (`format:
"floorplanner-design"`, Draft 2020-12) lives in the package:

    floorplanner/design/design-schema.v6.json    (packaged data)

**Version 6 is the document this app writes** (since
[`handoff/0271-report.md`](handoff/0271-report.md), Patrick, 2026‑10‑12). It is
the v5 model — rooms own outlines, vertices are the only coordinates, walls
are bindings — plus the additive blocks that came after the migration closed:

| block / key | since | what it holds |
|---|---|---|
| `roofs` | 0139 R1 | ridges with eaves and ridge heights, gable / hip / shed forms, per-end hip runs, dormers (with a host and their own openings) |
| `annotations` | 0263, 0270 | `text`, `dimension` (`pos`→`p2`, `offset_in`, `label_t`), `leader` (`pos` the arrow's tip, `p2` the text's end, `text`), `datum` |
| opening `sill_in` / `head_in` | 0255 | a window's elevation and head height above the level's base |
| furnishing kind `post` | 0258 | a column the 3D builder runs from its level to the roof above |
| settings `show_annotations`, `show_dimensions`, `show_callouts`, `callout_color`, `dimension_units`, `show_roofs`, `edit_roofs` | 0263, R2c | the Show and Roof menus' switches, saved with the plan |

**A version-5 document still validates under this schema** (every later block
is optional) and opens unchanged; the app writes it back as 6. Legacy
`floorplanner-json` (v1–v4) is converted on open by `floorplanner.design.importer`
and reported.

Load and use it from Python:

```python
from floorplanner.design.validate import load_schema, schema_errors, check

errs = schema_errors(doc) + check(doc)   # [] means valid
```

Or from the CLI (the schema defaults to the packaged one):

```
python tools/validate_design.py yourfile.json
```

[`design-schema.v5.md`](design-schema.v5.md) is kept so references to the
older name still resolve.
