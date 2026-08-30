---
# permanent key, independent of GitHub
id: 82
title: "fp2pdf dimension strings carry 1/16\" fractions Patrick wants whole feet-inches only"

# maps directly onto GitHub Issues fields
state: closed
state_reason: completed
labels:
  - type:task
  - area:io
milestone: null

# ours; becomes body prose after migration
opened: 2026-08-28
closed: 2026-08-30
closed_by: null
rank: 82
related: []
state_source: row
github_issue: null
---

# D82 — fp2pdf dimension strings carry 1/16" fractions Patrick wants whole feet-inches only

**Filed per Patrick's manual check on [PR #42](https://github.com/pjm4github/FloorPlanner/pull/42)
(`handoff/0116-ruling.md`)** — reported alongside D81, same check, same "merge
now, fix the PDF content separately" direction.

## The finding

`floorplanner/export/fp2pdf.py:ftin` (`:92`) formats a length to the nearest
**1/16 inch** and appends the reduced fraction when non-zero (`20'-6 1/2"`).
Every dimension string on the sheet goes through it: the wall-run dimension
rows (`dim_row_x`/`dim_row_y`, `:435`/`:452`ish, `label = ftin(b - a)`) and
each room's clear-size / ceiling-height label (`draw_rooms`, `:339`/`:343`).
Patrick's ask: PDF dimensions should read in **feet and inches only** — no
fractional-inch remainder — not that the underlying geometry is wrong, only
that `ftin`'s fraction term should not appear on this output.

## Site

`ftin()` is the single formatter every PDF dimension string calls (`fp2pdf.py`
has no second formatting path); a whole-inch mode is a change to this one
function's rounding, not a multi-site fix. `walls.py` and other editor-facing
labels are out of scope — Patrick's ask names the PDF specifically, not the
on-canvas readout.

## Not built here

Per Patrick's direction, this is tracked as a separate fix, not folded into
PR #42. Rounding to the nearest whole inch changes what a dimension STRING
reads without changing any stored geometry — worth a differential receipt
(does any wall in the existing corpus round to a value that reads as
ambiguous or that disagrees with its neighbour's rounded total) before
shipping, per this project's own rule that a task changing what an operation
reports owes a receipt.

## Ruling

**Closed 2026‑08‑30, [`handoff/0118-ruling.md`](../handoff/0118-ruling.md) →
[`0122-report.md`](../handoff/0122-report.md).** Built as **station
clustering + whole-inch telescoping**, not naive independent rounding
(`0118` §2): drifted stations under the sheet's own 1″ resolution merge to
their mean first, then `dim_row_x`/`dim_row_y` label adjacent pairs from
ROUNDED stations so row 1 sums to row 2 exactly — the differential receipt
this record itself called for, run corpus-wide at
`docs/evidence/pdf_dimension_telescoping_census.py` (964→856 stations
across 21 real sheets, telescoping holds on every one).
**Scope, precisely: the wall-run dimension ROWS only** — `ftin()` itself is
unchanged and every other caller (room clear-size / ceiling-height labels
in `draw_rooms`) still prints its 1/16″ form, per `0118` §2's own text
("`ftin` keeps its 1/16″ form for anything else that calls it"); this
record's own "Site" section named the dimension rows specifically, not
those labels. Patrick's own check on
[PR #43](https://github.com/pjm4github/FloorPlanner/pull/43) passed;
merged to `main` at `36fb6b5`.
