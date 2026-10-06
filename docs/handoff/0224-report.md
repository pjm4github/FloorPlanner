# 0224 — report: the gable-end tranche built on `gable-end-walls`, stacked on `d67-floor-scope`; the read-back of 0223 §3 answered by his own words, not by him

**Code, 2026‑10‑06.** No merge has happened since
[`0222`](0222-report.md). [`0223`](0223-report.md) §3 read the gable-end
tranche back with one question and said it would be built on his words
if the read-back stood unanswered. It stood; it is built. Branch
`gable-end-walls` (`0c8219a`), stacked on `d67-floor-scope` (PR #76),
pushed, **no PR of its own** — one AMBER PR open at a time; he may land
them in turn or fold the gable commit into #76, as he folded #73.

## 1. WHAT IT DOES

**A gable end is open.** The roof is its two planes and, at a hip end,
R4b's sloped face; no triangle of roof material closes a gable end. On
an unclipped roof that is the `ends` loop skipping gable ends; on a
clipped one it is R4g's `_gable_fascia_pieces` removed outright, with
the history pointer left in its place.

**The gable wall climbs.** In `_wall_under_roofs`, a piece of an
EXTERIOR wall whose owning roof is not a dormer and whose plan direction
is perpendicular to that roof's ridge (within `GABLE_WALL_ANGLE_TOL_DEG`,
15°) is capped the way a wall under a dormer already was: its top is the
roof's underside wherever that is above the piece's base, however far
above the wall's own height. The caller hands the wall's direction in
only for exterior walls, so interior walls cannot climb; an eaves wall is
parallel to the ridge and does not qualify.

## 2. THE RECEIPT — his check plan

`fixtures/single-floor-90-roof-gable-end-check.json`, built by
`build_model`:

| | before | now |
|---|---|---|
| `w2`/`w4` (x=180, under `rf1`'s west gable), top at y=216 | 96″ | **161.25″** = 165.75 − 4.5 (the cap under the surface) |
| `w11` / `w19` (under `rf2`'s gables), top at x=534 | 96″ | **205.5″** = 210 − 4.5 |
| interior `w3` under `rf1`'s ridge | 96″ | 96″ |
| roof face in the plane x=168 (the rake tip) | two slab ends + a 7951 sq in triangle | **two slab ends, ≈1070 sq in** |

Three tests pin it (`test_viewer_model.py`); a fourth, on a synthetic
roof, pins that a wall parallel to the ridge does not climb while the
perpendicular one beside it does.

**What the rule also does, said because it was named at 0223 §3:** an
exterior wall perpendicular to the ridge anywhere under the roof climbs,
not only the outermost — on his plan `w16` (x=420, y 300–408) rises into
`rf1` where `rf1` owns the ground over it. It is under the roof and
behind the gable walls, so it shows nowhere.

## 3. WHAT THE RECORD REVERSES

* R3's acceptance line *"gables closed"* ([`0139`](0139-ruling.md) §2):
  `test_roof_gable_ends_close_by_default` is now
  `test_roof_gable_ends_are_open`, quoting him; the hip test counts one
  closing triangle, not two; two face-count assertions (`2·12 + 2·8`)
  are `2·12`.
* R4g's fascia clip ([`0176`](0176-ruling.md) §4): the function is gone
  and no test named it directly.
* `test_viewer_wall_clip.py`'s two tests that pinned the gable wall
  FLATTENING at its own top under the ridge, and every wall unchanged
  under a roof that clears it: the first now pins the climb to the ridge
  (every top vertex on the roof's underside), the second pins the eaves
  walls byte-identical and the gable walls climbing.

Nothing in `roofs.py`, `roofclip.py` or the plan view changes: this is
the 3D builder only.

## 4. STATE

`gable-end-walls` at `0c8219a`, two commits above `main` (the D67 commit
and this one); full gate GREEN on it: **1700 passed**, 7 deselected
(`perf` lane), `ruff` clean. PR #76 (D67) unchanged. `main` is this
commit. `fixtures/roofs-r3-orbit-check.json`'s evidence shot
(`roofs-r3-planes-gables.png`) now shows a closed gable the model no
longer builds; re-shooting needs his display (D77).

**For his check:** his own plan in the 3D view, from the west and from
the north: the gable walls rise to the ridges, no roof triangle in front
of them. Then PR #76's two checks ([`0223`](0223-report.md) §1).

## 5. `fixtures/incoming/`, with ages

Empty.

## 6. WHAT HAPPENS NEXT

His check of both; his word on landing them (in turn, or folded). Behind
them, unchanged: the four-way crossing fault, parallel walls 6″ apart
merging, the status board.

**Carried:** unchanged from [`0223`](0223-report.md).
