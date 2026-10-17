# 0283 — report: PR #95 merged on his word; undo by difference (option A) built — only what changed is rebuilt, the full reload kept as the fallback

**Landed:** PR #95 · 6ed6049 · 2026-10-17 · AMBER · checked by Patrick: "land #95, then go ahead with option A"

**Code, 2026‑10‑17.**

## 1. PR #95 MERGED

[`0282`](0282-report.md)'s branch (the walk after a restore removed) landed
on `main` at **`6ed6049`**, fast-forward;
[PR #95](https://github.com/pjm4github/FloorPlanner/pull/95) MERGED; the
branch deleted, local and remote.

## 2. OPTION A — on `undo-diff`, ONE commit on `main`'s tip, AMBER

[`0282`](0282-report.md) §3's option A: keep the snapshot undo — its
states are exact — and apply a restore as a **difference**.

* **One build path.** `apply_design_to_scene`'s building blocks were moved
  VERBATIM into helpers (`_build_walls`, `_build_rooms`,
  `_build_furnishings`, `_build_annotations`, `_build_roofs`), which the
  full apply calls in the same order. The partial restore calls the same
  helpers, so the two cannot build an item differently. The refactor alone
  left 184 load, bridge, undo, annotation and dormer tests green.
* **`bridge.apply_design_difference(win, current, target)`** compares the
  document the scene shows with the one being restored **by content, ids
  removed** — every walk renumbers ids — with each reference replaced by
  what it points at (a wall's vertices, a room's outline vertices and
  walls, a dormer's host), and **vertex sharing** compared as well (each
  vertex's coordinates with its reference count), so a welded corner never
  equals two coincident ones. It rebuilds per **level** the coupled web
  (vertices, walls with their openings, rooms; junctions recomputed for
  the rebuilt walls only, which never cross floors), per level the
  furnishings and the annotations, and the roofs as one roofscape.
* **It declines — and the undo reloads in full, as before — whenever it
  cannot be sure:** anything outside those six blocks differs (settings,
  levels, groups, reference images, provenance — so a Show-menu toggle or
  a settings change undoes by reload), a vertex is shared between levels,
  an unused vertex differs, or groups exist alongside a change to the
  walls, rooms or furnishings they name. A failure part-way also reloads;
  with shadow verification on (`FP_VERIFY_DESIGN`) the result is checked
  against the restored state and reloads on any disagreement.

| On his R1 plan (unprofiled) | 0280 | 0282 | Now |
|---|---|---|---|
| Ctrl+Z | 0.34 s | 0.26–0.28 s | **0.17 s** |
| Redo | 0.34 s | 0.26–0.29 s | **0.18 s** |

(3.6 s before 0280.) The restore itself is now ~70 ms profiled; the
largest remaining piece is the walk before the undo that folds in pending
edits (~80 ms), which 0282 showed cannot safely be skipped.

## 3. RECEIPT

`tests/test_undo_diff.py` (36): eight kinds of edit (move and rotate a
furnishing, add an opening, move a corner, change a room's ceiling, add an
annotation, add a roof, delete a wall) on four repository plans — two of
them multi-floor — each undone and redone **by difference**, the scene
equal to the restored state exactly and the full reload never called;
the result equal to the full reload's item for item; a renamed level and
a settings change declined; a welded corner never equal to two unwelded
ones; renumbered ids alone no difference. `--quick` passed (1697); gate
GREEN. `undo-after-0283-R1.txt` beside 0280's probe output (the probe now
lets its setup settle as its own step, so the undo is the drag's alone).

## 4. WHAT HAPPENS NEXT

His check of Ctrl+Z in the app. Named: DXF export of annotations; his
backlog (0248's items 8 and 9).

**Carried:** unchanged from [`0282`](0282-report.md).
