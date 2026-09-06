---
# permanent key, independent of GitHub
id: 85
title: "A very short roof ridge is hard to select for deletion"

# maps directly onto GitHub Issues fields
state: closed
state_reason: completed
labels:
  - type:gap
  - area:ui
milestone: null

# ours; becomes body prose after migration
opened: 2026-09-04
closed: 2026-09-05
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

## Reproduced and fixed, 2026‑09‑05

Confirmed live with a screenshot and his own diagnosis: *"I cant deleted
it or select it. I think the dotted roof edges need to be selectable so
that I can select the roof."* Root cause matched his own read exactly:
`RoofItem.rebuild()` built `self._path` (what `shape()` strokes) from the
ridge segment alone — `paint()` also draws two dashed EAVE lines and, per
gable end, a dashed GABLE line, none of which were ever part of the
clickable shape. For a roof picked with a small span (a thin sliver
alongside a normal-length ridge) or a short ridge (a thin sliver alongside
normal-length eave lines), most of what actually reads on screen sat
outside the hit region entirely — his own "little tiny roof" and this
thin-span report are the same bug from two different axes.

**Fix** (`floorplanner/roofs.py`, `RoofItem.rebuild()`): `self._path` now
includes every segment `paint()` draws — the ridge, both eave lines, and
each end's gable line when that end is a gable — so `shape()`'s 8in
stroke covers the whole visible outline, not just the ridge. 4 new tests,
`tests/test_roof_hit_testing.py`: a thin-span roof selectable on its eave
line, a short-ridge roof selectable on its eave line (confirmed RED
against the unfixed `rebuild()`, GREEN after), a gable-end line
selectable, and the full select-then-delete round trip.

Built on branch `roofs-r3b-clip-line` (already open for R3b's own clip-line
work), gate GREEN, merged to `main` at [PR #53](https://github.com/pjm4github/FloorPlanner/pull/53).

## Closed, 2026‑09‑05

Patrick's own check, in chat: *"OK that works fine."* **CLOSED.**
