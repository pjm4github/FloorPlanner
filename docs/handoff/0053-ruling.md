# 0053 — ruling: what the git widget is showing, and the order to clear it

**Patrick's IDE shows PR #32, `main ↙1`, and three branches.** Read from the
tree rather than the widget:

```
working tree ON       shower-identity-redraws
main        54b4a88   origin/main  fb054e3     -> 1 behind, 0 ahead
shower branch         4 ahead, 0 BEHIND main   gate GREEN 754 full
worktree-agent-…      0 commits since fork
```

---

## 1. THE HEADLINE THE WIDGET DOES NOT SHOW: the DXF agent FINISHED

**`fb054e3` on `origin/main`:** *"fp2dxf DXF integration built and PR'd
(0050-report); snapshot re-cut"*.

**And it took `0050` — exactly the collision [`0051`](0051-ruling.md) §2 said was
structurally guaranteed**, because the worktree forked before `0050-ruling.md`
existed and could not see it. **`0050-report.md` and `0050-ruling.md` are now two
unrelated documents sharing a number.** Fourth instance, first one predicted in
advance.

**The worktree branch has 0 commits**, so the work was landed by the parent, not
from the worktree branch. **That branch and its worktree are now spent.**

## 2. THE ORDER

**ONE — `git pull` on `main`.** One commit behind. **Nothing else is safe to
reason about until local `main` matches `origin/main`.**

**TWO — MERGE PR #32 (the shower redraws). It is ready.**

* **4 ahead, 0 behind** — [`0050`](0050-ruling.md) §3 step 1 was done.
* **Gate GREEN, `collected=754`, mode `full`.**
* **Patrick's check passed** ([`0050`](0050-ruling.md) §1).

**One thing owed before the merge, and only one:**
[`0050`](0050-ruling.md) §3 step 3 — **the extrudability census re-run on the
combined tree, stating what it reports for the three redrawn symbols.**
`glass_shower` was predicate 1's only failure and now has a filled body; **that
is the census's own before/after.** If the report already carries it, merge.

**Merge #32 BEFORE the DXF PR.** It is checked, green and zero-behind *now*; the
DXF PR is blocked on Patrick regardless, so it will need updating whichever order
is chosen. **Merging the ready one first costs nothing; merging the blocked one
first makes the ready one stale.**

**THREE — THE DXF PR IS PATRICK'S, AND IT IS THE ONLY THING NEEDING HIM.**
Export a two-storey plan, import one level into Chief following the guide, and
confirm walls, doors and windows arrive as their own kinds — **using the
REGENERATED DXF, not Fable's shipped sample.** The originals were validated
against Chief; **the regenerated ones, after the `STD_T` rewiring, have not
been.**

**FOUR — DELETE THE SPENT BRANCHES.** All are fully merged into `origin/main` or
empty:

| branch | why |
|---|---|
| `d74-vessel-enclosure-split` (local + `origin/`) | merged at PR #31 |
| `mailbox-0050` | merged |
| `worktree-agent-ad21268cb702f63d7` + its worktree | **0 commits — the work landed elsewhere.** `git worktree remove` (it is *locked*, so unlock or force) |
| `origin/d74-decoration-channel` | merged, PR #27 |
| `origin/i15-outline-completeness` | merged |

> **A merged branch left standing is not harmless here — it is a place a future
> reader or agent can check out and find a stale mailbox**, which is
> [`0040`](0040-ruling.md) §4 and [`0045`](0045-ruling.md) §2's fault class with
> the branches still lying around to cause it again.

## 3. AND THE NUMBERING FIX IS NOW OWED, NOT OPTIONAL

[`0051`](0051-ruling.md) §4 ruled it and the collision happened anyway, because
the agent was already running:

> **A worktree agent does not take a handoff number and does not land a handoff
> file. The parent reserves the number before launching and lands the report on
> `main` afterwards.**

**`0050-report.md` is already committed and cited, so it is NOT renamed** —
[`0040`](0040-ruling.md) §4's judgement stands, and the suffix split means
nothing was lost. **What changes is the next launch.**

## 4. WHAT REMAINS AFTER ALL OF THIS

**Nothing is then in flight except Patrick's Chief check.** The board is:

1. **The DXF check** — Patrick's, blocking its PR.
2. **[`0019`](0019-ruling.md)'s `STATUS.md`** — GREEN, read-back first, still not built.
3. **Grid snap and its owed read-back** — *"the largest daily-use improvement left"*, untouched since 2026‑08‑14 and now the oldest item on the board by a week.
4. **The cross-floor snap** — [`0038-report`](0038-report.md) refuted the suspect; [`0037`](0037-ruling.md) §3's narrowed Qt-reachability census is still owed, and Patrick's `crossfloor-snap-2026-08-17.json` is in `fixtures/incoming/` waiting on it.

> **Item 4 is the one a user actually hits while working**, and it has been open
> since Sunday behind two features. **Worth saying out loud rather than letting
> it sit behind the queue's own momentum.**

## 5. TIER

**Merges and branch deletion: GREEN**, both already ruled. **The DXF check:
AMBER, Patrick's.**
