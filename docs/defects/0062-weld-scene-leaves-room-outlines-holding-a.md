---
# permanent key, independent of GitHub
id: 62
title: "weld_scene leaves room outlines holding a Vertex no wall holds, and D48's report cannot see it"

# maps directly onto GitHub Issues fields
state: open
state_reason: null
labels:
  - type:defect
  - area:geometry
milestone: null

# ours; becomes body prose after migration
opened: 2026-08-09
closed: null
closed_by: null
rank: 63
related: [48, 61]
state_source: measurement
github_issue: null
---

# D62 — `weld_scene` divorces a room outline from the walls at its corner

## Symptom

Found while validating an instrument for [D61](0061-a-room-move-permanently-adds-two-walls.md)'s
item 2, not by looking for it.

**Edit ▸ Coalesce all walls now leaves the majority of a plan's outline corners
holding a `Vertex` object that no wall at that coordinate holds any more.**
Measured on five plans, counting only PLACED rooms and scoping by floor:

| plan | divorced corners, as loaded | after `normalize_walls` |
|---|---:|---:|
| `wiscaway2026-08-08` (Patrick's) | **0** | **49** |
| `planc1.v5` | 0 | 56 |
| `farmplaceBIGmultifloor` | 0 | 24 |
| `roundedMultifloor` | 0 | 78 |
| `symmetricP1` | 0 | 57 |

Zero on every plan as loaded; large on every plan afterwards.

**This state should not exist.** The Phase 3 model is that *a corner is one
`Vertex` that the walls and the room outlines both hold*, which is why a wall
move carries the rooms with nothing to recompute (`OutlineEdge`'s own
docstring, `rooms.py:75`).

## Mechanism

Attributed by running each of `normalize_walls`'s three sub-passes alone:

    merge_collinear_scene   divorced +0   (it orphans corners instead: +22)
    weld_scene              divorced +49
    split_body_landings     divorced +0

`weld_scene`'s share step folds coincident wall ends onto one surviving
`Vertex` and **does not rebind the room outlines holding the loser**. Nothing
moves — `moved: 0` on `wiscaway` — so this is purely a rebinding of identity.

Distinguish it from the *other* thing the same pass does, which is not this
defect: `merge_collinear_scene` dissolves a wall junction and the outline goes
on naming a corner where **no wall end lies at all** (`wiscaway` 7 → 29).
That is D61's territory. This record is about the corner where a wall **is**
present and is no longer the same object.

## It is RUNTIME-ONLY — measured, not assumed

**The divorce does not survive a save and reload.** Applied the command, saved,
reloaded, counted: **49 → 0, 56 → 0, 78 → 0, 57 → 0** on the four plans, with
the round trip preserving every room and every area to the cent.

**So the harm window is bounded by the session**, and that lowers this record's
severity. It does not close it: the state is reachable inside a session by an
ordinary gesture (below), and everything a user does between opening a plan and
saving it happens inside that window.

**AND THE PAIRING IS WORTH STATING PLAINLY, because it is the sharpest
instrument boundary in the table so far.** `design_from_scene`'s weld on the way
out is **both** the mechanism that makes this state harmless across a save
**and** the mechanism that makes it invisible to `check(deep=True)`. One
mechanism, two effects, opposite signs — which is exactly why "legal under v5
and unreachable by two separate checks" is not a synonym for harmless.

## The mechanism, exactly: three callers, two of which repair

`share_coincident_ends` has three call sites, and the repair already exists:

| caller | what it does afterwards |
|---|---|
| `close_gap` — `walls.py:1101` | **repairs EVERY room on the floor** via `share_outline_vertices` |
| `join_room` — `extract.py:238` | repairs the **joined room only** (`:239`) |
| **`weld_scene` — `walls.py:556`** | **nothing** |

**And this repository already knew.** `close_gap` carries the reason in a
comment written at the P4.2 mini-gate:

> RESTORE THE P3.5 INVARIANT: … an outline left holding a
> coincident-but-distinct twin is a stranding the NEXT drag turns into a
> diagonal tear (found at the P4.2 mini-gate: close the gaps, drag a wall, and
> M Bath / Hall / Lounge drew dashed diagonals to corners their walls no longer
> held).

That is this defect, named, with its symptom, found by a manual check — so the
**harm is established by precedent in this tree**, not only by the one ambiguous
drag below. What P4.2 fixed at one call site was never applied at the other two.

`share_outline_vertices` is idempotent and is the repair. **Which sites should
call it is still a ruling, not a foregone conclusion** — `weld_scene`'s
docstring is explicit that it declines to do things that are "an edit to a wall
the user did not touch", and a plan-wide outline re-adoption may or may not fall
under that principle.

## Reachable from an ordinary gesture, at a low rate

A six-move label-drag walk on `wiscaway` with shuffle off (`extract → move →
join`, six joins, six welds, **zero welds in the extract phase**):

    step   0   1   2   3   4   5   6
    FULL   0   0   0   2   0   0   0

**Two divorced corners at one step of six, cleared by the next move.** Not every
move, and not persistent — consistent with `join_room` repairing the joined room
and not its neighbours.

## What it is NOT known to do

**The consequence is open, and is deliberately not claimed here.** `WallItem`
gathers the outline edges a corner drag must carry with `by_id.get(id(e.v))`
(`walls.py:1979`) — **by identity** — so a divorced edge is skipped. Read from
the source that is stranding.

**Measured, one sample does not settle it.** A real body drag on a wall at a
divorced corner (`Lounge`, `(456, 768)`) moved the wall, left that corner where
it was, and changed the room's area by nothing. That is consistent with
stranding **and** with the designed step-insertion at `walls.py:1999-2014`,
which exists precisely to leave a jog where a run moves and its neighbour does
not. Separating them needs more than one sample and it has not been done.

So: **the STATE is measured; the harm on THESE plans is not.** The P4.2
precedent above establishes the harm for `close_gap`'s case, which is why this
is filed rather than shelved. `evidence/d61_divorce_behaviour.py` is the probe,
and its arm A is a positive control that had to be fixed twice before its arm B
meant anything.

## The consumers of an outline vertex

By AST: **55 reads of `.outline` and 5 writes**, across 6 files and 20
functions. **Most are indifferent** — `path`, `area_sqft`, `_derive` and
`corners` read the vertex's POSITION, and a divorced vertex is at the right
position. That is why every area in every measurement is unchanged to the cent,
and why nothing shows the user anything until something moves.

**The one that misbehaves is `walls._plan_vertex_moves`** — the drag gather at
`walls.py:1979`, `by_id.get(id(e.v))`, keyed on identity. A divorced edge is not
found, so it stays where it is while its wall moves. Every other consumer either
reads a position or rebuilds the binding from scratch.

## Why nothing caught it

**`scene_identity_report` (D48/G2) reports `extra_vertices` 0 on four of the
five plans after `normalize_walls`** (6 on `planc1`). It is not broken. It
compares **wall ends to wall ends** — its own docstring says so — and an
outline corner holding a vertex no wall holds is outside the question it asks.

*A census inherits the blindness of the predicate that scopes it*, and this is
that rule landing on the newest instrument in the tree rather than an old one.
D48's report answers *"do two wall ends at one point share a vertex?"*
completely and correctly. Nobody has ever asked *"does the room's corner share
the wall's vertex?"*, and the two questions look the same from the outside.

**Would `check(deep=True)` have fired? No** — and the reason is D48's own
finding: `design_from_scene` **welds on the way out**, so the emitted document
has one vertex per point whatever the scene holds. The invariants have never
seen this and structurally cannot. That is a gap, not a limit: the question is
answerable at scene level, and D48 already built the layer to answer it.

## Evidence

`docs/evidence/d61-normalize-outline-arrow.txt` ·
`docs/evidence/d61-normalize-outline-arrow.json` ·
`docs/evidence/d61_normalize_outline_arrow.py` ·
`docs/evidence/d61_divorce_behaviour.py` ·
`docs/evidence/d61-leave-path-and-persistence.txt` ·
`docs/evidence/d61-leave-path-weld.json` · `docs/evidence/d61_leave_path_weld.py` ·
`docs/evidence/d61-divorce-persistence.json` ·
`docs/evidence/d61_divorce_persistence.py`

**Three instrument faults were found by controls before any of the above was
believed**, and they are recorded in the evidence file rather than here: a drag
that pressed a door instead of a wall; a divorce counter blind to a
half-carried corner; and a by-point test with no floor filter and no floating
exemption, which read 62 where the scoped answer is 49.

## Ruling

*(None yet. Reported, not directed.)* The measurements ordered at handoff 0003
are done and they narrow it: the state is **runtime-only**, the repair
(`share_outline_vertices`) **already exists and is already applied at two of the
three sites**, and the harm has a **precedent in this tree** (the P4.2
mini-gate's diagonal tears).

What is still a ruling: whether `weld_scene` should call the repair — its own
docstring declines to make "an edit to a wall the user did not touch", and a
plan-wide outline re-adoption may or may not sit under that principle — and
whether `join_room` should repair the neighbours it currently skips. Widening
`scene_identity_report` to ask the outline question is a separate call.
**Severity, given runtime-only: below D61's 2b, not above it.**
