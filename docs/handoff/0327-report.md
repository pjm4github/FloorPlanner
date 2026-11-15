# 0327 — proposal: 3D-camera PHASE 2 — the view becomes a controller (walk the room with WASD + mouse-look, write the move back to the plan camera, two-way). FOR THE REVIEWER TO RULE ON.

**Code, 2026-11-14.** Phase 1 landed on `main` (`0a88c9c`, the `3d-camera-view`
merge): a first-person 3D view BOUND to a plan camera that FOLLOWS the camera as
Patrick moves/turns it on the plan — one-way, plan → view. Patrick's original
ask was two-way: *"Choose whether the camera is the controller or the view is
the controller then make the connection between the 2 … an interactive tool for
moving around a room."* Phase 1 made the camera the controller. **Phase 2 lets
the VIEW drive too**: walk the room in the 3D window and the plan camera moves
to match. This is a PROPOSAL, not built — Patrick asked for it to be ruled on
before I build it. Tier when built: AMBER (user-visible). This document names
the design choices; §8 is the list the ruling should answer.

## 0. THE ONE INVARIANT — THE PLAN CAMERA STAYS THE MODEL

There is ONE source of truth: the `CameraItem` on the plan. The 3D view never
holds state the plan does not. Phase 2 does not add a second camera the two
have to be kept in sync — it makes the view an EDITOR of the one camera. A walk
input changes `CameraItem.setPos(...)` / `setRotation(...)`; Phase 1's existing
feed (`_emit_pose` → deferred `set_camera_pose`) then redraws the view from the
model, closing the loop. So "the view moved" and "the plan camera moved" are the
same event, read twice. This is the rule that keeps a two-way binding from
becoming two cameras drifting apart.

## 1. WHAT WRITES BACK, WHAT STAYS VIEW-LOCAL

| quantity | in a walk | why |
|---|---|---|
| position x, y (plan inches) | **writes back** to `CameraItem.pos()` | the plan camera stores it (`pos`) |
| yaw (heading) | **writes back** to `CameraItem.rotation()` | the plan camera stores it (`rotation`) |
| pitch (look up/down) | **view-local only** | the plan camera has no pitch field (Phase 1 passes `pitch=0` by default); see §8(c) |
| eye height / z | **fixed**, not written | `pose_3d()` derives it as `floor_elevation(floor) + CAMERA_EYE_H_IN` (65 in) |
| level / floor | **unchanged** | walking does not change storey (a future phase, §7) |

So Phase 2 writes exactly the two things the plan camera already owns: a point
and a heading. Nothing new is persisted, no schema change (unless we decide to
persist pitch — §8(c)).

## 2. THE MAPPING IS ALREADY INVERTIBLE — write-back is not new math

Phase 1's `fp3dq.plan_to_qml_pose(px, py, wz, rot_deg, ctr, pitch_deg)` returns
`(ex, ey, ez, yaw, pitch)` with:

```
ex = px - ctr[0]      ey = wz - ctr[2]      ez = py + ctr[1]      yaw = -rot_deg - 90
```

It is a pure rigid remap, so it inverts exactly. Given the QML camera's live
`position` `(ex, ·, ez)` and `eulerRotation.y` `yaw` after a walk:

```
px  = ex + ctr[0]
py  = ez - ctr[1]
rot = -yaw - 90           # normalise to [0, 360)
```

`ctr` (the world-frame recenter) is a constant for the open view (it is baked
when the model is built), so the inverse is a constant-offset formula, not a
re-derivation. **I propose adding `qml_pose_to_plan(ex, ez, yaw, ctr)` beside
`plan_to_qml_pose`, and a round-trip test asserting `plan → qml → plan` is the
identity** — that test is the whole correctness argument for write-back, and it
runs headless.

## 3. INPUT — two implementation options, a recommendation

`scene.qml` already imports `QtQuick3D.Helpers`, which ships **`WasdController`**
(WASD translate + mouse-look, the standard free-fly controller). Phase 1 binds
`fpCamera.position`/`eulerRotation` to the `pose` object. Phase 2 needs the
camera to be MOVED by input — and a value cannot be both bound to `pose` and
driven by a controller. So the two options differ in WHO owns the live camera:

- **Option A (recommended) — QML owns the camera during a walk, Python reads
  back.** Attach a `WasdController { controlledObject: fpCamera; enabled:
  cfg.walk }`. Replace the direct `position:`/`eulerRotation:` BINDINGS with
  initial values set once from `pose` when the view opens (or when a walk ends),
  so the controller is free to move the camera. On `fpCamera.position`/
  `eulerRotation` change, a throttled handler (a `Timer`, ~60 ms, or `onXChanged`
  coalesced) calls back into Python with `(ex, ez, yaw)`; Python inverts (§2)
  and applies to the `CameraItem`. Clean, uses the engine's own controller;
  the cost is the binding rework and a drive-arbitration flag (§5).
- **Option B — Python keeps the `pose` binding, translates keys to pose
  deltas.** The QML `View3D` captures `Keys`/mouse and emits deltas to Python;
  Python advances `(px, py, rot)` by a camera-relative step and sets both the
  `CameraItem` and (via the feed) the `pose`. No binding rework; but it
  re-implements WASD/mouse-look by hand and fights the engine for smoothness.

I recommend **A**. The ruling should confirm or pick B (§8(a)).

## 4. FOCUS & CAPTURE — the non-modal window has to catch the keys

The Phase 1 window is a non-modal `QDialog` hosting the `Plan3DQuickWidget`. For
WASD it must hold keyboard focus, and mouse-look needs pointer capture or it
fights window drag. Proposal: a **"Walk" toggle** in the window (and/or press
`W`-area only when focused) — click the view to CAPTURE (grab cursor, hide it,
mouse-look live), `Esc` to RELEASE (restore cursor, stop writing back). A visible
hint line ("click to walk · Esc to release") in the status text that is already
there. The toggle sets `cfg.walk`; when off, the view is back to Phase 1
(orbit/follow). The ruling should confirm the capture gesture (§8(d)).

## 5. UNDO, DIRTY, AND THE ECHO — the three traps

1. **Undo granularity.** A walk is a drag, not 300 moves. Proposal: coalesce a
   continuous walk into ONE undo step — open a move on capture, push a single
   `MoveCamera`/command on release (`Esc` or toggle-off), like a rubber-band
   drag ends one undo. Do NOT push per frame. (§8(b) — or: a walk is transient
   and only the final pose is undoable; or not undoable at all, view-only until
   release.)
2. **Dirty flag.** The plan becomes dirty once per walk (on release), not per
   frame. A walk that returns to the start (net zero) should ideally not dirty —
   decide in the ruling if that is worth a guard.
3. **The echo / oscillation.** When the VIEW drives, the write-back changes the
   `CameraItem`, whose `itemChange` fires `_emit_pose` → `set_camera_pose` →
   would shove the QML camera that the controller is already holding, causing
   jitter. Phase 1's push is already DEFERRED and COALESCED (singleShot(0)); add
   a **`_driven_by_view` guard** so while a walk owns the camera, the feed back
   to THAT view is suppressed (other bound views of the same camera still
   update). This is the drive-arbitration flag Option A needs.

## 6. SCOPE — what Phase 2 is NOT

No wall collision (you can walk through walls), no gravity, no stair-climbing,
no level change, eye height fixed at 65 in. Those are a later phase (§7). Phase
2 is: capture the view, walk/turn with WASD + mouse, see the plan camera move
live, release, one undo step. That is the "interactive tool for moving around a
room" Patrick asked for, with the plan camera as the recorded result.

## 7. AFTER PHASE 2 (named, not proposed here)

Phase 3 candidates: wall/floor collision so the walk stays in the room; a level
hop when you walk onto a stair (now that parametric stairs exist, 0323);
persisted pitch + a look-target the plan could draw; multiple cameras walked
independently.

## 8. THE RULING — questions for the reviewer

a. **Input path:** Option A (WasdController owns the camera, Python reads back)
   or Option B (pose stays bound, Python integrates key deltas)?
b. **Undo:** one coalesced step per walk (recommended), final-pose-only, or
   not undoable until explicitly saved?
c. **Pitch:** stay view-local (recommended, no schema change), or persist a
   `pitch` on the plan camera (schema + `design/model.Camera` + the plan glyph
   could then show a tilt)?
d. **Capture gesture:** click-to-capture / `Esc`-to-release with a cursor grab
   (recommended), or a plain toggle button with no pointer grab?
e. **Turn keys:** mouse-look + `Q`/`E` yaw + `WASD` translate — confirm the
   binding set, and whether `Shift` = run (bigger step).
f. **Boundaries:** anything in §6 you want pulled INTO Phase 2 (e.g. clamp the
   walk to the current level's floor bbox so you cannot wander to infinity)?

## 9. TEST PLAN (headless, before any Qt)

- `qml_pose_to_plan` round-trips `plan_to_qml_pose` to the identity (the
  correctness proof for write-back).
- a simulated `(ex, ez, yaw)` from a walk maps to the expected `(px, py, rot)`
  and applies to a `CameraItem` (via `scene`), leaving level and eye height
  untouched.
- the `_driven_by_view` guard: while a view drives, `set_camera_pose` is not
  re-fed to that view; a second bound view of the same camera still updates.
- undo: one walk = one undo step; after undo the camera is where it started.

## 10. OWED

- **Code:** this proposal (done). Build Phase 2 after the ruling, on a branch,
  gated, AMBER for Patrick's walk-test. Phase 2 touches `cameras.py`,
  `fp3dq.py`, `scene.qml`, `mainwindow.py` and new tests — **none of the
  furnishing lane's files** (`_gen_assets.py`, `assets/furnishings/`,
  `catalog.py`, the furnishing regions of `fp3d.py`, the furnishing tests), so
  it runs clear of a concurrent furnishings-enhancement lane.
- **Reviewer:** the ruling (next number), answering §8; no git.
