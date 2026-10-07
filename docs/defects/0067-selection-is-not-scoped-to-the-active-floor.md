---
# permanent key, independent of GitHub
id: 67
title: "Selection is not scoped to the active floor -- an inactive floor is drawn AND draggable"

# maps directly onto GitHub Issues fields
state: closed
state_reason: completed
labels:
  - type:defect
  - area:ui
milestone: null

# ours; becomes body prose after migration
opened: 2026-08-11
closed: 2026-10-07
closed_by: cdc54de
rank: 68
related: [11, 12, 53]
state_source: ruling
github_issue: null
---

# D67 — Selection is not scoped to the active floor

## The report

**Patrick, 2026‑08‑11:** grouping and dragging on the second floor **collects
vertices belonging to the first**, and the drag moves both.

**Expected, in his words:** while working on one floor, the others are **visible
if enabled** but **not selectable and not draggable**.

**This is testimony, not measurement** — and under the standing rule it earns the
same scrutiny as any premise. It is filed as reported and **has not been
reproduced**; the first task for whoever takes it is to reach the state
described.

## The rule, so the fix has a spec

> **VISIBILITY AND PERMISSION ARE SEPARATE GRANTS. An inactive floor may be
> drawn; it may not be hit-tested, selected, banded, or dragged.**

**This is the project's own *"retire visibility before permission"* arriving
inverted.** That rule was written for taking a guard *away*: retire the one
controlling what a subsystem can SEE before the ones controlling what it may
TOUCH, or you get a pass acting on geometry its graph cannot see. Here the
mirror happened — **visibility was granted to ghost floors and permission came
along with it**, because nothing scoped permission separately. The rule's own
corollary predicts exactly this: *a consumer that derives scope from the view
inherits whatever the view admits.*

## Candidate sites — named for whoever takes it, NOT measured

**Not a census.** These are leads, and the standing rule is that a census of a
call shape parses rather than greps:

* **`best_by_priority`** — resolves by TYPE and appears to have **no floor
  predicate at all**.
* **`select_in_rect`'s room half** — a full scan with `item_fully_inside`, likely
  unscoped too.
* **whatever applies the drag** — must be checked **separately**, because a
  selection correctly scoped can still be applied to a **shared vertex that
  crosses floors**.

**Prior art already on disk, measured for a different question and directly
relevant:** the `wall_ok` floor hypothesis raised and **refuted** during
[D63](0063-a-coalesced-outline-partly-rebounds-on-save.md) establishes that **a
shared vertex takes its floor from its first holder**. That is exactly the
ambiguity the third bullet is about.

## Family

**Filed with [D11](0011-four-competing-z-order-systems-two-of.md) / A2.** Both are
**floor scoping** — D11 is *z*, this is *selection* — and
[D12](0012-10-query-paths-ignore-the-floor-filter.md) (ten query paths ignoring
the floor filter) is the same class one layer down, already closed.

## Reproducibility, and a coverage boundary worth recording

**`examples/roundedMultifloor.json` EXISTS as a fixture, so this is headlessly
reproducible whenever it is taken up.** The suite's silence is about **nobody
having asked**, not about the case being unreachable — the D53 lesson exactly:
*you cannot write a regression test for a capability that was never there*, and
its sibling, *a question nobody posed leaves no red.*

**And the boundary itself is worth the record: `roundedMultifloor.json` is the
ONLY multifloor plan in the corpus.** Every multi-floor claim this project makes
rests on one drawing.

> **OUT OF DATE, corrected 2026‑09‑27 on
> [`0197-ruling.md`](../handoff/0197-ruling.md) §1's instruction.** That was
> true of `examples/` when it was written. 0197 §1 counted five multifloor
> plans on disk (`examples/farmplaceBIGmultifloor.json`,
> `examples/roundedMultifloor.json`, `fixtures/crossfloor-snap-2026-08-17.json`,
> `fixtures/wiscaway2026-08-30R1.json`, `…R2.json`), and
> `fixtures/wiscaway-2level-stacked-floor.json` has since made six. The
> reproduction below ran on `roundedMultifloor.json` because this record names
> it; **it has not been run on the other five.**

## REPRODUCED 2026‑09‑27 — measured, not fixed ([`0201-report.md`](../handoff/0201-report.md))

Ordered by [`0197-ruling.md`](../handoff/0197-ruling.md) §5. The probe is
[`docs/evidence/d67_crossfloor_probe.py`](../evidence/d67_crossfloor_probe.py),
its output [`d67-crossfloor-probe.txt`](../evidence/d67-crossfloor-probe.txt).
Second floor active, every result identical with "show other floors" on and
off.

**His report holds.** Band the second floor, group, drag: **floor 1 moves** —
3 vertices, 6 walls and 4 room outlines (`Hall`, `LOUNGE` and two more) changed
on `default`. The same group nudged by the arrow keys moves floor 1 the same
way.

**The three candidate sites above all measure CLEAN:**

| route | what it selected / moved |
|---|---|
| rubber band over the whole plan (`select_in_rect`) | `{'second': 46}` — nothing of floor 1 |
| select‑all | `{'second': 41}` |
| `SELECT` and a mouse click where only a floor‑1 furnishing lies (`best_by_priority`) | nothing |
| a shared `Vertex` across floors | **0** of 96 live vertices is held by walls of two floors, though 21 positions have a floor‑1 and a floor‑2 vertex coincident |
| one floor‑2 wall with both ends over floor‑1 vertices, dragged | floor 1 unchanged |

Inactive‑floor items are disabled (`enabled by floor {'second': 46}`), which is
what keeps every selection route off them.

**The leak is a fourth site, not among the three named:
`RoomItem.interior_walls()` (`floorplanner/rooms.py`) has no floor
predicate.** It returns every `WallItem` in the scene whose two ends lie inside
the room's outline. `MainWindow.group_selected` adds `room_walls(room) +
room.interior_walls()` for every selected room, so grouping the second floor's
`BR2` adopts two first‑floor partition walls lying inside its outline in plan
— (936,792)–(948,792) and (936,876)–(936,792) — and the group's members come
out `{'default': 2, 'second': 41}`. The drag then moves those two walls'
vertices, and every floor‑1 wall and room outline holding them follows.
`room_walls` returned nothing of another floor.

**Undo is COMPLETE, not partial.** One step restores both floors to pristine,
after the drag and after the nudge. **The pre‑committed blocking condition
below is therefore NOT met** — measured on the snapshot undo the editor runs
today, which restores the whole document; a `GestureCommand` that recorded
affected entities would have to be measured again when it exists.

**Not fixed** — the order was a measurement. The fix the measurement points at
is one predicate (`it.floor == self.floor`) in `interior_walls()`, with this
probe's gesture as its fail‑first test; whether `group_selected` should also
refuse any member of another floor, as the rule above reads, is the
reviewer's to say.

## THE CONSTRAINT ON PHASE 6 — a design requirement, not a fix

> **P6.b's command classes must carry the ACTIVE FLOOR as part of the settled-
> gesture boundary.**

**A command recorded without floor scope will faithfully replay a cross-floor
drag, and undo will faithfully undo it on both floors** — at which point this
stops being a selection bug and becomes **a property of the command model**,
which is far more expensive to remove later.

Applied at `floorplanner/commands.py` on the same day this was filed. **That is
not a fix for this defect** and does not close it.

## IT MAY BLOCK P6.d — pre-committed 2026‑08‑11

**If undo of a cross-floor drag comes back PARTIAL, this defect BLOCKS the Phase
6 cutover.** The question — whether a `GestureCommand` records the *operation* or
the *affected entities* — is pre-committed to P6.d's read-back with its
consequence decided in advance, so the answer cannot be argued with afterwards.
The test is one gesture on `roundedMultifloor`: drag across floors, undo, compare
floor 1 to pristine.

**A lossy undo is worse than the defect it fails to reverse.** This drag is
visible and correctable; a half-restoring undo is neither.

## Ruling

*(Open — filed 2026‑08‑11, reported by Patrick.)* **Filed, not fixed**, on the
reviewer's instruction. The candidate sites are leads for whoever takes it and
are explicitly **unmeasured**.

## Closed — 2026‑10‑07, `cdc54de`, PR #76 on Patrick's word

**The leak was a fourth site, not the three named above** —
[`handoff/0201-report.md`](../handoff/0201-report.md) §1 measured all
three clean and found `RoomItem.interior_walls()` with no floor predicate;
[`handoff/0202-report.md`](../handoff/0202-report.md) §4 found the same
class in the Door/Window tool's wall lookup. **Fixed, one predicate each**
([`handoff/0223-report.md`](../handoff/0223-report.md) §1): the room's own
floor's walls; a wall of the active level. `tests/test_d67_floor_scope.py`
replays both probes' gestures, red before and green after, with two
positive controls. Merged at `cdc54de` with the 3D gable-end tranche folded
in, his word *"fold into #76 and land"*
([`handoff/0225-report.md`](../handoff/0225-report.md)).
