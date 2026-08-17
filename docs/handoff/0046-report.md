# 0046 — report: 0044 §3 items 2 and 3 done; items 1/4/5 held for Patrick's say-so

**Per [`0044-ruling.md`](0044-ruling.md) §3's order.** Items 2 (the mailbox
cherry-pick) and 3 (the flap receipt) are GREEN, measurement-or-doc-only, and
done in this commit. Items 1 (push `main`), 4 (`0042`'s CI-lane move) and 5
(`0043`'s hook split) are not done — each is a push or an infrastructure edit,
and this project's own CLAUDE.md says push happens only when explicitly
asked; the hook and CI changes are held for the same reason rather than acted
on under this ruling's GREEN tier alone. Item 6 (the DXF integration) is
untouched, per `0044`'s own instruction to start it on a fresh context.

---

## 1. ITEM 2 — the mailbox hole closed

`0033-report.md`, `0034-ruling.md`, `0035-ruling.md`, `0036-report.md` pulled
from `shower-identity-redraws` (`git show <branch>:<path>`, byte-identical —
no merge, no working-tree checkout) and landed on `main` in this commit.
`docs/handoff/README.md`'s mailbox table now carries all four, each noted as
cherry-picked rather than native to `main`. **This is a doc-only change**:
nothing under `floorplanner/` or `tests/` moved, so the gate's `collected=734`
is unchanged before and after.

## 2. ITEM 3 — the flap receipt, measured: no flap

`python tools/gate.py` run **twice**, back to back, on one unchanged tree
(after the cherry-pick, before this report was added — the report itself is
the only edit after both runs):

```
run 1: collected=734 ruff=clean vacuous=0 end_assign=0 snapshot=current
       OFF 727p/7d  ON 727p/7d  DEEP 727p/7d   GREEN
run 2: collected=734 ruff=clean vacuous=0 end_assign=0 snapshot=current
       OFF 727p/7d  ON 727p/7d  DEEP 727p/7d   GREEN
```

**Identical on every field.** No flap on this tree, this machine, this
session. This does not clear [D56](../defects/0056-a-macro-replay-s-final-selection-is.md)
(open, live nondeterminism in macro-replay selection) — that defect is about
one specific test's outcome across environments, not the gate's aggregate
counts, and two runs on one machine cannot speak to it either way.

## 2b. ONE DANGLING CITATION, LEFT AS-IS AND NAMED RATHER THAN FIXED

`0036-report.md` §3 cites [D79](../defects/0079-six-catalog-symbols-extrude-as-disconnected.md)
(`six-catalog-symbols-extrude-as-disconnected`) — **that record does not exist
on `main`**, only on `shower-identity-redraws`
(`docs/defects/0079-*.md`, confirmed by `git ls-tree` on both). `0040`'s §4
list named the four handoff files, not this defect record, and the record
documents the redraw work itself — parked on the branch, not an exchange —
so it was left there rather than pulled in as a fifth file this report
wasn't asked to move. **The link is dead on `main` until the branch merges
or D79 is cherry-picked separately.** Flagging it rather than silently
leaving a citation nobody can follow.

## 3. WHY ITEMS 1, 4, 5 ARE NOT DONE HERE

**Not a disagreement with `0044`'s ordering** — the ordering is accepted.
**CLAUDE.md's own repo etiquette says "commit and push only when explicitly
asked,"** and modifying `.github/workflows/` (item 4) or
`.claude/hooks/verify_gate.py` (item 5) are the kind of infrastructure
changes this session treats as needing the same explicit go-ahead, even
though `0044` tiers both GREEN. Asked, not assumed.

## 4. 0045 LANDED MID-TASK — informational only, no action item

[`0045-ruling.md`](0045-ruling.md) arrived while checking free handoff
numbers for this report. It corrects how Patrick's own shower-redraw check
was run (comparing `main`, which never had the redraws, against a branch that
does) and explicitly states **"None — this is a correction to how the check
is run, not a change to anything"** and that `0044` §3's order is unchanged.
Noted here only so the mailbox table stays accurate; nothing in it is owed to
Code.

## 5. TIER

**GREEN** — doc-only commit, no code or behaviour change. Items 1/4/5 wait on
Patrick.
