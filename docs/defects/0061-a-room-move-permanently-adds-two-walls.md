---
# permanent key, independent of GitHub
id: 61
title: "A room move permanently adds two walls and two collinear vertices, and nothing removes them"

# maps directly onto GitHub Issues fields
state: open
state_reason: null
labels:
  - type:limit
  - area:geometry

milestone: null

# ours; becomes body prose after migration
opened: 2026-08-09
closed: null
closed_by: null
rank: 62
related: [66, 41, 52, 62]
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
`docs/evidence/d61_divorce_behaviour.py` ·
`docs/evidence/d61-leave-path-and-persistence.txt` ·
`docs/evidence/d61-what-2a-leaves.json` · `docs/evidence/d61_what_2a_leaves.py` ·
`docs/evidence/d61-leave-path-weld.json` · `docs/evidence/d61_leave_path_weld.py`

**AND A FACT ABOUT THE FIXTURE THAT CHANGES WHAT IT MEASURES:**
`fixtures/wiscaway2026-08-08.json` carries `settings.editing.shuffle: true`. As
it loads, a label-drag leaves the room **floating** and `join_room` never runs
(P4.3), so D61's producer does not fire on Patrick's own file under an ordinary
drag until he leaves shuffle or joins explicitly. Every gesture measurement here
states which shuffle state it used.

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

### 2a's FIX DOES NOT FULLY SURVIVE A SAVE — and that is the headline for the user

Measured on the same round trip that cleared D62. A pure open/save/reopen cycle
with **no command at all is stable** (159, 159, 159, 159 on `wiscaway`), so
saving is not a producer. But a coalesce partially rebounds across one save,
and then settles:

| plan | as loaded | after the command | after save + reopen | **durable** | rebound |
|---|---:|---:|---:|---:|---:|
| **`wiscaway`** | 159 | 119 | **126** | **33 of 40** | 7 |
| `roundedMultifloor` | 187 | 167 | **186** | **1 of 20** | 19 |
| `symmetricP1` | 140 | 136 | 136 | 4 of 4 | 0 |

`119 → 126 → 126 → 126`: a **one-time** partial undo, not compounding. **On
Patrick's plan 2a's durable benefit is 33 corners of the 69, not 40** — and on
`roundedMultifloor` it is 1 of 20, near-total loss. Nothing on disk said so
before, and the cause of the variation is not yet measured.

### THE PAIR IS ALREADY A FIXPOINT — one round is enough

The anticipated unlock — a wall coalesce removing a wall, freeing a corner a
wall needed — **does not occur**. Running `normalize_walls` + the outline pass,
then running the **pair** again, dissolves **0** more on all three plans; a third
round is also 0. So `Edit ▸ Coalesce all walls now` does not need to iterate.

### WHAT 2a LEAVES: 28 OF THE 29 ARE A NEIGHBOUR'S CORNER

Per room on `wiscaway`, after the wall pass. The classification was **checked
against production** — it reproduces production's removable count exactly
(40/40 here, 20/20 and 4/4 on the other two plans), so the reasons partition the
refused set rather than approximating it.

| room | corners | complaint | removed | left | a wall needs it | a co-holder turns |
|---|---:|---:|---:|---:|---:|---:|
| Rear Porch | 13 | 9 | 3 | 6 | 0 | 6 |
| Dining | 11 | 7 | 3 | 4 | 1 | 3 |
| MBR | 10 | 6 | 3 | 3 | 0 | 3 |
| Lounge | 10 | 6 | 3 | 3 | 0 | 3 |
| Foyer | 10 | 6 | 5 | 1 | 0 | 1 |
| GREAT RM | 9 | 5 | 1 | 4 | 0 | 4 |
| KITCHEN | 9 | 5 | 3 | 2 | 0 | 2 |
| BKF NOOK | 8 | 4 | 3 | 1 | 0 | 1 |
| SAFE | 8 | 4 | 3 | 1 | 0 | 1 |
| HALL | 8 | 4 | 1 | 3 | 0 | 3 |
| MUD | 7 | 3 | 3 | 0 | 0 | 0 |
| Util · WIC | 6 · 6 | 2 · 2 | 2 · 2 | 0 | 0 | 0 |
| CLST · PWDR · Pan | 5 each | 1 each | 1 each | 0 | 0 | 0 |
| Front Porch · PKT Off | 13 · 7 | 1 · 1 | 1 · 1 | 0 | 0 | 0 |
| M Bath | 9 | 1 | 0 | 1 | 0 | 1 |
| **TOTAL** | **159** | **69** | **40** | **29** | **1** | **28** |

**28 of the 29 are one reason: this room's ring runs straight through the
corner and another room sharing it TURNS there.** Dissolving it would move the
neighbour's area — the failure the area receipt exists to catch. Exactly **one**
corner in the whole plan is held by a wall that needs it.

**So the honest reading is that the 29 are REAL corners, not redundant ones**,
and it is checkable per room: KITCHEN shows 5 straight-through corners, 3 go, 2
stay because a neighbour turns at them.

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

## ACCEPTED LIMITATION WITH A DOCUMENTED MITIGATION — Patrick, 2026‑08‑11

**This is no longer an open defect awaiting a fix.** Reclassified `type:limit` on
D44's precedent, on Patrick's acceptance, in his terms:

> **`Edit ▸ Coalesce all walls now` is effective in his testing, and the
> accumulation is OBVIOUS IN THE SCENE rather than hidden.**

**That second clause is what makes deferring it safe, and it is the whole
reason** — the fault is **self-announcing and user-correctable**. A person
looking at a straight run sees the handles; the mitigation is one menu command
away; and 2a's dry run reports what it will remove before it removes anything.
A hidden accumulation with a working workaround would not qualify.

### WHAT REOPENS IT

An accepted limit needs its expiry written down, or it quietly becomes a
permanent one nobody re-examines. **This returns to `type:defect` and open if
either holds:**

1. **The accumulation stops being visible** — if any future change makes the
   redundant corners invisible in the scene, the self-announcing property is
   gone and with it the reason for accepting.
2. **The mitigation stops being sufficient on a larger plan** — if
   `Edit ▸ Coalesce all walls now` no longer clears it, or clears too little of
   it to matter, on a plan bigger than the ones measured here.

### WHAT SIX PASSES PRODUCED

Stated so the next reader sees the real ledger rather than nothing:

* **one real finding** — [D66](0066-a-departing-room-carries-its-neighbours-walls.md),
  a departing room **carrying its neighbours' walls**, because `extract` does not
  sever the binding `join` welded. Found while hunting this, real, and recorded.
* **one honest non-closure** — the producer of the **corner** accumulation is
  still **unknown**, and D66 does not explain it: a neighbour wall carried 24″ is
  not a degree-2 collinear vertex on a straight run.

---

## 2b CLOSES — NOT AS FIXED, AS **NOT ISOLATED** (ruled 2026‑08‑11)

**Stated plainly, because the implied close would be a lie.**

* Patrick's original complaint is real and measured: **26 degree-2 collinear
  vertices and 69 redundant outline corners** on one plan.
* **2a removes 40 of them and remains the mitigation he has** — `Edit ▸ Coalesce
  all walls now`, with the area bound and the refusal counts.
* **2b was to stop the recurrence. Six measurement passes have not isolated the
  producer of the CORNER accumulation.**

**What the passes found instead is a DIFFERENT defect** —
[D66](0066-a-departing-room-carries-its-neighbours-walls.md), a departing room
carrying its neighbours' walls, because `extract` does not sever the binding
`join` welded. **That is real, is recorded, and does not explain redundant
collinear corners.** A neighbour wall carried 24″ is not a degree-2 collinear
vertex on a straight run.

**So the producer of the corner accumulation is UNKNOWN**, and this record says
so rather than implying a fix. The stashed 2b implementation was **deleted**: it
targeted the *coalesce the vacated run* shape, and the three-state baseline
disproved that shape — an unverified change aimed at a refuted premise gets
deleted, the same rule as a green that was never red.

**The growth law itself is not in doubt and its SHAPE is now named.** Measured
on one fixture, driven by `_translate` (a floating room's walls do not move with
`setPos`, which never reaches the producer at all):

| walk | walls | collinear |
|---|---|---|
| **a NEW spot each move** | 4, 6, 6, 6, 7, 10 | −1, 1, **4, 5, 5, 8** — accumulates |
| oscillating ±6″ | 4, 0, 2, 0, 2, 0 | −1, −1, −3, −1, −3, −1 — **self-heals** |

**A return trip self-heals; only a walk that keeps landing somewhere new
accumulates.** Any future acceptance for this must name both its driver and its
walk, per the sibling rule in `WORKING_AGREEMENT.md`.

---

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
