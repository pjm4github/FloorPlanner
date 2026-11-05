# 0292 — report: PR #102 merged — dormer-window editor + read-only plan shadow (Phase C)

**Landed:** PR #102 · e584c29 · 2026-11-04 · AMBER · checked by Patrick in-app (the editor adds a dormer-face window; the dialog shows it) and verified end-to-end headless; landed on his word "Land #102 + fix load bug, then wall-gable windows"

**Code, 2026‑11‑04.** The record ([`0197-ruling.md`](0197-ruling.md) §7).

## 1. WHAT LANDED

`main` fast-forwarded to **`e584c29`**, one commit on `0053c54`. Phase C of the
dormer-windows plan (the single-record, many-views model). The dormer owns its
face windows as ONE record (`RoofItem.openings`); the 3D already read it
(`fp3d._face_openings`). This adds the two missing views.

- **Editor** — a "Dormer face windows" list in `RoofEndOnDialog` (dialogs.py,
  dormers only): Add/Edit/Remove via `_DormerWindowDialog` (a WWHH code, a
  from-end offset, a sill). It validates the code and **mints a schema-valid
  `id`** — the v6 `opening` schema REQUIRES `id`, and the editor is the first
  in-app author of dormer openings (found by the end-to-end check, below).
  `apply()` writes the working copy to `roof.openings`.
- **Plan shadow** — `RoofItem.dormer_face_window_spans()` (roofs.py) projects
  `openings` onto the face wall (`_dormer_wall_lines()[0]`); `paint()` draws a
  read-only blue band on the face. The floor's own storey (wall) windows are
  untouched.

Tests: `tests/test_dormer_window_editor.py` (9) — the dialog seeds from and
writes back the record; add/edit/remove; code validation and id mint/preserve;
the shadow spans (one per valid window, bad/off-face skipped, none without a
host). Verified end-to-end headless: editor → `openings` → `design_document()` →
v6 schema valid → shadow; `paint()` renders the shadow without error (1367 px).
Full gate GREEN (full mode, OFF+ON, 2016 passed).

## 2. WHAT HIS CHECK SURFACED (two things, neither a defect in this PR)

On his wiscaway plan he added a `3040` dormer-face window; the editor and dialog
worked (the window is in the record), but it **did not render in 3D**. Measured:

1. **The dormer-face window renders only for a SET-BACK dormer.** His dormers are
   CROSS-GABLES — the gable is formed by the UPPER-FLOOR WALL climbing into it
   (Phase A, 0290), so `fp3d` generates NO separate dormer face. Adding a face
   window to `rf4` changes the roof mesh by **0 triangles** (measured). For his
   houses a gable-end window must be a WALL window on the floor-above wall (his
   `w102`/`8048`, which DOES render and climbs into the gable). This is his own
   stated interim path, and it is the right one — NEXT, below.

2. **A cross-level load bug** (`design/bridge.py:1516`): a dormer is dropped on
   load unless `host.floor == item.floor`, which contradicts the cross-level
   model PR #101 landed (host a floor BELOW). His current files are same-floor
   (`rf4`/`rf5`/`rf8` on L1, host `rf1` on L1), so nothing is lost today — but a
   dormer re-levelled to the upper floor and saved would silently vanish on
   reload. Latent, real; scheduled below.

## 3. NEXT (his word, in order)

1. **Fix the cross-level load bug** (`bridge.py:1516`) — accept a host a floor
   below, matching `roofs.host_roof_at`; pin with a round-trip test.
2. **Windows in a plain gable end** — let a gable-end window be a WALL window on
   the floor-above wall that climbs into the gable (the Phase D direction), so it
   renders where his houses need it. His own plan files stay his, uncommitted.
