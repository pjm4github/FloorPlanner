# 0008 — read-back: Phase 6, the four questions

**Measurement only. No command class exists, `snapshot()` is untouched, nothing
is implemented.** Supersedes nothing in [`0007`](0007-readback-phase-6.md) — it
answers the four questions that one raised.

**D61 stage 2b is written but UNVERIFIED and PARKED**, in `git stash` (`stash@{0}`),
because Q4 below decides whether it should exist. It is not on any branch.

---

## Everything before Phase 6 — what shipped

| item | state |
|---|---|
| **I15 outline completeness** | **shipped**, PR #20 + #21 — boundary-gated, load reports, save asks |
| **I16 simple ring (D41)** | **shipped**, PR #21 — with `symmetricP1`'s spur removed, freeze re-cut, justification in the same commit |
| **D63 producer 1** | **closed** — rebound 0 on five plans, robust across four pairing tolerances |
| **D62 `weld_scene` repair** | **shipped**, PR #19 |
| **the area bound** | **shipped**, PR #19 |
| **`fixtures/incoming/` contract** | **shipped**, PR #19 |
| **D64, D65** | **filed, parked** — register entries, no work |
| **D61 stage 2b** | **NOT shipped** — written, unverified, stashed pending Q4 |

Gate on `main`: `collected=680 ruff=clean vacuous=0 end_assign=0`, OFF/ON/DEEP
each **673 passed, 7 deselected**, GREEN. Docs GREEN, **66 records**.

---

## Q1 — every `snapshot()` caller, and what it ACTUALLY protects

Eight sites. The column that matters is the third.

| site | appears to protect | **actually protects** |
|---|---|---|
| `mainwindow:124` `__init__` | undo baseline | the **empty-state baseline** — without it the first `_commit_if_changed` has nothing to diff and every new scene records a spurious step |
| `mainwindow:1439` `_commit_if_changed` | undo history | **undo history AND the per-mutation shadow-mode hook.** One walk feeds both: `state = self.snapshot(report=rep)` then `_verify_or_report("operation", doc=state, …)`. The comment says so — *"walking the scene twice here would double the per-edit cost"* |
| `mainwindow:1460` `_restore_state` | undo | **re-baselining after a restore**, so the restored state is not itself recorded as a step |
| `mainwindow:1470` `_reset_undo` | undo | the **New/Open clean baseline**, which is also what makes the title bar correct |
| `mainwindow:1381` `_persist_verify_corpse` | undo | **nothing to do with undo** — a diagnostic dump on a shadow-mode failure |
| `planio:614` `_write_plan` | save | **dirty tracking** — records what is now on disk |
| `planio:675` `save_path` | save | same, scripted path |
| `planio:729` `_is_dirty` | dirty flag | **a whole-document comparison** — `snapshot() != canonicalize(deepcopy(_saved_state))` |

**THE FINDING: `_commit_if_changed` is not an undo function. It is the
application's only per-mutation invariant hook, wearing undo's clothes.** Retire
snapshot undo naively and **P1.6 shadow mode goes silent** — the `FP_VERIFY_DESIGN`
path that has caught real corruption loses its trigger. That is the single most
expensive thing hidden in this phase, and nothing in the plan mentions it.

**Four of eight die with P6.2. Three are dirty tracking. One is diagnostics.**

---

## Q2 — the mutating surface, and where the command boundary falls

**82 mutating methods** (AST census, a lower bound). The user-facing surface is
**`MainWindow`'s 14 public mutators**. P6.1's nine command classes were written in
Phase 0 and have no entry for `coalesce_all_now`, `align_rooms_to_grid`,
`distribute_rooms` or `refresh_rooms_cmd`.

**THE DRAG IS IN NEITHER LIST**, and it is the commonest mutation in the
application. It is not a `MainWindow` method — it lives in the items' event
handlers. A command layer covering the menu and not the drag leaves the principal
gesture outside undo, which is D53's seam again.

### Where a single gesture splits, welds and coalesces

**A placed room's label-drag IS `extract_room` → move → `join_room`** (P4.2).
Measured on `fixtures/wiscaway2026-08-08.json`, `WIC`, using production's own
float mover, walls/vertices:

```
start                              103 / 94
move 1  after EXTRACT 109/100   after JOIN 107/97    cumulative +4 / +3
move 2  after EXTRACT 109/101   after JOIN 103/93    cumulative  0 / -1
move 3  after EXTRACT 109/99    after JOIN 105/95    cumulative +2 / +1
move 4  after EXTRACT 107/99    after JOIN 103/93    cumulative  0 / -1
```

**One gesture crosses six sub-operations** — copy-trim, privatise vertices, move,
split landings, weld, merge — and **the intermediate states are not documents**:
mid-gesture the room is `floating` and I12 governs it instead of I14. A command
whose `undo()` restored a mid-gesture state would restore a state no invariant
set describes.

> **THE BOUNDARY MUST BE THE SETTLED GESTURE, NOT THE SUB-OPERATION.** That is
> what the 180 ms debounce already implements, and Phase 6 should adopt it rather
> than re-decide it. The nine-class list implies sub-operation commands
> (`MoveVertices`) and would have to be re-cut.

---

## Q3 — incremental, or one cutover? **ONE CUTOVER, and this is measured**

**The undo stack is not driven by operations. It is driven by the scene.**

```
scene.changed → _mark_dirty → 180 ms single-shot timer → _commit_if_changed
              → snapshot(), compare, push
```

`_mark_dirty` guards on exactly one thing: `if not self._restoring`.

**So any command that mutates the scene is ALSO recorded by the snapshot path.**
A command stack and the debounce cannot both be live without every operation
being recorded twice, and undo becoming ambiguous about which layer owns it.

**There is exactly one existing escape and it is not enough.** `_restoring`
suppresses the debounce during a restore, and a command could set the same flag
while it works — but that suppresses recording for *undo/redo*, not for the
*forward* operation, which is precisely the case where both layers want to record.

> **ANSWER: Phase 6 is a CUTOVER, not fifteen PRs.** The commands and the
> debounce are two answers to *"what is one undo step?"*, and the scene-driven
> one cannot be partially retired — it fires on `scene.changed`, which no command
> can avoid emitting.
>
> **What CAN land incrementally is everything that is not the stack**: the
> command classes themselves (unregistered, tested directly), the dirty-tracking
> replacement, and the shadow-mode hook re-hosted off `_commit_if_changed`. **Do
> those first, in any order, and the cutover shrinks to swapping one trigger.**

---

## Q4 — which records die, and the stronger claim tested

| record | verdict |
|---|---|
| **D45** `_edge_wall` by geometry | **dies** — the record itself says *"Phase 6, with the command layer, where 'the document states the binding' is the natural replacement"* |
| **D42** party-wall drag self-intersection | **dies** — *"`MoveVertices` is exactly that seam"* |
| **D29** dirty timer on close | **shrinks** — belongs to the debounce, survives unless Q3's cutover removes it |
| **D43** negative-assertion sweep | **unrelated** — deferred *to* Phase 6 by date, not absorbed |

### The stronger claim: does a command that knows what it did remove 2b's need?

**No — and the measurement says why, in the table above.**

**The growth appears at JOIN, and it is a property of LANDING SOMEWHERE NEW.**
When `WIC` returns to its original berth (moves 2, 4), the join re-welds exactly
and the plan comes back to **103/93** — it self-heals, with no coalesce anywhere.
When it lands displaced (moves 1, 3), the join leaves **+4 walls / +3 vertices**.

**A command layer cannot touch this, because no undo is involved.** The walk is
six *forward* operations. A `Join` command that recorded precisely what it split
would make that split *reversible*; it would not make it *unnecessary*. **Undo
makes debris removable, not absent** — and the user who drags a room six times
and saves has never pressed undo.

**So 2b survives Phase 6 and is not made redundant by it.**

> **BUT ONE ATTRIBUTION IS NOT YET MEASURED, and it changes 2b's shape rather
> than its necessity.** The `+4` after a displacing join is presumably *some*
> legitimate new splits at the destination plus *some* un-fused stubs at the
> vacated site — and only the second is debris. **2b as specified coalesces the
> vacated run, which targets exactly the second.** Splitting that +4 between the
> two sites is the measurement I would take before writing 2b, and it is the one
> I did not take.

### And a correction on 2b's own acceptance

**The recorded growth law — `0, 2, 4, 6, 8, 10` — did not reproduce**, and the
reason is an instrument fault worth recording: a walk that moves the room with
`setPos` produces **`0,0,0,0,0,0`**, because a floating room's walls are moved by
`_translate`, not by the item's position. **`setPos` never reaches the producer at
all**, and a 2b test written that way would be **vacuous by precondition** and
would pass against code that fixes nothing.

With `_translate` the producer fires — but **oscillating, not monotonic**: the
counts return to baseline whenever the room lands back where it started. A
monotonic `0,2,4,6,8,10` needs a walk that never returns. **2b's acceptance must
state which walk it means**, or it is a different test from the one the record
believes it is.

---

## What turns Phase 6 GREEN

Three rulings, none needing code:

1. **Where does the shadow-mode hook live** once `_commit_if_changed` goes? It is
   the per-mutation invariant trigger and nothing in the plan mentions it.
2. **The command boundary is the settled gesture** — confirm, and re-cut P6.1's
   nine classes against the 14 mutators that exist now.
3. **Accept the cutover shape**: land the commands, the dirty-tracking
   replacement and the re-hosted verify hook incrementally; swap the trigger once.

**And one measurement before any of it:** the undo-latency baseline on the P0.3
grid. P6.1's acceptance is *"undo cost is independent of plan size"* — a
comparison against a number nobody has taken.
