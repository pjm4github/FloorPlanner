# 0043 — ruling: the gate is not too rigorous; the BAR IS ON THE WRONG EVENT

**Patrick, 2026‑08‑17:** *"Is the gate test too rigorous for the incremental
changes? … Is there a way we can do minor tests without the full gate between
fixes?"*

---

## 1. THE COST, MEASURED — the full gate runs the SAME SUITE THREE TIMES

```
Gate-OFF:  727 passed, 7 deselected in 25.23s
Gate-ON:   727 passed, 7 deselected in 32.26s
Gate-DEEP: 727 passed, 7 deselected in 35.08s
                                    ------- 92.6s of test time
```

**Plus `ruff`, plus the `--collect-only` census passes that reconcile the sums.**
Roughly two minutes, and **the 3× multiplier is the whole of it** — shadow mode
off, shadow mode on, deep invariants. **Not 727 tests. 2,181 test executions.**

**And a fast lane already exists:**

```
python tools/gate.py --quick     # ruff + OFF only  ->  ~25s
```

**3.7× faster, and it is already there.** So the answer to *"is there a way to do
minor tests without the full gate"* is **yes, and it has been all along.**

## 2. SO WHY DOES IT NOT HELP? — because `--quick` cannot be committed on

`gate.py`'s own docstring, deliberately:

> *Only a FULL-MODE run writes it. `--quick` skips two of the three gates and
> `--deep` skips two others; letting either satisfy the hook would make the guard
> weaker than the thing it guards.*

**The hook reads `.gate-result.json`. Only full mode writes it. So every commit —
including a one-line typo fix in a doc — costs the full 3× run.**

> ### THE FRICTION IS NOT THE GATE'S RIGOUR. IT IS THAT THE ONLY MODE WHICH UNLOCKS A COMMIT IS THE MOST EXPENSIVE ONE.

## 3. AND THE AGREEMENT ALREADY SAYS THE HOOK IS WRONG ABOUT THIS

[`../WORKING_AGREEMENT.md`](../WORKING_AGREEMENT.md), amended **2026‑08‑10**, in
the reviewer's own words correcting the reviewer's own phrasing:

> *"Gate each commit" is right for the case it was written for — P0.5's five
> **independent sub-fixes**, each a tree that genuinely existed. **It is wrong for
> a SERIES SPLIT FOR LEGIBILITY**, where several commits are one coherent change
> carved into readable pieces: **those intermediate trees never existed.**

**The rule was amended. The hook still enforces the pre-amendment version.** A
rule and its enforcement have disagreed for a week, and the cost has been paid
at every commit since.

## 4. THE RULING — THE BAR MOVES FROM EVERY COMMIT TO EVERY PUSH

**What the hook exists to stop, from `settings.json`'s own comment:** *"three of
the four incidents were **a claim about a gate rather than a gate**."*

> ### THAT IS A PROPERTY OF WHAT REACHES SHARED HISTORY, NOT OF EVERY LOCAL COMMIT.
>
> **A pre-push hook preserves it completely** — nothing un-gated can reach
> `origin`, CI, or a PR. **An intermediate commit is a private rollback point;
> a broken one costs nothing, and the amendment says such trees are *expected* to
> be un-runnable.**

**The shape:**

| event | requires |
|---|---|
| **commit** | a **`--quick`** result: `ruff` + OFF, ~25s. Written to the same file with `"mode": "quick"` |
| **push** | a **full-mode** result, GREEN, newer than every tracked file — **exactly today's rule, moved one event later** |

**This keeps the distinction `gate.py`'s docstring cares about** — *"you did not
run it"* and *"you ran it and it failed"* are still different, because a quick
result is still a **result**, not an absence. **What changes is only which result
suffices for which event.**

**NOT WEAKENED, AND THIS IS THE SENTENCE THAT MATTERS: nothing reaches `main`,
`origin` or CI on anything less than the full gate.** The strength is where it
always was; the *tax* moves off the twenty commits that never leave the machine.

## 5. THE FLAPPING CLAIM NEEDS ITS RECEIPT — and this project owns the instrument

**Patrick says the gate "seems to be flapping." I have no evidence either way,
and this project has a rule for exactly that:**

> *before a differential is quoted, **run the comparator twice on ONE tree**. If
> it disagrees with itself, either repeat until the distribution is the evidence,
> or compare a field that does not move — and say which you did.*

**Owed: `python tools/gate.py` twice on an unchanged tree, and the two trailers
side by side.** If the counts differ, **the test that differs is named** and it
is a defect, not a mood.

**Two things are already known and should not be re-discovered:**

* **The 7 deselected are the PERF LANE**, excluded by standing ruling — **that
  flap class is already retired**, and it is not what Patrick is seeing.
* **[D56](../defects/0056-a-macro-replay-s-final-selection-is.md) is OPEN and is
  live nondeterminism** — *"a macro replay's final SELECTION is nondeterministic
  — two answers from one `.fpm`"*, **6/6 on `main` against 8/4 on a branch**.
  **That is the first place to look**, and if the flap is real, D56 is the
  likeliest owner rather than a new record.

## 6. ONE THING NOT RULED, BUT WORTH ASKING LATER

**Does OFF / ON / DEEP need to be three full-suite runs?** Shadow mode (P1.6)
was a **migration instrument** — it verified that the scene and the document
agreed while the v5 model was being built. **The migration closed 2026‑08‑11.**

**Whether every test still needs running under shadow mode is a question with a
real answer**, and it is worth a census: how many tests can shadow mode's result
actually differ on? **Not ruled here** — it touches P1.6's guarantee, and the
answer might be "all of them." **But a 3× multiplier inherited from a closed
migration deserves the question**, which is the *migration telemetry retires with
the thing it measured* rule pointed at the gate itself.

## 7. TIER

**The hook split: GREEN** — no new semantics, and its receipt is a **fail-first**:
**a deliberately red tree must still be refused at push.** Without that
demonstration the change is indistinguishable from removing the guard.

**§5's double run: GREEN, measurement only, and it goes first** — if the gate is
genuinely flapping, that is a bigger problem than its speed.
