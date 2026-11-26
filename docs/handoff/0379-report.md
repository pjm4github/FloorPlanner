# 0379 — report on 0375: A matches your §1 point table exactly, B's corner works, BUT the fix over-reaches at the face CORNER (a wall top inside the grown box changes). A STOP, your call. AMBER.

2026-11-26, Code session, branch `dormer-climb-floor-0372` (A + B's corner in
the tree, uncommitted — held while I report this). I did item A to 0375 §2 and
item B's corner to 0375 §4; both verify against your exact figures. Regenerating
the evidence for O4' then turned up one class of change that breaks O4' §3
("nothing differs inside a grown box"), so I stopped rather than commit it.

## 1. What is built and verified

- **A (the fin fix), 0375 §2.** `dormer_over` is now `climb_dormer`, gated to the
  dormer's `wall_fp` box grown by HALF the wall's thickness; pieces are SPLIT at
  the grown-box edge first (so no straddling sliver). `_hidden_overhang_pieces`
  is untouched — I factored its box into a shared `_dormer_wall_box`,
  byte-identical at `grow=0`. On the frozen file, read at your §1 points clear of
  the L2 walls, every one matches your "override only in the dormer's box" column:

  | Point | before | after | §1 wants |
  |---|---|---|---|
  | front post S (797,812) | 200.4 | 134.2 | 134.2 |
  | front post N (947.5,812) | 200.0 | 134.2 | 134.2 |
  | cheek fin S (790,780) | 195.7 | 120.0 | 120.0 |
  | cheek fin N (955,802.5) | 195.0 | 110.2 | 110.2 |
  | face wall outer half (872,805.5) | 250.4 | 250.4 | 250.4 |
  | cheek wall outer half (795,740) | 199.0 | 199.0 | 199.0 |

- **B's corner (option b), 0375 §4.** The solid piers take a base-drop: a
  face/cheek-line wall (one that climbs into the dormer) runs its base DOWN to
  the first non-dormer roof drawn beneath it, cut at the equal-height line, only
  downward, only the piers (not headers/sills). On the hipped file: the gap under
  the face wall closes at x 800 and x 945 (the wall reaches the hip, 122) and the
  centre, where the skirt is above the base, is unchanged.

- 127 dormer/roof tests pass; `test_viewer_dormer.py`'s climb test updated for
  the grown box (its last climbing vertex is now at the grown edge, x 167.75).
  Ruff clean.

## 2. The stop: a wall top changes INSIDE the grown box at the face corner

O4' §3 says nothing inside a grown box may differ. It does, at the corner where
a cheek meets the face. Measured on **W01** (which O4' lists):

- at plan **(120, 98)** a wall top goes **149.5 → 116.5** — a 33 in drop. That
  point is inside the grown box (x 117–243, y 93–171), so it must be preserved,
  but it caps at the host instead.
- `climb_dormer` fires for that cheek wall at y ≥ 113 (returns the dormer) but
  NOT in the y 96–113 band next to the face; those pieces take `owner_of` (the
  host) and drop. Something in the face region — the face overhang, or the
  face-window climb-band — keeps those pieces from reaching `climb_dormer`.

Your §1 points sampled the cheek and face OUTER HALVES (y 740, y 805), not the
face corner, so the point table passed while this slips through. Your own scratch
("nothing differs inside a grown box") evidently does not have it, so you likely
know the constraint that keeps the cheek-at-face climbing.

## 3. What I need

A short word on the corner: the mechanism that keeps a cheek/face wall climbing
in the y-band next to the face, inside the grown box. I did not want to fix it
forward blind and risk shaving the dormer's own corner another way. Once that is
settled I finish the evidence (O4', the 22–26 cases with class + fall; your W02
before/after; the frozen and hipped looks via a walls-only render that shows the
change cleanly), run the gate and open the branch.

## 4. Unrelated: 0376–0378 filed; the furnishings preserved

0376/0377/0378 are filed with this. Per 0378 §3 step 1, before touching 0375's
git state I put your furnishing change set into a commit on branch
`furnishings-0376` (cut from `main`), by path: 18 files, the eight fingerprints
of 0378 §2 match, and `fp3d.py` / `test_viewer_dormer.py` are not in it
(`ad7e0a9`). The owed furnishings work (regen, the 8 schema keys, Qt tests,
prices, gallery, evidence) waits on that branch until `main` holds the dormer
work (0378 §3 steps 3–5). The 7 pyramid evidence cases you asked me to name
(0375 §4): C2-weld-timing, C3-differential, E1-free-standing-hexagon,
E2-octagon-bay-on-eave, E4-square-astride-ridge, E5-weld-off-both-whole,
E6-half-gazebo-arc (you find 5 with walls; C3 and one E have none).
