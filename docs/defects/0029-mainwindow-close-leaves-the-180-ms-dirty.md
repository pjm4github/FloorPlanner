---
# permanent key, independent of GitHub
id: 29
title: "MainWindow.close() leaves the 180 ms dirty timer running"

# maps directly onto GitHub Issues fields
state: closed
state_reason: completed
labels:
  - type:defect
  - area:ui
milestone: null

# ours; becomes body prose after migration
opened: null
closed: null
closed_by: null
rank: 27
related: [26, 28]
state_source: row
github_issue: null
---

# D29 — MainWindow.close() leaves the 180 ms dirty timer running

## Record

> **Moved verbatim** from the register (`docs/CODE_REVIEW_v2.md`, the row at its
> line 92) on 2026-08-06 — not reworded, not split, not
> reformatted. The register wrote each row as one continuous argument in which
> symptom, mechanism, evidence, ruling and receipt are interleaved, so dividing
> it into sections would have meant interpreting it. See
> [`README.md`](README.md) for the section shape new records take.

**`MainWindow.close()` leaves the 180 ms dirty timer running**, so a closed window goes on walking the whole document — snapshotting, verifying, and (before defect 26's guard) able to abort the process. Found as the app half of defect 28's leak. A user who closes one plan window while another is open pays a full document walk every 180 ms for a window they believe is gone, forever. Deliberately filed SEPARATELY from 28: it is a behaviour change in the app and must not be slipped in under a test-isolation fix. **FIXED at P3.6-followup, minimal scope:** `closeEvent` stops the timer, and only once the close is **accepted** — a close the user cancels must leave the window exactly as it was, debounce included, or the edit in flight when they hit the X never becomes an undo step. Pinned by `test_undo.py::test_closing_a_window_stops_its_dirty_timer`, which builds its window directly (the `win` fixture now destroys its own, which would hide the app behaviour under test) and asserts the precondition — that the edit actually started the debounce — before asserting the fix. **Receipt: fails against pre-fix code in a worktree**, on `assert not w._dirty_timer.isActive()`. **The broad lifecycle question — what else a window should release, and whether close/dispose belongs in the command layer — remains P6.1's to argue.**

## Site

`mainwindow.py` (`closeEvent`)

## Milestone

**P3.6-followup (done)**
