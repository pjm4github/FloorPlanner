# 0297 — ruling: THE 1½-STOREY ARC, consolidated — the one file Code picks up; phases, checkpoints, receipts, stop points

**His word, 2026‑11‑05:** *"crystallize that into a traceable Claude Code
ruling … implement the feature set with given checkpoints."* This file is
the arc's charter. It consolidates [`0293`](0293-ruling.md) (principle,
measurement, phases), [`0294`](0294-ruling.md) (windows on the dormer
face; the plan stack; the cut into the climbing wall), [`0295`](0295-ruling.md)
(the four views) and [`0296`](0296-ruling.md) (the `dormer` wall type;
promotion gating). Where this file and those disagree, THIS file governs;
where this file is silent, they do. Every item below cites its source so
the reason is one click away. Code reads this, acts on it, and cites it —
it does not transcribe it (handoff README, rule 2).

## 0. BEFORE ANY CODE — checkpoint 0

1. **Commit 0293–0297 as one doc-only commit** before any other git
   (WORKING_AGREEMENT, "doc edits are Cowork's, committing is Code's").
2. **Report `3761819`** (the cross-level load fix) in the next report's
   opening — commit, test, his word (0293 §0; 0197 §7).
3. **Empty `_to_delete/`** (one tarball of mine, 0293's measurement).
4. **Measure the three UNMEASURED items of 0293 §1** and quote them: the
   dialog's `level_base_in` on a cross-level dormer; `roof_clip_spans`'
   same-floor filter on an L2 wall under the L1 roof; `dormer_defaults`'
   room source. A reviewer's reading is testimony until measured.
5. **Fixtures (his, 0293 §6):** `fixtures/incoming/little-dormer-test.json`
   (modality 2: roof and dormer on L1, L2 present with four walls) and a
   new wiscaway R-file with L2 `height_in` reset 196 → 96. **P1 and P2 are
   RED until the wiscaway file exists**; P3–P5 run on little-dormer-test.
   Neither is committed; no test references `incoming/` (D51).

Report: `NNNN-report.md` closing checkpoint 0, then start P1.

## 1. THE PRINCIPLE EVERY PHASE OBEYS (0293 §2)

**A roof governs by ABSOLUTE height, not by level identity.**
(a) **The stacked climb** — a wall climbs into any roof above it, bounded
at the base of the storey above where that storey stands there.
(b) **The dash and the knee line read absolute height.**
(c) **A dormer has ONE datum: its host's**; its `level` is only its editing
home; after P1, 3D never reads it.
And from 0294 §1: **the dormer's `openings` record is THE home of every
dormer-face window**, whatever stands under the face.

## 2. THE PHASES — order P1 → P2 → P3 → P5 → P4 (0294 §5), all AMBER

Each phase: its own branch on the previous, a pre-work census (AST for
call shapes, grep for names), the full gate green on the final tree, a
numbered report with the receipts below VERBATIM from the instrument,
then the next phase. **Stop and report on double failure.** A changed
existing assertion is named in the report, every time.

### P1 — the stacked climb (3D) · 0293 §2a, §5 P1
* `_wall_under_roofs`: the climb (gable and dormer) granted by absolute
  height from any level; bounded at the storey above's base where a wall
  of that storey stands on the line (`_on_a_wall`'s predicate — one
  definition) or a room of that storey covers the piece; otherwise to the
  roof as today. Census first: every `lid == level` / `same_level` reader.
* **Receipts** (wiscaway R-file, L2 = 96″): L1 climbing pieces sharing a
  plan position with an L2 piece **15 → 0**; L2 climbs **0 → N**, N stated;
  `8048` a VOID by the `test_dormer_gable_3d.py` ray test; highest L1 top
  under an L2 wall ≤ L2 base. **Positive controls:** `dormer-test.json`
  byte-identical; little-dormer-test's x≈60/600 gables keep 235.5″ unless
  L2 stands over them — say which, measured; `test_gable_climb_level.py`
  green, any changed assertion named.
* **Checkpoint 1:** report; no manual check yet (batched, §4).

### P2 — the dash and the knee line (plan) · 0293 §2b, §5 P2
* `roof_clip_spans` over every live roof in absolute height, memoised
  against the building compose (`_compose_memo`); a room overlay
  `room_ceiling_break_lines` painted dashed by `RoomItem`, memoised (0276).
* **Receipts** (same file): L2 walls with a dash before → after; the knee
  line in BR2/BR3 at **y = 580 and 776** (0293 §5 P2 derives it from
  `rf1`'s record — quote the measured coordinates beside it); L1's dash
  count before = after.
* **Checkpoint 2:** report.

### P3 — the dormer's level, datum, dialog and views · 0293 §5 P3; 0295 §1; 0296 §1
* `level_base_in()` = host's base for a dormer; the note names both
  floors. "Pinned to" section (host id, level, pitch). "Edited on level"
  selector and the marker's **"Move to level ▸"**, both listing only
  EXISTING levels among {host's, the one above}; disabled with a note on a
  one-layer plan (0296 §1). `dormer_defaults` from the DRAWN level's
  rooms, in the host datum. The two schema descriptions corrected (0293
  §0). A dormer SHOWN on both its legal levels — solid on its own, ghosted
  on the other — regardless of "show other floors" or rooms (0295 §1).
  The macro records a promotion; say what the `DORMER` token carries.
* **Receipts** (little-dormer-test): promote `rf2` L1 → L2 → `build_model`
  **byte-identical** (OBJ bytes); the document differs in `rf2.level`
  only; grips/marker hittable on L2, not L1; save → reload → still L2,
  host `rf1`; **the four-view table of 0295 §1**, per quadrant, visible and
  hittable sets, on a file with no rooms.
* **Checkpoint 3 — CHECK SESSION A (§4).** Nothing merges past here
  without it.

### P5 — windows on the dormer face · 0294 §2, §3
* 3D: where a wall stands on the face and climbs, the dormer's `openings`
  are cut into THAT wall's climbing pieces — `_wall_under_roofs` gains
  `z_cap`; the head clamp to `z1 − z0` and the `to_top=False` under-sill
  piece both change for bands above the storey top; the straddling band
  is its own test. ONE projection shared with `dormer_face_window_spans`.
* Plan: `DormerWindowItem` — the second row (offset up-slope by t/2 + a
  screen gutter, ties to the face, dashed outline + gable glyph); drag
  along the face (snapped); double-click → dialog with that window
  selected; right-click edit/duplicate/delete; Delete; width/sill/head
  dialog-only; follows the dormer's layer (0295 §1).
* **Receipts:** a `3040` on `rf2` → a VOID by ray test, triangle delta
  ≠ 0 (0292's measured **0** quoted as the precondition), the wall's own
  storey window still a void; the promoted file: the same cut from the L2
  wall; `dormer-test.json` byte-identical.
* **Checkpoint 4:** report.

### P4 — the `dormer` wall type · 0296 §2–3
* `type: "dormer"` (enum, `STD_T`, no version bump — PR #98's precedent);
  `bound_to: {roof, part}` required iff `dormer`. Level = the storey ABOVE
  the host, always. Three checkboxes in the dialog + marker menu; on by
  default when that storey exists; never automatic at creation. Vertices
  derived via the vertex API at every rebuild, still written. Readable by
  every L2 wall operation (rooms, welds — deform-to-follow, dash, gaps,
  exports); every write on it refused with the dormer named; no openings.
  3D: nothing new — climbs (P1), yields the generated pieces (`_on_a_wall`),
  takes the face cut (P5). **Undo stated before the phase opens**: what
  the stack covers; refuse undo rather than half-undo (0296 §2).
* **Receipts** (0296 §3, verbatim): three L2 records bound to `rf2`; a
  room closes against them + one knee wall, `check(deep=True)` clean; C
  dragged 12″ ON L1 → the L2 cheek vertices, the welded knee wall and the
  room outline follow, nothing else changes (set equality both ways); a
  drag on the cheek itself refused, document byte-identical; generated
  cheek/face triangles for `rf2` → 0; reload keeps the binding; promotion
  moves no wall.
* **Checkpoint 5 — CHECK SESSION B (§4).**

## 3. TIERS AND AUTHORITY

All five phases AMBER: Code builds, gates, reports; **merge of P1–P3 waits
on session A, merge of P5–P4 on session B**. RED: P1/P2 before the wiscaway
R-file; P4 before its undo statement. Sonnet for censuses and memoisation;
not for P1's rule, P5's cut, or P4's binding. Auto-commit of GREEN
sub-work within a branch as the agreement allows; nothing merges on a red
gate or a failed check.

## 4. HIS PART — three gestures, two check sessions (0293 §6; 0294 §5; 0296 §4)

1. Now: wiscaway L2 height → 96″, saved as a new R-file in `incoming/`.
2. After P3: open little-dormer-test, promote `rf2`, save.
3. **Session A** (after P1–P3): on the wiscaway file in 3D — gables close
   with the L2 wall, `8048` visible, no doubled wall; on L2's plan — the
   dash, the knee line at the stated y's; the dormer dialog's "Pinned to",
   the level selector and its absolute heights; switch layers and move the
   dormer both ways — the four pictures match his diagram.
4. **Session B** (after P5–P4): on little-dormer-test — the two rows in
   plan, drag the dormer band, open the dialog from it, both windows in 3D;
   tick the walls on, draw the L2 room, drag C from L1 and watch L2.

Each check request is a report naming the plan loaded and the items in it
(WA 2026‑08‑15).

## 5. NOT IN THIS ARC (0293 §7)

Undo for roof edits as such; a knee-wall object; D69's panel; cheek
windows; his files in `incoming/` stay uncommitted and his.

## 6. HOW A PHASE CLOSES

Its report quotes every receipt above from the instrument that took it,
names the gate line in full (`tools/gate.py --trailer`), names every
changed assertion, and answers *"would `check(deep=True)` have fired?"*
for anything found on the way (the answer for this whole class is **no —
a limit**, 0293 §1; a phase that finds otherwise says so). The next phase
does not open until the previous report is on disk.

**Carried:** 0293 §0; 0294 §5; 0295 §1; 0296 §2.
