# 0279 — report: the wall-and-room drag hold, and repaint only what changed — every item audited to paint inside its own box, the screen checked for staleness on eleven kinds of drag

**Code, 2026‑10‑17.** His words after [`0278`](0278-report.md):

> *"go ahead with the wall and room drag hold, repaint only on what
> changed"*

The two items [`0276`](0276-report.md) §5 and [`0275`](0275-report.md) §5
step 4 named. Built on `drag-hold-minimal`, ONE commit on `main`'s tip,
AMBER for his check in the app. Measured on his
`wiscaway2026-10-13R1.json`; the probes and their output beside 0275's in
[`docs/evidence/0275-drag-timing/`](../evidence/0275-drag-timing/).

## 0. THE RESULT

Per-frame median, the same probe (`stale_probe.py`) on `main` and on this
branch:

| Drag | `main` (full repaint) | This branch | |
|---|---|---|---|
| Wall body slide, ground floor | 99 ms | 13 ms | 7.6× |
| Wall end stretch, ground floor | 89 ms | 15 ms | 6× |
| Wall end stretch, upper floor | 48 ms | 10 ms | 5× |
| Furnishing drag | 90 ms | 6–8 ms | 12× |
| Opening slide along its wall | 90 ms | 11–12 ms | 8× |
| Dormer eave grip | 52 ms | 15 ms | 3.5× |
| Wall body slide at 3× zoom | 34 ms | 12 ms | 3× |
| Room drag by its name | 154 ms | 16 ms alone · 80–95 ms in the probe's sequence | |
| Garage back-end knob | 192 ms | 93–104 ms | 2× |
| Main roof ridge grip | 75 ms | 61–72 ms | |

**Stale pixels on screen: none**, on every one of those drags — mid-drag,
at the release, and after the settle (§3).

The room drag's two numbers: on its own it is 16 ms a frame; in the
probe it runs after two other drags on the same floor have already
stretched walls into that room, and costs 80–95 ms there (not traced
further). The ridge grip and the garage knob move roofs whose own
geometry changes every frame, so their traces are recomputed by design;
they gain least.

## 1. THE HOLD

`roofs.hold_rooms(scene, on)`, set by `PlanView.mousePressEvent` on a left
button and released by `mouseReleaseEvent` (in a `finally`). While held, a
roof's clip trace (`RoofItem.clip_trace`) and a wall's roof-clip dashes
(`roof_clip_spans`) take the floor's rooms **as they were at the press**:
the cache is consulted on everything but the rooms. A roof whose **own**
geometry changes still recomputes (a grip drag still shows its roof's
trace live); a wall whose own line changes still recomputes its dashes.
Releasing the hold repaints the scene once, so everything is current the
moment the gesture ends.

The settle walk now also waits for a canvas gesture (0276's step 3
extended, as 0276 §5 proposed): a wall or room drag is one undo step at
its end. **A guard:** if the hold is set but no button is actually down —
a release that went to a modal dialog never reaches the view — the
settle walk lets the hold go instead of waiting for it, so the undo record
can never stall.

## 2. REPAINT ONLY WHAT CHANGED

`PlanView` runs `MinimalViewportUpdate` instead of `FullViewportUpdate`.
That is correct only if **every item paints inside its own
`boundingRect`** — ink outside it is left behind as a trail when the item
moves. So before switching, every visible item of both floors was painted
alone at 1× and 3×, with and without a selection, and the ink outside its
box counted (`bounds_audit.py`). Walls, rooms, openings and texts were
already inside. The offenders, all fixed:

| Item | What spilled | Fix |
|---|---|---|
| Furnishing (every kind) | its item callout under the footprint, up to 34 px out — mine, from 0267 | the box takes the callout in (`annotations.callout_rect`, at the view's scale) |
| Gate | its leaf and swing, up to 40″ out | the box counted a door's swing and not a gate's, though a gate paints the same one |
| Roof | its ridge callout, up to 6 px out on a short roof | the box takes the callout in |
| Ridge grip | its diamond's pen, 1 px | the box covers the diamond plus its pen |
| Measure | its antialiased edges, 2 px | 4 view pixels of pad |

After the fixes, the audit is clean on every floor, zoom and selection
(`bounds-after-R1.txt`; before: `bounds-before-R1.txt`).

**And a third cache, found in the profile:** a clipped roof re-cut its
dashed plan lines against its visible region on every paint, ~4 ms a
roof; `RoofItem._painted_plan_lines` keeps the cut per geometry, region
and join extension.

## 3. IS THE SCREEN EVER STALE?

A box audit cannot see the other way a minimal repaint goes wrong: an
item whose paint depends on **another** item (a wall's dashes on the
roofs, a roof's trace on the rooms) is not repainted when only that
other item reports a change. So `stale_probe.py` emulates the screen:
an image updated **only inside the regions of the viewport's real Paint
events**, compared after every move with a full render of the scene as
it is. Eleven gestures — wall body and end on both floors and at 3×, a
room by its name, a furnishing, an opening, the main roof's ridge grip, a
dormer's eave grip, the garage's back-end knob: **0 stale pixels**
mid-drag, at the release and after the settle. The release's full repaint
(§1) is what closes any cross-item dependency at the end of a gesture.

## 4. RECEIPT

`tests/test_drag_hold.py` (9): a room change under the hold does not
recompute a trace and a roof's own change does; a wall's dashes hold the
rooms and follow their own line; a left press holds and its release lets
go; a hold with no button down never stalls the settle walk; the view is
`MinimalViewportUpdate`; a furnishing's callout, a gate's swing and a
short roof's callout inside their boxes (the three fail on `main`); the
painted plan lines are cached and follow the roof. The drag-speed and
knob suites, the roof, clip-trace, grip and dormer suites green; `--quick`
passed (1651); gate GREEN.

## 5. WHAT HAPPENS NEXT

His check in the app — above all for anything left drawn behind a drag.
Named: DXF export of annotations; his backlog (0248's items 8 and 9).

**Carried:** unchanged from [`0278`](0278-report.md).
