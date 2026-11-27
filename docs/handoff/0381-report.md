# 0381 — report on 0380. A and B's corner implemented as ruled: `climb_dormer` gated on territory AND box, `roof_beneath` stops at a roof that buries the base. The point table reads exactly; O4′ holds. Stopping for Patrick (0380 O4 / 0375 §5).

2026-11-26, Code. Branch `dormer-climb-floor-0372` (on `2f39c90`, which carries
item B's §8.4 floor fix); A + B's corner now committed on it. PR #115.

## 1. The two faults, fixed where 0380 placed them

**A (§3).** `climb_dormer` had been gated on the grown wall box ALONE (0379).
`dormer_over` at `2f39c90` carried a second condition the box was being ADDED
to — the piece must lie in THAT dormer's TERRITORY cells — and dropping it let a
cheek wall uphill of the valley be cut at the dormer plane buried in the host.
Restored: `climb_dormer` returns a dormer only where the piece lies in its
territory cells AND inside its grown box (`fp3d.py`, `_wall_under_roofs`). The
`dormer_boxes` list now carries the cells again; nothing else in A changed.

**B's corner (§4).** `roof_beneath` took the highest non-dormer roof at or below
the base and so skipped a roof drawn ABOVE the base — on the frozen lean-to it
dropped the face wall through `rf4` to the host strip beneath. Rule, as ruled:
where any roof over the piece is at or above the wall's base, the base is closed
and nothing drops. `roof_beneath` now returns `None` the moment it meets a
covering roof at or above `z_lo`, and otherwise the highest roof strictly below.

## 2. The point table (0380 §2 and §4), measured by barycentric z at the column

`climb_dormer` with the territory restored, W01 cheek x = 120:

| y | 98 | 104 | 110 | 116 | 122 | 128 | 134 |
|---|---|---|---|---|---|---|---|
| read | 149.5 | 143.5 | 137.5 | 131.5 | 125.5 | 119.5 | 116.5 |

Exactly your `2f39c90` column. Frozen BR3 cheek (799, 640) = **211.2**. The six
points of 0375 §1 are unchanged (134.2 / 120.0 / 250.4 …).

B's corner, face-wall base (lowest wall z):

| | (803, 805.5) | (810, 805.5) | (942, 805.5) |
|---|---|---|---|
| lean-to (the plan as drawn) | 134.0 | 134.0 | 134.0 |
| hipped `rf4` | 124.0 | 128.7 | 123.7 |

The lean-to keeps its base across the whole outer width (`rf4` 139–143 buries
the 134 base). The hipped case drops only the outer half, where the hip is
below the base; the inner half stays at 134. **Why the hipped centre does not
drop the same way:** it is the same rule read twice. A roof at or above the base
closes it. On the lean-to, `rf4` lies above the base across the entire outer
strip, so nothing drops anywhere. On the hip, the surface rises toward the
ridge: over the centre it is above the base (closed, no drop), over the outer
corners it has fallen below the base (open, drops to the hip). One roof, two
places, the one test.

## 3. O1 — fail-first fixtures (in `tests/test_dormer_gable_3d.py`)

- `test_a_cheek_wall_uphill_of_the_valley_stands_to_the_host` — the committed
  W01 evidence fixture; asserts the x = 120 column follows the host (149.5 →
  116.5), not the dormer eave. Fails on 0379's box-only `climb_dormer` (116.5).
- `test_a_face_wall_over_a_lean_to_keeps_its_base` — your frozen BR3 plan is a
  user file, so the test is `skipif(not FROZEN.exists())` (it runs here and on
  your machine, is skipped in CI). Asserts the lean-to keeps 134 and the hipped
  variant drops 124.0/128.7/123.7. Fails on 0379's `roof_beneath` (112.9). I did
  not find a way to minimise this to a committed synthetic: the base-drop fires
  only where the climb territory, the eave-overhang restoration, the covering
  level's wall loops and the wall's own offset coincide, which your BR3 corner
  does and a small hand-built scene does not. If you want it in CI, I can cut a
  dedicated committed evidence JSON — say the word and I will.

## 4. O2 / O3 — the pins and O4′ made exact

The point table grew by the two you named (frozen (799,640)=211.2, W01
(120,98)=149.5), both pinned in the tests above.

**O4′ census, the corrected tree vs `2f39c90` over the 26 `0360` cases:**

- **0 wall tops raised, anywhere.**
- **No non-wall mesh differs** (name sets identical in every case).
- Wall-top *reductions* occur only in the class-2 cases (W02, W08, W26) — the
  fins the grown box + territory remove. These are OUTSIDE the grown box by
  construction: inside the box the corrected climb equals `2f39c90`'s (both have
  the territory and the box contains it), so inside-box tops are unchanged — 0
  points changed inside a grown box, as you measured.
- **B's below-base material is its own class** (0380 O3): the base-drop adds
  wall material BELOW a face/cheek base where a roof is genuinely beneath it, in
  8 of the 26 cases (W01, W07, W09, W25, W31, W37, W40, W61). It lowers bottoms,
  never raises a top, and never fires where a roof buries the base.

## 5. Gate, PR, and the stop

`tools/gate.py` GREEN (ruff + OFF + ON). A + B's corner + the two fixtures
committed on `dormer-climb-floor-0372`; snapshot re-cut; PR #115 updated. Per
0380 O4 / 0375 §5 I stop here for your look. Items C, D, E of 0372 are not
started.
