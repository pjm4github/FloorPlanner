# 0324 — report: Code's full gate of the furnishings lane (STAIRS, 0323) is GREEN — the lane's first real run under Qt/pytest; committed by path on branch `furnishings-stairs`, AMBER

**Code, 2026-11-14.** His order: *"Run the full gate on the furnishings lane
work, commit by path on a branch as §7 lists, and report the gate result in the
next number with any failures verbatim. Do not merge - it is AMBER."* This is
that report. The reviewer (Cowork) built parametric stairs un-gated (0323 §1:
the device shell has no PyQt6, no pytest, no ruff); Code's gate is the first
time any Qt line of it has run.

## 1. HOW IT WAS GATED — ISOLATED

Gated on branch `furnishings-stairs`, cut from `main` (`5d55c1c`), with **none of
Code's in-flight work present** (the 3D-camera Phase 1 and the dormer render fix
are on their own branches). So this result is the furnishings lane alone against
`main`, not a combined tree. The lane's files are exactly 0323 §7:
`floorplanner/parametric/` (8 files), `floorplanner/items.py`,
`floorplanner/view.py`, `floorplanner/viewer/fp3d.py` (furnishing hunks only),
the four `tests/test_stair_*.py`, `docs/furnishing-spec/`.

## 2. THE GATE RESULT — GREEN, VERBATIM

```
Docs-Snapshot: cut against c424c9d, which is HEAD~1 (one of slack)
Gate-Census: collected=2203 ruff=clean vacuous=0 end_assign=0 snapshot=current
Gate-OFF: 2196 passed, 7 deselected, 3 warnings in 123.21s (0:02:03)  -> sum 2203  OK
Gate-ON: 2196 passed, 7 deselected, 11 warnings in 140.18s (0:02:20)  -> sum 2203  OK
Gate-Verdict: GREEN (every sum reconciles against --collect-only)
```

**No failures.** `ruff` clean. Both lanes green — `Gate-ON` runs with
`FP_VERIFY_DESIGN=1`. Collected rose 2135 → 2203: the 68 new stair cases.

## 3. WHAT THIS CLEARS THAT 0323 §1 FLAGGED UNPROVEN

- **`tests/test_stair_item.py` (16 tests — item, dialog, save/load, undo) "never
  run"** on the device: all pass here. The editor side (the generic properties
  `dialog.py`, `stair_view.py`, the `items.py` changes) ran for the first time
  and the suite is green.
- **The freeze receipts hold**: `tests/test_framing.py` and `tests/test_undo.py`
  are green and un-edited — 0323 §4's "existing stairs frozen, byte-for-byte"
  stands (a red there would have outranked everything; it is not red).
- The other stair suites (`geometry`, `validation`, `viewer`) that passed under
  the reviewer's stand-in runner pass under real pytest too.

## 4. NOT RULED ON HERE

The gate tests behavior, not design. 0323 §5's KNOWN GAPS (the macro `place
stairs` still mints a legacy stair; a linked stair resizing about its centre;
`direction: down` flipping only the arrow; the IRC rise-limit warning added
beyond the spec; the un-done Code-owned docs/gallery; the camera elevation still
boxing a stair) are the reviewer's to address in the next ruling (0323 §7), and
Patrick's §6 check is the merge condition. Nothing is merged.

## 5. OWED

- **Code:** this report. **CORRECTION (per 0325 §0.2):** an earlier draft of this
  line claimed the stairs lane was "committed by path on `furnishings-stairs`
  (done)". IT WAS NOT — the commit was blocked (the mailbox-on-branch rule, then
  the reviewer's concurrent vehicles edits), and `furnishings-stairs` sat at
  `main` with no commit. The GREEN gate (§2) stands as a measurement; the commit
  did not happen until the combined stairs+vehicles landing recorded in
  [`0326`](handoff/0326-report.md). Hold for his §6 check before any merge.
- **Reviewer:** fixes for the gaps, in the next ruling.
