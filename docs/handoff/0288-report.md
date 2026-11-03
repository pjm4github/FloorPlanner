# 0288 — report: PR #98 merged — dormer plan controls, partition/beam wall types, and the wall-gap review tool

**Landed:** PR #98 · 23237a0 · 2026-11-02 · AMBER · his word on the pieces he checked in the app ("The partitioning looks perfect"; "the tool works perfectly" for the marker menu); landed on his order "accept the PR and merge this branch into main"

**Code, 2026‑11‑02.** The record ([`0197-ruling.md`](0197-ruling.md) §7).

## 1. WHAT LANDED

`main` merged **`23237a0`**, one commit `06b0581` on `634d47d`, built and gated across one session.

### Dormer plan controls (A–G, plan + 3D)

* The decoupled dormer model: `wall_span_in` (the cheek walls, control C),
  `overhang_in` (the eaves, control E), `end_overhang_in` (the face rake,
  control F) and `box_half_in` (the frame, control B); per-side grips and
  their drag handlers; the plan draws the walls, the green side eaves, the
  orange face eave and the brown roof lines.
* 3D: the cheek and face walls stand at `wall_span`, and the host roof now
  projects under the dormer's eave overhang all the way to the cheek walls —
  `fp3d._hidden_overhang_pieces` splits the hidden region along the dormer's
  wall box so the strip under the overhang is rebuilt rather than skipped
  with the box.
* The dormer tool rebound **M → H**; the blue marker sits at the apex and
  its right-click menu offers **edit / delete / outline** (the outline a
  violet footprint highlight, toggled per roof).
* Plan: the dormer's three outside walls draw as `EXTERIOR_T`-wide bands —
  his words, "the same size as the actual outside walls on the plan view" —
  not the old thin line.

### Wall types

* `partition` divides rooms in plan but builds **no 3D volume**; `beam` is a
  3D **ceiling beam** (a box hung `BEAM_DROP_IN` below the ceiling) that does
  **not** divide a room. Both draw **dashed** in plan, beam in timber brown
  and partition in grey.
* The schema enum and `STD_T` gain `beam`; `design.bridge.face_at` keeps
  beams out of the room-detection graph; `fp3d` skips partitions and builds
  the beam boxes.

### Review wall gaps

* The dialog is now **non-modal** with **Zoom to problem** (fits the view to
  the gap and boxes it in red), **Close selected gap** and **Rescan** — so a
  gap can be fixed by hand on the canvas and re-detected without closing the
  dialog.

Tests were added and updated across the dormers, the two new wall types, the
gap review and the 3D build.

## 2. A HANG FOUND AND FIXED WHILE GATING

The marker's new right-click menu calls `QMenu.exec()` — a modal event loop.
The pre-existing `test_marker_right_click_opens_the_end_on_dialog` right-clicks
the marker without mocking `QMenu.exec`, so under the gate's full suite (which
runs `gui`/`slow`, unlike `--quick`) it blocked for 38 minutes on an idle event
loop (47 s CPU). The test was updated to mock `QMenu.exec` to the "Roof
parameters…" item — the same pattern the ridge-menu test already uses — since
the marker's right-click now opens a menu rather than the dialog directly.

## 3. FOR THE RECORD

* `docs/SESSION_SNAPSHOT.md`: only the `SNAPSHOT-HEAD` marker and the `main`
  row were advanced for this landing (`ea5a4bc` → `634d47d` on the branch,
  then to `23237a0` here). **The narrative sections are NOT re-cut** for this
  work — they still describe the state through PR #97 and want the reviewer's
  own pass.
* His own plan files under `fixtures/incoming/` (the `wiscaway*`,
  `house_cutout*` and `dormer-test.json` designs he used to test) were left
  uncommitted, his to keep.
