# 0245 — report: the set-back dormer's face climbs from the roof itself — `_dormer_face`; his `short-angle-roofR3.json` promoted; PR #81 updated, one commit

**Code, 2026‑10‑11.** No merge has happened since
[`0238`](0238-report.md). His word on [`0244`](0244-report.md), with a
third file and a picture of the hole:

> *"OK the dormer ends looks good when the outside wall beneath it is
> climbed. There is one more problem, when the dormer is set back (see
> short-angle-roofR3.json) then the dormer face needs to climb up from
> the roof itself. See the hole in the image on the dormer when it is
> set back."*

## 0. WHAT THE HOLE WAS

R3 is R2 with the dormer's face moved from y=366 (6″ past `rf4`'s south
eaves line, standing on the eaves wall `w28`, which climbs into the
dormer) to y=336, 24″ inside it — on the roof, with no wall beneath.
0244 left the face what a gable end is, open unless a wall beneath
climbs; here nothing was beneath but `rf4`, so the dormer stood open
from `rf4`'s surface (180″ at that line) up to its rake (264″ at the
ridge).

## 1. THE RULE

**`_dormer_face`**: across the dormer's face line — the end whose ridge
point stands highest above the host; the back end sits on the host
plane — from one wall line to the other, a run of exterior-wall pieces
stands on the host's surface and rises to half an inch under the
dormer's OWN surface there: the rake, ridge height in the middle falling
to the eaves at the sides. `t` thick inward along the ridge. Same
construction as the cheeks ([`0244`](0244-report.md)): 3″ boxes, a
per-vertex base an inch into the host's slab, the top ring on the
dormer's surface per vertex, the run cut where the host meets the rake,
the ridge itself a station so the kink is honoured. **Built only where
the host lies below the rake and the point is inside the host's
footprint** — so R2's face, past the eave, gets nothing here and `w28`
goes on climbing (his *"when the outside wall beneath it is climbed"*),
and R3's face, on the roof, is closed.

## 2. MEASURED

* R3: wall across the face line y=336 from x=186 to 282, 6″ inward
  (y 330–336), base on `rf4` an inch in, top 263.5″ at the ridge; rays
  through the face plane inside the gap hit wall and no roof.
* R2: nothing generated on y=366; the ray through `w28`'s climb under
  the dormer hits, as before.
* dormer-gable-check: its face at y=190 is on the host, so it is now
  generated too (top 135.5″, x 170–230); the cheeks unchanged; the four
  0195 rays all hit wall.
* The roofs meshes untouched; `--quick` 1542 passed; ruff clean; the
  full gate GREEN on the branch commit.

Picture:
[`short-angle-roofR3-3d-southwest-built.png`](../evidence/short-angle-roofR3-3d-southwest-built.png).

## 3. FIXTURE AND TESTS

`fixtures/short-angle-roofR3.json` promoted under exit 1, his sentence
as its row. `tests/test_roof_overhang_3d.py` (22): R3 is R2 with the
dormer set back and nothing else; the face generated on R3 and not on
R2, with `w28`'s climb as the control. `tests/test_viewer_dormer.py`:
the dormer builds its cheeks AND its face on the host, nothing down to
the floor; the closure test names the face; the two wall tests read the
interior mesh alone.

## 4. WHERE IT STANDS

[PR #81](https://github.com/pjm4github/FloorPlanner/pull/81), still ONE
commit on `roof-overhang-build` rebased onto this landing: 0241–0245.
**AMBER** — his check on R3: the set-back dormer closed by wall on all
three sides, standing on the roof; and R2 as before. His criterion
stands: no end wrap, then #81 closes.

## 5. `fixtures/incoming/`, with ages

* `wiscaway2026-10-07R1.json` — his own, 2026‑10‑07; exit his to name.
* `README.md`.

## 6. WHAT HAPPENS NEXT

His check. Open: [`0241`](0241-report.md) §2's reach. Behind it: the
compose cost ([`0237`](0237-report.md) §0).

**Carried:** unchanged from [`0244`](0244-report.md).
