# 0086 — ruling: prepare the check session — Patrick checks out branches in the main tree

**Patrick will run the AMBER checks himself, in the working tree, one branch at
a time. No worktree.** That makes the state Code leaves behind the whole
precondition.

---

## 1. BEFORE CODE PAUSES — in this order

1. **Land the mailbox on `main`.** `0082`, `0083`, `0084`, `0085` are untracked
   or branch-only. Doc-only commit, per [`0084`](0084-ruling.md) §6 item 1.
2. **Finish or stash the hook work.** `verify_gate.py` and
   `test_verify_gate_hook.py` are modified right now. Land it green or revert
   it — **do not pause mid-edit.**
3. **Bring `main` into the two stale branches and re-gate each.**
   `cross-floor-align-fix` and `wall-label-fixes` are **2 commits behind**;
   `t-junction-grid-snap` is **1**. [`0045`](0045-ruling.md) is the record of
   what a check against a stale branch costs — it had to be re-run.
4. **Leave `HEAD` on `main` with `git status` clean.**

> ### A DIRTY TREE MAKES `git checkout` UNSAFE, AND PATRICK IS NOT USING A WORKTREE. CLEAN IS NOT TIDINESS HERE — IT IS THE PRECONDITION.

## 2. THE READY REPORT — short, and it is the thing Patrick works from

One table, one row per branch: **branch name · tip sha · gate verdict ·
commits behind `main` (must be 0) · the one question.** Nothing else.

Three branches this session:

| branch | question |
|---|---|
| `t-junction-grid-snap` (#36) | snap at 6″: draw then slide an interior wall — does every corner land on a 6″ line? |
| `cross-floor-align-fix` (#34) | second floor hidden: does a wall you draw jump to something you cannot see? |
| `wall-label-fixes` (#35) | a straight wall says nothing about its angle; a crooked one does not claim an exact cardinal |

**`t-junction-grid-snap` goes first** — Patrick's own reported bug, and the
least behind.

## 3. NOT IN THIS SESSION

**PR #37 (`wall-orthogonality-repair`) is excluded.** [`0084`](0084-ruling.md)
§1's `T` restore changes what the repair produces, so checking it now spends the
session on a build one commit from being different. **It joins the next one.**

**Do not hold this session waiting for the `T` work.** Three checks are ready;
the fourth is not.

## 4. TIER

**GREEN** — sequencing and a status table, no behaviour change. The checks
themselves stay AMBER and remain the merge condition for #34/#35/#36.

**After the ready report lands, Patrick pauses Code and I walk him through the
three checkouts from the state that report names.**
