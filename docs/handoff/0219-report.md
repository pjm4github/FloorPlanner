# 0219 — report: PR #74 merged on his word — the legacy converter, the v2 docs, whole-line replay and the recorder window's line numbers; the macro spec's six tasks are done

**Code, 2026‑10‑05.** The record ([`0197-ruling.md`](0197-ruling.md) §7).
[`0218`](0218-report.md) put the branch to him for his check. He ran it
and said, in two messages:

> *"OK that seems to fix the bottom-up select/replay issue that I was
> seeing."*

> *"line numbers look good, push the branch and merge"*

Done as said. `macro2-convert` was pushed, [PR #74](https://github.com/pjm4github/FloorPlanner/pull/74)
opened on it, and the branch landed on `main` at **`b849dff`**,
fast-forward. GitHub shows PR #74 MERGED. The branch is deleted, local
and remote, in the same step.

## 1. WHAT HIS WORD RESTS ON — recorded as it is

He **checked two of the four things** on his own screen: the bottom-up
replay, which he reported and now finds fixed — so the mechanism
[`0218`](0218-report.md) §3 gave (a bottom-up drag ends mid-line; half a
line is a different macro) is confirmed by the fix working, not only by
the code — and the line numbers. **The converter and the docs he has not
reported on**; they are merged on his instruction and on the converter's
tests, of which the strongest is that all eight committed
existing-format `.fpm` files replay to a byte-identical plan converted.
If `--convert` misbehaves on a macro of his own, that is the first place
to look.

## 2. A STEP OF MINE HE STOPPED, said because the record briefly ran ahead

In the session of [`0218`](0218-report.md) I committed the report to
`main` saying *"one PR, for his check"* and then went to push the branch
and open that PR. He declined that step. So from `130599d` until this
merge, `main`'s report and snapshot described a PR that did not exist;
I told him so at the time. It exists now and is merged, and nothing of
0218 needs amending — but the order was mine, and the report should not
have been pushed ahead of the thing it described.

## 3. WHAT LANDED

On the merged tree: **1683 passed**, 7 deselected (`perf` lane), `ruff`
clean, gate GREEN.

| | what it is |
|---|---|
| the converter | `python fp_macro.py --convert FILE …` rewrites an existing-format macro as v2, keeps `FILE.bak`, reports what has no v2 form and leaves it in the file as a comment |
| the docs | a *Macro language v2* section in `docs/macro_language.md` |
| replay | the lines a selection touches are replayed whole, top down, however it was dragged |
| line numbers | a gutter in the recorder window, 1-based, as a v2 error counts |

**With this, `MACRO_SPEC.md` §1's six tasks are all done.**

## 4. NAMED, NOT BUILT

**The error indicator in the gutter** — his own words: *"so an error can
highlight the broken line number with an error indicator (when that
feature is added)"*. A v2 error carries its line; the existing
language's errors carry a token and no line, so that half needs a
decision when it is built.

**Named limits carried,** unchanged: a roof ridge's End-On dialog is not
recorded; zoom and pan are; a shortcut in a macro is a real shortcut;
mouse precision is one pixel; and the converter's own
([`0218`](0218-report.md) §1) — whether a `PUP` left something open
cannot be known without running it.

## 5. `fixtures/incoming/`, with ages

`single-floor-90-roof-gable-end-check.json` — his own, 2026‑10‑03, exit
not yet named ([`0205`](0205-report.md) §3). `README.md`.

**Untracked, not mine, untouched:** `gen/` and
`docs/macro-spec/grammar/gen/`; and my own uncommitted draft
`docs/WORKING_AGREEMENT.proposed.md`. The `git stash` entry of an earlier
session (`WIP on main: 863204a`) is still there, untouched.

## 6. WHAT HAPPENS NEXT

Nothing is open on a branch. On his word, any of: the error indicator
(§4); and, untouched since [`0211`](0211-report.md) §4, the D67 pair, the
four-way crossing fault, parallel walls 6″ apart merging, the status
board, and the plan in `incoming/`.

**Carried:** unchanged from [`0218`](0218-report.md).
