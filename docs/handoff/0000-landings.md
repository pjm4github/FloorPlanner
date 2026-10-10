# 0000 — landings no report records: every merge before the mailbox, and the green-CI merges after it

**Written once, 2026‑10‑10, from GitHub's own record** (the status-board build,
[`0232-report.md`](0232-report.md) §3 (b), on Patrick's word "build it"): one
`**Landed:**` line per merged PR that no merge report carries — the 36 before
the mailbox existed (0030 is the first report), and the GREEN batches after it
that merged on green CI without a report of their own. The fields are the
PR's number, merge commit, merge date and title-tag tier as GitHub holds them;
where the record does not say what the merge rested on, the fifth field says
so and names the handoff files that mention the PR, when any do. **Not a
report and not a ruling**: `tools/status_index.py` reads it like any other
mailbox file, and nothing else does.

**Landed:** PR #1 · 03f3868 · 2026-07-31 · — · Phase 3 ??? vertices own the geometry (P3.1???P3.8) — not on the record
**Landed:** PR #2 · 0d6db8e · 2026-08-01 · — · P4.1 - Delete-wall keeps the room — not on the record
**Landed:** PR #3 · ec5f207 · 2026-08-01 · — · P4.1b - Defect 25's gesture-time message: the doorway says so at release — not on the record
**Landed:** PR #4 · 6d24969 · 2026-08-03 · — · P4.2 - Extract / join: rooms as durable movable units — not on the record
**Landed:** PR #5 · 4050e44 · 2026-08-03 · — · P4.3 - Shuffle mode: the editing flags go live — not on the record
**Landed:** PR #6 · ae9f0ad · 2026-08-04 · — · P4.4 - Concept rooms, nominal_size, duplicate-as-template — not on the record
**Landed:** PR #7 · d2944d1 · 2026-08-04 · — · Package the 3D viewer: optional extra, console script, and its home under floorplanner/ — not on the record
**Landed:** PR #8 · adaa519 · 2026-08-04 · — · 3D view popup: the same widget the CLI ships, opened read-only — not on the record
**Landed:** PR #9 · b2a7809 · 2026-08-05 · — · Viewer: the furnishing catalog becomes the single source for 3D — not on the record
**Landed:** PR #10 · 4b379fc · 2026-08-06 · — · P4.5 - Group semantics + z-order (mini-gate task; do not merge until the ten-item gate passes) — not on the record
**Landed:** PR #11 · ac93afc · 2026-08-06 · — · Docs refactor - the record leaves the two documents that had absorbed it — not on the record
**Landed:** PR #12 · 5792335 · 2026-08-07 · — · G1 (D43) - the negative-assertion count, and only the count — not on the record
**Landed:** PR #13 · 9ec2115 · 2026-08-07 · — · G3 (D27) - the Windows CI leg — not on the record
**Landed:** PR #14 · 974ef5b · 2026-08-07 · — · G2 (D48) - the scene-level identity check, report-only — not on the record
**Landed:** PR #15 · fe6574b · 2026-08-07 · — · G4 (D42) - the drag-side self-intersection report, the missing caller — not on the record
**Landed:** PR #16 · a1172be · 2026-08-07 · — · Viewer floors measurement, plan-snap, and the batch queued behind the red gate — not on the record
**Landed:** PR #17 · bcffa08 · 2026-08-08 · — · A1 (D47) - a fragment is a floating room, not a group of walls — named in `0002`
**Landed:** PR #18 · eae9b77 · 2026-08-09 · — · A1b (D53) - a room is selected by clicking it: type priority, not z-order — not on the record
**Landed:** PR #19 · c9e85f0 · 2026-08-11 · — · D62's weld_scene repair, D63 producer 1, the area bound, and the fixtures/incoming contract — named in `0005`, `0008`, `READ`
**Landed:** PR #20 · 4a38486 · 2026-08-11 · — · I15 outline completeness -- boundary-gated, with the two rulings it contradicts — named in `0008`
**Landed:** PR #21 · 1385547 · 2026-08-11 · — · I15 at both boundaries, I16 with symmetricP1's re-cut, and D65 — named in `0007`, `0008`
**Landed:** PR #22 · 36e9d09 · 2026-08-11 · — · P6.a: the per-mutation invariant hook gets its own name, off the snapshot path — not on the record
**Landed:** PR #23 · 4e08191 · 2026-08-11 · — · P6.b: the command classes at the settled-gesture boundary, dormant — not on the record
**Landed:** PR #24 · 6002445 · 2026-08-11 · — · D67 filed, and P6.b's commands now carry the active floor — not on the record
**Landed:** PR #25 · 96ddb5e · 2026-08-11 · — · D68: the 3D view renders the active floor, not every level — not on the record
**Landed:** PR #26 · b4d8ea4 · 2026-08-12 · — · Phase 5: settable wall types, railings and gates (D73 first) — named in `0020`
**Landed:** PR #27 · 3864f38 · 2026-08-13 · — · D74: decoration along the run, and the gate gets a symbol and a name — named in `0020`, `0053`
**Landed:** PR #28 · 33043ed · 2026-08-14 · — · prism: the plan symbol, extruded (AMBER ??? your look, not the gate) — not on the record
**Landed:** PR #29 · 6fc9a29 · 2026-08-14 · AMBER · Region extrusion: a pillow rises, a tub is hollow, and a sofa is a sofa (AMBER) — named in `0018`, `0021`
**Landed:** PR #30 · c214619 · 2026-08-15 · GREEN · D72 and D71: import-safe generator, render-and-look renderability check (GREEN) — not on the record
**Landed:** PR #31 · b813343 · 2026-08-16 · AMBER · The vessel/enclosure split, built -- and one thing the render cannot show (AMBER) — named in `0026`, `0027`, `0053`, `READ`
**Landed:** PR #32 · b6ac4d1 · 2026-08-17 · — · The three shower redraws: door/panel marks as beside shapes, not regions — named in `0053`, `READ`
**Landed:** PR #33 · 15bd553 · 2026-08-18 · AMBER · fp2dxf integration: fixtures, README split, menu + golden test (AMBER) — named in `0050`, `0054`, `0204`, `READ`
**Landed:** PR #34 · 536e6b3 · 2026-08-23 · — · Fix the cross-floor snap in _align_to_wall — named in `0064`, `0065`, `0067`, `0068`, `0069`, `0070`, `0071`, `0072`, `0077`, `0081`, `0089`, `0204`, `0205`, `READ`
**Landed:** PR #35 · 3aa6edd · 2026-08-23 · — · Fix two defects in the wall status-bar label — named in `0067`, `0068`, `0069`, `0070`, `0071`, `0072`, `0081`, `0090`, `READ`
**Landed:** PR #36 · ac6d763 · 2026-08-23 · — · Fix D80: T-junction start point now snaps to grid — named in `0071`, `0072`, `0081`, `0088`, `READ`
**Landed:** PR #40 · 4445fa4 · 2026-08-26 · — · Snap to Grid Orthogonal (0110-ruling.md sec2) — named in `0113`, `READ`
**Landed:** PR #41 · d897df3 · 2026-08-26 · — · Snap to Grid, plain (0108-ruling.md) — named in `0113`, `READ`
**Landed:** PR #42 · 8fb3404 · 2026-08-29 · — · Export menu + PDF plan set (0072-ruling.md sec4-5) — named in `0117`
**Landed:** PR #44 · a86d419 · 2026-08-30 · — · Generalize dim_row_x/dim_row_y into dim_row_along (0119-ruling.md sec3) — named in `0125`
**Landed:** PR #46 · bb9309a · 2026-08-31 · — · Grid-aware station filtering, family exclusivity, centerline note (0129/0130-ruling.md) — named in `0135`, `0136`, `0137`, `0138`
**Landed:** PR #48 · 7db6c3a · 2026-09-01 · — · R1: roofs in the v5 document -- model + round-trip + v5-to-6 migration, no UI — not on the record
**Not landed:** PR #59 · — · 2026-09-13 · closed · closed unmerged — R4f: the three-ridge clip -- upper envelope, computed globally; named in `0171`, `0172`, `0173`, `0174`, `0175`, `0178`, `0185`, `0203`
**Landed:** PR #62 · 6812368 · 2026-09-14 · — · 3D wall clip: walls capped at the roof surface in fp3d (Patrick's instruction on R5a's check), AMBER — named in `0188`, `0189`, `0190`
