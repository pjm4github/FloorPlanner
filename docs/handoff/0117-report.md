# 0117 — report: [`0116`](0116-ruling.md)'s manual check came back — menu passes, two PDF-content defects filed, PR #42 merges as-is

**Patrick's own check on `export-menu-pdf`, reported directly, 2026‑08‑28.**
The menu shape and the Save-As flow both passed: *"the menues looks good"*,
the PDF plan set exports and opens. Two content problems in the PDF itself
were found and are **not** blocking this merge, per his direction: *"The pdf
exporter can be a separate bug fix and we can push the PR#42."*

## 1. What passed

- `File ▸ Export` submenu — Rooms as CSV… / Chief Architect (DXF)… / PDF plan
  set… / Legacy v4…, one place, as `0116` §2 specified.
- `PDF plan set…` reaches the options dialog, then `QFileDialog.getSaveFileName`,
  and the resulting file opens as a real drawing.

## 2. What did not — filed, not fixed here

Both grounded against the actual code, not just the symptom, per this
project's own filing standard:

- **[D81](../defects/0081-fp2pdf-draws-every-door-as-the-same-generic.md)** —
  `fp2pdf.py:draw_opening` checks `door_type == "sliding"`, a value that does
  not exist in the catalog (`LH`/`RH`/`FRENCH`/`BIFOLD`/`POCKET`/`SLIDER`/
  `DOORWAY`/`GARAGE-*`, per `walls.py:_paint_door`). The check is always
  false, so every door — French, bifold, pocket, slider, garage, plain single
  — renders as the same generic single swing-leaf-plus-arc symbol.
- **[D82](../defects/0082-fp2pdf-dimension-strings-carry-1-16-fractions.md)** —
  `fp2pdf.py:ftin` rounds to 1/16" and appends the fraction
  (`20'-6 1/2"`) on every dimension string the sheet draws. Patrick wants
  feet-and-inches only on the PDF, no fractional-inch remainder.

Neither is built. Both are `open`, `area:io`, next work whenever picked up —
D81 as a genuine defect (the wrong thing is drawn), D82 as a task (the
geometry is right; the PDF's own formatting choice is not what was asked).

## 3. Disposition

**PR #42 merges now, unchanged**, per Patrick's explicit go-ahead — the menu
build and the PDF *pipeline* (dialog → convert → save → open) are what that
PR was checked against, and both passed. D81/D82 are follow-up work against
`fp2pdf.py`'s drawing content, tracked separately so they do not re-open an
already-passed check.
