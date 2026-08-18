---
# permanent key, independent of GitHub
id: 79
title: "Six catalog symbols extrude as disconnected fragments, not one body"

# maps directly onto GitHub Issues fields
state: open
state_reason: null
labels:
  - type:gap
  - area:viewer
milestone: null

# ours; becomes body prose after migration
opened: 2026-08-16
closed: null
closed_by: null
rank: 79
related: []
state_source: row
github_issue: null
---

# D79 — Six catalog symbols extrude as disconnected fragments, not one body

**Filed per [`handoff/0034-ruling.md`](../handoff/0034-ruling.md) §5 — one
record for six items, not six records**, found while building the
extrudability predicate ([`handoff/0029-ruling.md`](../handoff/0029-ruling.md),
[`0032-report.md`](../handoff/0032-report.md)) and left unfiled at the time,
pending this ruling.

## The finding

`floorplanner/viewer/fp3d.py:extrudability()` reports `body_fragments` as the
number of CONNECTED COMPONENTS among a symbol's top-level (non-nested) plan
shapes — two shapes are one component if their bounding boxes touch or
overlap within 3% of the viewBox's smaller dimension, a drafting-scale
tolerance for "meant to touch," not a scalar size threshold. `boat_trailer`
was the known instance ([`0012-ruling.md`](../handoff/0012-ruling.md),
[`0013-ruling.md`](../handoff/0013-ruling.md)): six slabs, no trailer.
**Measured over the whole catalog, six more items share the same shape**:

```
motorcycle          2 components
bicycle              2 components
garden_tractor       3 components
riding_mower_snow    6 components
drill_press          2 components
water_softener       2 components
```

**One mechanism, not six unrelated faults**: each item's real form is an open
frame or a set of separate physical bodies, drawn as disconnected filled
pieces that a solid extruder turns into floating fragments rather than a
recognisable object — the same shape `boat_trailer` already named.

## Where the line sits, so this is not a threshold guess

Per [`0012-ruling.md`](../handoff/0012-ruling.md)'s own rule — *inspect the
items either side of the line, print every raw value* — the closest-pair
bounding-box gap was measured for every catalog item with two or more
top-level shapes, as a percentage of the viewBox's smaller dimension:

```
...  jointer 2.75%  [3% cutoff]  water_softener 8.33%  ...
```

**Nothing sits between roughly 1% and 3%.** The closest item on the
"still connected" side is `jointer` at 2.75% (an ordinary two-piece tool
table, correctly not flagged); the closest on the "still disconnected" side
is `water_softener` at 8.33%. A margin of that width means the six items
above are not artifacts of where the tolerance happens to sit.

## Disposition, item by item

* **`bicycle`** already has a ruling — [`0013-ruling.md`](../handoff/0013-ruling.md)
  §3: *"stays as it is… a bicycle IS thin, and a 24×68 box says something far
  more wrong."* This record cites that disposition rather than reopening it.
* **`motorcycle`, `garden_tractor`, `riding_mower_snow`** are `vehicle` form
  — the same population [`0012-ruling.md`](../handoff/0012-ruling.md) already
  measured at 3 of 10 built cleanly. **The likely owner is the vehicle loft**
  design (`floorplanner/viewer/VIEWER_NOTES.md` §5), exactly as
  `boat_trailer`'s own disposition already states — not a redraw of these
  four symbols individually.
* **`drill_press`, `water_softener`** are not vehicles and have no existing
  disposition. `drill_press`'s column and base sit 9.6% of its viewBox apart;
  `water_softener`'s two tanks sit 5.4% apart — both real gaps, not rounding
  noise. Undecided: artwork fix (draw the pieces touching, if that is
  accurate) or accepted as correctly depicting two adjoined-but-separate
  physical objects.

## Where the gate stands today

`tests/test_extrudability.py::test_every_symbol_body_is_one_connected_region`
exempts all seven items (`boat_trailer` plus these six) by name, each with
its own stated reason — an exemption without a reason is how a known finding
becomes an ignored one. The six new exemptions cite this record.

## Ruling

*(Open — filed 2026‑08‑16, per `0034-ruling.md` §5.)* `type:gap`: a real
finding, not yet a scheduled fix. `bicycle` closed by citation to
`0013-ruling.md`; `motorcycle`/`garden_tractor`/`riding_mower_snow` point at
the vehicle loft; `drill_press`/`water_softener` are open questions with no
disposition yet.
