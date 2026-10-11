# 0244 — report: the dormer's sides, projected up to the dormer — generated cheeks standing on the host roof; PR #81 updated, one commit

**Code, 2026‑10‑11.** No merge has happened since
[`0238`](0238-report.md). His word on [`0243`](0243-report.md), which
had removed the dormer's cheek risers and left its sides open:

> *"the dormer sides should be generated so that they are projected up
> to the dormer."*

## 0. WHAT IS BUILT

`_dormer_cheeks(dormer, host, RC, t)` in `fp3d.py`: along each side of
a dormer — its wall line, `span_in` from the ridge, the overhang not
counted — a run of wall pieces stands on the HOST roof's surface and
rises to half an inch under the dormer's eaves, wherever the host lies
below those eaves and inside the host's own footprint. Exterior wall
material, `t` = the exterior thickness, inward. Built as short boxes
(3″ along the line; the host is planar between its cut lines, so a
box's base is flat to well under a sixteenth), each base an inch into
the host's slab and each top inside the dormer's slab, so no face is
shared with a roof and no slot is left. The run is cut, interpolated,
at the station where the host reaches the eaves; a box whose midpoint
is outside the host's footprint is skipped — past the host's own eave
there is nothing to stand on. `_prism_slab` gained a per-vertex bottom
(`bottom_zs`) for it.

**It is not 0194's deleted `_dormer_walls` back.** Those hung the
dormer's walls DOWN to the floor (his word then, [`0193`](0193-report.md)
/ [`0194`](0194-report.md): *"the walls of the dormer are being drawn
down from the dormer"*). These stand on the roof. The house walls under
a dormer still climb into it, unchanged.

**The front is a gable end and stays what a gable end is** — open, the
house wall beneath climbing into the dormer. On his R2 the dormer's
face stands on `rf4`'s south eaves wall `w28`, which climbs into the
dormer where the dormer's cells hold it, so the face is closed by the
wall. On the dormer-gable-check fixture, whose dormer face has no wall
beneath it, the face is open (the picture below). If he wants the face
generated too, it is the same run along the face line, one more call.

## 1. MEASURED

* R2: the left cheek at x=186 runs from y=300.5 (where `rf4` reaches
  the dormer's eaves, 216″) to `rf4`'s eave at y=360, not to the
  dormer's own end at 366; its top 215.5″, its base on `rf4` (156″ at
  the eave, an inch in); the rays through both cheek planes that hit
  no roof now hit the walls mesh.
* dormer-gable-check: cheeks at x=170 and 230 (plus `t` inward) from
  the face y=190 back to y=163, where the host reaches 116″; top 115.5″;
  no vertex below the host's eaves; every base vertex on the host's
  plane less an inch. The walls mesh of a dormer with no house walls is
  now exactly its two cheeks.
* The roofs meshes are untouched: everything 0241–0243 pinned holds.
* `--quick` 1540 passed; ruff clean; the full gate GREEN on the branch
  commit.

Pictures:
[`dormer-gable-check-3d-cheeks-built.png`](../evidence/dormer-gable-check-3d-cheeks-built.png)
(the fixture, face open, cheeks standing);
[`short-angle-roofR2-3d-southwest-built.png`](../evidence/short-angle-roofR2-3d-southwest-built.png)
and [`…-northwest-built.png`](../evidence/short-angle-roofR2-3d-northwest-built.png)
re-rendered.

## 2. TESTS

* `tests/test_viewer_dormer.py`: *a dormer builds no walls of its own*
  becomes *a dormer builds its cheeks on the host roof and nothing down
  to the floor* — the wall lines, the top, the floor never reached, the
  run's end where the host meets the eaves, every base vertex on the
  host's plane; the closure test now names the cheeks as what closes
  the eaves planes (wall hits, no roof hits) with the face open at the
  ridge; the climbing-wall test reads the interior mesh alone.
* `tests/test_roof_overhang_3d.py`: the R2 cheek test asserts wall
  where it asserted nothing of roof, the run's extent and heights.

## 3. WHERE IT STANDS

[PR #81](https://github.com/pjm4github/FloorPlanner/pull/81), still ONE
commit on `roof-overhang-build` rebased onto this landing: 0241, 0242,
0243 and this. **AMBER** — his check on R2: the dormer's sides stand as
wall from the roof up to its eaves. His criterion stands: no end wrap,
then #81 closes.

## 4. `fixtures/incoming/`, with ages

* `wiscaway2026-10-07R1.json` — his own, 2026‑10‑07; exit his to name.
* `README.md`.

## 5. WHAT HAPPENS NEXT

His check. Open: the dormer's face (§0); [`0241`](0241-report.md) §2's
reach. Behind it: the compose cost ([`0237`](0237-report.md) §0).

**Carried:** unchanged from [`0243`](0243-report.md).
