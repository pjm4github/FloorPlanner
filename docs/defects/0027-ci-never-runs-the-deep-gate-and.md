---
# permanent key, independent of GitHub
id: 27
title: "CI never runs the DEEP gate, and runs on Linux only - so the whole deep invariant set is unguarded"

# maps directly onto GitHub Issues fields
state: open
state_reason: null
labels:
  - type:gap
  - area:tooling
  - status:partial
milestone: null

# ours; becomes body prose after migration
opened: null
closed: null
closed_by: 65c4c02
rank: 28
related: [26, 28]
state_source: row
github_issue: null
---

# D27 — CI never runs the DEEP gate, and runs on Linux only - so the whole deep invariant set is unguarded

## Record

> **Moved verbatim** from the register (`docs/CODE_REVIEW_v2.md`, the row at its
> line 93) on 2026-08-06 — not reworded, not split, not
> reformatted. The register wrote each row as one continuous argument in which
> symptom, mechanism, evidence, ruling and receipt are interleaved, so dividing
> it into sections would have meant interpreting it. See
> [`README.md`](README.md) for the section shape new records take.

**CI never runs the DEEP gate, and runs on Linux only — so the whole `deep` invariant set is unguarded by automation.** From `.github/workflows/ci.yml`, not from memory: the shadow-mode step sets `FP_VERIFY_DESIGN: "1"` (the cheap twelve) and there is no `deep` step; every job is `runs-on: ubuntu-latest`. So P1.2's three O(n²) invariants — I5b, I11, I14, the two that caught the real corruption in `planc1.json` — are checked only by whoever runs the local gate by hand. **This is why defect 26 could be introduced and survive a green CI**: CI would not have run the gate that crashes, and would not have run it on the platform it crashes on. Filing it separately because it is a gap in the automation regardless of 26's fate, and because a Windows-only crash still matters — the app's primary development and use platform is Windows, so the severity does not drop with the repro environment, only the audience that sees it.

## Site

`.github/workflows/ci.yml`

## Milestone

**DEEP HALF CLOSED at `65c4c02` (P3.8); WINDOWS HALF OPEN, its own task.** The deep job runs `python tools/gate.py --deep` — CI calls the local gate rather than reimplementing it, so the invariant set, the perf exclusion and the census reconciliation are defined once and cannot drift apart. **It could not have landed earlier:** under `deep` a violation aborted the process (defect 26), so the job would have been red by design; defect 26's guard made it possible, defect 28's fixes made it reliable, and P3.8's perf exclusion keeps it deterministic on a shared runner. **Single py3.13 leg, stated as a choice** — the deep set is pure-Python invariant checking over the document the existing matrix job already exercises on both versions. **First green run: [30592873265](https://github.com/pjm4github/FloorPlanner/actions/runs/30592873265)**, and its census is byte-identical to the local Windows gate (`510 passed, 7 deselected, 5 xfailed`, sum 522) — the first cross-platform confirmation this branch has had. **The windows-latest half stays open as its own task:** the app's primary platform is Windows and the abort that started all this was Windows-only, so it is desirable — but it is explicitly NOT merge-blocking.
