# 0002 — report: repository state at 2026‑08‑09, for a fresh session

**A statement of repository state, read off disk.** Nothing here is recalled
from a conversation; every figure was taken from the tree at
`a604d40` and every claim points at a file, a commit or a record.

*(Numbered rather than date-named because this directory's protocol is
sequential and shared — see [`README.md`](README.md) §3. The date is above.)*

---

## 1. Where the tree is

| | |
|---|---|
| **`main`** | **`a604d40`** — *D61 stage 2a: the survivor question resolved, and the OUTLINE half built* |
| **`origin/main`** | same commit |
| **branches** | none but `main`, local or remote |
| **open pull requests** | **none** (`gh pr list --state open` → `[]`) |
| **working tree** | clean, including untracked |
| **gate** | `collected=668 ruff=clean vacuous=0 end_assign=0`; OFF / ON / DEEP each **661 passed, 7 deselected**; every sum reconciles; **`Gate-Verdict: GREEN`** |
| **docs lane** | **GREEN** — 62 records, front matter valid, index current, every defect reference resolves |
| **records** | **62 — 20 open, 42 closed** |

---

## 2. The vertex-accumulation work (D61)

The current programme. Three stages were ruled; **stage one and 2a are on
`main`, 2b has not started.**

| stage | commit | what is on disk |
|---|---|---|
| **one — find the producer** | **`4226f70`** | `docs/evidence/vertex-accumulation-stage-one.txt` + `vertex_accumulation_probe.py` |
| **the pre-implementation check** | **`664aa6a`** | `docs/evidence/coalesce-safety-check.json` + `coalesce_safety_check.py`; **D61 filed** |
| **2a — the primitive, dry run, command** | **`a604d40`** | `rooms.coalesce_outline_corners`, `MainWindow.coalesce_all_now(interactive=…)`, five tests in `tests/test_rooms.py` |
| **2b — the leave path** | — | **not started** |

**What stage one established** (from the evidence file): a room move that
returns whence it came is balanced to baseline; a move that lands somewhere new
costs **+2 walls and +2 vertices permanently**, both degree‑2 collinear, with
the collinear count running 0, 2, 4, 6, 8, 10 across six walks. The call site is
`split_wall_at` at `extract.py:232` inside `join_room`. Shuffle is **not** the
producer.

**What the check established:** a dissolve cannot produce an I14 weld pair
(measured, five plans). It **can** meet a ring degeneracy — a vertex may be
degree‑2 collinear among *walls* while a room outline **turns** at it, because
the outline's other edge there may be open. The predicate was corrected to
require **every** holding outline to run straight through the corner.

**What 2a measures on `fixtures/wiscaway2026-08-08.json`** (from `a604d40`'s
message and reproducible with the command): dry run **28 removable, 28 exact / 0
by angle**; applied, outline corners **159 → 119** and walls **103 → 81**; **no
room's area moves**, total **3870.5 → 3870.5**; a second run is a no‑op.

### THREE THINGS OWED ON 2a BEFORE 2b BEGINS

1. **The 28‑versus‑40 reconciliation.** The dry run reports **28** removable
   *vertices*; the applied pass takes outline corners from **159 to 119**, a
   difference of **40** corner slots. A corner held by several rooms is one
   vertex and several slots, which is the likely account — **it has not been
   measured, and the two numbers are both quoted in `a604d40`'s message
   without one.**
2. **Does `normalize_walls` MANUFACTURE redundant outline corners, and how many
   of the 69 does it account for?** Measured: it dissolves wall vertices while
   the outlines go on naming them — `(1062, 684)` and `(750, 684)` go from
   wall‑degree 2 to 0 and stay in Dining/KITCHEN and Foyer/GREAT RM/HALL. **Not
   measured:** whether the redundant‑corner count *rises* across a
   `normalize_walls` run on a plan that has not had one, and what share of the
   69 originates there rather than at `join_room`.
3. **Should `normalize_walls` call `coalesce_outline_corners` itself?** Today
   the wiring is in `MainWindow.coalesce_all_now`, so the menu command does both
   and every other caller of `normalize_walls` does only the wall half. **A
   report is owed on whether the two belong in one function** — it bears
   directly on 2b, which needs the outline pass to run from a gesture rather
   than from a menu.

---

## 3. 2b — ruled scope and acceptance

**Scope:** wire the primitive to the **leave path** — when a room vacates a run,
coalesce that run, using `coalesce_outline_corners`'s **scoped** form
(`rooms=…`). Same primitive, no second implementation. A vertex another room
still needs is protected by the existing predicate — it will have degree above
two, or its incident walls will not be collinear, or a holding outline will turn
at it — **so the safety is the predicate, not a special case.**

**Acceptance, as ruled, stated as a test rather than a description:**

> a move to a new location costs **+0 walls / +0 vertices net**, and **a walk of
> six moves ends with the same counts it started with**

**It fails today by construction** — stage one's table shows collinear going
0, 2, 4, 6, 8, 10 — so it is fail‑first without contrivance. The probe that
produces those counts is already on disk at
`docs/evidence/vertex_accumulation_probe.py`.

**Tier AMBER throughout.** Patrick's check on his own plan is the merge
condition, and the receipt he reads is the **room areas**.

---

## 4. Queued behind it

1. **The grid-snap pass.** Fully specified by ruling; **no record filed yet**.
   It carries its **reconciliation table** and **Ctrl's disposition**, and it is
   where snap-by-default lands as D61's stage three. Read-back items still owed
   on it: the angular threshold for "no usable intersection" and the distance
   threshold for "intersection too far", each justified; the modifier audit for
   shift; the angle convention found in the existing code; and whether any
   existing test asserts the old lattice-snap behaviour. **Partial measurements
   exist only in this session and are NOT on disk** — they must be re-taken.
2. **A2 — D11's runtime z collapse.** `ROADMAP.md:140` marks it **⏸ parked**:
   the *hang* is parked as not reproducible (`docs/evidence/d11-a2-z-step-measurement.txt`
   — five orders of magnitude on either z step changes no event count and the
   named test passes in ~0.3 s). **The record is not closed.** What survives:
   the four competing z systems, and ruling 4's scheme — z = `floor_term +
   stack_term + type_term`, the backdrop's −1e9 as a **type term**,
   `bring_to_front`'s full-scene scan dying, named constants pinned by a test.
   **The standing constraint is unchanged: instrument first, and do not choose
   constants that make a symptom go away.** The instrument is kept at
   `docs/evidence/d11_a2_z_step_counter.py` — do not re-derive it.

`docs/SESSION_SNAPSHOT.md` §2 carries the rest of the queue (A3, D59, A4/D49,
A5/D41, A6, Phase 5).

---

## 5. The open records, one line each

| id | type | |
|---|---|---|
| **D11** | defect | Four competing z-order systems, two of which run on every wall click. **A2's hang parked; the record is not** |
| **D41** | gap | I5b does not report a self-intersection the walk has planarised into a pinched loop |
| **D42** | gap | The party-wall drag has the same self-intersection exposure as the group bake |
| **D43** | task | Sweep the suite for negative assertions and measure how many establish preconditions |
| **D44** | limit | The invariants check CONSISTENCY, not HISTORY — an accepted limit |
| **D45** | task | `_edge_wall` answers "which wall covers this edge?" by GEOMETRY |
| **D46** | defect | `tools/make_site_demo.py` mints furnishing kinds that exist in no catalog |
| **D47** | task | `room_boolean("fragment")` builds duplicate wall loops. **STILL MARKED OPEN THOUGH ITS FIX MERGED AT PR #17 — a drift, flagged and not corrected, because the register is Patrick's** |
| **D48** | gap | The invariants have never checked the scene the user edits |
| **D49** | gap | I11 is reported nowhere in the shipped app — **the DEEP half**, after D59 split out |
| **D50** | defect | A level's elevation is DESTROYED by a load/save round trip |
| **D51** | defect | The census depends on the working tree, not the repository |
| **D52** | gap | Room-inside-a-room has no representation, and I11 misreports the workaround |
| **D54** | defect | A room label is sized from its NAME and clips its own area subtitle |
| **D55** | defect | Area totals DOUBLE-COUNT overlapping regions |
| **D56** | defect | A macro replay's final SELECTION is nondeterministic |
| **D58** | gap | `face_at` DISCARDS the walk report, so a straddler is recorded and thrown away |
| **D59** | gap | The CHEAP TWELVE never run at a document boundary either — and they cost nothing |
| **D60** | gap | Copy room and Paste room use a clipboard `Ctrl+V` cannot see |
| **D61** | defect | A room move permanently adds two walls and two collinear vertices — **the current work** |

---

## 6. Two standing rules added this session

Both in [`../WORKING_AGREEMENT.md`](../WORKING_AGREEMENT.md), and both bind
whatever comes next:

* **PARASITIC REACH** — when you repair a capability that never worked, budget
  for the affordances resting on the fault, and expect the user to report their
  loss as a regression. Five instances cross-referenced.
* **EVERY INSTRUMENT IS VALIDATED AGAINST A CASE KNOWN TO BE NON-ZERO BEFORE ITS
  ZERO IS BELIEVED** — a positive control, as a required practice. Two
  instruments failed this way inside one measurement.

Also added: *a reported repro is testimony, not measurement*; *a census inherits
the blindness of the predicate that scopes it*; and *a differential is only as
good as the stability of the field it compares*.
