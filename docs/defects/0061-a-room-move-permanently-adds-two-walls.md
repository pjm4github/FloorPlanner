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
related: [41, 52]
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
`docs/evidence/coalesce_safety_check.py`

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

*(Open — stage one complete, stage two not started.)* Acceptance for **2b** is
the growth law stated as a test: **a walk of six moves ends with the same wall,
vertex and collinear counts it started with.** It fails today by construction
(0, 2, 4, 6, 8, 10), so it is fail-first without contrivance — and it is the
only test in this repository that would have caught what Patrick has been living
with.
