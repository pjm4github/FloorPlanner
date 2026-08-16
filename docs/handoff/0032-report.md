# 0032 — report: the predicate built, the census run, D76 reconciled — the redraw brief changes

**Per [`0029-ruling.md`](0029-ruling.md) and [`0030-ruling.md`](0030-ruling.md)/[`0031-ruling.md`](0031-ruling.md).**
GREEN portion only — the redraws themselves are next, AMBER, separate report.

---

## 1. THE PREDICATE, BUILT — `floorplanner/viewer/fp3d.py:extrudability()` plus `tests/test_extrudability.py`

**One production function**, so a gate test and a census read the same fact
rather than each re-deriving it: `extrudability(parts, viewbox)` returns
`(filled_count, body_fragments, has_region)` from `svg_outlines()`'s own
return, unmodified.

**Predicate 2 needed a correction before it could ship, found while building
it.** A naive "count of top-level rings" flags **17** items, not one —
`dining_chair`'s seat-plus-backrest is two top-level rings and a perfectly
ordinary `build_prism` `beside` body (read the function: `shapes[1:]` that
are not nested become `beside` and stay grouped with the body), not a
fragmented one. **The real signal is CONNECTED COMPONENTS among the
top-level rings' bounding boxes**, touching-or-overlapping within 3% of the
viewBox's smaller dimension — a drafting-scale "did the artist mean these to
touch" allowance, not a scalar size threshold (the lawnmower/snowblower
mistake, deliberately not repeated). Verified against the two known cases:
`boat_trailer`'s six slabs are tens of viewBox units apart, six components,
correctly still fragmented; `dining_chair`'s seat and backrest are 0.25 units
apart on an 18-unit viewBox, one component, correctly not.

**Fail-first checked, both hard predicates**, by temporarily breaking each
and confirming the test names the break, then restoring: predicate 1
expected-to-empty still names `glass_shower`; predicate 2 with `boat_trailer`
removed from its exemption dict fails naming exactly `boat_trailer: 6`.

## 2. THE CENSUS, RUN OVER THE WHOLE CATALOG (95 items)

```
PREDICATE 1 -- no closed filled shape:      ['glass_shower']
PREDICATE 2 -- fragmented body (components>1):
    {'motorcycle': 2, 'bicycle': 2, 'garden_tractor': 3,
     'riding_mower_snow': 6, 'boat_trailer': 6,
     'drill_press': 2, 'water_softener': 2}
PREDICATE 3 -- body, no internal region: 73 of 95
```

**Predicate 2 catches SIX items beyond `boat_trailer`** — not anticipated by
`0029`. Sanity-checked by hand, not just by the geometry: `drill_press`'s
column and base sit 9.6% of the viewBox apart (a real gap, not a rounding
artifact); `water_softener`'s two tanks sit 5.4% apart. The four vehicles
match `0012`'s own finding that `vehicle` was the form most prone to this
(3 of 10 built cleanly). **None of the six is filed as a defect and none is
ruled on.** `tests/test_extrudability.py` exempts all six by name, each with
"found building this predicate 2026‑08‑16, not yet ruled" as its stated
reason — visible in the test, not hidden, and distinguishable at a glance
from `boat_trailer`'s actually-ruled exemption. **Left to you**: file as a
defect (one record, `type:gap`, six items) or six, or fold into the vehicle
loft's eventual scope. Not decided here — it wasn't this task's to decide.

**`walk_in_shower` HAS a region now** (`has_region=True`) — its bench,
correctly built since the vessel/enclosure split. `0029` §3 flagged this as
the reason the item might come off the redraw list. **It does not come off
the list — see §3.**

## 3. THE D76 RECONCILIATION `0030` §4 ORDERED, MEASURED BEFORE ANY REDRAW

**The bench is fully contained in the body on all three axes, not merely
z.** Measured directly on `build_model`'s own meshes for one `walk_in_shower`:

```
furnishings:glass (body)   x [-29.25, 29.25]  y [-20.25, 20.25]  z [0.0, 78.0]
furnishings:stone (bench)  x [-27.50, -16.50]  y [-18.50,  18.50]  z [0.0, 18.0]
```

Bench ⊂ body on x, y and z. **D76 stands, unamended.** The bench does not
protrude; it is invisible strictly because an opaque mesh fully enclosed by
a translucent one does not composite in this viewer, exactly as D76 states.

**I cannot independently confirm the specific dark mark Patrick's own render
showed at the middle enclosure.** [`fixtures/shower-glance-check.json`](../../fixtures/shower-glance-check.json)
(placed by `0031`) rendered fresh, same camera
([`docs/evidence/shower-glance-before.png`](../evidence/shower-glance-before.png)),
shows no distinguishing mark on any of the three at this angle/zoom — which
is *consistent* with D76 (nothing should be visible) but is a render, not a
measurement, so it is offered as corroboration, not as the receipt. The mesh
comparison above is the receipt.

## 4. WHY THIS CHANGES THE REDRAW BRIEF, NOT JUST THE LIST

**A distinguishing mark placed as a `region` (nested, annotated height,
`wells`/`on_body`/`grounded` in `build_prism`) inherits D76's limit whenever
the body is translucent glass.** `walk_in_shower`'s bench already proves
this: correct geometry, correct material, invisible. Redrawing `shower` or
`glass_shower` with a region-shaped door/curb would very likely ship the
same invisible fix a second and third time.

**`beside` parts do not have this problem.** `build_prism` puts a
non-nested top-level ring's extrusion into `body_parts`, sharing the BODY's
material — a translucent door panel standing NEXT TO the main body, not
enclosed by it, composites the ordinary way two adjacent meshes do. **So the
redraw's mark should be drawn as a `beside` shape** — a second, smaller
top-level ring in the plan symbol, outside or only partly overlapping the
main outline (a door leaf, a curb along one edge) — not as a nested
`data-h` region.

**This likely also reopens `walk_in_shower`**, whose only feature today is a
`grounded` (nested) bench. Making it read as a shower may mean adding a
`beside` mark alongside the existing invisible bench, rather than relying on
the bench at all.

## 5. THE REDRAW LIST, PER THE GLANCE TEST, NOT THE CENSUS ALONE

`0029` §3 asked the census to decide the list; **the render decides it
instead**, per `0030`'s own verdict — *"None of the three reads as a shower
at all"* — which is stronger than "distinguishable from its neighbours."
**All three stay on the list**: `glass_shower` (predicate 1: no body at
all), `shower` (predicate 3: body, no region), `walk_in_shower` (has a
region, but it is invisible — §3/§4 above).

## Gate

`ruff` clean. `tests/test_extrudability.py`, 3 tests, fail-first checked on
both hard predicates. Full suite to follow before commit.
