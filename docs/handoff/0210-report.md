# 0210 — report: the 3‑inch reach — his report against grid snap reproduced, 0208 §2(a)'s 9″ rule withdrawn, two more over-reaches found by the check plan; AMBER, stopped for his check

**Code, 2026‑10‑04.** No merge has happened since
[`0209`](0209-report.md). Branch `grid-snap-flat-3in` off `main` at
`c265210`, [PR #71](https://github.com/pjm4github/FloorPlanner/pull/71)
open, gate GREEN, **stopped for his check** (§5).

## 1. HIS REPORT

> *"I added a macro recording that I'm using to test the off-grid snap (in
> the incomming directory). I draw V37 and release at v38 (the last drawn
> horizontal wall) and I expect that wall to NOT SNAP to the veritcal wall
> because it is more than 3 inches away from the vertical wall. It snaps at
> 5.27 feet instead of 6 feet. Is that the correct operation?"*

Then, on my answer: *"fix it."*

**Reproduced, and it is the rule [`0208`](0208-report.md) §2(a) added.**
5.27 ft is 63.25″. A vertical wall at x = 63.25, off the 6″ grid; a
horizontal wall drawn toward it and released at x = 72 (6 ft):

| vertical wall at | released at | the end landed at |
|---|---|---|
| 60″ — on the grid | 72″ | 72″, no pull |
| **63.25″ — off the grid** | **72″** | **63.25″** — pulled 8.75″ onto the wall |

0208 §2(a) kept a 9″ reach toward a target that is off the grid, on the
reasoning that the grid cannot land an end there. [`0209`](0209-report.md)
§1 recorded that this rule was merged without his judgement of it. **He
has now judged it, and it is wrong:** nothing should pull from more than
3″. The reasoning was also unnecessary — the grid point nearest any line
is never more than 3″ from it, so an end *aimed* at an off-grid wall is
always within a 3″ reach.

**His own macro does not show the fault, and that is itself the finding.**
`fixtures/incoming/drawing-to-6plus.fpm` was recorded on an empty plan,
where the vertical wall it draws lands at exactly 5′‑0″ — on the grid —
and the last wall ends at 6′‑0″ as it should. The fault needs an off-grid
wall, and a macro cannot draw one: it has no Shift-drag. I inferred the
63.25″ from his number; **I have not seen the plan he tested on.**

## 2. WHAT'S BUILT — one reach for every pull

| | before | now |
|---|---|---|
| an end released 8.75″ from an off-grid wall | pulled onto it | **left where released** |
| an end released 2.75″ from it | pulled onto it | pulled onto it |
| an end dragged to 7.75″ from it | pulled onto it | lands on the grid |
| a press 7″ from an off-grid corner | starts on the corner | starts on the grid |
| a press 2.8″ from it | starts on the corner | starts on the corner |

* `WALL_PROJECT_STICK` is **3″** (it was 9″): the draw's align and the end
  drag's stick. The start catch uses `GESTURE_WELD_IN`, on the grid or
  off it. The "skip a target that is on the grid" test of 0208 §2(a) is
  gone — with a 3″ reach from a point already on the grid it can never
  fire.
* Normalize, Close gap and extraction still use `JOIN_TOL` (9″).

## 3. TWO MORE OVER-REACHES — found by the check plan failing its own second case

I built the check plan (§5) and its second wall, meant to stop 6″ from
the on-grid wall, landed **on** it. Traced, on `main`'s geometry:

**(a) The align pull had no limit on how far away the wall is.** A drawn
end is pulled to the projected line of an open-ended wall — *any*
open-ended wall in the plan, however far along that line. On the check
plan the off-grid wall **7 ft away** took the end from 5′‑6″ to
5′‑3¼″. Now the wall must pass within `WALL_PROJECT_NEAR` (4 ft) of
where the end would land — the limit, measured the same way, that the
end drag's stick has always had. This predates A6; the 9″-to-3″ change
only made it visible.

**(b) A wall body caught an end at 3.25″, not 3″.** `nearest_wall_body`
widens its reach to half the wall's thickness plus an inch — 3.25″ on an
interior wall, 4″ on an exterior one. For a gesture that is a pull from
beyond 3″. It now takes `exact=True` from the draw release and the start
snap and reaches exactly 3″; the explicit passes keep the widened reach.

Together (a) then (b) had moved the end 6″ in two steps, neither of them
the reveal's fault.

## 4. THE CHECK — receipts

`tests/test_grid_snap_default.py` is now **22 tests** (19 functions, three run at
both zooms). New: his case at
both zooms; an end aimed at the off-grid wall still reaches it; the same
two halves for an end drag; the start catch at 2.8″ and 7.1″; and the
check macro replayed verbatim on the check plan, asserting its four
landings. **Seven tests fail on `main`'s code and pass on the branch**,
run there.

Rewritten, each because it pinned a reach this report withdraws:
`test_walls.py`'s off-grid pull (written at 0208; now asserts 2″ pulls
and 8″ does not); `test_wall_move.py::test_orthogonal_stick_is_zoom_independent`
(asserted a 5″ stick; now 2″ sticks and 5″ does not);
`test_floors.py::test_align_to_wall_does_not_snap_to_a_hidden_floor`,
whose two walls stood 200″ and 400″ from the drawn end and now stand
20″ from it, inside both new limits — its negative assertion and its
positive control are otherwise as [`0063`](0063-ruling.md) §3 wrote them.

Full suite **1416 passed**, 7 deselected (`perf` lane), `ruff` clean,
gate GREEN — the branch's own run.

## 5. HIS CHECK

Open `fixtures/grid-snap-3in-check.json` and run
`fixtures/grid-snap-3in-check.fpm`, or follow
`fixtures/grid-snap-3in-check.md` by hand. Four walls, each with the
landing it must have; **the third is his case** — released at 6′, 8.75″
from the off-grid wall, and it must stay at 6′. Then the plan he first
saw it on.

## 6. FOUND, NOT BUILT

* **Two parallel same-type walls 6″ apart merge into one.** His macro's
  last two lines draw exactly that and the first wall disappears. It is
  the auto-coalesce tolerance, older than A6, and it means a 6″ gap
  between parallel walls cannot be drawn today. His to order.
* **The rule's wording, now simple enough to state once:** *a wall
  gesture lands on the grid; within 3″ of another wall's end or line it
  goes to that instead; Shift turns both off.*

## 7. `fixtures/incoming/`, with ages

* `drawing-to-6plus.fpm` — **his own, arrived 2026‑10‑04, the report
  behind this tranche.** Read and replayed, not edited. It does not
  reproduce the fault (§1). Its natural exit is **3, deleted as a
  duplicate** of `fixtures/grid-snap-3in-check.fpm`, which carries the
  case it was recorded to show — on his word.
* `single-floor-90-roof-gable-end-check.json` — his own, 2026‑10‑03,
  exit not yet named ([`0205`](0205-report.md) §3).
* `README.md`.

**Also in the working tree, not mine and not touched:** four files under
`docs/macro-spec/` are staged in the index (`MACRO_SPEC.md`,
`examples.macro`, two ANTLR grammars). They appeared during this
session, from outside it. This tranche's commit named its own paths so
that they were left out.

## 8. WHAT HAPPENS NEXT

His check (§5). On his word PR #71 merges, branch deleted in the merge
step, the merge recorded in the report that follows. Then the queue as
[`0209`](0209-report.md) §4 left it.

**Carried:** unchanged from [`0209`](0209-report.md).
