---
# permanent key, independent of GitHub
id: 40
title: "A missing optional dependency must degrade, not crash - the 3D popup is not built yet, and this"

# maps directly onto GitHub Issues fields
state: closed
state_reason: completed
labels:
  - type:task
  - area:viewer
milestone: null

# ours; becomes body prose after migration
opened: 2026-08-03
closed: 2026-08-03
closed_by: 0a37581
rank: 41
related: [26]
state_source: receipt
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

## Receipt

**Closed 2026-08-06, in its own commit, after the docs refactor migrated it
open.** The condition this record set was met on 2026-08-03 and the row was
never ticked; the refactor found the gap and, per the rule below, did not fold
the correction into the move.

The record required, verbatim: *"catch the missing dependency at the call site
and report **\"3D view needs `pip install -r requirements-viewer.txt`\"**
through the status channel."* On disk:

| | |
|---|---|
| `floorplanner/mainwindow.py:532` | `VIEWER_HINT = ("3D view needs pip install -r requirements-viewer.txt")`, used by `show_3d_view` |
| `tests/test_viewer_popup.py:139` | `assert "requirements-viewer.txt" in win.statusBar().currentMessage()` |
| `floorplanner/app.py:27` | the `try/except ImportError` guard, so the editor still starts without the 3D stack |
| `0a37581` | *3D view popup: the same widget the CLI ships, opened read-only* — merged at PR #8, 2026-08-03 |

The message is the one the record specified, at the call site the record
specified, in the channel the record specified, and a test asserts it. The
`## Milestone` cell above still reads "whichever task builds the 3D menu action"
and the `## Site` cell still reads "not yet built": **both were true when
written and are left as written**, because this record annotates rather than
rewrites. This section is the annotation.
