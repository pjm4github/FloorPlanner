---
# permanent key, independent of GitHub
id: 33
title: "Stranding on dirty-baseline files - the stated mechanism is REFUTED, and the finding needs the"

# maps directly onto GitHub Issues fields
state: closed
state_reason: not_planned
labels:
  - type:defect
  - area:groups
milestone: null

# ours; becomes body prose after migration
opened: null
closed: null
closed_by: null
rank: 24
related: [23]
state_source: row
github_issue: null
---

# D33 — Stranding on dirty-baseline files - the stated mechanism is REFUTED, and the finding needs the

## Record

> **Moved verbatim** from the register (`docs/CODE_REVIEW_v2.md`, the row at its
> line 89) on 2026-08-06 — not reworded, not split, not
> reformatted. The register wrote each row as one continuous argument in which
> symptom, mechanism, evidence, ruling and receipt are interleaved, so dividing
> it into sections would have meant interpreting it. See
> [`README.md`](README.md) for the section shape new records take.

**Stranding on dirty-baseline files — the stated mechanism is REFUTED, and the finding needs the reporter's list to proceed.** Hypothesis: rooms whose outline corners are unshared with wall vertices at load (the >0.6″ gap class) are the ones a group move leaves behind. **Measured directly on all three available files — `planc1TestV5.json`, `planc1TestV4.json`, `planc1.json`: ZERO rooms have an unshared outline corner at load, and a whole-plan group move (walls + furnishings, no clipping) strands ZERO rooms.** So the unshared-at-load class is empty on these files and cannot be the cause; the load path shares every corner, whether by v5 document identity or by `share_outline_vertices` on a converted plan. **What DOES strand, deterministically:** a rubber band that CLIPS a room's wall set — 10 rooms on `planc1TestV5.json` at a 92% band, the same 10 on three consecutive runs. That is **defect 23**, already registered, expected until P4.5, and its determinism comes from the band's geometry rather than from the file's baseline. **The proposed fix shape (widen the drag/bake gather to include room outlines) does not apply to it:** under a clipped band the room is not a group member at all — its walls were *duplicated* into the group and `room_owns_walls` is correctly false — so no widening of the member gather reaches it. That is the semantics question reserved at P4.5. **To go further this needs the reporter's gesture and left-behind list**, neither of which is on disk; if that list matches the 10 above, this is defect 23 and closes as a duplicate. **RESOLVED 2026-07-31 — DUPLICATE OF DEFECT 23, confirmed against a live reproduction.** Patrick reproduced it in the app on `planc1TestV5.json` (screenshot: Rear Porch, Great Room, M Bath and Hall left behind as dashed outlines at the original position), **once in many group/ungroup cycles** — and the intermittency is the tell. The app has no Ctrl+A: "select the entire plan" is a **rubber band**, and `select_in_rect` takes only items **wholly inside** it, so a hand-drawn band clips a wall now and then. **Measured by sweeping band coverage on that exact file: at 100% coverage ZERO rooms strand; every band short of it strands precisely the rooms it clipped** — 3 at 99%, 4 at 90%, 8 at 85%, 13 at 80% (top-left anchored), with a different set when the band is anchored bottom-right. The stranded set is a function of the clip, which is why it looked non-deterministic across hand-drawn attempts and is perfectly deterministic given the band. **WORKAROUND, exact:** band the whole plan — start the drag outside the plan's extent on every side. **Also fixed here:** `select_in_rect`'s docstring still promised the wall SYNTHESIS that P0.5 removed ("a fresh copy of that edge is synthesized… so the room comes through as a complete, movable loop"), i.e. the prose described the very mechanism whose absence produces this symptom. Prose and code now agree.

## Site

measured against `examples/planc1Test*.json`; `view.py` (`select_in_rect` docstring)

## Milestone

**closed as duplicate of 23 — the semantics remain P4.5's**
