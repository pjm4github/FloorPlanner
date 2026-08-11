---
# permanent key, independent of GitHub
id: 67
title: "Selection is not scoped to the active floor -- an inactive floor is drawn AND draggable"

# maps directly onto GitHub Issues fields
state: open
state_reason: null
labels:
  - type:defect
  - area:ui
milestone: null

# ours; becomes body prose after migration
opened: 2026-08-11
closed: null
closed_by: null
rank: 68
related: [11, 12, 53]
state_source: report
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

## THE CONSTRAINT ON PHASE 6 — a design requirement, not a fix

> **P6.b's command classes must carry the ACTIVE FLOOR as part of the settled-
> gesture boundary.**

**A command recorded without floor scope will faithfully replay a cross-floor
drag, and undo will faithfully undo it on both floors** — at which point this
stops being a selection bug and becomes **a property of the command model**,
which is far more expensive to remove later.

Applied at `floorplanner/commands.py` on the same day this was filed. **That is
not a fix for this defect** and does not close it.

## Ruling

*(Open — filed 2026‑08‑11, reported by Patrick.)* **Filed, not fixed**, on the
reviewer's instruction. The candidate sites are leads for whoever takes it and
are explicitly **unmeasured**.
