# 0193 — report: R5b merged on his word; the undo (already there, and 0192 corrected) and the macro's DORMER token; AMBER, stopped for his check

**Code, 2026‑09‑24.** Patrick's check of R5b passed — his words, in full:
*"this looks fine. lets do the undo. also make sure that the script tool
has commands to handle tha dormer."* On the first sentence PR #63
(`roofs-r5b-dormers`) landed on `main` at `919c48c`, fast-forward, the
branch deleted local and remote. The rest is **his own direct instruction
as authority** ([`0065`](0065-ruling.md) §2, quoted here as
[`0068`](0068-ruling.md) §5 requires) for what this report builds. Branch
`roofs-r5c-undo-macro` off `main` at `919c48c`, PR #64 open, gate
GREEN, **stopped for his check**: record a dormer in the macro recorder,
replay the text on a fresh plan, delete a host and undo it.

## 1. THE UNDO — it was already there, and 0192 §3 was wrong

[`0192`](0192-report.md) §3 said *"roof deletion has no undo today, and
did not before R5b"*. **That was false, and it was said from a grep, not a
measurement**: `roofs.py` names no undo because no item does — undo here
is snapshot-based, driven by the scene's own change signal
(`MainWindow._mark_dirty` ← `scene.changed`, debounced into one step by
the 180 ms dirty timer, restored through `load_data`). Removing a roof
fires that signal like any other change. Measured before anything was
written: a host and its dormer, deleted with `remove_with_dormers`,
settle into one undo step; `undo()` restores both, the dormer's `host`
resolved through the document and its back end re-derived; `redo()`
removes both again. A dormer sketched with the Dormer tool undoes the
same way.

So "the undo" costs no code. It costs two tests that pin the claim
(`tests/test_roof_dormer_macro.py`: the host-with-dormer round trip
through undo and redo, and the tool-sketched dormer's undo) and this
correction on the record. The named limit in 0192 §3 is withdrawn.

## 2. THE MACRO — a self-contained `DORMER` token

**The pattern is the one the language already uses for every
dialog-backed tool** (`DOOR x y WWHH`, `WINDOW`, `ROOM "name" x y`, `^O
"path"`): the recorder captures the dialog's values into one token and
suppresses the raw event, so replay never needs the dialog.

* **Runner:** `DORMER x y width eaves ridge [dx dy]` — the host is the
  roof whose drawn territory holds (x, y) (`host_roof_at`); the face
  snaps onto that roof's clip trace within the tool's own reach
  (`snap_to_trace`, and onto the grid along it) else to the grid; the
  ridge runs up-slope (`upslope_direction`) unless `dx dy` give its
  direction; `width` is the whole width (half each side); the two
  heights are the dialog's. Built exactly as the tool builds one
  (`RoofItem(..., host=)`, back end derived in `rebuild`). Errors, not
  clamps: no roof plane at the point; the point on the host's ridge
  line; a ridge the host never meets (the dialog's own refusal). Feet
  notation works as everywhere (`3'`). `M` and `TOOL roofdormer` select
  the tool (in since R5b).
* **Recorder:** `finish_roof_dormer` calls `on_dormer` after the dialog
  applies; it emits `DORMER x y width eaves ridge`, with `dx dy`
  appended only when the direction is not the default up-slope one
  (Shift). The raw press/drag for the Dormer tool is suppressed in the
  capture, as the door, window and room clicks are — so a recording
  reads `M` then one `DORMER` line.
* **Docs:** `docs/macro_language.md` gains the `DORMER` row, the `G`/`M`
  tool codes (the table had neither), and the recorder note; the
  grammar in `macro.py`'s own docstring likewise.

## 3. THE CHECK — receipts

`tests/test_roof_dormer_macro.py`, **9 tests** (`macro`): the two undo
tests of §1; `DORMER` on the plane (face on the trace and the grid,
18″ each side, the dialog heights, the derived back end, marker at the
face); with a direction and a width in feet; off every roof → error,
nothing built; a ridge the host never meets → error, nothing built;
`M` and `TOOL roofdormer`; the recorder emitting `M` and one
self-contained `DORMER 204 177 36 120 132.6` with no `CLICK`/`DRAG` and
no direction; and the round trip — record through the tool, replay the
text on a fresh copy of the house, the same dormer to the inch.

Full suite **1345 passed**, 7 deselected (`perf` lane), `ruff` clean, gate
GREEN — the branch's own run. Every pre-existing macro, ridge-tool and
dormer test passes unmodified.

## 4. NAMED

* A recorded dormer replays against whatever roof is under (x, y) at
  replay time — the token names a point, not a roof id, exactly as
  `DOOR x y` names a point, not a wall.
* The `DORMER` token's snap reach is the tool's own default (12″); a
  view-zoom-dependent reach is a UI matter, and a macro has no view.

## 5. `fixtures/incoming/`, with ages

`README.md` only — the two `w7` duplicates were deleted on `main` at
`1b150e5` ([`0191`](0191-ruling.md) §4, exit 2).

## 6. WHAT HAPPENS NEXT

His check. On his word PR #64 merges, branch deleted in the merge
step. Then R6 multifloor — waiting on his fixture and his one-line
display answer ([`0186`](0186-ruling.md) §4).

**Carried:** unchanged from [`0192`](0192-report.md), less its §3 undo
limit, withdrawn here.
