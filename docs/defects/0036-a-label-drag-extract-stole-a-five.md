---
# permanent key, independent of GitHub
id: 36
title: "A label-drag extract stole a five-room party wall, and the return join stranded it at the drop zone"

# maps directly onto GitHub Issues fields
state: closed
state_reason: completed
labels:
  - type:defect
  - area:geometry
milestone: null

# ours; becomes body prose after migration
opened: 2026-08-03
closed: null
closed_by: null
rank: 37
related: []
state_source: row
github_issue: null
---

# D36 — A label-drag extract stole a five-room party wall, and the return join stranded it at the drop zone

## Record

> **Moved verbatim** from the register (`docs/CODE_REVIEW_v2.md`, the row at its
> line 102) on 2026-08-06 — not reworded, not split, not
> reformatted. The register wrote each row as one continuous argument in which
> symptom, mechanism, evidence, ruling and receipt are interleaved, so dividing
> it into sections would have meant interpreting it. See
> [`README.md`](README.md) for the section shape new records take.

**A label-drag extract stole a five-room party wall, and the return join stranded it at the drop zone.** Reported by Patrick (2026‑08‑03) testing on `fiveRoomTest.json` with his `dragWallFuseStraggler.fpm`; reproduced headless verbatim: after the macro the interior column (three party segments, 420″, serving R1/R2/R3/R4/R5) sits fused as ONE wall at x=862.56 — the drag-out position — bound to four rooms whose outlines are 522″ away, while every room's outline stayed home (`check()` clean throughout: the vacated edges read as open, which is why no invariant fired). **MECHANISM, three links, each measured:** (1) the offset join round-trip leaves the returning room 6″ off *by design* (nothing moves beyond `SHARE_TOL`, finding 5a) and reshapes the neighbouring runs so the column's mid seam is **degree‑2 by vertex identity** — the horizontals now pass through mid-body; (2) a plain **CLICK** on the column runs the release merge (`perp_tol` = the 6″ auto-coalesce snap), absorbs the offset room's wall into the column across that legal seam, and **rebinds the room onto the survivor** (`walls.py` merge rebind, unconditional for absorbed walls' rooms) even though the survivor runs off the room's own edge — **binding-without-naming**: the edge goes honestly OPEN (finding 6a's upgrade-only rebind correctly refuses the 6″-away candidate) while the binding stands; (3) **`extract_room` used two different definitions of "the room's walls"** — step 1 partitions *what to copy-trim* by the OUTLINE, but the float moves the BINDING list (`_translate`'s holders are `room.walls`) — so the bound-but-unnamed wall fell in the gap: never copy-trimmed, never released, stolen bodily by the float; the return join rebound the room from its outline and dropped it off the stray. **FIXED at P4.3(6), in the operation whose contract broke:** `extract_room` step 1b releases every bound wall that no outline edge names — the outline is the one definition (P3.5's doctrine) — so it stays with the plan and its other rooms. **Receipt, fail-first:** the macro pinned verbatim (`test_fuse_straggler_macro_steals_no_wall` — after every line no bound wall is unnamed by all its rooms; at the end the wall count is the baseline's, nothing beyond the plan's extent, every room placed and closed at its loaded area) — red against `b23d685` in a worktree on the defect's own words (*"wall count 15 != baseline 16: a wall was minted or stranded"*), green on the fix; the fixed end state matches the fresh load: 16 walls, areas identical, zero open edges, `check()` clean. **Noted, not fixed here:** the producer state (a room bound to a survivor that spans none of its edges, minted by the release-merge's unconditional rebind) remains constructible; extract is now immune, and if it bites elsewhere the rebind semantics are **P4.5**'s (where binding/group semantics are decided). **CARRY MADE CONDITIONAL (ruled 2026‑08‑03):** the producer is carried to P4.5 **only while the CI watch exists** — `test_extract_join.py::test_the_merge_rebind_producer_is_watched`, whose PRECONDITIONS assert the producer still mints binding-without-naming (red the day merge semantics change → this row must be re-argued before the test is touched) and whose VERDICT asserts extract's step 1b releases the state (red the day the guard regresses → CI catches it, not a field macro). If the watch goes, the carry ruling goes with it. **RE-OPENED BY MEASUREMENT AT P4.5(7), on the conditional carry's own terms — not by the watch going red.** Guard 2 retired `merge_wall`'s group exemption, which made the producer reachable by a path the watch never covered: a **grouped** wall absorbing a room's wall. Measured immediately, before guard 3: `absorbed=True, minted_binding_without_naming=True` — the grouped merge **does** mint the state. **What is unchanged:** extract's step 1b still releases it on that path, and the float still does not steal the wall (both asserted in the new sibling watch `test_a_grouped_wall_merging_is_watched_too`, whose preconditions are asserted rather than branched on, so the day the minting stops the test goes red instead of silently passing). **What has changed, and is Patrick's to rule:** the carry's premise was that the producer is reachable only through the release-merge. It now has a second producer path, opened deliberately by this task. The containment still holds; the surface is wider. Guard 3 (`weld_scene`, snap-only) is **held** pending that ruling. **CARRY RULED VOID AND THE PRODUCER FIXED AT SOURCE, P4.5(9) — and it ended when its premise did, not because anyone changed their mind.** Both legs of the original grant are quoted so the record shows which: *"the producer is carried to P4.5 **only while the CI watch exists**"* rested on **reachability**, which was the stated discriminator and is now **measured false** (a grouped merge mints the state: `absorbed=True, minted=True`); and *don't pre-empt P4.5's semantics* is **moot, because this is P4.5**. **THE FIX:** the release-merge rebind binds a room to the survivor **only when the survivor spans an edge that room's outline names**. Not invented for the occasion — it is the thesis this phase enforced everywhere else (`room_walls()` over `bounding_walls()`; the outline as the single answer to which walls are a room's), and this rebind was the last site holding a different answer. **OPTION 1 (keep carrying, widen the watch) REJECTED, and why is worth keeping:** containment was a fact about `extract` — **a net under the hole, not a closed hole**. Every widening of the producer's surface made the net's coverage a fresh question, and guard 3 could have opened a third path. Closing at source retires the question instead of re-asking it. **RECEIPT, fail-first on BOTH paths:** each watch's preconditions went red on its own words (*"the merge no longer rebinds the absorbed wall's room"*) — which is the state being minted before and not after — and both are now ordinary regression tests asserting it is **not** minted, one per producer path. **The row's whole history, in order: constructible → carried under a falsifiable watch → reachable by measurement → fixed at source.**

## Site

`walls.py` (`apply_merge_plan_to_scene`, the rebind) — fixed; `extract.py` step 1b retained as defence in depth

## Milestone

**P4.3 (done) · CLOSED at P4.5**
