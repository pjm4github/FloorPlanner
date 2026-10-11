---
# permanent key, independent of GitHub
id: 88
title: "A joined roof end's extension is drawn across roofs it never reached"

# maps directly onto GitHub Issues fields
state: closed
state_reason: completed
labels:
  - type:defect
  - area:geometry
milestone: null

# ours; becomes body prose after migration
opened: 2026-10-11
closed: 2026-10-11
closed_by: null
rank: 88
related: [85]
state_source: ruling
github_issue: null
---

# D88 — A joined roof end's extension is drawn across roofs it never reached

## The report

**Patrick, 2026‑10‑11,** with `short-angle-roof.json`: *"a 2 floor building
with a short roof on both sides of the 1st floor, a second floor with a
roof that is lower than the ceiling height of the second floor and a roof
on the 1st floor that is at 45 degrees with the same pitch as the other
short 1st floor sections. The right short section on the first floor is
being projected through the joining 45 degree roof. Since the right short
roof ends before intersecting the 45 degree roof it shouldn't project out
to that roof."*

## The mechanism, measured

Each short first-floor roof's inner ridge end lies under the low
second-floor roof `rf4` (its surface 276″ absolute over a 216″ ridge) —
a JOINED end since R4d, extended so its planes close the join under the
host. `compute_roof_clips` gave that extension ground (`domain`) in
**every other live roof's footprint**: `for other in live`. So `rf1`'s
extension ran east under `rf4`, came out at `rf4`'s far end (x=366) and
was drawn across the 45° roof `rf3` wherever its surface stood above
`rf3`'s — the fan he saw; `rf2`'s ran west and was drawn over `rf1`. Its
reach was the largest host diagonal, 1344″ from `rf3`, which merely
contains `rf2`'s end (standing 80″ above its surface) and joins nothing.

## The fix

The extension's ground lies in its **hosts'** footprints — the roofs whose
footprint holds the swallowed end, the ones it is converging with there —
and nowhere else: `for other in hosts`. A roof the end never entered gets
none of it. The three-way junction (R4g, `threeRidgeFloorplan.json`)
keeps its ground: there `rf2`'s end stands inside `rf3` too, so `rf3` is a
host, and its planes still run on over `rf3` to their valley.

**Receipt:** `tests/test_roof_joined_domain.py` — the fixture composed in
absolute height, each short roof's ground within its own footprint, `rf3`
unjoined, and the junction counter-case; RED before the one-line change.
Every roof, clip, trace, viewer and dormer suite unchanged. Closed at the
landing recorded in [`handoff/0238-report.md`](../handoff/0238-report.md).
