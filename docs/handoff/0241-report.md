# 0241 — report: the lower roof runs under the overhang — 0240 §1 built on `roof-overhang-build`, AMBER; measured on his design and on every roof fixture, including two the order expected unchanged and the rule reaches

**Code, 2026‑10‑11.** No merge has happened since
[`0238`](0238-report.md). [`0240`](0240-report.md) §1 ordered the build
on his word (*"the wall loop test is right"*); this is it, on
`roof-overhang-build`, one commit, for his check of the 3D view.

## 0. WHAT WAS BUILT — where it lives

`floorplanner/viewer/fp3d.py`, the roof builder, two functions and
eight lines of wiring:

* **`_wall_loops(walls, rooms, vx, level)`** — the closed loops a
  level's walls enclose, in plan: every bounded face of the level's
  wall graph (each directed wall edge walked once, turning to the next
  edge counter-clockwise at every vertex; bounded faces come out with
  negative signed area in raw plan coordinates — pinned on a box), plus
  every room outline of the level. A dangling wall encloses nothing; two
  walls that cross without a shared vertex are not joined here any more
  than in the plan.
* **`_hidden_overhang_pieces(geom, lifted, clip, terr, loops_of, RC)`** —
  for a clipped roof: its own nominal footprint, split by its visible
  cells' edges, by every other roof's territory edges and by its own
  plane-change lines; each piece whose centroid is not in a visible cell
  is HIDDEN; the roof covering it is the highest territory holding the
  centroid; the piece is built **iff that centroid lies outside every
  wall loop of the covering roof's level**; where its surface would rise
  above the cover's it is cut at the equal-height line and only the part
  below kept (`_clip_by_values` on the height difference — the clip's
  own seam arithmetic).
* The wiring: after a clipped roof's visible cells, the pieces above are
  meshed exactly as the visible ones (`_prism_slab` at the roof's own
  surface); `build_model` keeps each roof's lifted geom and a per-level
  loop cache. `_wall_under_roofs` untouched — the gable wall climbed
  already (0239 §1).

Three guards, each a line, each tested: a covering level **with no wall
loops at all states nothing** and nothing new is built under its roofs
(the wall-less roof docs of `test_viewer_model.py` build as before —
without this, the T fixture's wing ridge came back under the main); a
**dormer** is not an overhang (it stands on the roof it hides); **blank
ground** the clip erased stays blank.

## 1. ON HIS DESIGN — measured

`fixtures/short-angle-roof.json`, roofs mesh, vertex sets before and after:

| | before | after |
|---|---|---|
| `rf1`'s east end | x=108, a vertical cut 12″ short of `w26` | **x=120, at the gable wall**: `(120, 240, 216)` its ridge end, `(120, 120/360, 96)` its eaves corners |
| `rf2`'s west end | x=366 | **x=354**, the mirror |
| between the gable walls, 120 < x < 354 | only `rf4` | only `rf4` — every vertex on its surface `276 − |y−240|` or its slab underside |
| `rf4`'s overhang slab, x 108–120 | present | present, unchanged |
| vertices | 125 | 155: **30 added, none removed** |

Straight from the mesher: `rf1`'s two cells x 108–120 either side of its
ridge, 12 × 240 sq in in all; `rf2`'s strip x 354–366 less the cell
`rf3` draws there (which lies inside the first floor's walls, so stays
unbuilt); `rf3`'s own strip under `rf4` at the same place; nothing for
`rf4`. Every added piece lies at or below the roof covering it.

The pictures, beside the old ones:
[`short-angle-roof-3d-west-junction-built.png`](../evidence/short-angle-roof-3d-west-junction-built.png),
[`…-slice-built.png`](../evidence/short-angle-roof-3d-west-junction-slice-built.png),
[`…-southwest-built.png`](../evidence/short-angle-roof-3d-southwest-built.png).
In the slice, `rf1`'s two rakes now run in to `w26`, under `rf4`'s
gable; the wall rises from them to the upper ridge — his sentence.

## 2. WHAT THE RULE ALSO REACHES — two of 0240 §1 item 4's "unchanged" are not

Item 4 expected the gable-end fixture, the three-ridge fixtures and the
dormer fixture to build unchanged. **Measured, vertex sets before and
after, rule on and off:**

| fixture | roofs mesh |
|---|---|
| `single-floor-90-roof-gable-end-check` | identical |
| `dormer-gable-check` | identical |
| `roofs-r3-orbit-check`, `r6c-two-level-tool-check` | identical |
| **`threeRidgeFloorplan`** | **+18 vertices** |
| **`threeRidgeShortRidgeFloorplan`** | **+6 vertices** |
| **`wiscaway-2level-stacked-floor`** | **+178 vertices** |

**The three-ridge fixtures.** At the re-entrant corner between rooms B
and D — outside the house's walls — `rf1`'s eaves strip (its footprint
runs to y=642) lies under `rf3`'s, a few inches lower, and the rule
builds it: slivers within 14″ of the 96″ eaves, every vertex at or under
`rf3`'s surface, inside `rf1`'s own footprint, nothing removed. Visible
from under `rf3`'s soffit only; the rendered pictures before and after
are indistinguishable at any angle from above, which is why no picture
is landed for them. This IS the rule as ordered — a lower roof's own
footprint under a higher roof's overhang, outside the walls — met on a
same-level pair at an inside corner rather than across levels.

**The two-level stacked fixture.** `L2`'s roof `rf3` covers the whole
first floor; `L2`'s walls cover part of it. Where `L2` has no walls
(the front, y 312–444, and the east wing) the first-floor roof `rf1`
was hidden under `rf3` and is now built beneath it:
[`wiscaway-2level-3d-before-overhang-rule.png`](../evidence/wiscaway-2level-3d-before-overhang-rule.png)
→ [`…-after-overhang-rule.png`](../evidence/wiscaway-2level-3d-after-overhang-rule.png).
In the after picture the east wing has its own lower roof under the
upper one; before, the upper roof hung over bare walls there. Again the
rule as ordered: outside `L2`'s loops is "overhang" however wide.

**One line narrows it, if he wants the three-ridge fixtures
byte-identical:** build only under a covering roof of a HIGHER level
than the hidden roof's (0239 §2's wording, *"a higher roof … nothing of
the higher level encloses the space underneath"*). That keeps his design
and the two-level fixture as above and leaves every same-level pair as
it was — at the cost of the same-level case the rule also describes, a
porch roof running under the main roof's eave. Not taken: his word was
the wall loop test, and the test says what it says. His to rule.

## 3. THE RECEIPT

* `tests/test_roof_overhang_3d.py`, 12 tests: the second floor's walls
  are one box and x=114 is outside it (x=200 inside; the first floor's
  seven loops hold x=114); a dangling wall encloses nothing, a room
  outline counts, another level's walls do not; the short roofs reach
  their gable walls and nothing of them lies between (the named
  vertices, before and after, rule on and off); the added pieces
  straight from the mesher, with their areas; **the seam cut** on a
  steep lower roof under a shallow upper one — only the eaves strips
  beyond 85.7″ of the ridge are built, 2 × 14.29 × 100 sq in, every
  vertex under the cover, and a low roof is built whole (a cut, not a
  filter); the no-walls and dormer guards; four fixtures identical; the
  three-ridge additions pinned by place, height and cover.
* Gate GREEN: 1785 collected, OFF and ON 1778 passed, 7 deselected (the
  perf lane); `--quick` 1531 passed; ruff clean.
* The three evidence pictures re-rendered (§1) by the commands 0240 §1
  item 5 gives, plus the southwest default; the two-level pair (§2).

## 4. TIER

**AMBER** — it changes what the 3D view draws. For his check: his
design on `default`, the 3D view, the west junction from the south-west
and from due west: the left short roof runs in under the upper gable to
the wall, the wall rises from it to the upper ridge; the right short
roof the same at x=354. Then, if he opens
`fixtures/wiscaway-2level-stacked-floor.json`, §2's east wing — the
rule's reach on a wider overhang, his to keep or narrow.

## 5. `fixtures/incoming/`, with ages

* `wiscaway2026-10-07R1.json` — his own, 2026‑10‑07; exit his to name.
* `README.md`.

## 6. WHAT HAPPENS NEXT

His check; his word on §2. Behind it: the compose cost
([`0237`](0237-report.md) §0, the patch at
`docs/evidence/roofclip-adjacency-memo.patch`), as its own tranche.

**Carried:** unchanged from [`0240`](0240-report.md).
