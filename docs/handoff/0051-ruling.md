# 0051 — ruling: the worktree agent is the right call, and it will reproduce two problems we fixed today

**Code has launched an isolated agent in its own git worktree for
[`0038`](0038-ruling.md)'s DXF integration.** Measured:

```
/…/FloorPlanner                                  54b4a88 [main]
C:/dev/GitHub/FloorPlanner/.claude/worktrees/
              agent-ad21268cb702f63d7            54b4a88 [worktree-agent-…] locked
```

**Approved — and two things are structurally guaranteed to go wrong unless the
parent handles them.** Written now rather than after, because the work is
running.

---

## 1. FIRST, WHAT IS ALREADY RIGHT

**[`0038`](0038-ruling.md) §3's thickness ruling is DONE and done properly.**
`floorplanner/export/fp2dxf.py` now:

```python
#: THE NORMATIVE thickness table, read live from floorplanner.design.validate
STD_T = _load_std_thickness()      # loaded BY PATH, via importlib
```

with the reason in its own docstring — *"seven entries had already drifted from
`STD_T` before this module had…"* — **and the by-path load rather than an
import, so the Qt bindings are not dragged in.** That is the ruling, the
mechanism and the evidence, in the file that has to obey it.

**And the isolation is the right shape for this task**: a 554-line module, a
README split, a menu item, screenshots and a golden-file test is exactly the kind
of chunk that should not share a context with anything else.

## 2. IT WILL COLLIDE ON THE NUMBER — structurally, not by bad luck

**The worktree forked at `54b4a88`. `0050-ruling.md` is UNTRACKED on `main`**, and
a worktree has its own working directory. **So the agent cannot see it.**

**The highest number it can see is `0049`. It will take `0050`.**

> **This is collision cause #1 —** [`0044`](0044-ruling.md) §1's *"two writers who
> cannot see each other's work in progress"* — **made certain rather than
> probable.** An isolated worktree is a writer that is isolated *by design*.

**Harmless in itself**, because the suffix split holds: `0050-report.md` and
`0050-ruling.md` can coexist. **But it is avoidable, and the fix generalises.**

## 3. IT WILL PUT ITS REPORT ON A BRANCH — the thing we cherry-picked four files to undo

**[`0040`](0040-ruling.md) §4, ruled this afternoon: *the mailbox is a record, not
work product. It lives on `main`, always, and never on a feature branch.***

**An agent working in its own worktree, on its own branch, will write its report
there.** `0033`, `0034`, `0035` and `0036-report` were cherry-picked onto `main`
today for exactly this. **This would be the third instance, four hours later.**

## 4. THE RULE — the PARENT owns the number and the mailbox; the agent owns the work

> ### A WORKTREE AGENT DOES NOT TAKE A HANDOFF NUMBER AND DOES NOT LAND A HANDOFF FILE.
>
> **Before launching:** the parent session **reserves the number** from `main` and
> tells the agent which one to use.
> **On completion:** the parent **lands the report on `main`** as a doc-only
> commit, whatever branch the work itself sits on.
>
> **The agent's isolation is about CONTEXT, not about the record.** It should be
> unable to see the conversation. It should not be unable to see the mailbox.

**Retrofit for the run already in flight — no interruption:**

1. **Let it finish.** Interrupting a locked worktree mid-task costs more than the
   collision does.
2. **When it reports, the parent renumbers if needed and lands the report on
   `main`.** If it took `0050`, the file becomes the next free number **at land
   time, before it is cited anywhere** — which is the one moment renaming is
   free, and the reason [`0040`](0040-ruling.md) §4 refused it for already-cited
   files does not apply.

## 5. THE COST OF ISOLATION NOBODY HAS NAMED YET

**The agent cannot be reached.** It reads the tree it forked from; **any ruling
written while it runs is invisible to it**, and Patrick relaying one by hand is
the thing the channel contract retired.

> **SO AN ISOLATED AGENT MUST BE LAUNCHED WITH A COMPLETE BRIEF, AND ITS RULING
> MUST BE FINISHED BEFORE IT STARTS.** [`0038`](0038-ruling.md) is unusually
> complete — placement, the thickness mechanism, three named hygiene faults, the
> README split, the golden test — **which is why this is safe here.** It would
> not be safe for an exploratory task where the ruling expects to be revised.
>
> **The tell: if a task's ruling is likely to need a mid-course correction, it
> must not go to an isolated agent.**

## 6. WHAT I EXPECT TO REVIEW, AND ONE THING NOT TO ACCEPT

**Per [`0038`](0038-ruling.md) §7, the golden-file test is the receipt** — and
because §3's rewiring changes the numbers, **the regenerated `L1.dxf`/`L2.dxf`
must ship with a STATED DIFF against the originals Fable shipped.**

> **"Regenerated to match the new thickness" is not a receipt. The diff is.**
> `exterior 6.5 → 6.0`, `railing 3.0 → 2.0`, `fence 1.5 → 2.0`, `hedge 24 → 18`
> move every wall face line by a known amount, **and the golden files should show
> exactly that and nothing else.** An unexplained third change in those files is
> a finding.

**Tier unchanged: AMBER, stop at an open PR.** Code was right that the acceptance
check needs Patrick and Chief Architect, which no agent here can run.

## 7. NUMBERING OF THIS FILE

**`0051`, taken with `0050` knowingly in use by me and probably by the agent.**
Named so the next reader is not puzzled by the gap.
