# 0104 — ruling: the fast lane already exists and is already running; the 3× is the real cost

**Patrick:** *"Is there a way for me to expand more agents to get work done
faster? I also want to eliminate the full regression test for every small change.
I only want to do testing on new features and any code that those new features
touch."*

---

## 1. THE TEST SPLIT HE WANTS IS BUILT, AND IN USE RIGHT NOW

**Measured, from `.gate-result.json` as it sits on disk:**

```
mode: quick   collected: 881
Gate-OFF: 874 passed, 7 deselected, 2 warnings in 41.47s
```

`tools/gate.py --quick` = **ruff + one suite pass, 41 seconds.** It **unlocks a
commit**. Full mode is required **only at `git push`** — [`0043`](0043-ruling.md)
§4 ruled it, [`0047`](0047-ruling.md) §4 set the four controls,
[`0049`](0049-report.md) built it with 18 tests. **Code is already committing on
quick.**

**And pytest already selects:** `pytest.ini` carries markers, `conftest` defaults
to `not slow and not gui` during feature work, `-m geometry` / `-m "groups or
io"` work today.

> **So the policy is not the friction.** Either full mode is being run where
> quick would do — **which is a habit, not a rule** — or the friction is §3.

## 2. DO NOT DERIVE "WHAT THE FEATURE TOUCHES" — this codebase cannot answer it

**A counter-example from three days ago, in this project's own record.**
[`0079`](0079-report.md) §1 changed `wall_orthogonality()` from a 4-tuple to a
5-tuple. It broke **`orthogonality_bands()`** — *"would have raised `ValueError`
outright on a 5-tuple — caught before it shipped, not after."*

> ### THE CONSUMER WAS IN ANOTHER MODULE AND ITS TEST IN ANOTHER FILE. A "TEST WHAT IT TOUCHES" RULE CATCHES THAT ONLY IF THE DEPENDENCY MAP IS RIGHT.
>
> **Here it is not computable:** submodules use **star imports**, four **late
> imports** close the `walls↔rooms` cycle, `MainWindow` is four **mixins**, and
> `SETTINGS` is a **module-global mutable dict** every path reads.
> **A change to `config.py` touches everything, and no static map says so.**

**RULED: no change-impact test selection.** The lane that is cheap and honest is
the one that already exists — **fewer PASSES, not fewer tests.**

## 3. THE REAL COST IS THE 3×, AND IT SHOULD BE MEASURED BEFORE IT IS CUT

```python
GATES = [
    ("OFF ", {},                                ["-m", "not perf"]),
    ("ON  ", {"FP_VERIFY_DESIGN": "1"},         ["-m", "not perf"]),
    ("DEEP", {"FP_VERIFY_DESIGN": "deep"},      ["-m", "not perf"]),
]
```

**Full mode is the same suite three times at three shadow-verifier strengths** —
~41 s each, ~2 minutes, which is [`0043`](0043-ruling.md) §1's *"92.6 s of 3×
test time"* that once read as a flap.

**OWED, GREEN, and it is a measurement not a guess:**

> **How many times has `ON` or `DEEP` gone RED while `OFF` was GREEN?** The gate
> has been writing `.gate-result.json` for weeks and CI keeps its logs.
> **If the answer is "often", the 3× is buying what it costs. If it is "never",
> DEEP belongs on push and CI only, and full mode drops to two passes.**
>
> **Do not cut it on the strength of it being slow.** P1.6's shadow verifier is
> the thing that catches document-model faults the unit tests do not.

## 4. AGENTS — where it pays, and the precondition that is NOT done

**It pays for read-only work**, which is most of what this project does before
it builds: censuses, bisects, corpus sweeps, audits. Those fan out cleanly and
their output never collides.

**It pays for GREEN items on disjoint files** — the `CLAUDE.md` trim beside a
code fix.

**It does not pay for AMBER.** Two agents produce two PRs that stop for **one
person's eyes.** The queue that stalled this project twice was never Code's
hands — [`0072`](0072-ruling.md) §7 measured it four deep on Patrick.
**Parallel AMBER work makes that worse, faster.**

**Three preconditions, all already ruled, one NOT done:**

| | |
|---|---|
| **per-task progress files** | **NOT DONE** — `docs/progress/` is still phase-named. `ROADMAP.md` §1 measured that the **only** merge conflicts in the whole GREEN batch were in the shared append-only progress file. **This is the blocker** |
| **separate worktrees** | one exists (`.claude/worktrees/agent-…`). **Proven necessary this week** — a shared working tree gave us a stale `index.lock` and a branch Patrick could not check out |
| **no number, no mailbox** | [`0051`](0051-ruling.md) §4 already rules it: a worktree agent takes no handoff number and lands no mailbox file; **the parent reserves and lands** |

## 5. TIER AND ORDER

| | | |
|---|---|---|
| 1 | **§4 — per-task progress files** | **GREEN.** The named blocker; nothing parallel starts before it |
| 2 | **§3 — the ON/DEEP measurement** | **GREEN.** Then a ruling on the 3×, not before |
| 3 | **Parallel agents on read-only work** | **GREEN** once 1 lands |
| 4 | **§1 — commit on `--quick` by default** | **already the rule.** If Code is running full on every commit, stop |
| 5 | **§2 — change-impact selection** | **refused**, with §2's reason |
