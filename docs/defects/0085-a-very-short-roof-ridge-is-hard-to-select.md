---
# permanent key, independent of GitHub
id: 85
title: "A very short roof ridge is hard to select for deletion"

# maps directly onto GitHub Issues fields
state: open
state_reason: null
labels:
  - type:gap
  - area:ui
milestone: null

# ours; becomes body prose after migration
opened: 2026-09-04
closed: null
closed_by: null
rank: 85
related: []
state_source: row
github_issue: null
---

# D85 — a very short roof ridge is hard to select for deletion

**Filed per Patrick's own report, 2026‑09‑04, in chat, in passing while
reporting a separate R3b crash** (not a numbered ruling): *"had a little
tiny roof (which I couldn't delete, by the way)."*

## The finding

Measured directly: `RoofItem.shape()` (`roofs.py`) is an 8in-wide stroked
outline of the ridge line plus the marker's own separate hit region — for a
ridge only a couple of inches long, `boundingRect()`/`shape()` come out to
roughly 10x8in in plan, a target easy to miss at a normal working zoom
(unlike the marker, which already has a view-scaled minimum hit radius —
`RoofEndMarkerItem._hit_radius()`, `HIT_PX = 14.0` — the ridge's own stroke
width does not scale with zoom the same way). Right-click (the only route
to "Delete roof," via `RoofItem.contextMenuEvent`) needs to land inside
that shape first.

## Site

`floorplanner/roofs.py`: `RoofItem.shape()` (stroke width fixed at 8.0
regardless of view scale) and `boundingRect()`/`_eave_ends()` (bounds
follow ridge length + span + overhang, so a short, unpicked-eaves ridge is
also thin). Not the marker — `RoofEndMarkerItem` already has a
view-scaled minimum hit radius; the ridge's own line does not.

## Not investigated yet

Not reproduced from a fresh sketch (a ridge under `MIN_WALL_LEN` is
discarded on release — `view.py`'s `_temp_roof` handling — so this is
about a ridge that is short but not THAT short, or one that reached this
state some other way, e.g. loaded from a document). No fix attempted;
unrelated to R3b's own clip-line work, which does not touch hit-testing.
Held, not scheduled against any tranche.
