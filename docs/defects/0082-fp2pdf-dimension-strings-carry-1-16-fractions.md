---
# permanent key, independent of GitHub
id: 82
title: "fp2pdf dimension strings carry 1/16\" fractions Patrick wants whole feet-inches only"

# maps directly onto GitHub Issues fields
state: open
state_reason: null
labels:
  - type:task
  - area:io
milestone: null

# ours; becomes body prose after migration
opened: 2026-08-28
closed: null
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
