# 0158 — report: R4b's check found three things — per-side eaves pick, editable spans, and the span measured to the ridge LINE

**Code, 2026‑09‑07, answering Patrick's own check of R4b
([`0157-report.md`](0157-report.md) §3, PR #55) — run the same day, three
findings, all fixed on the same branch. Still AMBER; his re-check is owed.**

---

## 1. WHAT HE FOUND, AND WHAT IT WAS

**Finding 1 — "overhang 24 both sides, but the footprint isn't symmetric."**
His screenshot, measured: the ridge sat about 6″ above the room's centreline;
the eaves pick took the span to the wall he clicked (about 93″) and
**mirrored it** to the far side, whose wall was about 107″ away — so the far
eaves-start line landed 14″ *inside* its wall and the 24″ overhang poked only
10″ past it. Both overhang fields were honoured; the footprint they were
added to was lopsided. R3b's clip line on the far wall was the same fact
seen from the wall's side. Root: `finish_roof_ridge` handed the roof ONE
number and R4a's normaliser stored `[v, v]`; nothing between R2 and R4b ever
measured the far side, and the 0154 plan left the two spans diverging only
through R4c's grips.

**Finding 2 — no way to correct it.** An existing roof's spans were not in
any dialog.

**Finding 3 — "on an angled roof the overhang must be orthogonal to the
wall it overhangs: 24 inches from a 45° wall."** This one was a real
measurement bug, not just a symmetry gap. `eaves_span_from_wall` measured
from the wall's midpoint to the ridge **segment**: correct while the midpoint
projects inside the ridge, but the **hypotenuse to the nearer ridge end**
once it projects past one — a ridge sketched shorter than its wall, or a 45°
wing's ridge shifted along the wing. The span inflates, and the eave line
lands further from the wall than the overhang says.

## 2. WHAT'S BUILT

* **`roofs.eaves_spans_per_side(scene, p1, p2, floor, picked)`** — the
  picked wall sets ITS side; the other side takes the nearest parallel wall
  **across the ridge** (`nearest_eaves_wall`'s own parallel/nearest rule,
  restricted to that side); a side with no such wall mirrors the other,
  which is exactly the pre-R4b result — every roof over one wall, or none,
  is unchanged. `ridge_side()` maps a point to `span_in`'s left/right index.
  Both pick paths use it: `finish_roof_ridge` (the click) and `cancel_temp`
  (the Esc auto-complete from the "disappearingroof" report). Which of the
  two walls is clicked no longer matters to the result (tested both ways).
* **`roofs.eaves_span_to_ridge_line()`** — the perpendicular distance from
  the wall's midpoint to the ridge's infinite line, which is what
  `_eave_ends` actually offsets by. Used by the per-side pick.
  **`nearest_eaves_wall` keeps the segment form on purpose**: it is the
  pre-R4a migration's search, and R4a's receipt is that a pre-R4a document
  loads with exactly the geometry it always had — a migration is not the
  place for a content correction ([`WORKING_AGREEMENT.md`](../WORKING_AGREEMENT.md)'s
  own rule). A roof that came in inflated that way is fixed from the dialog.
* **The dialog gains "Eaves span, left / right"** (ridge-to-wall-centreline,
  editable). A span edit moves the wall line on the drawing, re-derives
  the derived field (pitch is rise over the LEFT span), and — while bound —
  re-measures which rooms the footprint covers. `apply()` writes `span_in`.
  These are the same two values R4c's eave-edge grips will drag.
* The dialog's note now states the convention in his terms: a span is the
  ridge-to-wall-centreline distance; the overhang extends that far past the
  wall — **24″ is two 12″ grid lines**. On a 45° eaves wall (parallel to
  its ridge) the ridge's normal IS the wall's normal, so "orthogonal to the
  wall" holds by construction once the span is right.

**A limit named, not hidden:** a gable roof's eave is a straight line
parallel to its ridge. An eaves wall that is *not* parallel (the pick
tolerates up to 20°) cannot have a constant overhang; the span is measured
at its midpoint and the overhang is exact there.

## 3. THE CHECK — receipts

11 new tests in `tests/test_roof_params.py` (now 40): the pick measuring
each side to its own wall with the ridge 20″ off-centre — the shape of his
sketch — from either wall; a single wall still mirroring (the control, and
the preserved pre-R4b behaviour); a perpendicular gable-end wall not
mistaken for the far eaves; the Esc auto-complete path measuring per side;
**his own acceptance in his own words** — walls on the 12″ grid, ridge 12″
off-centre, overhang 24, both eave lines exactly `2 × GRID_MINOR` past their
walls; the dialog showing and writing both spans, a left-span edit
re-deriving pitch, a span edit re-measuring the binding; and the 45° wing —
walls parallel to a short, shifted ridge, both eave lines exactly 24″ from
their walls along the walls' own normals, with a positive control showing
the old segment distance gives the hypotenuse (122.5″) for the same
geometry where the line distance gives 100″.

Full suite passed, `ruff` clean, gate GREEN (numbers in the commit).

## 4. DISPOSITION

**Still AMBER.** PR #55 updated on the same branch; his re-check is the
same sentence as before plus the two things he added: an off-centre ridge
should now come out symmetric about the building, 24″ should read as two
grid lines past each wall, and the 45° wing's overhang should measure 24″
from its wall. R4c unchanged, next after this lands.

**Carried, unchanged:** D83/D84 (held); room-label rounding
([`0131`](0131-ruling.md) §2); delta-snap sites; D61-family; yard items.
