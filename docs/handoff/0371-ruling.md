# 0371 — ruling: 0370 widened to the dormer's EAVE overhang (the cheek-wall posts). Same rule, one fix. AMBER.

2026-11-25, reviewer session. Adds to `0370-ruling.md`; replaces nothing in it.
Untracked, written with the tree on `pyramid-roof-stage3-0367` at `6fc2fe3`.
If 0370 is already in hand, fold this in before you report.

## 1. Patrick's words

2026-11-25, same dormer: *"now fix the cheek walls on that same dormer. They
should be smooth with no 'corner posts'. Determine what causes them and then
tell CODE to implement a fix for them."*

## 2. What was measured (headless, `fp3d.build_model`, same plan as 0370 §2)

All wall material standing above the main roof beside dormer `f129`, other
than the L2 walls drawn under it, is four pieces. Two are 0370's. Two are new:

| Piece | Plan box (in) | z | It is |
|---|---|---|---|
| south cheek | x 785.0–796.9, y 777–783 | 0 → 200.1 | L1 exterior `w88` (the BATH front wall, y = 780) |
| north cheek | x 948.0–959.5, y 795–801 | 0 → 199.9 | L1 exterior `w114` (the garage front wall, y = 798) |

Each is the stretch of an L1 wall that passes under the dormer's 12 in EAVE
overhang, outside the cheek line. The main roof `rf2` is drawn there (a probe
at x 790, y 700 finds both: host 174.4–178.4, dormer 196–200), and the wall
rises through it to the dormer's underside: a fin about 71 in tall on the
south side and 82 in on the north.

Sweep of `f129`'s eave overhang, everything else held:

| Eave overhang | Cheek fins |
|---|---|
| 12 (as delivered) | 12 in wide |
| 6 | 6 in wide |
| 3 or 0 | none outside the wall body (and no eaves) |

No generated cheek piece is involved: with the half-width on the drawn side
walls the generated cheek yields everywhere.

## 3. The rule

0370 §3 stands and already covers this. One clarification: the "cut away
inside its own dormer" exemption reaches only between the dormer's two cheek
lines and behind its face. Outside the cheek lines, under the eave overhang,
the host is drawn and it stops the wall.

## 4. Orders (added to 0370's)

- **O1.** Add to the 0370 fixture an L1 exterior wall that crosses under the
  dormer's eave overhang beside a cheek. Assert no wall-material vertex above
  the host's surface there. RED on `6fc2fe3` first.
- **O2.** Readback on his plan: the two boxes of §2 hold no wall material
  above `rf2`, with the eave overhang at 12.
- **O3.** One report covers 0370 and 0371.

## 5. Recorded, not ordered

- **A second cause, in settings, not in the code.** In Patrick's own saved
  file the same dormer has half-width 96 while his L2 side walls stand 75.25
  from the ridge. The app then builds its own cheek on the eaves line, 20.75 in
  outside each drawn wall, and the L1 fins are 20 in wide. Setting the
  half-width to the walls cures that part. A finding that says "the eaves line
  stands N in outside the side wall drawn under this dormer" would have told
  him; whether to build it is for the pass over his other dormers.
- **Four furnishings left his plan on a save.** `wiscaway2026-11-25.json` as
  saved at 16:14 local has 2 `tall_cab` and 2 `corner_wall_cab` fewer than the
  13:30 copy; every other furnishing is identical apart from this dormer's
  settings. That is consistent with
  an app that did not know the 0368 kinds skipping them on load and saving
  without them. In your report, state which tree the app Patrick runs is
  launched from and whether it loads those four kinds.

## 6. Tier and Patrick's check

AMBER, the same single look as 0370 §6, with one line added: from each side of
the BR3 dormer, the cheek walls are plain from the main roof to the eave, with
no fin at the front corner.
