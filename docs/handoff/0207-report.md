# 0207 — READ-BACK: grid snap by default (A6) — what snaps today, clause by clause; four decisions before the build

**Code, 2026‑10‑03.** His word, [`0205`](0205-report.md) §1: *"I want to
close out teh snap to grid default (except for off angle walls) so we
can close out that feature,"* and today, *"proceed with the grid-snap
read-back."* [`ROADMAP.md`](../ROADMAP.md) A6 orders this read-back
before any code. **No code is changed by this commit.** Nothing merged
since [`0206`](0206-report.md).

## 0. THE SPEC ITSELF, AND WHAT OF IT IS ON DISK

A6 was *"ruled and fully specified 2026‑08‑14"* — in a conversation.
[`0002-report.md`](0002-report.md) §4 says so in terms: *"Fully specified
by ruling; **no record filed yet**"* and *"Partial measurements exist
only in this session and are NOT on disk — they must be re-taken."* What
the disk holds is five clause names and four acceptance lines
(`ROADMAP.md` A6), plus two phrases from 0002: the intersection join's
two refusals are *"no usable intersection"* (an angular threshold) and
*"intersection too far"* (a distance threshold).

So this read-back reads the clauses **as written**, measures the code
against them, and where a clause's detail was never recorded it says so
and proposes one — §3. Those are his to accept or change; they are not
recollections.

## 1. MEASURED — what each gesture does today

Probe [`docs/evidence/a6_grid_snap_readback_probe.py`](../evidence/a6_grid_snap_readback_probe.py),
output [`a6-grid-snap-readback-probe.txt`](../evidence/a6-grid-snap-readback-probe.txt).
Real mouse events, a fresh window per case, at 0.25× and 2× zoom. The
snap step is 6″ (`wall_snap_in`); "on grid" means both coordinates are
multiples of it.

| gesture | no modifier | Shift | Ctrl |
|---|---|---|---|
| **draw**, from an on-grid start | orthogonal, end **on grid** | free angle, end **on grid** | 15° steps, length in 6″ steps |
| **draw**, from an existing end that is off the grid, (123,203) | end (249,203) — **off grid** | end on grid | **off grid** |
| **drag an end**, on-grid wall | along the axis, **on grid** | on grid, and the wall is now **6″ off its axis over 156″** | 15° steps |
| **drag an end**, off-grid wall (123,203)–(243,203) | (279,203) — **off grid** | on grid, **7″ off axis over 153″** | off grid |
| **slide the body**, on-grid wall | perpendicular, on grid | — | **nothing moves** (the press toggled selection) |
| **slide the body**, off-grid wall | y 203 → 221 — **off grid** | — | nothing moves |

**The mechanism in one sentence: the default snaps the DISTANCE moved,
not the place landed.** `_wall_end_point` and `_axis_target` round the
length from the anchor (`wall_snap_len`); the body slide rounds the
displacement. A wall that is on the grid stays on it; a wall that is off
it stays off by the same amount, forever. This is the fault
[`0070-ruling.md`](0070-ruling.md) §3 named — *land on the grid, never
move by it* — fixed since for the T-junction start and for every roof
drag, and still present in the three wall gestures. **Only Shift lands on
the grid absolutely today, and it is the modifier the spec turns into
"unconstrained."** That is the inversion.

Three more, each measured:

* **Zoom changes where a wall lands.** Drawing (120,240)→(425,243) beside
  an open-ended wall at x=402: the end lands at **x=402 at 0.25×** and
  **x=426 at 2×**. A press 32″ from a wall end starts **on that end at
  0.25×** and **on the grid at 2×**. Both tolerances are divided by the
  view scale (`_align_to_wall`: `max(9, 16/scale)`; `_snap_start`:
  `max(6, 10/scale)`). Defect 13's ruling already moved
  `_project_to_orthogonal` to scene space for exactly this reason; these
  two were not moved with it.
* **A 6″ reveal cannot be drawn.** A wall released 6″ short of another
  wall's end is pulled onto it and welded; 12″ short is left alone. The
  weld radius is `JOIN_TOL` = 9″, larger than one grid step.
* **A shared corner carries both walls** — slide one leg of an L and the
  other's end follows. Already true (P3.3).

**The readout, mid-draw:** the wall paints its own length, and that
length is the snapped one (10′‑6″ for a cursor 127″ out). The status
bar's coordinate label shows the **raw cursor** (x 20′‑7″, y 11′‑1″). No
angle is shown anywhere. The status message is the tool's static help
line.

## 2. THE CLAUSES — EXISTS / PARTIAL / ABSENT

| clause, as written in `ROADMAP.md` A6 | today | evidence |
|---|---|---|
| **Snap by default** | **PARTIAL** — on-grid in, on-grid out; off-grid in, off-grid out | §1's table, rows 2, 4, 6 |
| **Shift means unconstrained, across both gestures** | **ABSENT** — Shift is "free angle, on the grid" in both drawing and end-dragging; nothing leaves the grid on purpose | rows 1, 3 |
| **The angled-wall rule quantises length along the ray** | **EXISTS** under Ctrl (15° steps, length rounded to 6″). **Out of this close-out by his word**; named, not touched | row 1, Ctrl |
| **Intersection joins, with their two refusals** | **PARTIAL** — an end sticks to the line of a nearby wall only when that wall is within 6.9° of perpendicular (`abs(u·v) ≤ 0.12`), within 9″ of the drag (`WALL_PROJECT_STICK`), and passes within 48″ (`WALL_PROJECT_NEAR`). Those are refusals in fact; nothing reports them, and the draw gesture uses a different, zoom-scaled rule | `_project_to_orthogonal`, `_align_to_wall` |
| **The live readout shows snapped values, not cursor position** | **PARTIAL** — length snapped, on the wall; position raw, in the status bar; angle absent | §1, last paragraph |
| *acceptance:* a shared vertex carries both walls | **EXISTS** | probe G |
| *acceptance:* two coincident ends meet on the grid and weld | **EXISTS** | probe F, first line |
| *acceptance:* a 6″ reveal untouched | **ABSENT** — it is welded shut | probe F, second line |
| *acceptance:* identical landing at every zoom | **ABSENT** in drawing | probe E |

## 3. WHAT THE READ-BACK OWES BESIDES THE TABLE

**The thresholds, with their reasons.** The two that exist are the stick
(9″) and the perpendicularity cut (0.12, about 6.9°). The one the
acceptance forces is new: **the weld radius on a drawn or dragged end
must be under one grid step**, or a 6″ reveal is impossible by
construction. Proposed: **3″, half a step** — any release within half a
step of a grid point lands on that point, so two ends aimed at one point
already coincide exactly, and anything further is a different grid point
and was meant. `JOIN_TOL` itself stays 9″ for the explicit passes
(Normalize, Close gap, a pixel-extracted plan), which
`_snap_wall_ends`' own docstring says depend on it.

**The modifier audit for Shift.** Shift acts in four places: drawing a
wall or a roof ridge (free angle, on grid); dragging a wall end, plain or
a room's (the same); the dormer drag (frees the ridge direction);
selection (toggle on a room, D53). Only the first two change.

**The angle convention.** `atan2(dy, dx)` in scene coordinates, y down,
so angles run clockwise on screen from +x; `geometry.heading_deg` reports
the same as a compass heading in [0, 360). Ctrl rounds that angle to
`rotate_snap_deg` (15°). No change proposed.

**Ctrl's disposition.** Ctrl is: 15° steps when drawing or dragging an
end; selection toggle on a wall body, an opening, a room; the fine 1″
arrow nudge; rotation snap on a furnishing; the band-select arm. **One
dead path found:** the body slide has a *"Ctrl: move freely"* branch
that cannot be reached by pressing Ctrl, because a Ctrl press on the body
toggles selection and never starts a drag (probe D: nothing moves).
Proposed: Ctrl keeps every meaning it has; the dead branch is deleted
with the build.

**Does snapping cover an operation's output, or only the cursor?**
([`0056`](0056-report.md)'s clause.) Today, only the cursor — and not
all of that. A weld moves an end onto whatever it lands near, on grid or
off (probe F). **And one gesture manufactures the off-axis walls the
orthogonality census counted:** a Shift end-drag on a square wall leaves
it 6″ off axis over 156″, about 2.2° (§1, row 3). Proposed for this
close-out: cursor gestures only; operations keep their own rules, and the
manual "Snap wall to grid" actions ([`0108`](0108-ruling.md)–[`0110`](0110-ruling.md))
remain the tool for a wall already off the grid.

**Tests that assert today's behaviour** and would be rewritten, not
deleted: `test_walls.py::test_shift_still_free_angles` (Shift lands
(96,42) from a cursor at (95,41) — *"free, grid-only"*);
`test_roof_ridge_tool.py`'s Shift ridge (on-grid cursor points, so it
passes either way); `test_macro.py`'s Shift drag replay. The 9″ weld is
pinned by `test_welding_*` through `weld_wall_ends` directly, which a
narrower radius on the gesture alone would not touch.

## 4. FOUR DECISIONS, HIS — each with what I would build

1. **"Snap by default" means the end LANDS on the grid, not moves by a
   step.** For an axis-aligned wall: drawing and end-dragging round the
   end's coordinate along the axis; the body slide rounds the wall's
   coordinate across it. A wall drawn from an off-grid corner then gets
   an on-grid far end while its near end stays where that corner is —
   the tool does not move an existing corner. **Recommended: yes.** It is
   0070 §3's rule, already how every roof drag behaves.
2. **Shift becomes truly unconstrained — the raw cursor, no grid, any
   angle.** Today's "free angle on the grid" then has no key. With angled
   walls out of this close-out, Ctrl's 15° steps remain the way to draw
   one. **Recommended: yes, as the spec says** — but it is the one change
   a user will feel as a loss, so it is his to confirm.
3. **The weld radius on a gesture drops from 9″ to 3″**, so a 6″ reveal
   survives and coincident ends still weld. **Recommended: yes**; the
   explicit passes keep 9″.
4. **The readout:** the status bar shows the snapped end position, the
   length and the angle of the wall under the cursor while drawing or
   dragging an end. **Recommended: yes**, one line, replacing the raw
   coordinate for the length of the gesture.

Not a decision, because the acceptance already decides it: the two
zoom-scaled tolerances become scene-space constants (9″, the stick), as
defect 13 ruled for their sibling.

**Out, by his word:** the angled-wall rule and every angled wall's
behaviour under these gestures. An angled wall's end-drag keeps rounding
length along its own axis, as now.

## 5. THE BUILD, WHEN HE SAYS

One AMBER tranche, `grid-snap-default`: the three gestures (§4.1), Shift
(§4.2), the gesture weld radius (§4.3), the two tolerances, the readout
(§4.4), the dead Ctrl branch. The ridge tool shares the wall's end rule
and follows it. Fail-first tests from this probe's own cases — an
off-grid wall's end and body landing on the grid, the same landing at
0.25× and 2×, the reveal surviving, Shift leaving the grid. His check:
the four acceptance lines, on a plan of his.

## 6. `fixtures/incoming/`, with ages

`single-floor-90-roof-gable-end-check.json` — his own, 2026‑10‑03, exit
not yet named ([`0205`](0205-report.md) §3). `README.md`.

**Carried:** unchanged from [`0206`](0206-report.md).
