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

## Receipt

**Landed at A1, 2026-08-07.** A fragment is now a **floating room**, not a group
of walls. `room_boolean("fragment")` calls `extract_room` on each piece instead
of wrapping its walls in a `GroupItem`.

The op's own comment — *"so it moves as a self-contained, fully-enclosed unit"* —
already named the right property. It was written before `extract` existed, so it
reached for the only mechanism there was. `extract_room` is the mechanism it
wanted: every edge's wall becomes the room's own, the corners an outside wall
touches are privatised, outline and walls fold onto one vertex per corner, and
the state flips. The piece is self-contained because nothing else references its
geometry — **I12 by construction** — rather than because a group says so.

**Differential, on this record's own two-overlapping-rooms case:**

| | before | after |
|---|---|---|
| `room_owns_walls` | **false for all nine** (group, room) pairs | **true for all three** rooms |
| walls shared between pieces | the defect | **0** for all three pairs |
| drag a piece +300/+300 | **4 of 4 walls, 0 of 16 outline corners** — stranded whole | **4 of 4 corners and 4 of 4 walls** — the region rides |
| `open_edges` after the drag | `{Overlap 2, Room 1 1, Room 2 1}`, each dashed edge with a real wall on it | **`{0, 0, 0}`** |
| groups created | 3 | **0** |
| walls bound to no room | 4 orphans | **0** |
| distinct `Vertex` objects | 20 over 10 points | 18 over 16 points |
| `check(doc, deep=True)` | CLEAN | CLEAN |

**`test_fragment_groups_each_piece_with_its_own_walls` is a hard pass.** Its
`xfail` said "flips when fragment converts to extract"; it has, and the marker
is gone, so the property can regress. It was **the suite's last xfail** — the
census now reads `632 passed` with no xfailed at all.

**One thing the naive change did not fix, and how it was found.** Replacing the
group with `extract_room` alone left **4 orphan walls**: `bind_room_walls` binds
by GEOMETRY, and `fragment` builds one wall per region, so on a shared edge a
room could be bound to a neighbour's coincident copy — which extraction then
correctly copy-trimmed, minting a copy and leaving the original bound to nobody.
`_claim_region_walls` fixes it by narrowing the candidate set: each outline edge
is matched to the wall spanning it **from this region's own list only**.
Geometry still decides which wall covers which edge; the candidate set is what
changed.

**A no-op was written and removed rather than shipped.** A `_weld_region_loop`
pass folded each region's freshly built loop onto one vertex per corner —
measured 12 → 6 on a six-wall loop, so it did what it claimed. It made **no
difference to the final state** (8/7/4 wall-vertices either way), because
`bind_room_walls` re-splits a corner downstream. Code that demonstrably does
nothing is worse than none, so it went; the residual is recorded against D48
instead, where the mechanism actually lives.
