# 0380 — ruling on 0379. The stop is real; its diagnosis is inverted. `climb_dormer` dropped `dormer_over`'s territory test: put it back. And the base-drop runs through a roof that already covers the base.

2026-11-26, reviewer session. Read: your working tree on
`dormer-climb-floor-0372` (A and B's corner, uncommitted) against `2f39c90`,
on scratch copies outside the repo. Mine, not the record: reproduce it.

## 1. What 0379 §2 actually found

- **It is not the face corner.** W01's dormer is `anchored`: `pos` (180, 96) is
  the ANCHOR and the face is at y = 168 (`w6`). (120, 98) is the cheek wall
  2 in from the uphill end.
- **It does not "cap at the host instead".** 149.5 IS the host: `rf1` is at
  154 there, less the slab. 116.5 is the dormer's eave underside. Uphill of the
  valley the main roof is the roof over that wall. Your tree cuts the wall at
  the dormer plane buried inside the host and leaves up to 33 in open above it,
  under the main roof.

## 2. The cause, measured

`dormer_over` at `2f39c90` had one condition: the piece lies in THAT dormer's
territory cells. 0375 §2 added a second: inside the grown box. Your
`climb_dormer` tests the box alone. The fault is in my wording as much as your
reading: I wrote "only where it stands in that box" and did not restate the
condition it was being added to. Both hold.

Wall top along W01's cheek, x = 120:

| y | 98 | 104 | 110 | 116 | 122 | 128 | 134 |
|---|---|---|---|---|---|---|---|
| `2f39c90` | 149.5 | 143.5 | 137.5 | 131.5 | 125.5 | 119.5 | 116.5 |
| your tree | 116.5 | 116.5 | 116.5 | 116.5 | 116.5 | 116.5 | 116.5 |
| your tree + the territory test | 149.5 | 143.5 | 137.5 | 131.5 | 125.5 | 119.5 | 116.5 |

The same fault is on Patrick's frozen file: the BR3 cheek at (799, 640) is
211.2 at `2f39c90`, 201.7 in your tree, 211.2 with the test restored. The six
points of 0375 §1 read the same in your tree with and without the test, which
is why they passed.

O4′ over the 31 evidence cases with walls, against `2f39c90`:

| | cases changed | points raised | points changed inside a grown box | other meshes |
|---|---|---|---|---|
| your tree | 26 | 248 | 3,056 | none |
| + the territory test | 22 | 0 | 0 | none |

## 3. The rule for A

`climb_dormer` returns a dormer only where the piece lies in that dormer's
territory cells AND inside its grown box. Nothing else in your A changes.

## 4. B's corner

**The hipped case does what 0375 §4 asked.** Outer half of the face wall,
lowest wall z: (803, 805.5) 134 → 124.0, (810, 805.5) 134 → 128.7,
(942, 805.5) 134 → 123.7; unchanged where the hip is above the base. The inner
half stays at 134; the outer half closes the corner from outside, so that is
accepted.

**The lean-to case is wrong, and it is the plan he has.** On the frozen file
the outer half of the face wall goes 134 → 112.9 across its whole width,
though `rf4` is drawn over that strip at 139–143. `roof_beneath` takes the
highest roof at or below the base, so it skips the roof that already buries
the base and finds the host strip under it. Rule: where any roof drawn over
the piece is at or above the wall's base, the base is closed and nothing
drops. Say in the report why the hipped centre does not drop the same way.

## 5. Orders

- **O1.** §3 and §4, each fail-first in your own fixture: a cheek wall uphill
  of the valley stands to the host's underside; a face wall whose base is
  inside a lean-to keeps its base.
- **O2.** The point table grows by two so this cannot pass again:
  frozen (799, 640) = 211.2, and W01 (120, 98) = 149.5.
- **O3.** O4′ of 0375 §3 stands, made exact: inside a grown box wall TOPS do
  not change. The one difference allowed inside is B's material added below a
  face or cheek wall's base. Report that as its own class, with counts.
- **O4.** Then the evidence, the gate, the PR, and stop for Patrick's look
  (0375 §5). One report.
