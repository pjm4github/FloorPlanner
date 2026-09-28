# 0201 — report: PR #68 merged on his word; D67 REPRODUCED (a fourth site, undo complete); the roof paths and the level's elevation, measured on his fixture — measurements only, nothing fixed

**Code, 2026‑09‑27, on [`0197-ruling.md`](0197-ruling.md) §5.** First the
record (0197 §7): Patrick's check of PR #68 passed — his words, *"merge PR
#68"* — and on that word `roofs-r6b-composition` was landed on `main` at
`297587c`, fast-forward, the branch deleted local and remote. R6.b is
closed. His next word: *"proceed with the D67 reproduction and the
roof-elevation measurement."* This report is that, and only that: **no
code under `floorplanner/` is changed by this commit.**

**One more commit to record.** `main` gained `fe783ef` (*"floor and roof
work"*, author PJMoran, not made by this session) while the measurement
was in progress. It committed the four evidence files as they stood at
that moment — the elevation probe **with a syntax error in it** (an
f-string broken across two lines, my slip) and its `.txt` holding the
first run, which lumped six readings into one comparison. Both are
corrected in this commit; the numbers below are from the corrected runs.
`fe783ef` was unpushed when this was written and rides to `origin` with
this commit's push.

## 1. D67 — REPRODUCED

0197 §5: *"One headless run on `roundedMultifloor.json`: drag across
floors, undo, compare floor 1 to pristine. If that undo comes back
partial, D67 says it blocks the cutover and the consequence is
pre-committed."*

Probe [`docs/evidence/d67_crossfloor_probe.py`](../evidence/d67_crossfloor_probe.py),
output [`d67-crossfloor-probe.txt`](../evidence/d67-crossfloor-probe.txt).
Second floor active. Every line below is identical with "show other
floors" on and off (the two sections of the output differ only in the
visibility census).

**His report holds.** Band the second floor, group, drag:

| | floor 1 (`default`) | floor 2 (`second`) |
|---|---|---|
| after the group drag | **MOVED** — 3 vertices, 6 walls, 4 room outlines (`Hall`, `LOUNGE`, two more) | moved |
| after undo, 1 step | **unchanged from pristine** | unchanged from pristine |
| the same group, three arrow nudges | **MOVED** | moved |
| after undo, 1 step | unchanged from pristine | unchanged from pristine |

**D67's three candidate sites, which it marks unmeasured, all measure
clean:**

| route | result |
|---|---|
| rubber band over the whole plan (`select_in_rect`, both halves) | selects `{'second': 46}` |
| select‑all | `{'second': 41}` |
| `SELECT` and a mouse click where only a floor‑1 furnishing lies (`best_by_priority`) | selects nothing |
| a `Vertex` shared across floors | **0** of 96 live vertices is held by walls of two floors; 21 positions carry a floor‑1 and a floor‑2 vertex coincident, as two objects |
| one floor‑2 wall, both ends over floor‑1 vertices, dragged | floor 1 unchanged; undo restores floor 2 |
| the band ungrouped, arrow nudges | nothing moves on either floor — `nudge_selected` moves groups and loose furnishings only, so this is not a reading of D67 either way |

Inactive‑floor items are disabled whether drawn or not (`enabled by floor
{'second': 46}`), and that is what keeps every selection route off them.

**The leak is a fourth site: `RoomItem.interior_walls()`,
`floorplanner/rooms.py`, has no floor predicate.** It returns every
`WallItem` in the scene with both ends inside the room's outline.
`MainWindow.group_selected` (its only caller) adds `room_walls(room) +
room.interior_walls()` for each selected room. On this plan the second
floor's `BR2` stands in plan over two first‑floor partition walls,
(936,792)–(948,792) and (936,876)–(936,792); `interior_walls()` hands them
over, and the group comes out with members `{'default': 2, 'second': 41}`
from a selection that was `{'second': 46}`. The drag moves those two
walls' three vertices by (61, 37) — the drag asked for (60, 36) — and
every floor‑1 wall
and room outline holding one of them follows. `room_walls` returned
nothing of another floor.

So the selection is scoped; **the group is not.** D67's title names
selection, and his words — *"grouping and dragging on the second floor
collects vertices belonging to the first"* — named the step that does it.

**Undo: COMPLETE.** One step, both floors back to pristine, compared on
every vertex, wall, room outline and furnishing of each floor. **The
pre‑committed condition — a PARTIAL undo blocks the Phase 6 cutover — is
not met.** What that was measured on: today's snapshot undo, which
restores the whole document and so cannot restore half of it. A
`GestureCommand` recording affected entities does not run this path and
would need the same gesture measured against it when it exists.

**Limits of the measurement, named.** One plan, the one D67 names; the
other five multifloor plans on disk were not run. The group and its drag
land in one undo step here because the headless run commits once after
both; in the app the 180 ms timer may settle them as two. The output's
`a -> b` lines pair two sorted lists, so they show which values left and
which arrived, not which became which.

**Not fixed — the order was a measurement.** The fix it points at is one
predicate in `interior_walls()` (`it.floor == self.floor`), with the
probe's gesture as its fail‑first test. D67's record carries the
reproduction and, on 0197 §1's instruction, the correction of its
*"ONLY multifloor plan"* line; its state stays open.

## 2. DOES ANY ROOF PATH READ THE LEVEL'S ELEVATION?

0197 §5: *"does any roof path read the level's elevation today? … When
the level base stops being zero, say whether the dialog's seeded heights
— R3b's governing ceiling — are still right, measured on his fixture, not
reasoned about."*

Probe [`docs/evidence/roof_elevation_readers_probe.py`](../evidence/roof_elevation_readers_probe.py),
output [`roof-elevation-readers-probe.txt`](../evidence/roof-elevation-readers-probe.txt),
on `fixtures/wiscaway-2level-stacked-floor.json` (L1 at 0″, L2 at 100″).
Each reading taken as drawn, then again with L2 moved to 0″ and to 250″
through `set_floor_levels`. A reading that moves with the elevation reads
it.

**Two places read it, both R6.b's:** `roofs.sync_roof_clips`
(`floor_elevation(rf.floor)` into `compose_building`) and
`fp3d.build_model`. Nothing else under `floorplanner/` that handles a
roof names an elevation.

| reading, six roofs | L2 at 0″ | L2 at 250″ |
|---|---|---|
| stored eaves / ridge | identical | identical |
| the room‑top binding (`bound_eaves_height`) | identical | identical |
| **the End‑On dialog's seeds — eaves, ridge, pitch, wall‑top line** | **identical** | **identical** |
| the Dormer tool's default eaves and slope | identical | identical |
| the R5a clip trace, length | **changed on 4** | identical |
| the composed region | **changed on 5** | identical |
| walls the R3b dash marks | **upper 1 of 44 → 0 of 44** | identical |

**The seeded heights do not read the elevation, and they are still
right.** They are level‑relative, the wall‑top line they are drawn
against is level‑relative, and the ceilings they are compared to are
level‑relative — one datum throughout, the level's own base, so nothing
in the dialog is wrong by 100″. Where they land in the building, measured
in 3D with each roof built alone:

| roof | stored ridge | elevation + ridge | mesh top |
|---|---|---|---|
| L1 main, L1 wing | 296.0 | 296.0 | 296.00 |
| L2 rf3 | 235.1 | 335.1 | 335.06 |
| L2 rf4 / rf5 / rf6 | 199.4 / 179.0 / 188.6 | 299.4 / 279.0 / 288.6 | 299.43 / 279.00 / 288.55 |

Difference zero on all six. An L2 eaves seeded at its rooms' 96″ ceiling
stands at 196″ in the building.

**The trace and the dash read the elevation at one remove — through the
composed territory.** `_within_territory` cuts the dash to the roof's
region and the trace takes its joined extension from the clip; both are
composition results, and composition has depended on the elevation since
R6.b. With L2 at 0″ the two levels' roofs stand at one datum, L1's main
roof takes 345 589 in² instead of 96 292, the four upper roofs shrink,
and the one dashed upper wall loses its dash. With L2 at 250″ every
reading equals the as‑drawn one: **on this fixture the upper roofs
already stand clear of the lower ones at 100″**, so lifting them further
changes nothing. That is a fact about this drawing, not a rule.

## 3. FOUND WHILE MEASURING — named, none acted on

* **The dialog calls the level's base "the ground line."** Its note
  reads *"Both heights measured from the level's own base (the ground
  line)"* (`dialogs.py`, the label and the canvas comment). True on L1;
  on L2 the base is 100″ up. The numbers are right and the word is not.
  The dialog shows no absolute height anywhere, so rf3's eaves read 25.0
  with nothing to say it stands at 125.
* **The wall‑top line is the governing ceiling only while the eaves are
  bound.** Unbound, it is the default 96″. On both L1 roofs the dialog
  draws the line at 96 while the binding would measure 120 from the
  rooms under them. Independent of the elevation — the same on L1 at 0″.
* **The Dormer tool's default eaves on L2 is 120″** (ceiling 96 + 24),
  level‑relative like everything else: 220″ in the building.
* Carried from [`0200`](0200-report.md) §6, unchanged and still his: the
  crossed‑arm rule reads the plan not the height; the dash and the trace
  compare against same‑level roofs only; L2's storey height is 196″ in
  his file.

## 4. `fixtures/incoming/`, with ages

`README.md` only.

## 5. WHAT HAPPENS NEXT

R6.c — the roof tool across levels — on his word, and its ruling if the
reviewer writes one. **For that ruling:** whether the D67 fix (§1, one
predicate and its test) goes first, since the hazard 0197 §5 names for
the roof tool is this one; and the wording in §3.

No tests added or changed; no code changed. Full suite **1383 passed**,
7 deselected (`perf` lane), `ruff` clean, gate GREEN.

**Carried:** unchanged from [`0200`](0200-report.md).
