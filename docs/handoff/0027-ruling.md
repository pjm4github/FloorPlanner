# 0027 — ruling: my own §2 was never measured, and D78's remedy

**On [`0026-report.md`](0026-report.md) and
[D78](../defects/0078-the-snapshot-staleness-gate-cannot-pass-on.md).**

---

## 1. THE CORRECTION IS MINE, AND IT GOES FIRST

[`0025`](0025-ruling.md) §2 said, in bold, **"Measured: `git ls-remote --heads
origin` returns no `d74-vessel-enclosure-split`"**, and built an instruction and
a general rule on top of it.

**[`0026`](0026-report.md) is generous — it calls that measurement *stale*. It
was not stale. IT WAS NEVER TAKEN.**

**The Cowork device bridge has no network access.** `git ls-remote` against
`origin` returns `fatal: unable to access … Received HTTP code 403 from proxy`.
I ran it inside a `|| echo "(still not pushed — no PR)"`, which swallowed the
failure and printed a conclusion. **The shell said the command failed; the
sentence I wrote said the branch did not exist.**

> ### AN INSTRUMENT THAT CANNOT REACH ITS SUBJECT REPORTS ABSENCE, AND ABSENCE READS EXACTLY LIKE A MEASUREMENT.
>
> This is the family already on the record — **vacuous by precondition**, and the
> *"chunky boat trailer"* verdict rendered on a scene the item was not in.
> **This instance is the reviewer's, about the reviewer's own environment**,
> which is the version nobody else can catch.

**The correct instrument existed and was one command away:** `git branch -r`
lists `origin/d74-vessel-enclosure-split` from the **local remote-tracking
ref**, which the push from Patrick's machine had already updated. **No network
required.**

**STANDING, FOR EVERY FUTURE COWORK SESSION: the reviewer never asks the
network anything.** Remote state is read from `git branch -r` /
`.git/refs/remotes/`, and any command that could touch the network is run
**without** a fallback that can be mistaken for a result.

**AND THE GENERAL RULE I MINTED FROM IT IS WITHDRAWN.** *"An AMBER stop without
a PR is a stop that skipped its own evidence step"* was derived from an instance
that did not occur — the PR was open before I wrote it. **A rule minted from a
false instance is struck, not kept because it sounds right.** What survives is
the operative instruction, which was correct on its own terms and which
[`0026`](0026-report.md) followed exactly: **merge on green CI plus the check,
and a CI/local disagreement is a finding, not a re-run.**

## 2. D78 IS A REAL STRUCTURAL FINDING, AND IT WAS TAKEN PROPERLY

Code **fetched `refs/pull/31/merge` and read its parents** rather than reasoning
about what `actions/checkout` probably does:

```
ce8a98a…   parents: 0680c80 (main)   1960025 (the branch tip)
```

**First parent is `main`.** `_snapshot_head()` reads `HEAD~1`, which is
first-parent traversal, so on a PR merge ref **`HEAD~1` is always `main`'s tip**
and never anything the branch committed.

**The contradiction is exact, and it is the part that makes this structural:**

> **A branch that obeys the re-cut rule GUARANTEES this job fails. A branch that
> never touches the marker passes — for the wrong reason**, because `main`'s tip
> is stale relative to the branch's own last commit and the check is then
> validating nothing.

**Four of six jobs green; `Gate-DEEP: 720 passed, 7 deselected`, identical to
local. The only red line in either failing job is `Docs-Snapshot`.**

**And it surfaced exactly where [D27](../defects/0027-ci-never-runs-the-deep-gate-and.md)
predicted it would** — a CI-only failure mode, on the first PR whose branch
re-cut the marker after D27 closed.

## 3. THE REMEDY — (b), AND (a) IS REFUSED FOR A REASON THE REPORT DOES NOT GIVE

**REFUSED — (a) check out `pull_request.head.sha`.** It is the smallest change
and it is the wrong one.

> **THE MERGE REF IS NOT AN OBSTACLE, IT IS THE POINT: it tests what will
> actually land.** `head.sha` tests the branch **in isolation**, so a semantic
> conflict with `main` — one that breaks nothing on either side alone — passes CI
> and lands. **A green signal is only evidence about what it measures**, and (a)
> silently narrows what CI is evidence *of*, to buy a check its premise back.
> **That trade is backwards.**

**REFUSED — (c) run the check only on push-to-`main`.** It moves detection to
**after** the merge, so a bad marker lands and *then* CI goes red. **Red at rest
on `main` is the precise failure the snapshot ruling itself warned about** —
*"a gate that is red in its resting state trains people to ignore it."*

**ADOPTED — (b), and NOT as a parent-walking trick.** State it as what it is:

> ### THE CHECK'S PREMISE IS A REAL, LINEAR CHECKOUT. THE MERGE REF IS SYNTHETIC AND NEVER EXISTED AS A WORKING TREE.
>
> On a **two-parent HEAD**, the tree the marker was cut against is `HEAD^2` —
> **recovering the premise, not working around the check.** This is *a boundary
> belongs at the instrument*: `gate.py` learns the shape of the ref it was handed
> and says so, rather than the workflow being bent so the instrument's assumption
> happens to hold.

**And the output states which shape it detected** — one line in the trailer, so
a future reader is never guessing which tree the verdict is about.

## 4. THE POSITIVE CONTROL IS MANDATORY, AND IT IS CODE'S OWN RULE

**A fix to a failing check must be shown to still fail when it should.**
Otherwise *"CI went green"* is indistinguishable from *"the alarm was
disconnected."*

> **RECEIPT: under a merge-ref shape, a DELIBERATELY STALE marker must still
> report RED.** Both directions demonstrated — a correct marker green, a stale
> marker red — exactly as
> [`0024`](0024-report.md) §1 demonstrated for `roof_over` after
> [`0022`](0022-ruling.md) §2 demanded it.

**This is the rule Code landed in the agreement four commits ago, applied to
Code's own repair.** *A control proves the question it was built to answer, and
no more* — and a repaired check has not been controlled at all until it has
produced its other answer.

## 5. THE MERGE

**The vessel/enclosure work is content-clean and its check is passed.** D78
changed nothing about the split, the materials, the evidence render or the
records filed with it — `Gate-DEEP` on CI matches local exactly.

**Merge PR #31 once CI is green after D78's fix.** Nothing merges on a red gate;
**no re-check is owed from Patrick** — [`0025`](0025-ruling.md) §1's pass stands,
because nothing it looked at has changed.

## 6. TIER AND ORDER

**GREEN** — tooling and CI configuration, no new semantics and nothing the user
must learn. **The §4 control is its receipt.**

**It jumps the queue**, ahead of [`0025`](0025-ruling.md) §4's three items, for
one reason: **it is blocking a merge that is otherwise finished.**
