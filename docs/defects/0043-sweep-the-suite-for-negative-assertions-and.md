---
# permanent key, independent of GitHub
id: 43
title: "Sweep the suite for negative assertions and measure how many establish their preconditions"

# maps directly onto GitHub Issues fields
state: open
state_reason: null
labels:
  - type:task
  - area:tests
milestone: null

# ours; becomes body prose after migration
opened: null
closed: null
closed_by: null
rank: 46
related: []
state_source: row
github_issue: null
---

# D43 — Sweep the suite for negative assertions and measure how many establish their preconditions

## Record

> **Moved verbatim** from the register (`docs/CODE_REVIEW_v2.md`, the row at its
> line 111) on 2026-08-06 — not reworded, not split, not
> reformatted. The register wrote each row as one continuous argument in which
> symptom, mechanism, evidence, ruling and receipt are interleaved, so dividing
> it into sections would have meant interpreting it. See
> [`README.md`](README.md) for the section shape new records take.

**Sweep the suite for negative assertions and measure how many establish their preconditions.** Filed at P4.5 (2026‑08‑04), **argued Phase 6**, not now. The rule it follows from is in the Working agreement: *absence and prevention are indistinguishable in the result*, so a test asserting "X did not happen" passes identically whether X was prevented or never attempted — which makes negative assertions the place vacuity concentrates. **The evidence that it is worth measuring rather than assuming:** two near-misses in two days, both negative, both caught only by a human re-reading (`weld_scene == (0,0)` with nothing weldable in the scene; a watch whose first draft branched on its outcome instead of asserting it). Neither is machine-detectable — `tools/gate.py`'s vacuity check catches tautology only. **The first step is only the COUNT**, deliberately: enumerate the negative-assertion shapes (`assert not …`, `== 0`, `is None`, `not in`, `== before`), report how many are in the suite, then how many assert their preconditions, and publish the hit rate before proposing anything. A remediation plan written before the count would be sized by intuition, which is the thing this project keeps finding wrong.

## Site

`tests/` (whole suite)

## Milestone

**argued Phase 6**

## Evidence

**The count, taken 2026-08-07 (G1). This is the first step and only the first
step** — the record is explicit that a remediation plan written before the
number would be sized by intuition.

    tools/negative_assertions.py --json docs/evidence/d43-negative-assertions.json

| | |
|---|---:|
| test files | 45 |
| assertions | 1598 |
| **negative assertions** | **287** (17% of all assertions) |
| with a positive assertion earlier in the same test | 157 |
| **hit rate** | **54%** |
| **with no positive assertion at all** | **130**, across **98** tests |

By shape: `not X` 71 · `== empty` 64 · `== 0` 41 · `not in` 36 · `== before` 33 · `is None` 30 · `!=` 12

**What "establishes a precondition" means here, and why the hit rate must not be
quoted without it.** The intent — *the test proved the mechanism could have
fired before asserting that it did not* — is not decidable by a script. The
machine-checkable proxy is: does a POSITIVE assertion appear earlier in the same
test function? Both error directions were spot-checked rather than assumed:

* **Overcount was NOT observed.** Three "established" rows were sampled; all
  three asserted positively about the same subject as the negative claim. Three
  proves nothing about 157, but it is what was looked at.
* **Undercount was observed.** `test_ungrouped_walls_survive_gc` asserts only
  `counts(sc) == before`, yet establishes its precondition thoroughly **by
  construction** — build, group, move, bake, ungroup, collect. None of that is an
  assert, so the proxy calls it bare.

So **the bare list is a superset of the suspect ones**: everything genuinely
vacuous is in it, together with tests that are fine and merely quiet. That is
the right error direction for sizing a read.

**A classifier fault found and fixed by spot-checking, before any number was
quoted.** The first draft counted `assert r.returncode == 0` as negative. `== 0`
is two different claims: *this count is zero* (absence) and *this process exited
zero* (success, as positive as they come). `test_model_imports_zero_qt` was
flagged for the success check while its real negative assertion — `assert not
qt` — lives inside a string executed in a subprocess and is invisible to any AST
pass over that file. Success probes are now excluded; the count moved 291 → 287
and the bare list 135 → 130.

**The shape that concentrates the risk, from the read-first list.** Tests that
assert a *report* is empty — `check(doc, deep=True) == []`, `unwelded_ends == 0`,
`open_edges == 0` — without first asserting the input was non-empty. A document
with no walls satisfies all three.

### Proposal, sized by the number rather than by intuition

**Read 130 assertions in 98 tests. Do not touch the other
157.** At roughly two minutes per test to read and judge, that is a
half-day, not a project — and the list is enumerated in the evidence file, so it
is a work-list rather than a search. Remediation is one added precondition per
genuinely bare test, which is a smaller edit than the read that finds it.

**Still argued Phase 6**, unchanged. This step buys the ability to schedule that
work against a real number.
