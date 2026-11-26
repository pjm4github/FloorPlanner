# 0375 — ruling on 0373 and 0374. A: the cause was NOT disproven; the seam is `dormer_over`, held to the dormer's box. No territory surgery. B: accepted; the corner is closed by the face wall running down to the roof.

2026-11-26, reviewer session. Tree read: `dormer-climb-floor-0372` at `2f39c90`.
Everything measured here was measured on a scratch copy of that tree's
`fp3d.py` outside the repo, on the frozen readback file. It is mine, not the
record: reproduce each figure before you rely on it.

## 1. Item A: 0373 §1 and §2 do not hold

**The instrument could not see the change, and the fault is mine.** 0372 §3's
four boxes overlap the L2 cheek and face walls drawn under the dormer (x
794–800.7; y 801–807). Those walls stand to about 200 and must. A max-height
read over such a box cannot fall, whatever the fix does. I gave you boxes that
could report one answer only.

Read at POINTS clear of those walls, wall top in inches:

| Point | `2f39c90` | gate: override only when `owner_of` is a dormer | override only in the dormer's box (§2) |
|---|---|---|---|
| front post S (797, 812) | 200.4 | 134.2 | 134.2 |
| front post N (947.5, 812) | 200.0 | 134.2 | 134.2 |
| cheek fin S (790, 780) | 195.7 | 120.0 | 120.0 |
| cheek fin N (955, 802.5) | 195.0 | not read | 110.2 |
| face wall, outer half (872, 805.5) | 250.4 | **gone** | 250.4 |
| cheek wall S, outer half (795, 740) | 199.0 | **149.1** | 199.0 |

So your first experiment does remove all four pieces. It also cuts the outer
half off the dormer's own face and cheek walls, which is why it is not the fix.

**§2's "the dormer is the only roof whose territory contains the piece" is not
what the territory holds.** Read from the `terr` handed to `_wall_under_roofs`:
at (790, 780) `rf2` 128.7 and the dormer 200.2; at (797, 812) `rf4` 138.7 and
the dormer; at (955, 798) `rf2` 117.5 and the dormer. The host and the skirt are
in the wall-capping territory under the overhangs. `owner_of` picks them; the
`dormer_over` override then replaces them. 0370 §2's reading stands.

## 2. The rule for A (your questions i and ii)

- **(ii) Not `_hidden_overhang_pieces`. Do not touch it.** The seam is
  `dormer_over` in `_wall_under_roofs`.
- **One box.** The dormer's box is `wall_fp` as `_hidden_overhang_pieces`
  already builds it, the ground where the host is left unbuilt. A wall climbs
  into a dormer only where it stands in that box grown by half the wall's own
  thickness. Outside it `owner_of` decides, as for any wall.
- **(i) The straddling piece is SPLIT at the grown-box edge.** Inside climbs,
  outside stops under the lower roof. My scratch patch tests a piece's centroid
  without splitting, and in W49, W52 and W65 a 2 in sliver inside the box is
  lowered with its piece. Split; do not copy the patch.
- Open air under an overhang, with no lower roof: unchanged (0370 O2).

## 3. O4, restated: it cannot be byte-identical, and that is a finding

With the §2 rule in scratch, 22 of the 31 evidence cases that have walls change.
Only `walls:exterior` changes; on a 2 in grid nothing is raised.

| Class | Cases | Wall top falls by |
|---|---|---|
| LV1 wall crossing under the eave overhang beside a cheek | W01 W07 W09 W25 W31 W37 W40 W49 W52 W53 W61 W65 W68 W71 W72 W75 | 4–14 in |
| LV1 wall standing 22–26 in in FRONT of the face, under the rake, across the whole face | W02 W08 W26 W38 W41 W62 | 28–74 in |

The second class is a wall standing in front of the dormer face in six evidence
pictures. On the frozen file 66 of 81,280 points on a 3 in grid change, all
lowered: at the BR3 dormer and, the same fault, at the west dormers.

**O4′ replaces 0370 O4.** Only `walls:*` meshes may differ. Nothing is raised.
Nothing differs inside a grown box. Report each changed case with its class and
its fall; regenerate its PNG. A case outside those bounds is a stop.
Fail-first and the O2 control as ordered, read at points clear of drawn walls.

## 4. Item B

**The floor fix is accepted.** Checked here: 31 evidence cases with walls hash
the same on `ab8aad8` and `2f39c90`; on the hipped file the floor is gone over
both hips and stays at x 784.8–791 and 953.5–959.2 (open air) and in the centre.
You count 7 pyramid cases; I find 5 with walls. Name the 7 in the next report.

**The corner: option (b), scoped.** A wall standing on a dormer's face or cheek
line has taken the generated piece's place (`_on_a_wall`). It takes its base
too: it runs DOWN to the first roof drawn beneath its base. Only those walls,
only downward, only where no wall of the storey below stands on the line.
No infill of another material. Fail-first on the hipped file: no gap under the
face wall at x 800 and x 945; the centre, where the skirt is above the base,
unchanged. O4′ applies.

## 5. Tier and Patrick's look, batched

AMBER. One report for the branch. His look, once A and the corner are in:
1. The frozen file from the front and both sides: no posts, plain cheeks.
2. The hipped file: both lower corners of the face wall closed.
3. W02 before and after: the wall in front of the dormer face is gone.
