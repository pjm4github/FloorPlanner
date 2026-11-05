# 0299 — report: P1 of the 1½-storey arc — the stacked climb (3D), built on a branch, receipts verbatim

**Code, 2026‑11‑05.** The record ([`0197-ruling.md`](0197-ruling.md) §7). P1 of
the arc ([`0297`](0297-ruling.md) §2, [`0293`](0293-ruling.md) §5 P1). Built on
branch `p1-stacked-climb` (one commit on `c85ab38`); AMBER, **not merged** — the
merge of P1–P3 waits on his check session A (0297 §3). No manual check yet
(batched, 0297 §4). Next: P2 does not open until this report is on disk — it now is.

## 1. THE CENSUS (AST/grep over `fp3d.py`)

The level-identity readers of the climb all sit in `_wall_under_roofs`: the
`nearby` build keyed `dm and lid == level` (a same-level dormer) and `lid ==
level` (same level), consumed by `owner_of`, `dormer_over` and the climb
condition `to_top and (dormer or (same_level and gable_wall_of(geom)))`. The
territory (`terr`) already carried every building roof in ABSOLUTE height
(R6.b); only the CLIMB was gated on level. No other reader of `lid == level` /
`same_level` governs the climb.

## 2. THE RULE (0293 §2a)

`_wall_under_roofs`: the climb (gable and dormer) is granted by ABSOLUTE height
from whatever level the roof stands on — `dormer_over` now finds a covering
dormer on ANY level, and the climb condition is `to_top and (dormer or
gable_wall_of(geom))`, the `same_level` gate gone. It is BOUNDED at the base of
the storey directly above wherever that storey stands over the piece — a room of
it over the piece (`_wall_loops`, `_pip`) or a wall of it ALONG the piece's line
(`_on_a_wall`, reused — one definition). Where nothing of the storey above is
there, the climb runs to the roof as before. So 0254's fix comes by the bound,
not the level test: an L1 gable stops at L2's base and L2 closes the gable with
its own wall and window. The storey-above base/walls/loops are built once per
level in `build_model` (`_storey_above`) and passed in.

## 3. RECEIPTS — VERBATIM (instrument `docs/evidence/p1-stacked-climb/`)

**His wiscaway R-file `wiscawayL2-fix.json` (L2 height 96; L2 base 120 — he set
the elevation to 120, not the 100 0293 §5 assumed, so the numbers are on his
actual file; the rule is base-agnostic).** `receipts.py`, BEFORE → AFTER:

```
                       BEFORE   AFTER
L2 climbs (0 -> N)        0       14
DOUBLED (L1 above L2      7        0
  base where an L2 piece
  shares its plan)
highest L1 top under    289.5    120.0   (= L2 base)
  an L2 piece
8048 window hits         4        0      (0 = a void)
```

The charter's "15 → 0" was Patrick's count on the 100-base original; on his saved
file (L2 base 120) it is **7 → 0**. The 8048 L2 gable window renders as a VOID
(the L2 wall climbs; the first-floor wall no longer covers it, 0290 §2 closed).

**Positive controls (`controls.py`).**
* `dormer-test.json` (one level, no storey above) builds **byte-identical** —
  fingerprint `d7ebb7970ee297d9` BEFORE and AFTER.
* `little-dormer-test.json` gables at x≈60/600: **235.5 → 156.5/155.5**. These L1
  gable walls are collinear with the L2 box walls (`w20`/`w23` at x=60/600): the
  parts under the L2 box (y 576–744, including the ridge-height point) are bounded
  at L2's base (96); the gable corners OUTSIDE the box keep climbing to the roof
  (max 156.5). "Said which, measured" (0293 §5 P1).

## 4. TESTS, AND THE ONE CHANGED ASSERTION (0297 §6)

* `tests/test_gable_climb_level.py` stays GREEN — the L1 gable wall still stops at
  L2's base under an L2 roof, now by the BOUND's reason, not the level test. A new
  case pins P1's new capability: `test_an_upper_wall_climbs_into_a_first_floor_
  roof_and_its_window_shows` — a gable roof on L1 rising through L2, the L2 gable
  wall climbs into it and its window is a void.
* **CHANGED ASSERTION, named:** `tests/test_roof_shed_form.py::
  test_the_promoted_dormer_fixtures_are_unchanged_by_plan_c`. `_on_a_wall` now has
  a SECOND role — the stacked-climb bound — so on a two-level plan toggling it also
  moves the climbing-wall tops. The test now asserts the walls:exterior VERTEX
  COUNT is unchanged for all three fixtures (the face-yield adds/removes nothing),
  and full byte-identity only for the single-level fixture (`dormer-gable-check`,
  where the bound never fires). R2/R3 (L2 present) keep the count, not the
  positions.

Full gate GREEN on the final tree (OFF+ON; 2020 passed, 7 deselected — the perf
lane). Would `check(deep=True)` have fired on any of this? **No — a limit, not a
gap** (0293 §1): the invariants know nothing of heights or of 3D; the instrument
for this class is the headless build with a receipt, which this phase is gated on.

## 5. NEXT

P2 — the dash and the knee line (plan), on the same file (0293 §5 P2, 0297 §2);
its own branch on `p1-stacked-climb`. His files under `incoming/` stay his,
uncommitted.
