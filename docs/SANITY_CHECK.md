# Manual sanity check

Two moments in this migration are worth checking by hand. Everything else is either invisible or covered by the suite.

| Gate | When | Why then | Risk to your data |
|---|---|---|---|
| **Gate 1** | End of Phase 0 (**now** — after P0.6) | Phase 0 is behaviour-preserving *except* five deliberate fixes and one deliberate regression. Anything else you notice is a real bug, and the signal is clean because nothing structural has moved yet. | None — file format unchanged |
| **Gate 2** | After **P2.2** (save writes v5) | The file format changes. This is the only point in the migration that can touch your real plans. | **Back up your plan files first** |

Phase 1 is a shadow model with no user-visible effect; P0.7 is tooling. Phase 3 runs on a branch, so `main` stays checkable throughout.

---

# Gate 1 — end of Phase 0

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

**Back up your real plan files before this one.** Save now writes v5, and opening a v1–v4 file converts it and marks the document dirty.

- [ ] Copy your real plans somewhere outside the repo first
- [ ] Open a real v3/v4 plan. **A conversion report should appear** — welds performed, rooms whose area changed, duplicate openings removed
- [ ] Sanity-check those numbers against the plan you know. On `planc1.json` the expected report is: 31 wall ends welded, M Bath 591.6 → 182.0 sf, Hall 243.5 → 61.5 sf, 2 duplicate doors removed
- [ ] Room areas elsewhere should be **unchanged** — only rooms named in the report should move
- [ ] The document should open **dirty**. Closing without saving must leave the original file untouched on disk — verify with `git status` or a file timestamp
- [ ] **Save As to a new filename** (not over the original). Reopen it: opens clean, not dirty, no conversion report
- [ ] `python tools/validate_design.py <yourfile>` → Schema PASS, Invariants PASS (schema defaults to the packaged `floorplanner/design/design-schema.v5.json`)

If a room's area changes and it *isn't* in the conversion report, stop and report it. That would mean the weld moved geometry it shouldn't have.
