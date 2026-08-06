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
