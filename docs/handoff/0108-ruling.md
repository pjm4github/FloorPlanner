# 0108 — ruling: "Snap wall to grid" — a per-wall manual action, and it is NOT the orthogonality repair

**Patrick:** *"I need a way to force a selected wall to snap to a grid so I can
go over an existing plan, by selecting each wall, one by one and right clicking
on it to snap to the grid."*

**Accepted. It is the half of item C that [`0066`](0066-ruling.md) §3 deliberately
left out — and he is volunteering to be the guard it lacked.**

---

## 1. IT IS A DIFFERENT OPERATION FROM THE REPAIR — do not reuse `repair_wall_orthogonality`

| | makes the wall… | example |
|---|---|---|
| **orthogonality repair** | exactly **axis-aligned** — equalises one coordinate | 89.99° → 90° |
| **snap to grid** (this) | both endpoints on **grid multiples** | y = 389.0628″ → 390″ |

**A wall can be perfectly axis-aligned and badly off-grid** — `wiscaway`'s
`y = 389.0628` is a *horizontal* wall. **The repair would not touch it.**
**And two ends that round to the same row make the wall axis-aligned as a side
effect, not as the goal.**

> ### SAME GUARDS, DIFFERENT ARITHMETIC. Reusing `repair_wall_orthogonality(t_in=…)` because it takes a bound would produce the wrong operation with the right paperwork.

**And it is simpler in one way:** both endpoints snap, so
[`0079`](0079-report.md) §2(c)'s *which endpoint moves* question does not arise.

## 2. WHY IT IS ALLOWED TO EXCEED `T`, WHICH THE REPAIR IS NOT

[`0066`](0066-ruling.md) §3: *"Below `1/16″` … invisible. **Above it, the
correction is a real edit and the user must see it before it happens.**"*

> **This action IS the user seeing it.** One wall, chosen by hand, on screen,
> with undo. **`T` does not apply — it was a proxy for a human, and the human is
> present.** **31 of the corpus's 63 near-axis walls are above `T`** and have had
> no route to correction until now.

## 3. THE FOUR REFUSALS — and they are the acceptance

**Snapping moves a shared `Vertex`. Every wall and every room outline on that
corner moves with it** (P3.1, and `RoomItem` holds the same objects — that part
is correct by construction and must not be "fixed").

| refuse when | why |
|---|---|
| **the result is degenerate** — both ends round to the same grid point | a zero-length wall. Nobody would think of this until it happened |
| **an opening would run off the wall** | the length changes when the ends round apart. **This is invariant `I7`, and it already fires on `wiscaway`** — measured |
| **`check()` gains a violation** that was not already there | [`0082`](0082-ruling.md) §2's differential, on a **stable key** ([`0082`](0082-ruling.md) §4) |
| **any wall's deviation or grid error INCREASES** | [`0084`](0084-ruling.md) §2's post-condition, extended to the grid — [`0083`](0083-report.md) §5 measured a neighbour thrown to **4.679°** by exactly this mechanism |

**On refusal: change nothing and say why.** On success: **one undo step**, and a
status line naming the vertices that moved **and what rode along with them**.

## 4. SHAPE

* **`WallItem.contextMenuEvent`** (`walls.py:2452`) already carries wall types
  and "Detach wall from room". **One more action, after a separator.**
* **Multi-select applies to each selected wall in turn**, and the guards are
  **re-evaluated between walls, not precomputed** — [`0082`](0082-ruling.md) §3's
  stale-predicate lesson, which cost a whole build.
* **Relocation uses `close_gap` / `Vertex.relocated_to`**, the same primitive the
  repair uses — identity-carrying, not a coordinate rewrite.
* **NO "snap all walls" button.** That is the unbounded repair with no human in
  it. He asked for one at a time; that is the feature.

## 5. EFFORT

**Small.** Every part exists: the menu, the relocation primitive, the invariant
differential, the post-condition, the undo commit path. **What is new is the
arithmetic (round both ends to `wall_snap_in`) and the four refusals.**

**Estimate: comparable to D80** — ~30 lines of code, ~60 of tests, **one test per
refusal plus the happy path**, no read-back needed because §3 is the
specification.

## 6. TIER

**AMBER** — it changes what an operation produces.

**Check, one question:**

> **Open `wiscaway2026-08-09R`, select the wall at x ≈ 78.97 ft, snap it.
> Does it land on 79.00 without moving anything you did not expect?**

**It queues behind PR #37 and PR #38**, which are built and waiting on him
already — but it is the first thing after them, because it is the only route
this project has to the 31 walls above `T`.
