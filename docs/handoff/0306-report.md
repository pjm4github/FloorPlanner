# 0306 — report: P4 of the 1½-storey arc MERGED — the `dormer` wall type, plus three 2026‑11‑08 render fixes

**Code, 2026‑11‑08.** The record ([`0197-ruling.md`](0197-ruling.md) §7). P4 of
the arc ([`0296`](0296-ruling.md); [`0297`](0297-ruling.md) §2, order
P1→P2→P3→P5→**P4**), the final phase. Built on branch `p4-dormer-wall-type`,
cut from `main` (08364cc, the P5 merge, [`0304`](0304-report.md)). **MERGED into
`main`** on his word after his **CHECK SESSION B** ("the 3D view looks perfect
now … merge and push this into main") — a two-parent local merge. P4 itself was
reported FEATURE-COMPLETE at [`0305`](0305-report.md); this report records the
merge and the three render faults he found while checking the branch, each fixed
on it before the merge.

## 1. P4 — THE `dormer` WALL TYPE (0296)

Full detail at [`0305`](0305-report.md). In brief: a dormer mints its face +
two cheeks as real `dormer`-type `WallItem`s on the storey ABOVE its host
(read-only, `bound_to` round-trips), so the L2 attic room CLOSES against them;
the ceiling clamps to the roof underside; a promoted dormer's knee line and wall
dashes read the HOST's datum; a hand-drawn knee wall welded to a cheek follows it
(deform-to-follow); and a dormer buried under its own L2 walls is reachable by
Alt+click cycling and a ridge double-click.

## 2. HIS CHECK-SESSION-B RENDER FAULTS, FIXED ON THE BRANCH

* **The dormer face window was cut "down to the floor"** (`b57366a`). The wall
  below a dormer face window used `to_top=False`, capping at the host roof — but
  a dormer gable can sit ABOVE the host, so the gable was left open from the roof
  up to the sill (a slot). `_wall_under_roofs` gained a `climb_cap`: the
  wall-yield under-sill climbs the gable like the piers but stops at the SILL, so
  the window stays a hole and the wall below it is solid
  (`tests/test_p5_dormer_face_windows.py`).

* **A "leftover roof edge" when switching a dormer's level** (`9c2073f`). A
  roof's floor is a COMPOSE INPUT (`sync_roof_clips`/`compose_building` read
  `floor_elevation(rf.floor)`), so a dormer edited on its host's OWN level
  penetrates the host and gives it a plan seam — drawn solid brown while the host
  floor is active. `move_dormer_to_level` only re-clipped on an ELEVATION change
  (a level move is not one), so the host kept the old level's seam after the
  dormer left. It now `sync_roof_clips` on every dormer level move, so the host
  re-clips and the seam clears (and returns on the way back); the clean-load look
  is unchanged (`tests/test_p4_dormer_wall.py::test_promoting_a_dormer_reclips_the_host_no_stale_seam`).
  His word: editing the dormer ON the host floor keeps the seam active and
  visible, which this preserves.

* **Thin vertical holes in the gable ends at the ends of the L2 walls**
  (`c4317ca`). `_wall_under_roofs` grants a gable wall's climb and BOUNDS it at
  the storey-above base wherever that storey stands over the piece — judged by
  the piece's CENTROID. A header/pier that reached a few inches past the end of
  an L2 gable wall was therefore capped at the L2 base over its whole width, with
  no wall climbing the overhang: a thin hole from the L2 base to the roof at the
  wall's end (his V15/V35 slivers). A gable climb piece is now SPLIT at the
  storey-above footprint edge (the walls of the floor above running ACROSS the
  gable) before the bound is judged, so no piece straddles where that storey ends
  and the overhang climbs the full gable; the clip algorithm is untouched
  (`tests/test_viewer_ceiling.py::test_no_gable_hole_at_the_end_of_an_upper_wall`).

## 3. GATE

Full mode, GREEN at each commit and at the merge. The 7 deselected are the perf
lane (standing P3.8 flap-class ruling).

## 4. NEXT

**The 1½-storey arc is COMPLETE** (P1→P2→P3→P5→P4, all merged). Nothing is open
on a branch. His standing next items, named not ordered: his **#1** (the L2 knee
line, now that the attic room closes) and **#3** (a dimensioned gable-end window
elevation), and 0248's items 8–9 (the porch steps/base and a porch roof turning a
corner). The local `p4-dormer-wall-type` branch is done; the remote
`p5-dormer-face-windows` ref still awaits an approved delete.
