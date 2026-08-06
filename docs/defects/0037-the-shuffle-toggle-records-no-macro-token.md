---
# permanent key, independent of GitHub
id: 37
title: "The Shuffle toggle records no macro token and has no keyboard shortcut - a user-facing MODE the"

# maps directly onto GitHub Issues fields
state: closed
state_reason: completed
labels:
  - type:defect
  - area:ui
milestone: P4.4

# ours; becomes body prose after migration
opened: null
closed: null
closed_by: null
rank: 38
related: []
state_source: row
github_issue: null
---

# D37 — The Shuffle toggle records no macro token and has no keyboard shortcut - a user-facing MODE the

## Record

> **Moved verbatim** from the register (`docs/CODE_REVIEW_v2.md`, the row at its
> line 103) on 2026-08-06 — not reworded, not split, not
> reformatted. The register wrote each row as one continuous argument in which
> symptom, mechanism, evidence, ruling and receipt are interleaved, so dividing
> it into sections would have meant interpreting it. See
> [`README.md`](README.md) for the section shape new records take.

**The Shuffle toggle records no macro token and has no keyboard shortcut — a user-facing MODE the recorder cannot see.** Filed at the P4.3 dispositions (2026‑08‑03). The `CARET_SHORTCUTS` one-table design (P4.2(19)) made "adding a menu shortcut is one row" true — but the shuffle toggle is a toolbar-only `QAction` with no shortcut, so it bypassed the table entirely and the recorder records **nothing** for it: a replayed session that toggled shuffle mid-way replays with the wrong mode, silently. Same class as the pre-P4.2 unnamed chords, now on a shipped mode. The fix shape is the table's own: assign a chord, add the row (`^`-token + `MainWindow` method — `_set_shuffle` exists), and the design-guard test enforces the wiring. **Phase: P4.4** — the earliest next task, the fix is one table row plus a chord choice, and P4.4's duplicate-as-template workflow is exactly where floating rooms and shuffle get exercised together in recorded macros; leaving it later means every P4.4-era reproduction macro is mode-ambiguous. **CLOSED at P4.4(2) with the ruled chord `^H`.** `Ctrl+H` on the toolbar action; the `CARET_SHORTCUTS` row (`H` → `toggle_shuffle`) makes the one-table design whole again. The recorder emits an **absolute** token for a flip from *any* route (toolbar click or chord) through the `on_shuffle` hook — `^H "on"` / `^H "off"`, the `on_floor` pattern — so a replayed session lands in the mode the recording ended in rather than silently the wrong one; bare `^H` toggles for hand-written macros, and the quoted form is idempotent on replay. `MainWindow.toggle_shuffle`/`set_shuffle_mode` drive the **action**, so the toolbar cannot drift out of sync with the setting. Pinned three ways (token semantics, the recorder's absolute emission, the chord on the action).

## Site

`mainwindow.py` (`a_shuffle`, no shortcut), `macro.py` (`CARET_SHORTCUTS`, no row)

## Milestone

**P4.4 (done)**
