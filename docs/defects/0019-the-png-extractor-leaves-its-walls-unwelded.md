---
# permanent key, independent of GitHub
id: 19
title: "The PNG extractor leaves its walls unwelded - and it has TWO arms"

# maps directly onto GitHub Issues fields
state: closed
state_reason: completed
labels:
  - type:defect
  - area:io
milestone: null

# ours; becomes body prose after migration
opened: null
closed: null
closed_by: null
rank: 33
related: []
state_source: status-table
github_issue: null
---

# D19 — The PNG extractor leaves its walls unwelded - and it has TWO arms

## Record

> **Moved verbatim** from the register (`docs/CODE_REVIEW_v2.md`, the row at its
> line 98) on 2026-08-06 — not reworded, not split, not
> reformatted. The register wrote each row as one continuous argument in which
> symptom, mechanism, evidence, ruling and receipt are interleaved, so dividing
> it into sections would have meant interpreting it. See
> [`README.md`](README.md) for the section shape new records take.

**The PNG extractor leaves its walls unwelded — and it has TWO arms.** Detected walls are written out with no weld pass, and per the corrected **F5** nothing welds them afterwards either, because load doesn't and coalesce doesn't. So every extracted plan is born with open junctions — precisely the condition that leaks room detection between spaces. Measured at P1.6: 2 unwelded ends on the `test_extract` fixture. **File arm:** `fp_extract.py` writes a plan file which is later opened — closes automatically once P2.1 welds on load. **In-app arm:** `extract_from_reference` (`mainwindow.py:1644`) injects walls *directly into the live scene* and commits, bypassing every load path, so **P2.1's weld-on-load never sees them**; this arm needs an explicit weld pass after the detected walls are written. Ride it with P2.1 — closing only the file arm would leave the exact reported reproduction alive. Not caught by shadow mode either (an `unwelded_ends` rise is report-only: the 9″ tolerance is a gesture, not an invariant), so it must be fixed on purpose rather than by a gate.

## Site

`fp_extract.py`; `mainwindow.py:1644` (`extract_from_reference`)

## Milestone

**P2.1 (both arms)**
