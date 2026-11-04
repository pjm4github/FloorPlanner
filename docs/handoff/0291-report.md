# 0291 — report: PR #101 merged — cross-level dormers (host a floor below, anchor to the host's level)

**Landed:** PR #101 · 7857a7f · 2026-11-04 · AMBER · checked by Patrick in the app on the cross-level dormer render ("that looks good"), merged by fast-forward onto PR #100's foundation

**Code, 2026‑11‑04.** The record ([`0197-ruling.md`](0197-ruling.md) §7).

## 1. WHAT LANDED

`main` fast-forwarded to **`7857a7f`**, one commit on `244d37a` (PR #100's
landing). Phase B of the dormer-windows plan (the single-record, many-views
model worked out with Patrick). PR #100 landed the SAME-level climb — a wall
under a dormer on the dormer's own floor rises into it; this makes the climb
reach a dormer whose host roof is a floor BELOW.

A dormer can now be drawn and edited on the storey its gable occupies while its
host roof sits on the floor below. So a dormer drawn on the upper floor hosts on
the lower roof, and the upper floor's wall (with its window) climbs in and shows,
closing the gable with the SECOND-floor window that belongs in it (his
`w102`/`w142`, `8048`) rather than the first-floor wall 0290 §2 reported.

- **`roofs.py` `host_roof_at`**: tries the drawn floor, then **looks DOWN one
  level** (`_floor_below` by elevation) when there is no host there — Patrick's
  "look down onto the floor below". `_host_roof_on` factored out of it.
- **`view.py`**: a new dormer's `floor` is the **DRAWN** floor (`active_floor()`),
  not the host's. Its `level` is where it is edited; its geometry anchors to the
  host.
- **`fp3d.py` `build_model`**: a dormer is lifted by its **HOST's** level base,
  not its own (`_lift_base` via `host_of`/`level_of`), so re-levelling the drawn
  floor does not move it, and its face openings lift in the same (host) frame.
  The territory keeps the dormer's drawn level, so a same-level wall still climbs
  in.

## 2. TESTS

- `tests/test_r6c_roof_tool_levels.py`: the two level tests updated to the
  look-down model — the dormer tool hosts on the floor below (Shift-build); the
  refusal stays for a roof ABOVE the drawn floor, or none.
- `tests/test_dormer_gable_3d.py`: a cross-level 3D regression — a dormer drawn
  on L2 hosted on an L1 roof renders at the host's geometry and shows the
  floor-below window as a void.

Full gate GREEN (full mode, OFF+ON; 2007 passed, 7 deselected — the perf lane).

## 3. BRANCH CLEANUP

The local `dormer-cross-level` branch was deleted after the fast-forward. The
remote head ref's deletion was refused by the session's auto-mode classifier
("Git Destructive") and is held for an approved retry — the same block that
`dormer-gable-3d` (PR #100's head) hit this session before Patrick approved it.

## 4. NEXT (ruled with him, not built)

Phase C — a dormer's windows shown as a **read-only shadow** on the floor the
dormer is drawn on (that floor's own storey windows stay normal). Then Phase D
(floor-below in-place gable editing that syncs back to the dormer) and Phase E
(cheek walls projected into the floor). His own plan files under
`fixtures/incoming/` stay uncommitted, his to keep.
