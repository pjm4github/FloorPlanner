---
# permanent key, independent of GitHub
id: 47
title: "room_boolean(\"fragment\") builds duplicate wall loops instead of extracting, so a fragment is not a"

# maps directly onto GitHub Issues fields
state: open
state_reason: null
labels:
  - type:task
  - area:geometry
milestone: null

# ours; becomes body prose after migration
opened: 2026-08-05
closed: null
closed_by: null
rank: 47
related: []
state_source: row
github_issue: null
---

# D47 — room_boolean("fragment") builds duplicate wall loops instead of extracting, so a fragment is not a

## Record

> **Moved verbatim** from the register (`docs/CODE_REVIEW_v2.md`, the row at its
> line 112) on 2026-08-06 — not reworded, not split, not
> reformatted. The register wrote each row as one continuous argument in which
> symptom, mechanism, evidence, ruling and receipt are interleaved, so dividing
> it into sections would have meant interpreting it. See
> [`README.md`](README.md) for the section shape new records take.

**`room_boolean("fragment")` builds duplicate wall loops instead of extracting, so a fragment is not a movable unit — and `duplicate_wall`'s death did not touch it.** Ruled 2026‑08‑05 at P4.5, **argued as the FIRST task after P4.5 merges, ahead of grid snap.** `mainwindow.py:982‑996` builds "a COMPLETE wall loop for every region — shared edges get a wall per region (no dedup)", then groups each region's walls; nothing welds them. **P4.5 retired `duplicate_wall`, but this is a SECOND duplication site it never reached, so the phase's retirement of copy-on-group is INCOMPLETE and this row is the statement of by how much.** Measured on the two-overlapping-rooms case (`docs/evidence/defect23-fragment.json`, reproduce with `docs/evidence/defect23_fragment_probe.py`): the product carries **20 distinct `Vertex` objects over 10 geometric points** — four corners hold 3, 4, 4 and 3 duplicates each — and `room_owns_walls` is **False for all nine (group, room) pairs**, so *no fragment group can carry its own room*; the Overlap room's outline names two of its own group's walls and two of its **neighbours'** copies. Consequence at the gesture, measured: dragging the Overlap piece +300/+300 moves **4 of 4 walls and 0 of 16 outline corners** — the room is stranded whole — and `open_edges` goes 0 → {Overlap 2, Room 1 1, Room 2 1} with **all four dashed edges having a real scene wall spanning them**, which is the mini-gate's cross-cutting watch. `check(deep=True)` is CLEAN throughout and the **save succeeds**, writing three rooms in their ORIGINAL positions plus four orphan walls bounding nothing. **The fix is `extract`, not a repair of the loops:** the op's own comment ("so it moves as a self-contained, fully-enclosed unit") describes P4.2's floating room, written before `extract` existed; a floating room is I12 by construction and I11‑exempt, and the app's own gesture message already names the remedy ("undo, or **extract** the room before moving it"). Pinned by `test_fragment_groups_each_piece_with_its_own_walls`, rewritten at P4.5 to assert the ownership property with its preconditions and marked `xfail(strict=False)` against this row.

## Site

`mainwindow.py` (`room_boolean`, the region-walls loop)

## Milestone

**the first task after P4.5**
