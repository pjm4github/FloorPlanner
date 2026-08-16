---
# permanent key, independent of GitHub
id: 78
title: "The snapshot-staleness gate cannot pass on a PR's default merge-ref checkout"

# maps directly onto GitHub Issues fields
state: closed
state_reason: completed
labels:
  - type:defect
  - area:tooling
milestone: null

# ours; becomes body prose after migration
opened: 2026-08-15
closed: 2026-08-16
closed_by: null
rank: 78
related: [27]
state_source: row
github_issue: null
---

# D78 — The snapshot-staleness gate cannot pass on a PR's default merge-ref checkout

**Found on PR #31** (`d74-vessel-enclosure-split`), per
[`handoff/0025-ruling.md`](../handoff/0025-ruling.md) §2's instruction to push,
open the PR, and merge on green CI plus the check. CI came back RED on two of
six jobs; this is that finding, reported rather than resolved by re-running,
per the same ruling's own words: *"if CI disagrees with the local gate, that
disagreement is a finding and comes back as a report — it does not get
resolved by re-running until green."*

## The finding

**`records (gate --docs)` and `pytest deep invariants (py3.13)` both failed
CI, and both failed for the identical, single reason:**

```
Docs-Snapshot: RED -- docs/SESSION_SNAPSHOT.md was cut against bf22ee2,
which is neither HEAD (ce8a98a) nor its parent.
```

**`ce8a98a` is not this branch's tip.** `actions/checkout@v5`, with no `ref:`
override, checks out `refs/pull/31/merge` on a `pull_request` trigger — a
synthetic commit GitHub builds by merging the PR branch into the base.
Measured directly (`git fetch origin pull/31/merge`,
`git log -1 --format="%H %P"`):

```
ce8a98a6...  0680c80c... (main)  1960025...   (this branch's own tip)
```

**Two parents, in that order — first parent is `main`, not the branch.**
`gate.py`'s `_snapshot_head()` reads `HEAD` and `HEAD~1`, where `~1` is
git's first-parent traversal. On this ref, `HEAD~1` is therefore **always
`main`'s current tip**, never anything the feature branch itself committed.

**Everything else in both failing jobs is clean.** `Gate-DEEP: 720 passed, 7
deselected` — identical to the local run. `Docs-Defects`, `Docs-Index`,
`Ref-Audit`, `Ref-Ids`, `Docs-GitHub` all report the same numbers CI's own
`--docs` lane printed moments earlier in the passing local run. **The only
red line in either job is `Docs-Snapshot`.**

## Why this is structural, not a one-off mismatch

**The re-cut rule and the CI checkout model contradict each other.** The
standing rule (`SESSION_SNAPSHOT.md`'s own re-cut instruction, and the gate's
own design intent) is: point the marker at the tip of the branch doing the
work, one commit of slack. But on the default PR checkout, the check's
`HEAD~1` is the BASE branch's tip, which is unrelated to the feature branch's
own commit history and does not advance as the feature branch gains commits.

**So the marker can only satisfy CI's version of this check by equalling
`main`'s current commit — i.e., by NOT being re-cut for the branch's own
work at all.** A branch that follows the re-cut rule correctly (as this one
did, twice, for two legitimate reasons) **guarantees** this CI job fails,
regardless of whether the branch's own state is fresh. A branch that never
touches the marker would coincidentally pass, for the wrong reason —
`main`'s tip is stale relative to the branch's actual last commit, and the
check would be validating nothing.

**Nothing about local `python tools/gate.py` catches this**, because a local
checkout has no merge-ref shape to synthesize — `HEAD` and `HEAD~1` are
always the real, linear commit history of whatever is checked out. This is
exactly the CI-only failure mode [D27](0027-ci-never-runs-the-deep-gate-and.md)
was closed to surface, on the first PR whose branch re-cut the marker after
D27 closed.

## What this is not

Not a flaky test, not a real invariant failure, not anything wrong with the
vessel/enclosure split, the evidence render, or the records filed alongside
it (D75, D76, D77) — all of those are exactly as the local gate and 0025's
check confirmed.

## Ruling

Filed 2026‑08‑15, on Code's own report,
[`handoff/0026-report.md`](../handoff/0026-report.md), with three candidate
remedies and none chosen. **Ruled 2026‑08‑16, [`handoff/0027-ruling.md`](../handoff/0027-ruling.md)
§3 — (b) adopted, (a) and (c) refused.** (a) (check out
`pull_request.head.sha` explicitly) was refused because it changes what CI is
*evidence of* — a semantic conflict with `main` that breaks nothing on either
branch alone would then pass and land. (c) (push-to-`main` only) was refused
because it moves detection to after the merge, reproducing the exact
red-at-rest failure the staleness ruling itself warns against. **(b)**:
`_snapshot_head()` (`tools/gate.py`) now detects a merge commit via `git
rev-parse HEAD^@` (all parents, one call, no history walk) and, when `HEAD`
has two or more parents, reads `HEAD^2`/`HEAD^2~1` instead of `HEAD`/`HEAD~1`
— recovering the real, linear checkout the check was written for, since
`HEAD^2` is the branch's own tip on a `refs/pull/N/merge` ref, not the
synthetic merge commit. The shape detected is now printed as its own trailer
line, `Docs-Snapshot-Shape: linear` or `merge (using HEAD^2, the branch's
own tip)`.

## Receipt

**Both directions demonstrated on a REAL two-parent git commit**, per
[`0027`](../handoff/0027-ruling.md) §4's own instruction that a repaired
check is uncontrolled until it has produced its other answer too —
`tests/test_gate.py::test_a_merge_ref_checkout_with_a_correctly_cut_marker_is_GREEN`
and `::test_a_merge_ref_checkout_with_a_STALE_marker_is_RED` each build a
throwaway repo (`git init`, a root commit, a `feature` branch, `git merge
--no-ff` to reproduce the exact `[base, head]` parent order measured on PR
#31's own `refs/pull/31/merge`), check out the merge commit detached — the
same state CI's `actions/checkout@v5` produces — and run the real
`_snapshot_head()` against it: a marker cut against the branch's own parent
passes, a deliberately unrelated marker fails, both correctly attributed to
the `merge` shape in the trailer. All 9 tests in `tests/test_gate.py` pass,
the 7 pre-existing ones unchanged.
