---
# permanent key, independent of GitHub
id: 40
title: "A missing optional dependency must degrade, not crash - the 3D popup is not built yet, and this"

# maps directly onto GitHub Issues fields
state: open
state_reason: null
labels:
  - type:task
  - area:viewer
milestone: null

# ours; becomes body prose after migration
opened: 2026-08-03
closed: null
closed_by: null
rank: 41
related: [26]
state_source: row
github_issue: null
---

# D40 — A missing optional dependency must degrade, not crash - the 3D popup is not built yet, and this

## Record

> **Moved verbatim** from the register (`docs/CODE_REVIEW_v2.md`, the row at its
> line 106) on 2026-08-06 — not reworded, not split, not
> reformatted. The register wrote each row as one continuous argument in which
> symptom, mechanism, evidence, ruling and receipt are interleaved, so dividing
> it into sections would have meant interpreting it. See
> [`README.md`](README.md) for the section shape new records take.

**A missing optional dependency must degrade, not crash — the 3D popup is not built yet, and this row is what keeps it honest when it is.** Filed with the packaging commit (2026‑08‑03). `pyqtgraph`/`PyOpenGL` are an *extra* (`pip install -e ".[viewer]"`), and `viewer/fp3d.py` is careful today: the import lives inside `make_view`, so `build_model`, `--dump` and `--obj` all run headless with neither installed — **verified: `import viewer.fp3d` succeeds on a machine with no pyqtgraph**. The risk arrives with the in-app menu action: a `View ▸ 3D…` that raises `ModuleNotFoundError` into a Qt callback is the *same failure class* as defect 26 (an exception escaping a Qt callback) and the same user-facing class as a toggle that silently does nothing — the user clicks a menu item and the app misbehaves rather than telling them something. **Required when the action is built:** catch the missing dependency at the call site and report *"3D view needs `pip install -r requirements-viewer.txt`"* through the status channel.

## Site

not yet built; `viewer/fp3d.py` (`make_view`) is already correct

## Milestone

**whichever task builds the 3D menu action**
