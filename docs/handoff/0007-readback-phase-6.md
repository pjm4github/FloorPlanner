# 0007 — read-back: Phase 6, command undo

**Measurement only. No command class exists, `snapshot()` is untouched, and
nothing is implemented.** Every figure is from
`docs/evidence/phase6_readback_census.py` → `phase6-readback-census.json`, run on
`main` after PR #21.

**Why this exists:** Phase 6 is RED in the charter — *"command undo — the largest
remaining task; retires `snapshot()`"*. **RED means a ruling is missing, not that
the work is large.** This produces the material that ruling needs.

**How it counts:** `snapshot` is an *identifier*, so it is grepped exactly.
*"Which methods mutate the document"* is a **shape**, so it is an `ast` walk —
the P3.6/P4.5(40) lesson, where the same grep-shaped census missed five writers
twice.

---

## Q1 — `snapshot()`'s callers, and the headline is that RETIRING SNAPSHOT UNDO DOES NOT RETIRE `snapshot()`

**43 call sites** across the undo machinery, in **two files only** —
`mainwindow.py` (35) and `planio.py` (8). The eight `snapshot()` calls split by
**what they are for**, which is the split that matters:

| purpose | sites | dies with P6.2? |
|---|---|---|
| **undo history** | `__init__`, `_commit_if_changed`, `_restore_state`, `_reset_undo` | **yes — 4 of 8** |
| **dirty tracking** | `_write_plan`, `save_path`, `_is_dirty` | **no — 3 of 8** |
| **shadow-mode diagnostics** | `_persist_verify_corpse` | **no — 1 of 8** |

**So P6.2 as written — "retire snapshot undo" — leaves half the callers
standing**, and the *"a tidy-up pass that outlives its mess"* rule says each then
needs re-justifying rather than inheriting. Concretely:

**Dirty tracking is a whole-document comparison.** `_is_dirty` is
`self.snapshot() != canonicalize(deepcopy(self._saved_state))` — it builds and
compares the entire document on every check. A command stack answers the same
question in O(1) (`QUndoStack.isClean()`, an index comparison). **That is a
second, separable win that P6.2 does not currently claim**, and it is a different
decision from undo: replacing it changes what "dirty" *means* from *"the document
differs from disk"* to *"the stack is not at the saved index"*, and those diverge
whenever an operation is its own inverse.

> **RULING NEEDED:** does Phase 6 take dirty tracking too, or does `snapshot()`
> survive as the dirty comparator? If it survives, say so at the function, or
> the next reader will assume P6.2 removed it.

---

## Q2 — what the command interface must cover

**82 mutating methods**, 57 public, in ten modules. That is the *lower bound* on
what commands must eventually account for — but it is not the command surface,
because most are helpers reached from something else.

**The user-facing surface is `MainWindow`'s 14 public mutators:**

`delete_selected` · `nudge_selected` · `align_rooms_to_grid` ·
`distribute_rooms` · `refresh_rooms_cmd` · `room_boolean` · `group_selected` ·
`ungroup_selected` · `coalesce_all_now` · `cut_selected` · `paste_clipboard`
(+ `undo`, `redo`, `closeEvent`, which are the machinery itself)

**P6.1's nine named classes were written in Phase 0 and the gap is now visible.**
`AddItems`, `DeleteItems`, `MoveVertices`, `EditOpening`, `EditRoomProps`,
`Group`/`Ungroup`, `Extract`/`Join`, `ChangeSettings`, level ops — that list
predates **extract/join (P4.2)**, **floors**, **shuffle**, the **outline
coalesce**, and **align/distribute**. It has no entry for `coalesce_all_now`,
`align_rooms_to_grid`, `distribute_rooms` or `refresh_rooms_cmd`, and its
`Extract`/`Join` entry was a guess made before those operations existed.

**And the drag is missing from both lists**, which is the important omission: the
commonest mutation in the application is a mouse drag on a wall or a room label,
and it is not a method on `MainWindow` at all — it lives in the items' event
handlers. **A command layer that covers the menu and not the drag would leave the
principal gesture outside undo**, which is the same shape as D53's seam.

> **RULING NEEDED:** is the command boundary the *menu action*, or the *settled
> gesture*? The debounce (`_commit_if_changed`) currently makes that choice
> implicitly, and it is the single biggest design question in Phase 6.

**Boundary of this census, stated:** an AST walk finds what the source says. A
method that mutates only through a helper it calls indirectly is counted at the
helper, so 82 is a **lower bound**.

---

## Q3 — which queued items genuinely die with it

Read off the records rather than from memory. **Four name Phase 6 as their home,
and only two of them actually die there:**

| record | what it says | verdict |
|---|---|---|
| **D45** — `_edge_wall` answers "which wall covers this edge?" *by geometry* | *"Phase 6, with the command layer, where 'the document states the binding' is the natural replacement"* | **DIES** — a command carries the binding it made |
| **D42** — the party-wall drag's self-intersection exposure | *"Phase 6, with the command layer (`MoveVertices` is exactly that seam); explicitly not P4"* | **DIES** — it is a seam that only exists because there is no command |
| **D29** — `close()` leaves the 180 ms dirty timer running | names P6.1 | **SHRINKS, does not die** — the timer belongs to the debounce, which survives unless Q2's ruling removes it |
| **D43** — sweep the suite for negative assertions | *"Phase 6, not now"* | **UNRELATED** — deferred *to* Phase 6 by date, not absorbed by it |

**What does NOT die, against the subsumption claim as I put it:**

- **D61's vertex accumulation.** The claim was that *a command that knows what it
  did doesn't need a coalesce pass to clean up after it*. **That is half true and
  the half that fails is the half that matters:** the producer is `join_room`
  adding walls and vertices, and a `Join` command records that faithfully —
  recording it correctly is not the same as not doing it. **Undo makes it
  reversible, not absent.**
- **D62 / D63 / D65** — `weld_scene`'s family. These are properties of the
  geometry the operation produces; a command wrapper changes who can undo them,
  not what they are.
- **I15 / I16** — document properties, by construction outside an undo stack.

> **So the honest tally is TWO records closed, one shrunk, and the vertex family
> untouched.** Phase 6 shortens the board, but by less than "several of the
> queued items" — and I should not have said that without checking it, which is
> what this row is for.

---

## What P6.3 needs that nobody has measured

*"Undo cost is independent of plan size — undo time on a 20-room plan ≈ undo time
on an 80-room plan"* is P6.1's stated acceptance. **There is no baseline for it.**
The P0.3 harness exists and `tests/bench_rooms.py` measures the room path, but
**no number for the current snapshot-restore undo has ever been taken**, so the
acceptance has nothing to compare against. Taking it is cheap and belongs *before*
any command lands, not after.

---

## Recommendation

**Phase 6 can move RED → AMBER on three rulings**, none of which needs code:

1. **Does it take dirty tracking**, or does `snapshot()` survive as the comparator?
2. **Is the command boundary the menu action or the settled gesture?** — the one
   that decides whether the drag is inside undo.
3. **Is P6.1's nine-class list re-cut** against the 14 public mutators that exist
   now, or kept and extended as work proceeds?

**And one measurement first, whatever is ruled:** the undo-latency baseline on the
P0.3 grid, because P6.1's acceptance is a comparison against a number that does
not exist yet.
