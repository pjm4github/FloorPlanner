---
# permanent key, independent of GitHub
id: 27
title: "CI never runs the DEEP gate, and runs on Linux only - so the whole deep invariant set is unguarded"

# maps directly onto GitHub Issues fields
state: closed
state_reason: completed
labels:
  - type:gap
  - area:tooling
milestone: null

# ours; becomes body prose after migration
opened: null
closed: 2026-08-07
closed_by: 10e13c0
rank: 28
related: [26, 28]
state_source: receipt
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

## Receipt

**The Windows leg landed 2026-08-07 (G3); the half closes when CI proves it
green, not when the job is written.** `.github/workflows/ci.yml` gains a
`windows` job: `windows-latest`, Python 3.13, `QT_QPA_PLATFORM=offscreen`,
running the suite and the shadow-mode pass. Until it existed, **nothing
automated had ever run this suite on the platform the app is primarily
developed and used on** — every job in the workflow was `ubuntu-latest`.

| | |
|---|---|
| deep half | closed at `65c4c02` (P3.8); CI calls `tools/gate.py --deep` rather than reimplementing it |
| Windows half | this job — **green on 2026-08-07**, `pytest (windows)` passed in 1m52s on run `31140126308` |

**One Python version, deliberately.** The Linux matrix already covers the 3.10
floor and 3.13; what was missing is the *platform*, not another interpreter.

**No Qt system libraries.** The PyQt6 wheels are self-contained on Windows —
which is why the Linux jobs install six apt packages and this one installs none.

Evidence before the job ran anywhere: both of its commands were run on this
Windows machine, `625 passed, 7 deselected, 1 xfailed` each. Per the roadmap, a
red Windows leg is **a finding, not a failure of this task**.

**Both halves are now closed, so the record is.** The green run is the closing
evidence, not the writing of the job — the same distinction this record's own
first draft got wrong and corrected before merge.

`closed_by` names `10e13c0`, the commit that adds the job. The deep half's sha
(`65c4c02`, P3.8) is kept in the Milestone cell above, where the register wrote
it; a record has one `closed_by` and this one closes on its later half.

`status:partial` is dropped: it exists to say "open BECAUSE one half remains",
and no half remains.
