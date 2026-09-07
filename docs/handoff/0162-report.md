# 0162 — report: R4c — five grips on a selected roof

**Code, 2026‑09‑07, answering [`0154-ruling.md`](0154-ruling.md) §3's R4c row
and [`0160-ruling.md`](0160-ruling.md) §2's named receipt, the tranche after
R4b ([`0161`](0161-report.md), closed).**

---

## 1. WHAT'S BUILT

**A selected roof grows five grips** — two eave edges, two gable ends, the
ridge — `RoofGripItem` in `roofs.py`, a Qt child of its `RoofItem` exactly
as the marker is, each at the midpoint of the line it drags, shown only
while the roof is selected, hit region view-scaled like the marker, empty
shape while roofs are not editable. An end grip sits 18″ *outside* its end
line and below the marker in z: a gable end's line runs through the ridge
endpoint the marker may sit at, and the marker — the End-On dialog's first
door — keeps its click.

**The drag math lives on `RoofItem`**, so every receipt below is measured
without a mouse and the mouse tests only prove the wiring:

* **Eave-edge drag → that side's `span_in`, nothing else.** The outer eave
  line moves to the cursor; the overhang rides along; the other side, the
  ridge and the overhang are untouched; the span stays ≥ 1″. **This is
  [`0160`](0160-ruling.md) §2's receipt** — the grips write the same two
  values the dialog's "Eaves span, left / right" fields show, and a test
  reads the dialog back after a drag to prove there is one convention.
* **Gable-end drag → that ridge endpoint, along the axis.** The end line
  (gable line, or a hip end's outer eave) lands where the cursor projects;
  direction is preserved, so the roof stays the same rectangle, longer or
  shorter; a hip end's extension rides along; the ridge keeps 12″. *A
  decision, named for him:* the endpoint moves along the ridge axis only.
  A free 2-D move would rotate the whole roof from one end, which is a
  different gesture from "move that endpoint"; if he wants it, it is its
  own grip behaviour, not this one loosened.
* **Ridge drag → sideways between fixed eave edges** —
  [`0140`](0140-ruling.md) §4's deferral, due here. Both eaves-start lines
  stay byte-identical (asserted as a before/after list of the four eave
  corners), the two spans rebalance, clamped so neither drops under 1″.

**Every drag LANDS ON the grid, never moves by it** —
[`0070`](0070-ruling.md) §3's class, ruled to be tested, not remembered.
The quantity snapped is the **absolute coordinate of the dragged line**
along the ridge's own axis or normal, from the scene origin: for an
axis-aligned ridge that is literally the line's x or y landing on
`wall_snap_in`; for the 45° wing it is the same rule in the roof's own
frame — a rotated grid of the same pitch anchored at the origin, the only
sense in which a diagonal line can be "on" a square grid. Nothing snaps a
delta. The test that tells the two apart starts OFF grid (span 100.37) and
drags +17.73: a displacement snap would land at 230.37 with the offset
carried forever; the built one lands on a grid line.

**Undo needed nothing new.** The settled gesture is the app's own debounced
snapshot, one step, as for every other drag — pinned: two mid-gesture
moves, one commit, one undo restores the original span, redo restores the
drag.

`items.py`: `RoofGripItem` enters `HIT_PRIORITY` beside the marker (marker
first, matching z). `view.py`: the ridge tool's press guard adds the grip
class, so a grip press while the sticky ridge tool is active is the grip's
own drag, not a second ridge — the marker's own precedent.

## 2. THE CHECK — receipts

`tests/test_roof_grips.py`, **21 tests**: the grips hidden until selected,
at the line midpoints, following a rebuild, no hit shape when not
editable, clear of the marker; the eave drag editing that side only with
the overhang riding along, the right side, the land-not-move receipt, the
ridge-crossing clamp; the end drag along the axis with an off-axis cursor,
the minimum ridge, a hip end's outer eave landing on the cursor; the ridge
drag between byte-identical eave edges, its clamp, and the dialog reading
the rebalanced spans; the 45° wing's eave and end drags on the roof's own
grid with the lines still parallel; one undo step per gesture; and through
the mouse — the ridge grip, an eave grip, and the ridge-tool guard.

Full suite **1226 passed**, 7 deselected (`perf` lane), collected 1233.
`ruff` clean. `python tools/gate.py` (full mode): **GREEN**.

Both roofs rendered offscreen and looked at, selected: five grips each,
the hip end's grip on its outer eave, the 45° wing's grips oriented with
it. (The render is what caught the end-grip/marker collision, fixed before
the commit.)

## 3. DISPOSITION — AMBER, PR open, waiting

**R4c is AMBER** ([`0154`](0154-ruling.md) §3's row): PR up on branch
`roofs-r4c-grips`, not merged until Patrick's own check — *drag all five on
the main roof and the 45° wing.* What to look for: the eave edge lands on a
grid line with the overhang riding along; the end grip lengthens the roof
along its ridge; the ridge slides between eaves that do not move; Ctrl+Z
undoes one drag at a time; and on the 45° wing the same, in the roof's own
frame.

One decision for his eye, above: end grips move along the axis only.

**Then R5** — dormers, RED, its own ruling.

**One hygiene note:** `git stash list` shows one entry from an earlier
session (`WIP on main: 863204a File D85 …`). Not this session's, not
dropped — his call whether it holds anything.

**Carried, unchanged:** D83/D84 (held); room-label rounding
([`0131`](0131-ruling.md) §2); delta-snap sites; D61-family; yard items.
