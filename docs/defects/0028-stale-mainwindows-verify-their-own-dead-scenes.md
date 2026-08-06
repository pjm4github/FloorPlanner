---
# permanent key, independent of GitHub
id: 28
title: "Stale MainWindows verify their own dead scenes during later tests, reporting I11s that belong to"

# maps directly onto GitHub Issues fields
state: closed
state_reason: completed
labels:
  - type:defect
  - area:tests
milestone: null

# ours; becomes body prose after migration
opened: 2026-07-29
closed: null
closed_by: null
rank: 20
related: []
state_source: row
github_issue: null
---

# D28 — Stale MainWindows verify their own dead scenes during later tests, reporting I11s that belong to

## Record

> **Moved verbatim** from the register (`docs/CODE_REVIEW_v2.md`, the row at its
> line 85) on 2026-08-06 — not reworded, not split, not
> reformatted. The register wrote each row as one continuous argument in which
> symptom, mechanism, evidence, ruling and receipt are interleaved, so dividing
> it into sections would have meant interpreting it. See
> [`README.md`](README.md) for the section shape new records take.

**Stale `MainWindow`s verify their own dead scenes during later tests, reporting I11s that belong to whoever left them.** REWRITTEN 2026-07-29: the original entry blamed a group rotation, and **rotation is exonerated by measurement** — a tight headless loop over ten angles (5–270°) produced ZERO new violations. **Mechanism (suspected, not yet dissolved):** the `win` fixture ends with `w.close()`, which hides a window but neither destroys it nor stops its 180 ms dirty timer; `live_mainwindows` measured at **7, 10, 11** across a session. Any later test that pumps the event loop — the macro runner calls `processEvents()` after every token — lets a stale timer fire, walk its own dead scene and report. The Python stack cannot show this: the C++ callback boundary leaves no frame, so a corpse looks like it belongs to the running test. Hence a macro test that builds ONE 240×180 room yielding a corpse containing symmetricP1's twenty. **CORPSE TABLE COMPLETE 2026-07-29 — every corpse is owned, and `'Kitchen'/'Pan'` is owned by `tests/test_groups.py::test_a_group_move_leaves_the_outlines_still_holding_their_corners`.** Found by direct sweep, not by waiting for the race: three sweeps (each test's own scene at its own teardown; every quiescent point via `fault_profile`; and forcing `_commit_if_changed` on every live window after every test) plus a 10-run re-harvest that kept the FULL documents the reduced evidence file had dropped. **Attribution is by document signature:** every 20-room corpse is symmetricP1 translated +48″ in x with one corner displaced a further (+12,+12) — that test's literal script (`test_groups.py:545` and `:557`), performed by no other test. Confirmed two more ways: run ALONE it errors at its own `win` teardown 1 in 12, and on a red DEEP run **pytest already blames it correctly** (`ERROR … test_a_group_move_leaves_the_outlines_still_holding_their_corners`, at "win fixture teardown") — the leak misattributes the corpse FILE, never the pytest error. **ROOT CAUSE, and the "race picks the victim" claim is withdrawn:** the test picks its party wall with `next(w for w in win.scene.items() …)`, and scene item order is not stable across processes, so the *pick* varies — no race in the choice. It then re-points the moved vertex for the party wall's **two** rooms only (`for r in (a, b)`), so a **third** room whose outline holds that same corner is left behind and, where geometry allows, overlaps a neighbour. **18 of 59 candidate picks produce an I11 (31%), matching the measured 4-in-10 red DEEP runs; re-pointing every holder gives 0 of 59** — which is what both app corner-movers already do (`_DragVertex.ends`/`.edges`, `GroupItem._corner_records`). **Two corrections to this entry's own earlier reasoning:** `window.visible=false` is not a staleness tell (no fixture window is ever shown), and a stale window's walk is in fact SILENT today — forcing it 518× produced 0 reports, because every I11 in a stale scene sits in that scene's accepted baseline. **NOT established, and not asserted:** that an equivalent APP gesture can strand a holder — 38 synthetic endpoint drags moved the corner in none of them, so that run's "0 stranded" is vacuous and is discarded rather than quoted. Evidence: `docs/evidence/defect28-ownership.json` (+ the original `defect28-corpses.json`). **FIXED at P3.6-followup in two commits.** (A) the owning test: a deterministic `min(…, key=geometry)` pick, and every room holding the corner is re-pointed — 18-of-59 → 0-of-59, and 15 consecutive solo DEEP runs green. (B) the fixture leak: `dispose_window` closes, lets the close-time signals settle, *then* stops the timer (closing restarts it — the first cut had this backwards) and destroys the window with `sendPostedEvents(None, DeferredDelete)` (`processEvents()` alone never delivers it, so `deleteLater` left the window standing). Peak live MainWindows **16 → 0**, peak holding a live timer **9 → 0**, alive at session end **12 → 0**. The guard is stated as the invariant — *no window outlives its test holding a live dirty timer* — not as a budget on the count, and its **fail-first receipt is 333 teardown errors** against pre-fix code in a worktree. It also immediately caught a second leak of the same class in `test_scaling._measure`, fixed at source rather than tolerated. **Re-certified: 10/10 green full-mode `gate.py` runs.**

## Site

`tests/test_groups.py` (the owning test); `tests/conftest.py` (`dispose_window` + the guard); `tests/test_scaling.py`; app half is defect 29

## Milestone

**P3.6-followup (done)**
