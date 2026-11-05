# 0301 — report: P2 of the 1½-storey arc — the dash and the knee line (plan), built on a branch

**Code, 2026‑11‑05.** The record ([`0197-ruling.md`](0197-ruling.md) §7). P2 of
the arc ([`0297`](0297-ruling.md) §2, [`0293`](0293-ruling.md) §5 P2). Built on
branch `p2-dash-knee`, stacked on `p1-stacked-climb` (P1); AMBER, **not merged** —
the merge of P1–P3 waits on his check session A. No manual check yet (batched).
Next: P3 does not open until this report is on disk — it now is.

## 1. THE RULE (0293 §2b)

The plan's roof readings now read ABSOLUTE height, the one way 3D composes
(`floor_elevation`), so a roof governs a wall or a room on ANOTHER level.

* **The R3b wall dash** (`roofs.roof_clip_spans`): every live roof, not only one
  on the wall's floor; `_clip_spans_against_one_roof`'s affine math is unchanged —
  the per-roof ceiling is shifted by the two levels' base difference
  (`ceiling + wall_base − roof_base`), so the comparison is absolute. Same floor →
  the shift is 0 → byte-identical. Memoised on every roof's geometry, territory
  and level base (0276), held during a drag (0279).
* **The knee line** (`roofs.room_ceiling_break_lines`, new; painted dashed by
  `RoomItem.paint`): where any roof's surface crosses a room's ceiling plane
  (`base + ceiling`, absolute), inside the room outline — his ask, "walls that
  have a full height ceiling should get the dashed line that indicates where a
  flat ceiling starts." A DERIVED OVERLAY, never a wall and never stored, the same
  discipline as the wall dash and R5a's roof trace (`roof_clip_trace`, whose
  `_trace_lines_local`/`_trace_to_scene` it reuses). Memoised like the dash.

## 2. RECEIPTS — VERBATIM (instrument `docs/evidence/p2-dash-knee/receipts.py`)

**His `wiscawayL2-fix.json` (L2 height 96, base 120).**

```
WALL DASH by level (dashed / total):   BEFORE        AFTER
  L1:                                  9 / 95        9 / 95     (unchanged)
  L2:                                  5 / 51       19 / 51     (+14 cross-level)

KNEE LINE (rf1: ridge 294 abs at y=678, 12/12; L2 ceiling 216 abs -> 78 from
  the ridge -> y = 600, 756):
  BATH : y in [498.0, 501.5, 600.0, 632.5]
  BR2  : y in [741.5, 756.0, 789.9, 860.5, 864.0]
  BR3  : y in [741.5, 756.0, 789.9, 860.5, 864.0]
  OPEN : y in [600.0]
```

**L1's dash count is unchanged (9 → 9)** — an L2 roof over an L1 wall stands above
its ceiling, so it adds no dash. **L2 gains 14 dashes** — the L1 main roof it rises
through now dashes the L2 walls below its surface (0293 §1 M2's 0 dashes closed).
**The knee line in BR2/BR3 lies at y = 756** and in BATH/OPEN at y = 600 — hand-
checkable from `rf1`: ridge 294″ abs at y=678, 12/12 pitch (span 198); L2 ceiling =
base 120 + 96 = 216″ abs; the roof is at 216″ **78″ from the ridge** (294 − 216),
so the line lies at **678 ± 78 = 600 and 756**. (The charter's 580/776 was the
original file's L2 base 100; his is 120.)

## 3. TESTS, AND THE ONE CHANGED ASSERTION (0297 §6)

* New: `tests/test_roof_clip.py::test_a_room_gets_a_knee_line_where_the_roof_
  crosses_its_ceiling` (the line at y = 100 ± PERP_THRESH on each slope) and
  `::test_no_knee_line_when_the_whole_roof_is_above_the_ceiling`.
* **CHANGED ASSERTION, named:** `test_a_roof_on_a_different_floor_does_not_clip`
  → `test_a_roof_on_another_floor_clips_by_absolute_height`. P2's whole point: a
  roof clips by absolute height, not floor identity; in a bare scene (one datum)
  a cross-floor roof clips exactly as a same-floor one does.

Full gate GREEN on the final tree (OFF+ON; 2022 passed, 7 deselected — the perf
lane). Would `check(deep=True)` have fired? **No — a limit, not a gap** (0293 §1):
the invariants know nothing of heights; the instrument is the headless receipt.

## 4. NEXT

P3 — the dormer's level, datum, dialog and the four views (0293 §5 P3; 0295;
0296) — its own branch on `p2-dash-knee`. His files under `incoming/` stay his.
