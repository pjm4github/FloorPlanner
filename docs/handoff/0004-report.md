# 0004 — report: the four ordered measurements, and what they decide

**Ordered at 0003's ruling: the weld-path question, then the save/reload test,
then the 29's per-room breakdown and the fixpoint check.** All four are done.

**The two that decide: 2b is NOT gated by D62, and the pair does NOT need to
iterate.** But the same runs turned up something that matters more to Patrick
than either — **2a's fix partly evaporates on save**.

---

## 1. Does 2b's leave path reach `weld_scene`? NO. The join does.

**The leave never welds.** 0 welds in the extract phase, in both shuffle states,
and 0 across a six-move walk. The gesture's single weld is
`share_coincident_ends` at **`extract.py:238`, inside `join_room`**.

**2b's own addition is a DISSOLVE, not a weld**, wired to the leave. So 2b does
not increase D62 exposure at all.

**But D62 is not menu-only either.** A six-move walk (shuffle off, Rear Porch):

    step   0   1   2   3   4   5   6
    FULL   0   0   0   2   0   0   0

Two divorced corners at one step of six, cleared by the next move — consistent
with `join_room` repairing the joined room and not its neighbours. **So the join
half reaches D62 today, at a low rate, with no 2b in the tree.**

**Recommendation: 2b proceeds; D62 queues as its own AMBER item.** Ruling yours.

### The control that changed the answer

**`fixtures/wiscaway2026-08-08.json` carries `settings.editing.shuffle: true`.**
As it loads, a label-drag leaves the room **floating** and `join_room` never runs
(P4.3). Measured against that state alone the gesture welds nothing — true of the
**shuffle** path and silent about the ordinary drag 2b targets.

The first run of this probe reported exactly that: *"the gesture does not weld at
all — D62 is independent of 2b."* **Right answer, wrong question**, and it would
have gone into this report as the finding. What caught it was a second control —
*did `extract_room` AND `join_room` actually run?* — which read `{extract: 1,
join: 0}`. Both states are now measured and labelled.

**Worth a ruling on its own:** Patrick's working file has shuffle saved ON, so on
his own plan an ordinary label-drag leaves rooms floating and **D61's producer
does not fire** until he joins explicitly. That may be intended; it changes what
"a room move" means on his file, and D61's growth law was measured on a clean
plan with shuffle off.

---

## 2. Does the divorce survive a save? NO — it is runtime-only.

Applied the command, saved, reloaded, counted:

| plan | in the scene | after save + reload |
|---|---:|---:|
| `wiscaway` | 49 | **0** |
| `planc1.v5` | 56 | **0** |
| `roundedMultifloor` | 78 | **0** |
| `symmetricP1` | 57 | **0** |

Controls: something to persist (PASS), round trip lossless — every room, every
area identical (PASS), and **the saved file was actually readable (FIRED)**: the
v5 document is **flat**, and my first reader walked `levels[*].walls`, found
nothing, and reported a confident `0 orphan refs` off **0 walls and 0 rooms**.
Denominators now print beside that count.

**So the harm window is bounded by the session. D62 drops in severity — below
2b, not above it.** It does not close: everything a user does between opening a
plan and saving happens inside that window.

**The pairing you asked to have stated, and it is the sharpest boundary yet:**
`design_from_scene`'s weld on the way out is **both** the mechanism that makes
this state harmless across a save **and** the mechanism that makes it invisible
to `check(deep=True)`. One mechanism, two effects, opposite signs. Recorded in
D62 and in `WORKING_AGREEMENT.md`'s instrument table.

### The consumers, and the one that misbehaves

By AST: **55 reads of `.outline`, 5 writes, 6 files, 20 functions.**

**Most are indifferent.** `path`, `area_sqft`, `_derive`, `corners` read the
vertex's **position**, and a divorced vertex is at the right position — which is
why every area in every measurement is unchanged to the cent, and why nothing
shows the user anything until something moves.

**The one that misbehaves is `walls._plan_vertex_moves`** — the drag gather at
`walls.py:1979`, `by_id.get(id(e.v))`, keyed on identity.

**And this repo already knew.** `close_gap` (`walls.py:1101`) calls
`share_coincident_ends` and then repairs every room on the floor, with a comment
written at the P4.2 mini-gate:

> RESTORE THE P3.5 INVARIANT: … an outline left holding a coincident-but-distinct
> twin is a stranding the NEXT drag turns into a diagonal tear (found at the P4.2
> mini-gate: close the gaps, drag a wall, and M Bath / Hall / Lounge drew dashed
> diagonals to corners their walls no longer held).

**That is D62, named, with its symptom, found by a manual check.** So the harm has
a precedent in this tree, not only my one ambiguous sample.

**The mechanism is now exact — `share_coincident_ends` has three callers:**

| caller | repair afterwards |
|---|---|
| `close_gap` `walls.py:1101` | **every room on the floor** |
| `join_room` `extract.py:238` | the **joined room only** |
| **`weld_scene` `walls.py:556`** | **none** |

`share_outline_vertices` is the repair, exists, and is idempotent. **What P4.2
fixed at one call site was never applied at the other two.** Whether `weld_scene`
should call it is still a ruling — its docstring is explicit about declining
"an edit to a wall the user did not touch".

---

## 3. THE THING THAT MATTERS MOST TO PATRICK: 2a partly evaporates on save

Not asked for; found in the same round trip.

| plan | as loaded | after the command | after save + reopen | **durable** | rebound |
|---|---:|---:|---:|---:|---:|
| **`wiscaway`** | 159 | 119 | **126** | **33 of 40** | 7 |
| `roundedMultifloor` | 187 | 167 | **186** | **1 of 20** | 19 |
| `symmetricP1` | 140 | 136 | 136 | 4 of 4 | 0 |

**A pure round trip with no command is stable** — 159, 159, 159, 159 — so saving
is not a producer. The rebound is a **one-time** partial undo that settles
immediately (`119 → 126 → 126 → 126`).

**On Patrick's plan 2a's durable benefit is 33 of the 69, not 40.** On
`roundedMultifloor` it is **1 of 20** — near-total loss. Why it varies that much
is not measured, and I did not chase it.

**This bears on 2b directly.** 2b's acceptance is *"a walk of six moves ends with
the counts it started with"* — measured **in session**. If a save partly undoes
outline coalescing, 2b's receipt should probably be taken across a save too.
**Flagging, not changing: the acceptance is yours.**

---

## 4. The 29, per room — and the pair is already a fixpoint

**THE PAIR DOES NOT NEED TO ITERATE.** Running `normalize_walls` + the outline
pass, then running the **pair again**, dissolves **0** more on all three plans; a
third round is also 0. The anticipated unlock — a wall coalesce freeing a corner
a wall needed — does not occur. **So `Edit ▸ Coalesce all walls now` does not
need to change.**

**The 29, per room on `wiscaway`.** The classification was checked against
production and reproduces its removable count exactly (40/40, 20/20, 4/4), so the
reasons partition the refused set rather than approximating it.

| room | corners | complaint | removed | left | wall needs it | co-holder turns |
|---|---:|---:|---:|---:|---:|---:|
| Rear Porch | 13 | 9 | 3 | 6 | 0 | 6 |
| Dining | 11 | 7 | 3 | 4 | **1** | 3 |
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

**28 of the 29 are one reason: this room runs straight through the corner and a
room sharing it TURNS there.** Dissolving it would move the neighbour's area —
the failure the area receipt exists to catch. **Exactly one** corner in the plan
is held by a wall that needs it.

**So the honest reading is the one you anticipated: the 29 are real corners, not
redundant ones.** Patrick can check it per room — KITCHEN shows 5
straight-through corners, 3 go, 2 stay because a neighbour turns at them.

---

## What I recommend, and what is yours

* **2b proceeds.** Its leave path does not weld; its addition is a dissolve.
* **D62 queues as its own AMBER item**, below 2b. Runtime-only, repair already
  written, three call sites of which one is correct.
* **The menu command needs no iteration change** — it is already a fixpoint.
* **Two things I flag and did not act on:** whether 2b's receipt should be taken
  across a save, given §3; and whether the shuffle flag saved in Patrick's
  fixture is deliberate.

**2b has not started.**

---

## Register

D61 and D62 both updated with the measurements above — the durability table, the
per-room 29, the fixpoint result, the three-caller table, the consumer census and
the P4.2 precedent. **No new records filed.** Index unchanged at 63 records, 21
open, 42 closed.
