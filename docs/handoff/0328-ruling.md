# 0328 — ruling: 3D-camera PHASE 2 may be built, on Option A with four conditions — two of 0327's own claims do not hold against the code; and the furnishings lane's next work is declared

**Reviewer (Cowork), 2026-11-14.** Rules on [`0327-report.md`](0327-report.md).
Tier when built: **AMBER**. §0's invariant — the plan `CameraItem` is the one
model and the view is an editor of it — is adopted as written. It is the right
rule and everything below follows from it.

## 1. TWO CLAIMS THAT DO NOT HOLD — corrected before anything is built on them

**(i) §5.1's undo design names a mechanism this repo does not have.** *"Open a
move on capture, push a single `MoveCamera`/command on release."* Undo here is
not a command stack: it is a whole-document snapshot taken by `_settle`, 180 ms
after the last scene change (`mainwindow.py`, `_dirty_timer`). Every write-back
is a scene change. So, as proposed, a walk files an undo step **each time the
walker pauses for 180 ms**, and each one is a full document walk — the cost
0275 measured at 79 ms a frame, which is why `_settle` already defers while
`roof_clips_held` / `rooms_held`. **The mechanism is a HOLD, and it exists:**
add a camera-walk hold that `_settle` honours the same way, taken on capture
and dropped on release. One walk is then one snapshot, by the code path roofs
and rooms already use.

**(ii) §2's round trip is exact as arithmetic and NOT exact through the item.**
`CameraItem.itemChange` snaps every position to the grid (`grid_snap`,
`cameras.py:136`). `qml_pose_to_plan` may invert `plan_to_qml_pose` to the
last bit; `setPos` then moves the answer. The proposal's test (§9, first
bullet) proves the formula and says nothing about the write-back.

## 2. THE ANSWERS TO §8

| | ruling |
|---|---|
| **a. Input path** | **Option A**, subject to condition C1. |
| **b. Undo** | One step per walk, **by a hold in `_settle`** (§1 i) — not a command. A walk that ends where it began costs nothing: `_commit_if_changed` already compares snapshots, so no extra guard. |
| **c. Pitch** | View-local. Persisting it is a schema change and has no ruling: RED. |
| **d. Capture** | Click to capture, Esc to release — subject to condition C3. |
| **e. Keys** | WASD + mouse-look + Q/E yaw, Shift = run. Agreed. |
| **f. Boundaries** | **One thing pulled in:** clamp the written position to `canvas_rect()`. A camera walked off the canvas is a plan item nobody can find. No wall collision in this phase. |

## 3. CONDITIONS

**C1 — measure the controller before trusting it.** §1 of the proposal fixes
the eye height; §3 hands the camera to `WasdController`. Show, by a probe and
not by recollection, what that controller does to the camera's **height** when
the user (a) presses W while pitched up or down, and (b) presses its vertical
keys. If either moves the eye off 65 in, Option A must pin `position.y` every
tick and disable the vertical keys — or fall back to Option B. Report the
measurement in the build report. *(Reviewer's expectation, unverified: it is a
free-fly controller and will climb.)*

**C2 — the write-back must leave QML before it touches the scene.** Phase 1's
merge message records a re-entrant-QML crash (`0xC0000409`) fixed by deferring
the pose push. A QML handler that calls into Python, which moves the
`CameraItem`, which emits a pose back toward QML, is the same shape entered
from the other end. The callback queues; nothing mutates the scene inside a
QML signal's stack. The `_driven_by_view` guard is necessary and is not
sufficient for this.

**C3 — Esc must not close the window.** The Phase 1 window is a `QDialog`, and
a `QDialog` rejects on Esc. While a walk is captured, Esc releases the walk and
is consumed. A test asserts the dialog is still visible after it.

**C4 — the hold can never stall the undo record.** `rooms_held` is let go when
no button is actually down (`_settle`, the 0279 comment). The walk hold needs
its own equivalent: dropped on release, on the window losing focus or closing,
and on a design reload. A test for each.

## 4. THE TESTS §9 MUST ALSO CARRY

- The round trip **through `CameraItem.setPos`**, asserting the error is within
  the snap step — the claim §1 (ii) says is currently unproven.
- One walk of several write-backs with a pause over 180 ms in the middle:
  exactly one undo step, and `_settle` did not snapshot during it.
- After release, the view's camera equals the model's (the view re-syncs to
  the snapped pose; while driving, it was not re-fed).

The pure inverse and its arithmetic test are **GREEN** and may merge on a green
gate ahead of the rest.

## 5. THE FURNISHINGS LANE — DECLARED, SO THE TWO LANES STAY APART

- **Built, un-gated, in the tree now:** side elevations for the remaining eight
  vehicles; `data-half` and `data-plan` in the loft. Files: `_gen_assets.py`,
  `assets/furnishings/` (regenerated), `floorplanner/viewer/fp3d.py`
  (`load_side_profile`, `build_vehicle` only), `tests/test_vehicle_profile.py`,
  `tests/test_viewer_model.py`, `docs/evidence/0325-vehicles/fleet_*.png`.
  Stand-in runner: 84 pass, the one failure is the test that imports PyQt6.
  **Code: gate and commit by path, on its own branch. AMBER.**
- **Planned, not built:** parametric cabinets and a room STYLE —
  `docs/furnishing-spec/CABINETS_AND_ROOM_STYLE_PLAN.md`. It is a plan for
  Patrick's decisions. **It will need `cameras.py` and `dialogs.py` (the wall
  elevation) and the JSON schema** — the first is Phase 2's file. Nothing in it
  starts until Patrick answers it, and the elevation step is sequenced AFTER
  Phase 2 lands, so the two never edit `cameras.py` at once.
- **Left over from 0325, still in the tree:** `assets/icons/*` and
  `docs/gallery/21-cars-suv-3d.png` show as modified. The icons are this
  session's generator run (line endings; content should be identical — verify
  with a diff, then restore or commit). The gallery image is not this
  session's.
- **A record gap, noted:** the merge of the furnishings lane and Patrick's
  AMBER check live only in the merge message and the snapshot — no numbered
  file. The message says "after the double-click fix"; no furnishing code
  changed between the gated branch and the merge. Say in the next report what
  that phrase refers to.

## 6. OWED

- **Code:** build Phase 2 on a branch under §2-§4; gate; AMBER for Patrick's
  walk test. Separately, gate and commit the vehicles (§5).
- **Reviewer:** nothing further on Phase 2 until the build report. No git.
