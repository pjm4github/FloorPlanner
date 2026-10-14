# 0276 — report: 0275's steps 1–3 built — the roof clip trace and the wall dashes out of the per-paint path, the settle walk held through a roof gesture; and a second fault found on the way, the settle walk re-arming itself forever

**Code, 2026‑10‑14.** His word on [`0275`](0275-report.md):

> *"Go ahead with steps 1 to 3"*

Built on `drag-speed`, ONE commit on `main`'s tip, AMBER for his check in
the app. Measured with 0275's own probes on his
`wiscaway2026-10-11R3.json`, before and after, the outputs filed beside
0275's in [`docs/evidence/0275-drag-timing/`](../evidence/0275-drag-timing/).

## 0. THE RESULT

| | Before (0275) | After |
|---|---|---|
| Idle full repaint | 246 ms | 38 ms |
| Main roof, ridge grip | 331 ms · 3.0 fps | 40–50 ms · 20–25 fps |
| Main roof, eave grip | 330 ms · 3.0 fps | 65 ms · 15 fps |
| Dormer, eave grip | 330 ms · 3.0 fps | 44 ms · 23 fps |
| Furnishing drag, roofs shown | 337 ms · 3.0 fps | 39 ms · 26 fps |
| Settle walks fired mid-drag | 30 of 30 moves | 0 |
| The app sitting idle, 2 s | a walk + a full repaint every ~280 ms | nothing |
| `RoofItem` paint, 8 roofs | 214 ms | 7 ms |

The eave grip is the slowest of the three because it changes the dragged
roof's spans, so that one roof's trace (about 25 ms) is recomputed every
frame — correctly; the other twelve are not.

## 1. STEP 1 — THE ROOF CLIP TRACE, COMPUTED ONCE PER CHANGE

`RoofItem.clip_trace()` (`roofs.py`) returns `roof_clip_trace(scene,
self)` from a memo, recomputing only when its key changes. The key is
**exactly what the trace reads**:

* `RoofItem.geometry_key()` — the ridge, spans, overhangs, both heights,
  the form, the ends and their hip runs, the floor;
* whether the roof is clipped, and its join extension;
* `floor_rooms_key(scene, floor)` — every room on the floor as *itself*,
  the **vertex objects** of its outline, its no-outline fallback path
  object, and its ceiling height; and the floor's thickest wall (the
  trace's margin).

Vertex identity stands for position because a vertex is never moved in
place — a moved corner is a new `Vertex` (`relocated_to`) — and the key
holds the objects, so no id can be reused while it lives. This answers
R5a's own worry ("rooms change without the roof hearing about it"): the
roof does not need to hear, it compares. The key costs tens of
microseconds; the trace it guards, tens of milliseconds.

`_drawn_trace` (the trace cut to the visible region) memoizes the cut on
the trace and the region object; `snap_to_trace` (the dormer tool's
placement) reads the same cache.

## 2. STEP 2 — THE WALLS' ROOF-CLIP DASHES, THE SAME WAY

`roof_clip_spans(scene, wall)` keeps its answer on the wall, keyed on the
wall's line and thickness, every roof on the floor (its geometry and its
visible region) and the floor's rooms key.

## 3. STEP 3 — THE SETTLE WALK HELD THROUGH A ROOF GESTURE

The debounce timer's slot is now `MainWindow._settle`: while a roof
gesture holds the clips (`roof_clips_held` — a grip, a ridge or a dormer
drag, the same hold R6.b set up for the compose) it re-arms and returns;
once the gesture releases it commits and updates the totals. A drag is one
undo step at its end, whatever its frames cost.

## 4. A SECOND FAULT, FOUND ON THE WAY — MINE, FROM 0264

Measuring the furnishing drag turned up a cost no drag explained: **with
the app sitting idle, the settle walk ran about every 280 ms, forever,
each time followed by a full repaint.** The cause is the callout work of
[`0264`](0264-report.md): after every walk, `_commit_if_changed` stamped
the document ids and called `scene.update()` so the callouts would show
them. That update emits `scene.changed`, which re-arms the settle timer,
which walks again. On his plan that is a 79 ms walk and a 40–250 ms
repaint, three or four times a second, with nothing happening — part of
"it seems to have slowed down tremendously" that 0275 did not see,
because 0275 measured drags, not stillness.

Fixed: `stamp_document_ids` returns how many items' ids **changed**, and
the walk repaints only then. Measured with a new idle probe
(`drag_idle.py`): before, 7 repaints in 2 idle seconds (each after a walk);
after, none.

## 5. WHAT IS STILL SLOW, MEASURED AND NAMED

**A drag that moves walls or rooms under roofs.** The probe's second
furnishing drag turned out to move room outlines (its press lands on what
carries the room — the cache's own instrumentation showed the outline
corners moving). Every roof over that floor then has a genuinely new key
on every frame and recomputes its trace: about **7 fps** on his upper
floor. That is the cache working — the dashes must follow the walls — and
outside steps 1–3. The way to it is R6.b's own: **hold the traces during a
wall or room drag** (draw the last ones, recompute once at the release),
the same hold the compose already takes, plus extending step 3's settle
hold to that gesture. Named here for his word; not built.

**The release.** Composing the 13 roofs at a grip's release is 393–470 ms,
once per gesture (0260's number).

**The default floor.** Idle repaint with the lower floor active is 85–90 ms
against the upper's 38 — more walls and rooms on screen, the upper floor's
roofs ghosted over it; the same per-paint walls' work, not a trace.

## 6. RECEIPT

`tests/test_drag_speed.py` (8): the cached trace is the computed trace;
paint after paint does not recompute it; another roof's drag leaves a
roof's trace cached and the moved roof's is recomputed; a ceiling change
and a region change reach the cached trace; a moved corner (the real
`relocate_corners`) reaches it; a wall's dashes follow a roof's height and
a room's ceiling; the settle walk waits for a roof gesture and fires after
it; a settle walk with nothing changed does not re-arm its own timer
(fails on the shipped code). The existing roof, clip-trace, dormer and
undo suites unchanged and green. `--quick` passed (1636); gate GREEN.

Filed beside 0275's: `drag_after.py` → `after-0276-r3.txt`,
`other-drags-after-0276-r3.txt`, `drag_idle.py` →
`idle-before-0276-r3.txt` / `idle-after-0276-r3.txt`.

## 7. WHAT HAPPENS NEXT

His check of the drags in the app. Then, on his word, §5's wall-and-room
drag hold, and 0275's step 4 (`MinimalViewportUpdate`, with his eye on
it).

**Carried:** unchanged from [`0275`](0275-report.md).
