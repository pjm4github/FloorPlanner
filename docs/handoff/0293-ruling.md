# 0293 — ruling: the 1½-storey — a roof shapes the storey it rises THROUGH, not only the one it stands on; the dormer's level, datum and walls

**On his instruction, 2026‑11‑05**, after his look at the second-floor
rooms under the 12/12 roof: *"find a way to manage the interaction between
the floors, the dormer, the host roof, the face walls and the cheek walls
… make a plan."* And his workflow, in his words (§3), which this ruling
builds the tools for.

## 0. RECORD, FIRST

* **`3761819` (the cross-level load fix, 0292 §3 item 1) landed with no
  numbered report** — the same gap 0197 §7 closed twice. Code's next
  report opens by recording it: the commit, the test, his word.
* **The schema's own text is stale against the code it describes**, two
  places, corrected in Phase 3: `roof.host` says *"must name a roof on the
  same level"* (false since PR #101 and `3761819`); `roof.openings` says
  sill/head are *"above the dormer's level base"* while `fp3d` lifts them
  in the HOST's frame (0291 §1). A record whose description disagrees
  with its reader is the duplication disease in prose.

## 1. THE MEASUREMENT — taken, not reasoned

**Instrument:** `fp3d.build_model` headless on his two files (the
`floorplanner/` tree at `3761819`, numpy only), with
`_wall_under_roofs` wrapped to log each wall piece's `level`, its own top
`z_hi`, and the top it was actually built to. A piece is a CLIMB when its
built top exceeds `z_hi + 0.6`. Positive control: the climbs it reports on
L1 are the gable climbs 0254 pinned, at the heights 0290 §1 measured.

| plan | L1 pieces | L1 climbs | highest L1 top | L2 pieces | L2 climbs | L2 base |
|---|---:|---:|---:|---:|---:|---:|
| `fixtures/incoming/little-dormer-test.json` (today's) | 66 | **26** | **235.5″** | 10 | **0** | 96″ |
| `fixtures/incoming/wiscaway2026-11-01R1.json` | 196 | **59** | **289.5″** | 87 | **0** | 100″ |

1. **The first-floor walls climb THROUGH the second storey; the second-floor
   walls never climb.** On wiscaway, L1 gable pieces at plan (138, 679),
   (318, 677), (444, 678) are built to 289.5″ — 190″ above L2's base.
2. **Doubled walls in one plane.** **15 of the 59** climbing L1 pieces share
   a plan position with an L2 piece: at (318, 677) the L1 piece and the L2
   piece BOTH top out at 289.5″. His L2 gable window `8048` is behind an L1
   climb. That is 0290 §2's *"the gables close with the FIRST-floor wall"*,
   still live.
3. **L2's `height_in` is 196″** in wiscaway while every L2 room says 96″ —
   him forcing the L2 walls to the ridge, because nothing else would.
4. **The dormer's generated face is 0 triangles for two of his three
   dormers** (`rf4`, `rf8`; `rf5` gets 36) — every face yields to a house
   wall (`_on_a_wall`), so the face is wherever the wall is, and 0292 §2's
   finding that a face window never renders for his houses follows.

**UNMEASURED, found in the source, for Code to measure before Phase 3** (a
reviewer's reading is testimony, WORKING_AGREEMENT's own rule):

* `RoofEndOnDialog.level_base_in()` reads `roof.floor`. A dormer drawn on
  L2 over an L1 host (PR #101's model) would print absolute heights
  L2-elevation too high, while `fp3d` lifts it by the host's base.
* `roof_clip_spans` takes only roofs with `it.floor == wall.floor`; an L2
  wall under the L1 roof gets no R3b dash from it, and under a dormer drawn
  on L2 the dash compares host-datum heights to an L2-datum ceiling.
* `dormer_defaults` seeds the cheek top from `host.floor`'s rooms — the
  floor BELOW the rooms the dormer serves.

**Would `check(deep=True)` have fired on any of this? No**, and it is a
limit, not a gap: the invariants know nothing of heights or of 3D. The
instrument for this class is the headless build with a receipt, which is
what every phase below is gated on.

## 2. THE PRINCIPLE — RULED

**The root cause is one premise, repeated:** every rule deciding how a roof
shapes a wall or a room is keyed on *same level* — the gable climb
(`same_level and gable_wall_of`), the dormer climb (`dm and lid == level`),
the R3b dash (`it.floor == wall.floor`), the seeded dormer eaves, the
room-top binding. A 1½-storey breaks it: the roof stands on L1's eaves walls
and shapes L2's walls and rooms. PR #101 patched one rule, for dormers
only, and in doing so gave the dormer two datums the dialog does not know.

**RULED: a roof governs by ABSOLUTE height, not by level identity.** Three
corollaries, binding on every reader (plan, dialog, 3D):

**(a) The stacked climb.** A wall climbs into a roof whose absolute surface
over the piece is above the piece's base — a gable wall (exterior,
perpendicular to the ridge) or any wall inside a dormer's territory —
**from whatever level the roof stands on.** The climb is BOUNDED at the
base of the storey above wherever that storey stands there: a wall of the
level above on the same line (`_on_a_wall`'s predicate, reused — one
definition) or a room of that level over the piece. Where nothing of the
storey above is there, the climb runs to the roof as today. So: with L2
walls on the gable, L1 stops at L2's base and L2 closes the gable with its
own window (0292 §3 item 2, delivered by this rule rather than a new one);
with no L2 at all (his attic, modality 2), L1 climbs to the ridge as now;
0254's case (L1 wall under an L2 roof, L2 wall above) stays fixed, by the
bound rather than by the level test.

**(b) The dash and the ceiling-break line read absolute height.** R3b's
wall dash: every live roof, its heights composed as 3D composes them
(`Lifted`/`floor_elevation`, 0186 §4 — ONE arithmetic), against the wall's
level base plus the room ceiling. And a ROOM gets the line he asked for —
*"walls that have a full height ceiling should get the dashed line that
indicates where a flat ceiling starts"* — as the level set
`roof_abs(x, y) = room_base + ceiling` drawn dashed inside the room outline:
the knee line. It is a DERIVED OVERLAY, never a wall and never stored —
the same discipline as R3b's dash and the R4d clip.

**(c) A dormer has ONE datum: its host's.** `eaves_h_in`, `ridge_h_in`, and
every opening sill/head on a dormer are measured from the HOST roof's level
base — what PR #101 built and 0291 tested in 3D. The dormer's `level` is
its EDITING HOME only: which floor's plan shows its grips and marker, whose
rooms seed it, where its walls (Phase 4) are made. **After Phase 1, 3D never
reads a dormer's `level`** — which is what makes promotion (§3) a change
with a measurable zero.

## 3. HIS WORKFLOW — RULED IN, and the schema already carries it

His two modalities, verbatim in intent: **(1)** roof on L1 → create L2 →
draw L2 walls, the full-height ones showing where the flat ceiling starts →
a dormer made on L2 that *"pins itself to the host roof on L1 but allows the
user to adjust the face and cheek walls with the control handles on that
floor"*. **(2)** roof and dormer both on L1, an attic with no L2; later a
second floor is created and the dormer is *"promoted"* — *"now part of the
second floor and all controls live on the second floor."* And the dialog
must *"describe the host roof that the dormer is pinned to"* and *"select
the active level and allow the user to move the dormer between levels."*

**The schema supports it as written, with no new field:** `roof.level` and
`roof.host` are independent; `3761819`'s loader accepts a host on the
dormer's level or the one directly below; the writer (`bridge.py:936,
968`) writes both. Promotion is an edit of `level` alone — under (c) the
geometry does not move, so **the receipt for promotion is a byte-identical
`build_model` before and after** (the OBJ, or the mesh arrays), plus the
plan delta: grips and marker on L2, ghost on L1. The only schema change in
this arc is text (§0) and Phase 4's additive wall field.

## 4. HIS THREE "NO PREFERENCE"S — RULED FOR HIM, with the reason

* **Rooms under the roof (knee line):** (b) above. The app draws the break
  line; he draws walls where he likes. A knee wall is a wall he draws, and
  the dash/line tells him where. Not a knee-wall object — the record has
  enough wall kinds.
* **Cheek and face walls:** **BOUND WALLS on the dormer's editing level.**
  Real `walls` records (rooms bound to them, windows on them, welded like
  any wall) whose ends are DERIVED from the dormer's wall lines at every
  dormer rebuild — the `eaves_bind` discipline exactly: derived, still
  written, re-derived on edit, never on load. The binding is stored on the
  wall, additive (`bound_to: {"roof": id, "part": "face" | "cheek_left" |
  "cheek_right"}`, ROADMAP R-B, no version bump). The C/D grips are the ONLY
  way to move a bound wall; a direct drag is refused with a status line
  naming the dormer. Release is a dialog action and leaves an ordinary
  wall. Refused alternatives: generated-and-unsynced copies (two records,
  D62's shape), or walls as source with the dormer snapping to them (the
  grips would then be decoration, against `DORMER_CONROLS.md`).
* **Windows:** **a window lives on a wall.** With (a) the L2 gable wall
  climbs and its window shows; with bound walls the dormer face is a wall.
  The dormer's own `openings` list keeps exactly one job — a face with NO
  wall standing on it (the set-back dormer, 0248 §2 item 4) — and the dialog
  SAYS which case holds, by the same predicate 3D uses (`_on_a_wall`): a
  wall on the face line → the list is disabled with *"the face is wall W23
  on level L2 — its windows are edited there"*; none → the list is live.
  One home per window, chosen by a stated predicate, never by silent
  geometry. "Create walls" (Phase 4) MOVES any existing face `openings`
  onto the new face wall — a window loses nothing at the bind.

## 5. THE ORDER — five phases, every one AMBER, stacked for ONE check session

Never two open AMBER tranches at once (0186 §5) — so: build and gate each
as its own PR on the previous, headless receipts as the gate, and **his
in-app check once per batch (§6)**, not per phase. Every receipt is a
differential with its provenance named; "green gate" alone is not
acceptance (WORKING_AGREEMENT, 2026‑08‑04).

**P1 — the stacked climb (3D).** `_wall_under_roofs`: grant the climb by
absolute height (2a) for gable and dormer alike; bound it at the storey
above where that storey stands. Census first: every reader of `lid ==
level` / `same_level` in `fp3d.py`, by AST not grep (the call-shape rule).
Receipts, on `wiscaway2026-11-01R1` **with L2 `height_in` reset to 96** (his
gesture, §6): L1 climbing pieces sharing a plan position with an L2 piece
**15 → 0**; L2 climbs **0 → N > 0**, N stated; the `8048` gable window
a VOID by the ray test `test_dormer_gable_3d.py` already uses; the highest
L1 top on a gable with an L2 wall above it ≤ L2 base. Positive controls:
`dormer-test.json` (one level) builds **byte-identical**; `little-dormer-test`'s
gable pieces at x≈60 and x≈600 keep 235.5″ **unless** an L2 wall or room
stands over them — say which, measured. `test_gable_climb_level.py` stays
green, now for the bound's reason; if any assertion there must change, name
it (a changed test is a red flag).

**P2 — the dash and the knee line (plan).** `roof_clip_spans` over every
live roof in absolute height (2b), memoised against the building compose
(`_compose_memo`, 0281's lesson — paint must not recompose); a
`room_ceiling_break_lines(scene, room)` overlay painted dashed by
`RoomItem`, memoised like `roof_clip_spans` (0276). Receipts, same file:
L2 walls with a dash **before (measured, expected 0) → after**; the knee
line in `BR2`/`BR3`: `rf1` has eaves 96″, ridge 294″ (abs; L1 base 0),
span 198″ → 12/12; L2 base 100″ + ceiling 96″ = 196″ abs → the roof is at
196″ **98″ from the ridge** (`(294 − 196) / 1`), so the line lies at
y = 678 ± 98 = **580 and 776**. Checkable by hand; quote the measured
coordinates beside these. The L1 plan is unchanged (its dash count before
= after).

**P3 — the dormer's level, datum and dialog.** (i) `level_base_in()` for a
dormer = the host's level base (2c); the note names both floors. (ii) A
"Pinned to" section: host id and level, its pitch; an **"Edited on level"**
selector limited to the host's level and the level directly above
(`host_roof_at`'s look-down, mirrored); apply = promote/demote. (iii)
`dormer_defaults` seeds from the DRAWN level's rooms, converted into the
host datum: `(base_drawn − base_host) + ceiling + DORMER_EAVES_ABOVE_CEILING_IN`.
(iv) The two schema descriptions (§0). (v) Measure the three UNMEASURED
items of §1 first and quote them. (vi) The macro: does the `DORMER` token
carry the drawn level, and what token does a promotion record? Say,
measured; a gesture the recorder cannot replay is not finished. Receipts,
on `little-dormer-test.json`: promote `rf2` L1 → L2 → `build_model`
**byte-identical** (OBJ bytes, named); the plan: grips and marker hittable
on L2, not on L1 (`_roof_hittable`); save → reload → still on L2 with host
`rf1` (the `3761819` test, extended to the promoted file).

**P4 — bound walls.** Schema: `wall.bound_to` (§4), the conditional that a
bound wall's `level` is the dormer's and its `roof` a dormer. Dialog:
*Create face and cheek walls* / *Bind existing* (a wall within tolerance of
each line) / *Release*. `RoofItem.rebuild` re-derives bound ends through
the vertex API (no `.p1 =`; the gate's census forbids it). A direct drag
of a bound wall is refused. "Create" moves the dormer's `openings` onto the
face wall. Receipts: on the promoted `little-dormer-test`, create the
walls → three `walls` records on L2 with `bound_to`; drag C left by 12″ →
the left cheek's `v1`/`v2` move by 12″ and nothing else in the document
changes (set equality, both directions, on the `design_document()` diff);
the generated cheek/face triangles for that dormer **→ 0** (the
`_on_a_wall` yield, measured); a room drawn against face + cheeks + one
interior wall closes (`check(deep=True)` clean) and its area is the
expected rectangle. Undo: say plainly what the command stack covers here
(roof edits have no undo today, 0192) — a bound-wall move that undoes the
WALL but not the dormer is the resurrected-wall shape (row 44); if the
stack cannot hold both, refuse undo for the gesture and say so in the
status line rather than half-undo.

**P5 — windows, the receipt phase.** No new mechanism expected. On the P4
file: a `3040` on the bound face wall renders (ray test, a void); the
dialog's `openings` list reads disabled with the wall named; on
`dormer-test.json` (no wall under the face) it stays live and the existing
shadow (Phase C) draws. If P5 needs code, that is a finding against P1–P4,
reported, not absorbed.

**Tiers:** all five AMBER (user-visible). RED until the two fixtures exist
(§6, his first two gestures). Sonnet for the censuses and the memoisation;
not for P1's rule or P4's binding.

## 6. HIS PART — batched, three gestures and two check sessions

1. **Now:** open `wiscaway2026-11-01R1.json`, set L2's height back to
   **96″**, save as a new R-file under `fixtures/incoming/`. P1 and P2 are
   RED without it — a receipt taken on a 196″ storey measures the
   workaround, not the rule.
2. **After P3 lands headless:** open `little-dormer-test.json`, promote
   `rf2` to L2 in the dialog, save. P4's fixture.
3. **Check session A (after P1–P3 are stacked and green):** on file 1 in
   3D — the front gables close with the L2 wall, `8048` visible, no doubled
   wall at the gable; on L2's plan — the dash on the walls under the roof,
   the knee line in `BR2`/`BR3` at the stated coordinates; the dormer
   dialog's "Pinned to" and level selector, and the absolute heights it
   prints. The check request names the plan and the items, the standing
   rule.
4. **Check session B (after P4–P5):** create the walls on the promoted
   dormer, drag C and D, draw a room against them, put a window in the
   face, look in 3D.

## 7. NOT IN THIS ARC

Undo for roof edits as such (named at 0192, still open — P4 states its
boundary, it does not close this). A knee-wall object. D69's panel. The
`openings` list beyond its one remaining job. His own files stay his,
uncommitted, as every report says.

**Carried:** unchanged from [`0292`](0292-report.md), plus §0's two items.
