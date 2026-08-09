# 0003 — report: D61's three owed items, measured

**Ordered by the 0002 exchange: item 2 first, then 1, then 3, and the register
drift corrected as bookkeeping.** All three are answered. Every figure below is
from `docs/evidence/d61-normalize-outline-arrow.json`, taken on `main` at
`cbb0c7d` (code identical to `a604d40`), on five plans.

**Headline: 2b's scope is unchanged.** The arrow points up, and by so little
that it does not re-scope anything. But the measurement turned up something
else, and that part does need a ruling.

---

## Item 2 — the direction of the arrow

**Does `normalize_walls` raise the redundant-outline-corner count? YES, on 2 of
5 plans, by +2 vertices each. Never down.**

| plan | redundant vtx / slots BEFORE | AFTER | delta |
|---|---:|---:|---:|
| **`wiscaway`** (Patrick's) | 26 / 38 | **28 / 40** | **+2 / +2** |
| `roundedMultifloor` | 11 / 17 | **13 / 20** | **+2 / +3** |
| `planc1.v5` | 0 / 0 | 0 / 0 | 0 |
| `farmplaceBIGmultifloor` | 1 / 2 | 1 / 2 | 0 |
| `symmetricP1` | 2 / 4 | 2 / 4 | 0 |

Room areas unchanged to the cent on every plan; outline corner slots unchanged
at 159/175/136/187/140.

**How much of the 69 does it account for? NONE.** The complaint count is
**69 → 69** on `wiscaway` and unmoved on all five plans. `normalize_walls` does
not add to what Patrick is looking at.

**Attributed to a sub-pass**, each run alone on a second load:

    merge_collinear_scene   merged 22   REDUNDANT +0    truly-orphaned +22
    weld_scene              shared 91   REDUNDANT +2    DIVORCED +49
    split_body_landings     split   0   REDUNDANT +0

**The producer is `weld_scene`**, on both plans where the count moved. Merging
cannot make a ring straighter than it was, and it doesn't: +0 on all five.

**So D61 does NOT have two producers in any sense that matters.** `join_room`'s
split is the mechanism; the wall pass contributes 2 of 28 and 0 of 69. **The
record's mechanism story stands and 2b closes the thing that matters.** No
rewrite is owed on that ground — though the record needed rewriting anyway, see
below.

### The boundary of "before"

`planio.load_data` calls `merge_all(scene)` at `planio.py:204`, gated by
`auto_coalesce`, which defaults `True`. **So "a plan that has never had one"
does not exist through the UI** — a plan as loaded has already had a plan-wide
collinear merge. "Before" here means *as the user sees it on opening the file*.
The sub-pass attribution is what compensates: it shows what each half does from
that state.

---

## Item 1 — 28 versus 40, closed by measurement

**The multiplicity account was right, and it is now measured rather than
explained.** The 28 dissolved vertices are **16 held by one room and 12 held by
two**: 16 + 24 = **40 slots exactly**. Outline corners **159 → 119**.

    RESIDUE 0 — and 0 on all five plans
    rounded      13 = 6x1 + 7x2 = 20 slots   187 -> 167
    symmetricP1   2 = 2x2       =  4 slots   140 -> 136
    farmplace     1 = 1x2       =  2 slots   136 -> 134
    planc1.v5     0             =  0 slots   175 -> 175

**There is no cascade.** A second dry run after applying reports **0 removable
on every plan**, so the preview does not under-report and does not need to
iterate to a fixpoint. The ruled contingency does not fire.

**The identification was not restated from the predicate.** The dissolved set
was obtained by *applying* the production report on a separate load and diffing
the outline corner map. Production's count and the diff agree on all five plans
(28=28, 13=13, 2=2, 1=1, 0=0).

### Where the 69 came from

It is reproducible and its predicate is now pinned: **the LOOSE per-room count**
— this room's ring runs straight through the corner, no wall test and no
agreement between co-holding rooms. Cross-checked against the three per-room
figures in `a604d40`'s message:

    Rear Porch  13 corners / 9 redundant    MEASURED 13 / 9
    Dining      11 corners / 7 redundant    MEASURED 11 / 7
    KITCHEN      9 corners / 5 redundant    MEASURED  9 / 5

**The number was sound; only its MEANING was unstated**, and it sat one
paragraph from 28 and 40 with nothing joining them. Four counts, on `wiscaway`:

| | | |
|---|---:|---|
| the **complaint** | **69** slots | what a person sees |
| 2a **vacates** | **40** slots | the strict predicate |
| 2a **dissolves** | **28** vertices | the same set as objects |
| 2a **leaves** | **29** slots | a wall needs the corner, or a co-holder turns at it |

**That 29 is what 2a leaves on Patrick's plan and it appeared nowhere on disk
before this run.** It is the honest answer to "did 2a fix my problem": it
removed 40 of the 69 things he can see.

---

## Item 3 — should `normalize_walls` call `coalesce_outline_corners`? REPORT ONLY

**The question's premise is false, and that is the finding.** 0002 put it as
*"the menu command does both and every other caller of `normalize_walls` does
only the wall half"*.

**There is no other caller.** `normalize_walls` has **exactly one production
call site** — `mainwindow.py:1216`, inside `coalesce_all_now`. Everything else
is three tests in `test_topology_ops.py`. So:

* **the blast radius is empty.** "A convenience with a blast radius across
  every existing caller" cannot happen; there is one caller and it already does
  both halves.
* **the repair-at-cause reading is dead too**, on item 2's number: the wall
  pass contributes 2 of 28 and 0 of 69, so folding the outline pass into it
  would not be repairing anything at cause.

**Two reasons not to fold, and the second is the real one:**

1. **The wiring at the call site is a dialogue, not geometry.** `coalesce_all_now`
   runs the dry run, sorts the four worst rooms, builds a `QMessageBox` and only
   then applies. Lifting that into `walls.normalize_walls` puts a modal in the
   geometry layer — and the dry-run-then-confirm is the *safety* the ruling made
   non-negotiable, so it cannot simply be dropped on the way.
2. **2b does not want `normalize_walls` at all.** 2b needs the **scoped** form
   from a gesture — `coalesce_outline_corners(scene, rooms=…)` on the run a room
   just vacated. `normalize_walls` is plan-wide by definition. Folding them
   would give 2b a plan-wide pass inside a gesture, **which is exactly what the
   2a ruling refused** ("a global sweep built first is one nobody dares run
   inside a gesture").

**Recommendation: leave them separate; 2b calls the primitive directly from the
leave path.** No change to `normalize_walls`. Reported, not done — this is
yours to rule.

---

## THE THING THAT WAS NOT ASKED FOR — filed as D62

Validating the orphan count split it in two, and the second half is bigger than
the item that produced it.

**`weld_scene` leaves room outlines holding a `Vertex` that no wall at that
coordinate holds.** Placed rooms only, floor-scoped, floats exempt:

| plan | as loaded | after `normalize_walls` |
|---|---:|---:|
| `wiscaway` | **0** | **49** |
| `planc1.v5` | 0 | 56 |
| `farmplace` | 0 | 24 |
| `roundedMultifloor` | 0 | 78 |
| `symmetricP1` | 0 | 57 |

**Zero on every plan as loaded; large on every plan after Edit ▸ Coalesce all
walls now.** Under the Phase 3 model — *a corner is one `Vertex` the walls and
the outlines both hold* — this state should not exist.

**The consequence is NOT established and I am not claiming it.** `WallItem`
gathers the outline edges a drag must carry with `by_id.get(id(e.v))`
(`walls.py:1979`) — by identity — so a divorced edge is skipped, which reads as
stranding. **Measured, one sampled drag does not separate it** from the designed
step-insertion at `walls.py:1999-2014`: the wall moved, the corner stayed, the
area did not change, and both stories predict that.

**`scene_identity_report` (D48/G2) reports `extra_vertices` 0 on four of the
five plans after the pass.** It is not broken — it compares **wall ends to wall
ends**, and the outline question is outside its scope. *A census inherits the
blindness of the predicate that scopes it*, arriving at the newest instrument in
the tree. **And `check(deep=True)` cannot fire either**: `design_from_scene`
welds on the way out, so the document has one vertex per point whatever the
scene holds — D48's own finding, biting a second time.

**Filed as [D62](../defects/0062-weld-scene-leaves-room-outlines-holding-a.md),
open, with no direction proposed.** What is owed before anything is built: does
a divorced corner strand in practice, on more than one sample; and does the fix
belong in `share_coincident_ends` or in widening D48's report. Both yours.

---

## What the controls caught, which is most of the value

**Every number above survived a control that killed an earlier version of
itself.** Named in the evidence file beside the results, as ordered.

| control | verdict | what it caught |
|---|---|---|
| **A** — the two known corners `(1062, 684)` / `(750, 684)` must be reported at wall-degree 0 with their named holders | **PASS** | nothing; it gates belief in the zeros on the other four plans |
| **B** — are those two also *dissolvable*? | **FAIL, correctly** | that "no wall needs this corner" and "every holder runs straight" are different questions. B was never the gate |
| **divorce self-test** — detach one wall → PARTIAL +1; detach the rest → FULL +1 | **PASS** (after two rewrites) | the counter only fired when *every* wall had left, so a half-carried corner was invisible |
| **drag arm A** — a non-divorced corner must follow | **PASS** (after one rewrite) | the drag pressed the wall's **midpoint**, which on a real plan is a **door**. It selected the `OpeningItem`, the wall never moved, and arm B's "did not follow" would have been reported as evidence |

**Three more faults in my own instruments**, found by controls rather than by
results: no **floor** filter on the by-point test (62 where the scoped answer is
49); no **floating-room** exemption (the 13 are MUD, PWDR, Pan, Util); and an
`areas_unchanged` check reading a key the production function does not set when
nothing is doomed, which reported a false area change on `planc1`.

**The self-test's first version also failed for the wrong reason** — it demanded
a zero baseline and the plan has a pre-existing PARTIAL of 1, so the assertion
was **unsatisfiable on that fixture**. Rewritten to assert the **transition**,
which is what a control is for: that the instrument *moves*, not that the world
is empty.

---

## Register corrections made, as ruled bookkeeping

* **D61's status** now reads *stage one and 2a on `main`, 2b not started*, with
  2a's shipped surface and its measured receipt. It described 2a in the future
  tense while 2a was on disk.
* **The 69 moved into the record** with its provenance, its predicate, and the
  four-count table that separates it from 28 and 40.
* **Item 2's answer and item 1's reconciliation** are in the record, not only in
  a commit message.
* **D62 filed**; `tools/defects_index.py` regenerated — **63 records, 21 open,
  42 closed**, `--check` clean.

---

## What has not started

**2b.** Its scope is unchanged by item 2 and its acceptance is unchanged: a move
to a new location costs +0 walls / +0 vertices net, and a walk of six moves ends
with the counts it started with. It remains AMBER, and Patrick's check on his
own plan with the room areas as the receipt is still the merge condition.

**Nothing about D62.** Reported only.
