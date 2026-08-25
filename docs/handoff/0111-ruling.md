# 0111 — ruling: closing out the open PRs — three, not two, and one check session

**Patrick:** *"tell me how to handle the PR and lets close that out."*

---

## 1. THE STATE, MEASURED

| branch | PR | own commits | behind `main` |
|---|---|---:|---:|
| `wall-report-id-fix` | the report's `W7 · w19` label + `WallRowList` | 4 | 3 |
| `wall-orthogonality-repair` | #37 — item C | 9 | 3 |
| `wall-label-angle-clause` | #38 — heading + deviation | 1 | **9** |

**Three, not two.** `wall-report-id-fix` is AMBER on its own tier
([`0102`](0102-report.md)) — it shows both ids, which the user sees — **so it
needs a check like the others.**

**And Code is mid-work right now:** `verify_gate.py`, `ci.yml`, `gate.py`,
`test_verify_gate_hook.py` are all modified and uncommitted —
[`0107`](0107-ruling.md)'s items in flight. **Nothing below starts until that
lands or is reverted** ([`0086`](0086-ruling.md) §1's rule, and Patrick uses no
worktree).

## 2. A STRAY THAT MUST NOT BE COMMITTED

```
floorplanner/export/plans.pdf   28,213 bytes, untracked, NOT gitignored
fp2pdf.py:624   ap.add_argument("-o", "--out", default=Path("plans.pdf"))
```

**A test that exercises the CLI without `-o` writes a PDF into the source
tree.** Same class as D72 — **a test with a side effect on the repository.**

**Delete it and gitignore `plans.pdf`**; better, **give the CLI test an explicit
`-o tmp_path/…`** so nothing is written outside the test's own directory. **One
line each, and it stops a 28 KB binary landing in a commit by accident.**

## 3. BEFORE THE SESSION — Code's four steps, in order

1. **Land or revert the in-flight [`0107`](0107-ruling.md) work.** Do not pause
   mid-edit.
2. **Land `0107`–`0110` on `main`**, doc-only. Four rulings are untracked.
3. **§2's cleanup.**
4. **Bring `main` into all three branches, re-gate each on the combined tree,
   push.** `wall-label-angle-clause` is **9 behind** — the largest gap any branch
   has carried into a check, and [`0045`](0045-ruling.md) is the record of what
   that costs.
5. **`HEAD` on `main`, `git status` clean.** Then a short ready report: branch ·
   tip · gate · behind-`main` (**must be 0**) · the question.

## 4. THE CHECK SESSION — three branches, one sitting, in this order

**`wall-report-id-fix` — first, because the other two are read through it.**

> Open `fixtures/wiscaway2026-08-09R.json`. **Edit ▸ Wall orthogonality report.**
> Does each row name a wall you can find — `W7 · w19 … at (x, y)ft` — and does
> **clicking a row select and centre that wall** on the canvas?

**`wall-orthogonality-repair` (#37) — second.**

> Same file. **Edit ▸ Repair wall orthogonality.** The preview must offer
> **five** walls, largest correction **0.041″**. **More than five, or any move
> measured in inches, is a finding — stop.** Apply, then: **does the drawing
> still look like your drawing?**

**`wall-label-angle-clause` (#38) — third, two minutes.**

> Any plan. A wall you drew straight says **nothing** about its angle. **Ctrl**-drag
> an end to 45° — still nothing. **Shift**-drag to a freehand angle — the bar
> shows `angle NNN.NNNNdeg (N.NNdeg off axis)`, and the second number is never
> `0`.

**Back to `main` between each. If anything looks wrong mid-check, stop and say
so — a check that got adjusted is not the check.**

## 5. AFTER — merge order, then the queue

**Merge in the same order, sequentially**, each taking the current `main` in and
re-gating before it merges so every re-gate sees the previous merge
([`0050`](0050-ruling.md) §3). **Delete each branch, local and remote.**

**Then, and only then:**

1. [`0107`](0107-ruling.md) §6's remainder — `--docs` in the push hook, the
   matrix to `["3.13"]`, DEEP out of local full mode
2. [`0110`](0110-ruling.md) §5 — Snap to Grid Orthogonal, then plain, then the
   disabled 15° item

**Nothing else opens a branch until these three are merged and deleted.** Three
concurrent AMBER PRs on one checker is the state
[`0072`](0072-ruling.md) §7 measured as the project's real bottleneck, and it
has rebuilt itself.

## 6. TIER

**GREEN** — sequencing. **The three checks stay AMBER and remain the merge
condition for their own PRs.**
