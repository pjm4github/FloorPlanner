---
# permanent key, independent of GitHub
id: 81
title: "fp2pdf draws every door as the same generic swing leaf, never reading the catalog door_type"

# maps directly onto GitHub Issues fields
state: open
state_reason: null
labels:
  - type:defect
  - area:io
milestone: null

# ours; becomes body prose after migration
opened: 2026-08-28
closed: null
closed_by: null
rank: 81
related: []
state_source: row
github_issue: null
---

# D81 — fp2pdf draws every door as the same generic swing leaf, never reading the catalog door_type

**Filed per Patrick's manual check on [PR #42](https://github.com/pjm4github/FloorPlanner/pull/42)
(`handoff/0116-ruling.md`)** — the Export menu and PDF wiring itself passed
(menu shape, Save-As flow, a real PDF lands); this is a content defect in what
the PDF draws, reported separately so it does not block that merge.

## The finding

`floorplanner/export/fp2pdf.py:draw_opening` (`:278`) branches on

```python
sliding = kind == "door" and op.get("door_type") == "sliding"
```

but **no door in this application ever carries `door_type == "sliding"`.** The
real catalog, drawn by `walls.py:_paint_door` (`:2921`), is `LH`, `RH`,
`FRENCH`, `BIFOLD`, `POCKET`, `SLIDER`, `DOORWAY`, and the `GARAGE_DEFAULTS`
keys (`GARAGE-1`, `GARAGE-2`, …) — a sliding door's type string is `SLIDER`,
uppercase, never the lowercase word `"sliding"`. So `sliding` is always
`False`, the sliding-panel branch (`:305`) is dead code, and **every opening
of `kind == "door"` falls through to the single generic swing-leaf-plus-arc
branch (`:279`)** regardless of its actual `door_type` — a French double door,
a bifold, a pocket door sliding into the wall, a garage overhead door, and a
plain single door all render as one identical hinged leaf, distinguished only
by which side it hinges on. The `WWHH door_type` text label
(`walls.py:2899`, e.g. `"3068 POCKET"`) is correct in the *editor*; nothing
equivalent reaches the PDF symbol.

## Site

`floorplanner/export/fp2pdf.py:265-320` (`draw_opening`) is the only place a
door's graphic is chosen for PDF output; it duplicates none of
`walls.py:_paint_door`'s per-type branches (`LH`/`RH`/`FRENCH`/`BIFOLD`/
`POCKET`/`SLIDER`/`DOORWAY`/garage) and has no fallback that reads
`door_type` at all outside the one dead `"sliding"` check.

## Not built here

Per Patrick's direction, this is tracked as a separate fix, not folded into
PR #42. A repair should draw (or clearly abbreviate) each catalog type rather
than adding more special-case string literals one at a time — `fp2dxf.py:324`
already appends the raw `door_type` string into its exported entity, which is
a second, differently-shaped precedent worth reading before choosing this
fix's shape.
