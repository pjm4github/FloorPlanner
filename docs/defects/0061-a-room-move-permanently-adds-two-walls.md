---
# permanent key, independent of GitHub
id: 61
title: "A room move permanently adds two walls and two collinear vertices, and nothing removes them"

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
rank: 62
related: [41, 52, 62]
state_source: report
github_issue: null
---

# D61 — A room move permanently adds two walls and two collinear vertices

## Symptom

Named by Patrick twice as his biggest problem, and evidenced: on a 3,300+ sq ft
plan the Kitchen's top edge is **a single straight run carrying more than a
dozen vertex handles**. It accumulates in files he is actively working in.

Measured on his own plan as it loads (`fixtures/wiscaway2026-08-08.json`):

    walls 103   rooms 19   vertex objects 101   distinct points 100
    degree-2 vertices 60
    DEGREE-2 COLLINEAR 26        <- what a coalesce would dissolve

**THE SIZE OF THE COMPLAINT IS 69, NOT 26, AND IT IS AN OUTLINE FACT.** Measured
at `a604d40` and re-measured at stage 2a's follow-up. `normalize_walls` — Edit ▸
Coalesce all walls now, on the menu since P3.4 — coalesces the WALL GRAPH and
leaves the outlines exactly as they were: on `wiscaway`, walls 103 → 81 and
wall-graph collinear 26 → 3, while **outline corners stay 159 and the redundant
ones stay 69, before and after**. So the thing Patrick is looking at — "a
straight run carrying more than a dozen handles" — was never what the wall
coalesce touched.

    KITCHEN       9 outline corners, 5 redundant
    Rear Porch   13 outline corners, 9 redundant
    Dining       11 outline corners, 7 redundant

**THREE COUNTS, AND THEY ARE NOT THE SAME COUNT** — they sat one paragraph apart
in `a604d40`'s message with nothing joining them, which is what sent stage 2a's
follow-up to measure all three with one instrument
(`evidence/d61-normalize-outline-arrow.txt`):

| | on `wiscaway` | predicate |
|---|---:|---|
| **the COMPLAINT** | **69** slots | this room's ring runs straight through the corner. No wall test, no agreement between co-holding rooms |
| **what 2a VACATES** | **40** slots | the strict predicate below |
| **what 2a DISSOLVES** | **28** vertices | the same set, counted as objects rather than slots |
| **what 2a LEAVES** | **29** slots | looks redundant to a person; refused because a wall needs the corner or a co-holding room turns at it |

## Mechanism

**The growth law**, measured on a clean plan by driving real label-drags through
the view (`docs/evidence/vertex-accumulation-stage-one.txt`, probe beside it):

| gesture | walls | vtx | deg2 | **collinear** |
|---|---:|---:|---:|---:|
| loaded | 16 | 12 | 5 | 0 |
| move out | 20 | 17 | 12 | 0 |
| move **back** | **16** | **12** | 5 | **0** |
| walk ×6 (each to a NEW spot) | 20→30 | 17→27 | 8→18 | **0, 2, 4, 6, 8, 10** |
| shuffle walk ×3 | 32 | 31 | 22 | 12, then **+0/+0** |

**A move that returns the room whence it came is balanced** — exactly to
baseline. That is why "move a room and move it back" shows nothing, and why this
is invisible to any test that does it. **A move that lands the room somewhere
new costs +2 walls and +2 vertices, permanently**, and both are degree-2
collinear.

**Shuffle is not the producer.** A shuffled room stays floating (P4.3), so join
never runs: the first shuffled move pays the extract cost once and every later
one is +0/+0.

**The call site**, per gesture:

    walls.split_wall_at   extract.py:232, inside join_room
    Vertex.at         x4  walls.py:1184  WallItem.__init__
    Vertex.at         x4  walls.py:1185  WallItem.__init__
    Vertex.at         x4  extract.py:178 _private
    walls.merge_wall  x6  extract.py:254, inside join_room

Twelve corners minted per gesture, ten reabsorbed. **The two that remain are the
splits.** `join_room` splits every plan wall a landing room corner rests on,
which is **correct** — that is how a corner becomes a junction.

**Nothing ever intended to remove them, and that is the finding.**
`join_room`'s docstring says coalescing *"touches only the runs the room's own
walls sit in … never the whole plan"*. `merge_wall` does run and does reabsorb
the room's own privatised walls — but when the room later **leaves** that spot,
the split it caused is in a run the room no longer occupies, so nothing revisits
it. **The split is placed by a join and owned by nobody afterwards.** Not a bug
in `split_wall_at`, not a leak in extract/join as a pair: an **asymmetry** — the
join splits and no gesture un-splits.

## Evidence

`docs/evidence/vertex-accumulation-stage-one.txt` ·
`docs/evidence/vertex_accumulation_probe.py` ·
`docs/evidence/coalesce-safety-check.json` ·
`docs/evidence/coalesce_safety_check.py` ·
`docs/evidence/d61-normalize-outline-arrow.txt` ·
`docs/evidence/d61-normalize-outline-arrow.json` ·
`docs/evidence/d61_normalize_outline_arrow.py` ·
`docs/evidence/d61_divorce_behaviour.py`

### THE SECOND PRODUCER — measured after 2a shipped, on five plans

Ordered before 2b, because a producer 2b does not close changes what 2b is.
**`normalize_walls` DOES raise the redundant-outline-corner count, and by very
little: +2 vertices on two of five plans (`wiscaway` 26 → 28, `rounded`
11 → 13), never down, and 0 on the other three.** The producer inside it is
**`weld_scene`**, on both plans where it moved; `merge_collinear_scene` and
`split_body_landings` change it by 0 everywhere.

**Against the 69 it accounts for NOTHING.** The complaint count is 69 → 69 on
`wiscaway` and unmoved on all five plans. So D61's mechanism story stands:
`join_room`'s split is the producer that matters, and 2b closes it. The wall
pass contributes 2 of 28, which is not a reason to re-scope 2b.

**And the 28-versus-40 reconciliation is closed, measured rather than
explained:** the 28 dissolved vertices are **16 held by one room and 12 held by
two**, so 16 + 24 = **40 slots exactly, residue 0** — the same on all five plans
(`rounded` 6×1 + 7×2 = 20; `symmetricP1` 2×2 = 4; `farmplace` 1×2 = 2;
`planc1.v5` 0). **There is no cascade**: a second dry run after applying reports
0 removable on every plan, so the preview does not under-report and does not
need to iterate.

### THE PRE-IMPLEMENTATION CHECK — and it changes the predicate

Two questions were ordered before any code. Measured on five plans.

**Q2 — can a dissolve produce a vertex pair inside I14's 0.6″ weld distance?
NO.** A dissolve moves nothing, so it cannot bring two vertices closer; zero
candidates on all five plans. Closed.

**Q1 — can a dissolve create or destroy a ring degeneracy? YES — and not in the
way anticipated.**

| plan | collinear | wall-graph spur tips | **outline TURNS at one** | **outline SPUR at one** |
|---|---:|---:|---:|---:|
| `wiscaway` (Patrick's) | 26 | 0 | **3** | 0 |
| `planc1.v5` | 3 | 0 | **4** | **1** |
| `farmplace` | 10 | 0 | 0 | 0 |
| `roundedMultifloor` | 13 | 0 | 0 | 0 |
| `symmetricP1` | 2 | 0 | 0 | 0 |

**A vertex can be degree-2 and collinear in the WALL GRAPH while a room's
OUTLINE turns 90° at it.** The outline's other edge there is an **open edge**
(`wall: null`), which the wall graph cannot see. On Patrick's own plan that is
**3 of the 26** — `Dining/v55`, `GREAT RM/v39`, `HALL/v39`, all with an outline
dot of 0.0.

**Dissolving those and "dropping the vertex from the outline" would change the
outline's SHAPE — and therefore the room's area**, which is precisely the
failure the area receipt exists to catch. The predicate as specified would have
produced it on his file, on the first run, in three rooms.

**And `planc1.v5` carries an outline SPUR at a collinear vertex** (`M Bath`,
outline dot **1.0**): the ring goes out and back along one line. That is D41's
degeneracy sitting exactly on a dissolve candidate.

**So the predicate must be strengthened**, and this is a spec change rather than
an implementation detail:

> a vertex is dissolvable only if it is degree-2 in the wall graph with its two
> walls **opposite-directed** and collinear, **AND every room outline containing
> it is also straight there**

The wall test alone is necessary and not sufficient. **Reported rather than
handled quietly**, as ruled.

**It touches D41's scope**: D41 proposes *"a room outline is a simple ring; no
vertex appears in it twice"*. The outline-spur case above is a ring that is
non-simple by *touching*, which I5b deliberately does not report and which D41
is the proposal for — and a coalesce that dissolved there would silently alter
it. The two are the same subject from opposite ends: D41 detects the degeneracy,
this predicate must refuse to walk into it.

## Ruling

**Stage one is answered. Stage two is authorised in two parts**, and the
predicate above is the correction the check produced.

* **2a** — the scoped primitive, a dry run, and a manual command. **The scoped
  form is the primitive; the whole-plan form is that primitive called with
  everything** — one implementation, two callers, because a global sweep built
  first is one nobody dares run inside a gesture.
* **2b** — wire it to the **leave path**, closing the asymmetry at cause: when a
  room vacates a run, coalesce that run.

**Safety, non-negotiable**: the dry run reports what it would remove, per room,
and changes nothing; the applied form is **one undoable operation**, not a
sequence that can leave a half-cleaned plan.

**The receipt Patrick reads is the room areas** — Kitchen 441, Great Rm 346,
M Bath 144, Hall 72, WIC 60, Safe 41, Sun 159 — unchanged before and after, plus
a second run that is a no-op and a plan total against the toolbar's 3,3XX.

## Receipt

*(Open — stage one and stage **2a** are on `main`; **2b** has not started.)*

**2a shipped at `a604d40`**: `rooms.coalesce_outline_corners(scene, rooms=None,
dry_run=True)` — the scoped form is the primitive — plus
`MainWindow.coalesce_all_now(interactive=…)` and five tests in
`tests/test_rooms.py`. On `wiscaway`: dry run **28 removable, 28 exact / 0 by
angle**; applied, outline corners **159 → 119** and walls **103 → 81**; **no
room's area moves**, total **3870.5 → 3870.5**; a second run is a no-op.

Acceptance for **2b** is
the growth law stated as a test: **a walk of six moves ends with the same wall,
vertex and collinear counts it started with.** It fails today by construction
(0, 2, 4, 6, 8, 10), so it is fail-first without contrivance — and it is the
only test in this repository that would have caught what Patrick has been living
with.
