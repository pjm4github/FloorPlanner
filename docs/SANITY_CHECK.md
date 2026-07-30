# Manual sanity check

Three moments in this migration are worth checking by hand. Everything else is either invisible or covered by the suite.

| Gate | When | Why then | Risk to your data |
|---|---|---|---|
| **Gate 1** | End of Phase 0 (after P0.6) | Phase 0 is behaviour-preserving *except* five deliberate fixes and one deliberate regression. Anything else you notice is a real bug, and the signal is clean because nothing structural has moved yet. | None — file format unchanged |
| **Gate 2** | After **P2.2** (save writes v5) | The file format changes. This is the only point in the migration that can touch your real plans. | **Back up your plan files first** |
| **Gate 3** | End of Phase 3 (**now** — before PR #1 merges) | Phase 3 rebuilt what geometry *is*: vertices own it, rooms store outlines, the detection engine is gone. The suite says the document is right; only a human can say the editor still feels right. It is also the last point before the branch lands on `main`. | None to files — but this is the last look before `main` moves |

**Gate 1 — PASSED** (2026‑07‑26). **Gate 2 — PASSED** (2026‑07‑27), with **one finding, found and fixed** before Phase 3 branched: commit `d665e06`. **Gate 3 — pending**, and it is item 5 of the Phase-3 merge checklist in `V5_MIGRATION_PLAN.md`.

Phase 1 is a shadow model with no user-visible effect; P0.7 is tooling. Phase 3 runs on a branch, so `main` stays checkable throughout.

---

# Gate 1 — end of Phase 0

**Status: PASSED** — user-run 2026-07-26 against Phase 0 complete. Next: Gate 2, after P2.2.

```
python FloorPlanner.py
```

**Work on a copy.** `examples/planc1.json` is a test fixture with known corruption in it — open it, but don't save over it.

## A. Nothing obviously broke (~3 min)

- [ ] App launches; toolbar and menus render
- [ ] Open `examples/planc1.json` — 20 rooms, names, doors, windows, furnishings all present
- [ ] Draw a wall · draw a room · name it · drop a furnishing · add a door
- [ ] Undo and redo several times, including across those operations
- [ ] Switch floors, if you have a multi-floor plan
- [ ] Save As to a scratch file, close, reopen — it round-trips

## B. The five P0.5 fixes — each has a specific observable

| # | Fix | Do this | Was | Should be |
|---|---|---|---|---|
| 1 | `RoomItem` unbind | Delete a room, then click a wall that bordered it | Could raise on a deleted C++ wrapper | No error |
| 2 | Undo snapshot aliasing | Edit a room's properties (ceiling, finish), then Undo | Undo might not restore, or produce no undo step at all | Properties revert |
| 3 | **Floor-scoped refresh** | Two floors, a room on each. Switch to floor 1. **Rooms ▸ Refresh rooms** | **Floor 2's room was deleted** | Both survive |
| 4 | Read-only selection | Rubber-band across several rooms. Watch the wall count and the dirty/unsaved indicator | New walls appeared; document went dirty from a *selection* | Nothing created; still clean |
| 5 | Price write location | **AI ▸ Update furnishing prices…** (needs an API key — skip if not set up), then `git status` | `assets/furnishings/manifest.json` was modified | That file untouched |

**Fix 3 is the one that mattered most** — it was silent data loss. If you only check one thing, check that.

## C. The known regression — confirm how it feels

- [ ] Rubber-band a room whose edge is a **longer party wall**, group it (Ctrl+G), move it → **the room region no longer follows.** This is expected; it's in the plan's Known regressions table, restored at **P4.2**.
- [ ] Confirm the workaround: **drag that room by its name label** instead → region follows correctly.

Worth doing deliberately so it doesn't surprise you in a week.

## D. The performance win — the headline

- [ ] Open `planc1.json`. **Ctrl-click all 20 rooms, one at a time.**

Before P0.6 each click got slower than the last, because selecting room *k* re-ran path-boolean geometry for all *k* already selected. Measured at 64 rooms: **75.5 ms → 1.7 ms**, and it was super-quadratic (ratio 27) before. On 20 rooms it should now feel instant.

- [ ] Pan and zoom around a populated plan — should feel no worse, and possibly better after the P0.6 caching.

## E. What is deliberately still broken — don't report these

| Symptom | Fixed at |
|---|---|
| **Ctrl+G on many rooms is still slow** (and still creates ~106 duplicate walls on this plan) | **P3.8** |
| **Deleting a wall on a room perimeter appears to do nothing** — no wall removed, no message (defect 17) | **P4.1** |
| M Bath overlaps Great Room and Hall in `planc1.json`; a 591 sf master bath | **P2.1** (weld on load) |
| Groups vanish on save/reload, and an unrelated undo dissolves them | **P4.5** |
| "Bring to front" is reverted by the next undo of anything else | **P4.5** |

Deleting a room wall is worth trying once — it's a small thing that has probably been quietly annoying you.

## Report back

```
Gate 1
A (regression sweep):  pass | issues: ...
B (five fixes):        1_ 2_ 3_ 4_ 5_
C (known regression):  confirmed | unexpected: ...
D (selection speed):   instant | still laggy
anything else:         ...
```

Anything in A, or a "was" behaviour still present in B, is a real finding — that's the point of doing this by hand.

---

# Gate 2 — after P2.2 (the format cutover)

> **RESULT: PASSED, one finding — fixed on `main` at `d665e06` before branching.**
>
> Reopening the app's own legacy-v4 export of a converted plan reported *"5 wall ends moved"*. It should always be **0** — the application's own output must never need repair. Cause: the importer welded the wall ends but left the **stored room corners** at their pre-weld positions, so the planarise cut each repaired wall 1.53″ from its own new end and left a sliver — the ghost of the gap the weld had just closed. Fixed by welding the corners with the walls.
>
> **The lesson, in one line: both paths were covered; their composition was not — covered-paths ≠ covered-compositions.** P2.2 round-tripped only through `load_data` (the faithful apply, which never welds), so the export was never taken back through the *converter*. The regression test now drives the whole journey rather than either half.
>
> Note the expected conversion numbers below were written before that fix and before the two-counter correction; the current report for `planc1.json` reads **4 wall ends moved (31 junctions checked)**, M Bath 591.6 → 182.0 sf, Hall 243.5 → 61.5 sf, 2 duplicate doors removed.

**Back up your real plan files before this one.** Save now writes v5, and opening a v1–v4 file converts it and marks the document dirty.

- [ ] Copy your real plans somewhere outside the repo first
- [ ] Open a real v3/v4 plan. **A conversion report should appear** — welds performed, rooms whose area changed, duplicate openings removed
- [ ] Sanity-check those numbers against the plan you know. On `planc1.json` the expected report is: 31 wall ends welded, M Bath 591.6 → 182.0 sf, Hall 243.5 → 61.5 sf, 2 duplicate doors removed
- [ ] Room areas elsewhere should be **unchanged** — only rooms named in the report should move
- [ ] The document should open **dirty**. Closing without saving must leave the original file untouched on disk — verify with `git status` or a file timestamp
- [ ] **Save As to a new filename** (not over the original). Reopen it: opens clean, not dirty, no conversion report
- [ ] `python tools/validate_design.py <yourfile>` → Schema PASS, Invariants PASS (schema defaults to the packaged `floorplanner/design/design-schema.v5.json`)

If a room's area changes and it *isn't* in the conversion report, stop and report it. That would mean the weld moved geometry it shouldn't have.

---

# Gate 3 — end of Phase 3 (before PR #1 merges)

**Status: PENDING.** Item 5 of the Phase-3 merge checklist (`docs/V5_MIGRATION_PLAN.md`, Phase 3 banner): the merge does not happen until this is passed and its findings dispositioned.

```
python FloorPlanner.py
```

**Work on copies.** `examples/planc1.json` and `examples/sample_plan.json` are frozen fixtures — open them, never save over them.

## A. Conversions and reports (~5 min)

- [ ] Open `planc1.json` (v3): the **conversion report appears** — welds, area corrections (**M Bath 591.6 → 182.0**, **Hall 243.5 → 61.5**), duplicate doors, and **opening entries** (new since Gate 2). Console quiet otherwise
- [ ] Open `symmetricP1.json` (v5): opens **clean, not dirty**, console silent
- [ ] **Save As** from each, then reopen: clean, no report, and `python tools/validate_design.py <file>` → **PASS / PASS**

## B. Phase-3 behaviours, each with its observable

- [ ] **Whole-plan band → group → move**: every room tracks (was: porches stranded). Console silent
- [ ] **Deliberately clip one room** with the band → group → move: that room **strands** — expected until P4.5 — with **one** status-line warning naming *the edit*, not the legacy file, **said once**
- [ ] **Draw a wall T-ing through a doorway**: the door is **reported**, not silently dropped or slid
- [ ] **Drag a wall endpoint** to stretch a wall with a door on it: the door **keeps its distance from its near end** — no drift, no mirroring
- [ ] **A room with an open side shows a dashed edge** (the cue missing since P3.5 is back)
- [ ] **Select all 20 rooms one by one, group, ungroup, undo, redo**: no lag, no console output

## C. Deliberately still broken — don't report these

| Symptom | Fixed at |
|---|---|
| Deleting a room's perimeter wall does nothing | **P4.1** |
| Clipped-band room stranding | **P4.5** (defect 23, semantics ruling pending) |
| Groups vanish on save/reload; unrelated undo dissolves them | **P4.5** |
| Z-order / bring-to-front reverted by undo | **P4.5** |

## Report back

```
Gate 3
A (conversions/reports):  pass | issues: ...
B (six behaviours):       1_ 2_ 3_ 4_ 5_ 6_
C (known-broken):         confirmed | unexpected: ...
anything else:            ...
```

Anything in A, or a B observable that does not appear, is a real finding — that is the point of doing this by hand.
