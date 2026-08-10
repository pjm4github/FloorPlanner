# 0005 — report: reboot state, 2026‑08‑10

**Written from disk, not from the conversation.** Every figure below was read
off the tree or off a command's output at the time of writing.

---

## 1. Where the tree is

| | |
|---|---|
| **`main`** | **`175c474`** — *The four ordered measurements: 2b is not gated, and 2a partly evaporates on save* |
| **`origin/main`** | **`175c474`** — pushed this session (was `cbb0c7d`) |
| **branch** | **`d62-weld-and-fixture-layout`** @ **`5f5cd3e`**, pushed, tracking `origin/` |
| **open PR** | **[#19](https://github.com/pjm4github/FloorPlanner/pull/19)** — *"D62's weld_scene repair, D63 producer 1, the area bound, and the fixtures/incoming contract"*, base `main`. **Not reviewed.** |
| **working tree** | clean, including untracked |

**`main` carries evidence, register and handoff only.** All code work is on the
branch. Two commits are on `main` this session: `0791f42` (D61's three owed
items) and `175c474` (the four ordered measurements).

### The gate, both heads

| | census | OFF | ON | DEEP | verdict |
|---|---|---|---|---|---|
| **`main` @ `175c474`** | `collected=668 ruff=clean vacuous=0 end_assign=0` | 661 passed, 7 deselected | 661 passed, 7 deselected | 661 passed, 7 deselected | **GREEN** |
| **branch @ `5f5cd3e`** | `collected=674 ruff=clean vacuous=0 end_assign=0` | 667 passed, 7 deselected | 667 passed, 7 deselected | 667 passed, 7 deselected | **GREEN** |

**The 7 deselected are the PERF LANE**, excluded from every mode by the standing
P3.8 flap-class ruling (`tools/gate.py:66`) — not an ad-hoc deselection, and the
same 7 that have been deselected since. Every sum reconciles against
`--collect-only`. Docs lane **GREEN** on both.

### Records

**`main`: 64 records — 22 open, 42 closed.** D63 was filed on the branch
alongside the code it describes and then brought onto `main` as a doc-only
change, so the register a fresh session reads is complete. The branch carries an
identical copy of the record and a regenerated index, so the merge is clean.

---

## 2. `fixtures/incoming/` — and a placement conflict, SINCE RULED

> **RULED in [`0005-ruling.md`](0005-ruling.md): *"fixtures/ stands, as you had
> it."*** The question below is closed and the tree is already in the ruled
> state — nothing to do. The reasoning is kept because the precedent is: a
> characterised failure does not pass back through the intake.

**The intake directory, its README and its enforcement test are on the BRANCH,
not on `main`.** `main`'s `fixtures/` holds `README.md`, `fragment2room.json`
and `wiscaway2026-08-08.json` and nothing else.

**`fixtures/incoming/` is EMPTY** (README only), on the branch. Nothing is
awaiting triage, so the two-handoff staleness rule has nothing to report.

### The conflict, stated plainly

The reboot instruction was *"copy `examples/wiscaway2026-08-09R.json` to
`fixtures/incoming/` and remove it from `examples/`"*. **I did not do that, and
the reason is that an earlier ruling in the same exchange said the opposite and
is the one that is coherent with the contract now on disk:**

> *"fixtures/, beside wiscaway2026-08-08.json. Not examples/ … with a README
> line naming all seven violations and stating that it is retained BECAUSE it
> fails, in the same form as the wiscaway freeze."*

That is what is on the branch. Putting the file in `incoming/` instead would
break **two** clauses of the intake contract committed in the same PR: files
there are **uncharacterised** (this one is characterised, with all seven
violations named), and **no test may reference a file in `incoming/`** — while
`test_the_2026_08_09R_fixture_is_still_dirty_in_all_seven_ways` references it by
name.

**The gate goal behind that instruction is already met**: `examples/` no longer
contains the file, and the gate is GREEN at both heads with no ad-hoc
deselection. **If the intent was the intake after all, say so and it is a
two-minute move plus deleting the guard test.**

### The contract, and it is measured

Three tiers — `examples/` frozen clean corpus, nothing imperfect enters it ·
`fixtures/` **characterised** failures, each named in `fixtures/README.md` ·
`fixtures/incoming/` **uncharacterised** intake, no test may reach it.

**Three exits, and the exit is named when taken:** promoted to `fixtures/` with a
README entry *and a fail-first test*; deleted as a **duplicate**, naming the
fixture that covers it; deleted as **no-defect-found**, naming what was checked.
**A file here is never edited or repaired** — if promoted it is frozen as it
arrived. **Every handoff lists the directory with each file's age**, and a file
untriaged across two handoffs is itself a finding.

**Enforced, not asserted.** `tests/test_fixture_layout.py` plants a deliberately
invalid plan in `incoming/` and fails if any corpus collector picks it up.
Measured when the directory was created: **the full gate ran GREEN with a real
seven-violation plan sitting there**, against `1 failed` for the same file in
`examples/`. A structural claim ("the glob is scoped to `examples/`") would pass
whether or not the directory existed; only a plant that must be reported if seen
makes it a measurement.

---

## 3. D61 — where it stands

**Stage one and 2a are on `main` (`4226f70`, `664aa6a`, `a604d40`). 2b HAS NOT
STARTED.**

**2b's acceptance is now taken ACROSS A SAVE — ruled this session:**

> a walk of six moves ends with the same wall, vertex and collinear counts it
> started with, **measured after save and reload**, not in session

In-session-only would measure the wrong thing, and §4 is why. **Tier AMBER**;
Patrick's check on his own plan is the merge condition and the room areas are
the receipt he reads.

**Three things that change 2b's baseline, all measured this session:**

1. **The leave path does not weld.** 0 welds in the extract phase in both
   shuffle states and across a six-move walk. The gesture's single weld is
   `share_coincident_ends` at `extract.py:238`, inside `join_room`. 2b's own
   addition is a **dissolve**, so it adds no D62 exposure.
2. **2a now removes 33 on `wiscaway`, not 40** (branch), and all 33 are durable
   across a save. The predicate was corrected — see §4.
3. **Patrick's fixture has `settings.editing.shuffle: true`.** Under shuffle a
   label-drag leaves the room floating and `join_room` never runs, so **D61's
   producer does not fire on his 08‑08 file under an ordinary drag**. It fires
   when he **joins**. `fixtures/wiscaway2026-08-09R.json` is the same drawing a
   day later with shuffle **off**: walls 103 → 134, vertex objects 101 → 201,
   outline slots 159 → 241, redundant-looking corners 69 → 129.

**The four counts, on `wiscaway2026-08-08`:** 69 the complaint (what a person
sees) · 40 slots the strict predicate vacated · 28 vertices behind them · 29
left. **28 of the 29 are "a room sharing this corner turns at it"** and exactly
one is "a wall needs it", so the 29 are **real corners, not redundant ones**.

---

## 4. D63 — the rebound is its own defect, with TWO producers

**Filed as record [D63](../defects/0063-a-coalesced-outline-partly-rebounds-on-save.md), on `main`.** The record was
brought onto `main` from the branch so the register a fresh session reads is
complete; the branch carries an identical copy, so the merge is clean.

Run the coalesce, save, reopen: some removed corners come back, **once**, then it
settles. A pure round trip with **no** command is stable (159, 159, 159, 159), so
saving is not a producer on its own.

**THE DECOMPOSITION, and it is an exact arithmetic identity:**

> **`inserted_after_the_pair − inserted_after_the_wall_pass == overlap`** —
> exactly, on all five plans.

| plan | 2a removed | inserted by the save | of which 2a's | inserted after the **wall pass alone** |
|---|---:|---:|---:|---:|
| `wiscaway 08‑08` | 40 | 7 | **7** | 0 |
| `roundedMultifloor` | 20 | 19 | **13** | 6 |
| `farmplace` | 2 | 2 | **2** | 0 |
| `symmetricP1` | 4 | 0 | 0 | 0 |
| `planc1.v5` | 0 | 3 | 0 | 3 |

* **Producer 1 — the coalesce coming undone.** Largely closed, see below.
* **Producer 2 — a wall-pass-side insertion** putting back corners 2a never
  touched: 6 on `rounded`, 3 on `planc1` where the outline pass removed
  **nothing at all**, so producer 1 cannot account for it. **Untouched.**

**Two investigations, not one**, and the identity is what says so.

### Producer 1: the save was right and the coalesce was wrong

`design/bridge._walk` emits **one outline edge per wall** (invariant I5), so a
room edge crossing a T-junction is several edges however few corners the scene
holds. **The coalesce was removing corners the document model requires** and the
save was putting them back correctly. The diagnosis was inverted until measured.

Of the re-inserted corners **4/4**, **4/4** and **16/16** had a wall **end** at
them; of those that stayed removed, **0/33**, **0/94**, **1/7**.

Two terms were added to `wall_ok` (branch): a wall **ending** here that does not
**hold** the vertex; and a collinear pair that **cannot merge** — `merge_wall` is
same-type only, so a 6″ `exterior` meeting a 4.5″ `interior` head-on stays two
walls and needs an outline edge each.

| plan | removed | durable | rebound |
|---|---:|---:|---:|
| `wiscaway 08‑08` | 33 | **33** | **0** *(was 40 / 33 / 7)* |
| `wiscaway 08‑09R` | 94 | **93** | 1 |
| `symmetricP1` | 4 | **4** | 0 |
| **`roundedMultifloor`** | 6 | 0 | **6 — UNRESOLVED** |

Pinned by `tests/test_rooms.py::test_a_coalesced_corner_stays_gone_across_a_save`.
**A floor-scoping hypothesis for `rounded` was written and REFUTED** — the result
is byte-identical with and without it. It stays because the floor rule is right,
and the code comment says it fixed nothing.

---

## 5. D62 — the repair as it stands

**Filed on `main` (`0791f42`); the fix is on the branch.**

`weld_scene` folds coincident wall ends onto one `Vertex` and left every room
outline holding whichever twin lost. `share_coincident_ends` has **three**
callers: `close_gap` repaired every room on the floor, `join_room` repaired the
joined room, **`weld_scene` repaired nothing**. What P4.2 established at one call
site — with a comment naming the symptom, diagonal tears in M Bath / Hall /
Lounge, found by a **manual check** — was never carried to the others.

**Fail-first receipt:** `share_outline_vertices` needed **0** re-adoptions on a
plan as loaded, **139** / **146** straight after `weld_scene`, and **0** on a
second call. Divorced corners after the menu command: **49/56/78/57 → 0/0/0/0**.
No room area moves.

**It is runtime-only** — the divorce does not survive a save (49→0, 56→0, 78→0,
57→0) — which bounds the harm to the session. **And the pairing is the sharpest
instrument boundary in the table:** `design_from_scene`'s weld is **both** what
makes the state harmless across a save **and** what hides it from
`check(deep=True)`. One mechanism, two effects, opposite signs, so those are
**one fact read twice, not two supports**.

### TWO THINGS EXPLICITLY NOT DONE

* **The `join_room` widening is REVERTED.** Both sites were tried; neither
  changed the six-move walk (`0,0,0,2,0,0,0` before and after) and five
  constructed offsets on a three-room scene reproduced nothing. No receipt, so
  it was reverted and the test written for it removed rather than kept as a
  green that was never red. `extract.py` is untouched.
* **THE STEP‑3 DIVORCE IS UNATTRIBUTED.** A six-move label-drag walk on
  `wiscaway` shows two divorced corners appear at step 3 and clear at step 4.
  **It is not `join_room`'s neighbour gap.** Producer unknown.

---

## 6. The area bound — spec ruling, on the branch

> *"No room's area moves"* was never a property of the operation; it was a
> property of one plan.

`wiscaway 08‑08` reports `22 exact / 0 by angle` — the angular path never fires
there. `wiscaway 08‑09R` reports `23 exact / 61 by angle`, and **dissolving a
NEAR-collinear vertex must change area: arithmetic, not a bug.**

So the guarantee is a **bound enforced by REFUSAL, not by avoidance**:

* **`AREA_BOUND_SQFT = 0.005`** — half the 2‑dp display resolution, declared with
  its reason at the constant in `rooms.py`
* every dissolve computes the exact area it would move (the triangle it cuts
  off) and is **refused and counted** if it exceeds the bound
* the dry run reports the **exact/angle split**, the **max area delta** and the
  refusal counts by reason — and the dialog shows all three

Measured: max delta **0.001747 sq ft** on 08‑09R (61 angular dissolves, none
refused); **0.000000** on the other three plans.

**THE DISPLAY CAVEAT, stated at the constant because the arithmetic cannot keep
the other promise:** no positive bound stops a *displayed* figure flipping its
last digit — a value on a rounding boundary moves at any epsilon. `Garage` went
`4868.36 → 4868.35` on a **2e‑5** change. **The MODEL is bounded; the display is
not.**

**A prediction on the record, to be CHECKED rather than assumed:** the angular
path's share should collapse once grid-snap-by-default lands — Patrick's on-grid
argument predicts it. **Re-measure the exact/angle split then.**

---

## 7. The queue

1. **D63 producer 1** — *largely done on the branch*. What remains:
   **`roundedMultifloor`'s 6/6 rebound**, cause unknown.
2. **The area bound** — *done on the branch*. Remaining: re-measure the
   exact/angle split after grid snap, per the prediction above.
3. **D61 stage 2b** — not started. Acceptance **across a save**. AMBER.
4. **Grid snap** — carries its **reconciliation table** and **Ctrl's
   disposition**, and is where snap-by-default lands as D61's stage three.
   Read-backs still owed: the angular threshold for "no usable intersection" and
   the distance threshold for "intersection too far", each justified; the
   modifier audit for shift; the angle convention in the existing code; and
   whether any existing test asserts the old lattice-snap behaviour.
   **Partial measurements from earlier sessions are NOT on disk and must be
   re-taken.**
5. **A2 — D11's runtime z collapse.** `ROADMAP.md:140` marks it ⏸ parked: the
   *hang* is parked as not reproducible; **the record is not closed.** The
   instrument is kept at `docs/evidence/d11_a2_z_step_counter.py` — do not
   re-derive it. Standing constraint unchanged: instrument first, and do not
   choose constants that make a symptom go away.

Also open and untouched: **D63 producer 2**, and **the step‑3 divorce**.

`docs/SESSION_SNAPSHOT.md` §2 carries the rest (A3, D59, A4/D49, A5/D41, A6,
Phase 5).

---

## 8. What a fresh session should read, in order

1. `docs/SESSION_SNAPSHOT.md` — the index and state marker
2. this file
3. `docs/WORKING_AGREEMENT.md` — the standing rules, including the plan-file
   placement tiers added this session
4. `docs/ROADMAP.md` — tiers and autonomy
5. `docs/defects/INDEX.md`

**And PR #19**, which holds all the code described above and is unreviewed.
