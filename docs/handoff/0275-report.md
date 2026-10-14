# 0275 — report: why the UI is slow under a drag — measured; one function called from `paint()` is 85% of every frame; a recommendation, nothing changed

**Code, 2026‑10‑13.** His words after [`0274`](0274-report.md):

> *"I need you to do a speed analysis of the UI application. It seems to
> have slowed down tremendously. Slowness is especially apparent when
> there is a drag operation. Is it possible that the event loop can be
> bypassed or shortcutted to handle the drag without a full repaint or a
> full event loop? Do a timing analysis of a complete multifloor plan when
> a roof and dormer are being dragged by the control knobs and see if
> there is some wasteful data scanning that is unnecessary. Create a
> report after doing the analysis and make a code enhancement
> recommendation."*

**An analysis and a recommendation. No application code is changed by
this report.** The probes and their raw output are filed under
[`docs/evidence/0275-drag-timing/`](../evidence/0275-drag-timing/) and
re-run with one command each (§6).

## 0. THE ANSWER, FIRST

* **The drag runs at 3 frames a second** on his two-floor plan
  (`wiscaway2026-10-11R3.json`: 166 walls, 33 rooms, 13 roofs, one
  dormer). Every roof grip, the dormer's grips, and equally a furnishing
  dragged across the floor.
* **The event loop is not where the time goes.** The grip's own handler —
  the mouse move delivered, the roof's geometry updated — takes **0.5 ms**.
  Bypassing the loop would save half a millisecond out of 330.
* **The repaint is, and inside it one function.** `RoofItem.paint` calls
  `roof_clip_trace` — the dashed line where a roof meets the ceiling plane
  — and **recomputes it from scratch on every paint of every roof**: 214
  of the 246 ms a repaint costs. It answers the same question with the
  same inputs thousands of times.
* **Because a frame takes longer than 180 ms, the settle walk fires inside
  the drag** — the debounce timer that is supposed to wait for the gesture
  to end expires between two moves, every move, and adds a document
  snapshot (79 ms) to each frame. A second cost that exists only because
  of the first.
* **Recommendation (§5): cache each roof's clip trace on its own
  geometry.** Measured as a monkeypatch on the same drag: **3.0 → 22
  frames a second**, idle repaint 246 → 45 ms, and the mid-drag settle
  walks stop on their own. Three smaller steps take it to 26–70 fps.
* **A workaround today:** *Roof ▸ Show roof* off. A furnishing drag goes
  from 3 fps to 26 fps with the roofs hidden, measured.

## 1. WHAT WAS MEASURED, AND HOW

The real path, not a model of it: `QMouseEvent`s sent to the view's
viewport and routed by Qt to the `RoofGripItem` (press, thirty to forty
moves out and back, release); after each move the event loop runs until
idle, so the frame includes the repaint the scene asked for and any timer
that came due. The window is a real `MainWindow` at 1600×1000 on the
**windows** platform (the real raster and font engines — 0267's lesson:
offscreen under-draws) with `WA_DontShowOnScreen`, so it paints and is not
shown. Wall-clock medians; a `cProfile` pass for attribution (which
roughly doubles the absolute times and is used only for proportions).

## 2. A FRAME, AS SHIPPED

| Drag (R3, upper floor active) | Frame | Rate | Settle walks fired mid-drag |
|---|---|---|---|
| Main roof, ridge grip | 331 ms | 3.0 fps | 30 of 30 moves |
| Main roof, eave grip | 330 ms | 3.0 fps | 30 of 30 |
| Dormer (shed), eave grip | 330 ms | 3.0 fps | 30 of 30 |
| A furnishing, roofs shown | 337 ms | 3.0 fps | — |
| A furnishing, *Show roof* off | 38 ms | 26 fps | — |

Where the 330 ms goes:

| Stage | Time | |
|---|---|---|
| The grip's handler (`drag_ridge` / `drag_eave`, `rebuild`) | 0.5 ms | the clip compose is already held to the release (R6.b) — this part is right |
| One full-viewport repaint | 246 ms | idle, nothing changing, costs the same |
| The settle walk (`_commit_if_changed` → `snapshot()`) | 79 ms | fires because the frame exceeds the 180 ms debounce |
| At the release: `sync_roof_clips` (compose 13 roofs) | 393 ms | once per gesture; 0260's number, unchanged |

The repaint, by item class (one pass over the visible scene):

| Class | Items | Total | Each |
|---|---|---|---|
| **`RoofItem`** | 8 | **214.3 ms** | 26.8 ms |
| `WallItem` | 50 | 22.6 ms | 0.45 ms |
| `RoomItem` | 10 | 3.0 ms | 0.30 ms |
| `OpeningItem` | 16 | 1.9 ms | 0.12 ms |
| everything else | 17 | 1.0 ms | |

## 3. THE WASTEFUL SCAN, NAMED

`RoofItem.paint` → `_drawn_trace` → **`roof_clip_trace(scene, roof)`**
(`roofs.py:715`), per roof, per paint. Inside it, per call:

1. `_floor_rooms` walks **every item in the scene** to collect the
   floor's rooms and converts each outline to polygons; `_trace_margin_in`
   walks every item again for the thickest wall.
2. For each distinct ceiling height × each trace line, `_cut_params`
   intersects the line with every edge of every room (three offsets and a
   vertex circle each), producing a list of cut points.
3. For each piece between cuts, `_governing_ceiling` asks **every room**
   whether it holds the midpoint; `_TraceRoom.holds` answers with
   `QPainterPath.contains` and then, on a miss, the distance from the
   point to **every edge of the room**.

The profile of one 40-move drag (8 roofs painting): `roof_clip_trace`
780 calls → `_governing_ceiling` 42,660 → `holds` 681,660 →
**`dist_point_segment` 5,899,740 calls**, 32 million `QPointF.x()`/`.y()`
reads. That is 95% of the time under `paint`.

**Every one of those calls had the same inputs as the paint before it.**
The trace depends on the roof's own geometry, its floor's rooms, the
floor's thickest wall, and the roof's join extension. In a drag only the
*dragged* roof's geometry changes; the other twelve are recomputed
identically. With nothing dragged at all — a scroll, a hover, a selection
— all of them are.

**How it came to be.** The trace arrived at R5a (`d3b61d3`, 2026‑09‑13)
with a docstring that argues for computing it in `paint()`: *"rooms change
without the roof hearing about it, and this is a handful of segments
against a handful of outlines, not the junction-clip work CLAUDE.md keeps
out of `paint()`"*. That was true of the fixture it was written against.
It is not a handful on a real plan: 33 rooms, 13 roofs, and roofs of the
other level painting too (8 of the 13 are visible with the upper floor
active).
`CLAUDE.md`'s trap (*"don't move junction-clip work into `paint()` — path
booleans per repaint stalls"*) names walls; this is the same fault in the
roof's paint. The slowdown he feels "tremendously" is this cost growing
with each roof added to his plan since: iteration 11's dormer and the five
porch pieces took it from 7 roofs to 13.

**The second scan, smaller, same shape:** `WallItem.paint` calls
`roof_clip_spans(scene, wall)` (`walls.py:1734`) for its own dashes — per
wall, per paint, each reading the room ceiling at the wall and every roof
on the floor: 22 ms a repaint.

**The view repaints everything.** `PlanView` runs
`FullViewportUpdate` and the scene `NoIndex`: any change anywhere repaints
every visible item. That is what turns one roof's cost into every drag's
cost, and it is why a *furnishing* drag pays for the roofs.

## 4. HIS QUESTION: CAN THE EVENT LOOP BE BYPASSED?

It can, and it would not help: the loop's share of a frame is the 0.5 ms
handler. Qt already coalesces — one paint per pass of the loop however
many moves arrived — and the measurement shows exactly one paint per move.
The frame is slow because the **paint is slow in Python**, and the paint
is slow because it **computes** instead of drawing. The fix is to stop
computing in `paint()`; then the loop that is there is fast enough.

What *is* worth taking from the idea is "without a full repaint": step 4
below (repaint only what changed) is that, and it is worth a further
factor on a small item's drag once the paint itself is cheap — but applied
first it would not have fixed this: the dragged roof's own bounding
rectangle covers most of the plan.

## 5. THE RECOMMENDATION

In order of return. Each line's number is **measured**, as a monkeypatch
applied to the shipped code on the same drag (`drag_experiments.py`),
cumulative.

| Step | Idle repaint | Roof-grip drag | Dormer eave drag |
|---|---|---|---|
| As shipped | 246 ms | 331 ms · 3.0 fps | 330 ms · 3.0 fps |
| **1. Cache each roof's clip trace on its own geometry** | 45 ms | **45 ms · 22 fps** | 46 ms · 22 fps |
| 2. Cache the walls' roof-clip dashes the same way | 28 ms | 44 ms · 23 fps | 46 ms · 22 fps |
| 3. Hold the settle walk while a grip is down | 28 ms | 44 ms · 23 fps | 45 ms · 22 fps |
| 4. `MinimalViewportUpdate` | 28 ms | 38 ms · 26 fps | **14 ms · 71 fps** |

**Step 1 — the fix.** `RoofItem` keeps its trace and a key; `_drawn_trace`
recomputes only when the key changes. The key is what the trace reads:
the roof's ridge, spans, overhangs, heights, form and ends; whether it is
clipped and its join extension; **and a rooms epoch for its floor** — a
counter bumped when a room on that floor changes shape or ceiling height,
or a wall's thickness changes. That last term is the answer to the R5a
docstring's own worry ("rooms change without the roof hearing"): the roof
does not need to hear, it needs a number to compare. Where a
room's outline and ceiling are set is to be read when the work is done;
the settle point is a safe place to bump the counter if the setters prove
scattered. This is `CLAUDE.md`'s rule applied — and it is **not** the memoization
that file warns against: that trap is about the wall path build, measured
cheap; this is a measured 214 ms.

**Step 2** is the same pattern on `roof_clip_spans`, keyed on the wall's
ends and a roofs epoch (bumped by `RoofItem.rebuild` and `apply_clip`).
17 ms a frame.

**Step 3** is a guard, not a speed-up once step 1 is in: the settle timer
must not fire while a mouse button is down on a grip, whatever a frame
costs — otherwise any future slow paint brings the mid-drag snapshot back,
and a snapshot taken mid-gesture is also the wrong undo step. Step 1 makes
it stop firing *by being fast*; step 3 makes it stop firing *by rule*.

**Step 4** needs care and its own check: `FullViewportUpdate` was chosen
for a reason (items whose paint reaches outside their `boundingRect` —
callouts, labels, the dimension arrows — leave trails under a minimal
update). It is the one step here with a visible-regression risk, and the
one to take last and look at.

**Not recommended.** A drag overlay or a cached pixmap of the static
scene: larger, riskier, and unnecessary at 22–70 fps. Rewriting
`roof_clip_trace`'s inside test (a bounding-box reject was tried: no gain
on the one roof still recomputing, 16 ms). Touching the release's 393 ms
compose: it is once per gesture and 0260 already took it from 32 s.

**Shape of the work:** steps 1–3 are one tranche, AMBER (they change what
`paint()` does; the receipts are the existing trace tests staying green, a
new test that a room edit invalidates the trace and a roof drag does not
recompute the others, and this report's probe re-run for the numbers).
Step 4 a second, AMBER, with his eye on it.

## 6. THE EVIDENCE

In [`docs/evidence/0275-drag-timing/`](../evidence/0275-drag-timing/):

| File | What it is |
|---|---|
| `drag_profile.py` → `profile-r3.txt` | The staged timing of five grip drags and the `cProfile` attribution |
| `drag_experiments.py` → `experiments-r3.txt` | The per-class paint cost, the settle and compose costs, and the five cumulative variants of §5 |
| `drag_other.py` → `other-drags-r3.txt` | A furnishing drag with the roof display on and off; idle repaint per floor |

```
python docs/evidence/0275-drag-timing/drag_experiments.py fixtures/incoming/wiscaway2026-10-11R3.json
```

(The plan is his, in `fixtures/incoming/`, uncommitted; any plan with
roofs on two floors reproduces the proportions.)

**Not measured, said so:** the shed dormer's *ridge* grip in the probe's
drag direction is clamped (it repainted on a third of the moves), so its
row is left out of the tables; a real GPU-backed window was not timed —
the raster backend the probe uses is the one the app's `QGraphicsView`
paints with, so the proportions hold.

## 7. WHAT HAPPENS NEXT

His word on the recommendation. Nothing is open on a branch.

**Carried:** unchanged from [`0274`](0274-report.md).
