# 0303 — report: P1–P3 of the 1½-storey arc MERGED into `main` after check session A

**Code, 2026‑11‑05.** The record ([`0197-ruling.md`](0197-ruling.md) §7). The
1½-storey arc ([`0297`](0297-ruling.md), charter; sources [`0293`](0293-ruling.md)–
[`0296`](0296-ruling.md)) built P1→P2→P3 as branches stacked on each other, each
AMBER, the merge of the three held for his **CHECK SESSION A** (0297 §3/§4). He
ran P1+P2+P3 together, found three bugs (fixed below, on the branch), then: *"The
ghosted outline on L1 looks complete now, merge P1–P3."*

## 1. WHAT MERGED

`p3-dormer-level` (which carries P1 + P2 + P3) into `main`, by PR. The phase code
— already reported at [`0299`](0299-report.md) (P1, the stacked climb in 3D),
[`0301`](0301-report.md) (P2, the dash + the knee line) and [`0302`](0302-report.md)
(P3, the dormer's level/datum/dialog and the four views) — is now on `main`. The
arc's remaining phases are **P5** (windows on the dormer face) then **P4** (the
`dormer` wall type); check session B follows them.

**One merge resolution, as ruled:** `floorplanner/dialogs.py` and
`floorplanner/levels.py` both carry PR #104's derived-floor-base work (on `main`)
and P3's work (on the branch). The two sit in different regions of each file and
auto-merged; the result keeps **both** — `FloorLevelsDialog`'s "Sits on the floor
below" + `set_floor_levels`'s cascade (#104) and `RoofEndOnDialog`'s two-column
layout + `move_dormer_to_level` (P3).

## 2. THE THREE CHECK-SESSION-A FIXES (on the branch, in this merge)

1. **A cross-level dormer lost its `host` on save → it popped a storey in 3D.**
   `design/bridge.py` `_roofs_of` names a dormer's host by the id *its own
   level's* walk minted, but a host a storey below sits in another level's
   bucket, never in that per-level `by_item` — so the link was dropped, and
   `build_model._lift_base` then fell back to the dormer's own level base
   (+1 storey). `design_from_scene` now accumulates every roof item's minted id
   ACROSS all levels and re-resolves each dormer's host after the level loop.
   Regression: `test_a_cross_level_dormer_keeps_its_host_through_a_scene_round_trip`.
   (His 3D after the fix: *"looks good"*; he re-saved the fixture.)

2. **The End-On dialog opened taller than the desktop.** Its fields are now two
   `QFormLayout` columns — heights/form/spans/overhang left, ends/hips/"Pinned
   to"/"Edited on level" right — joined in an HBox; the sketch canvas and the
   window list are height-capped and the inputs width-fixed. ~1132×893 (was
   ~1078×1090).

3. **A promoted dormer drew an INCOMPLETE ghosted outline on its host level.**
   `RoofItem.paint` gated the whole dormer branch on `self.is_dormer() and not
   ghost`, so the ghosted copy skipped its cheek/face wall bands and coloured
   eaves — only the ridge/slopes drew. Now `self.is_dormer()`; when ghosted the
   branch paints the full outline in the ghost ink (wall bands as a gray outline,
   eaves gray, the read-only window shadow skipped). Regression:
   `test_a_promoted_dormer_paints_its_full_outline_ghosted_on_the_host_level`
   (spies on `_dormer_eave_lines`, reached only inside the dormer branch).

## 3. GATE

Full mode, GREEN on the branch tip the merge brings in. The 7 deselected are the
perf lane (standing P3.8 flap-class ruling).

## 4. NEXT

**P5** — windows on the dormer face (0294: the plan `DormerWindowItem` second
row + the 3D cut into the climbing wall), its branch on `main`; then **P4** — the
`dormer` wall type (0296). Check session B after P5–P4. The merged branches
`p1-stacked-climb`/`p2-dash-knee`/`p3-dormer-level` are done; their remote refs
await an approved delete (the "Git Destructive" classifier). Named, not ordered:
his backlog (0248's items 8 and 9).
