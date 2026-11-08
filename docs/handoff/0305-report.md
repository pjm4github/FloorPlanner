# 0305 — report: P4 of the 1½-storey arc — the `dormer` wall type

**Code, 2026‑11‑07.** The record ([`0197`](0197-ruling.md) §7). P4 of the arc
([`0296`](0296-ruling.md); [`0297`](0297-ruling.md) §2, order P1→P2→P3→P5→**P4**).
Built on branch `p4-dormer-wall-type`, cut from `main` (08364cc, the P5 merge,
[`0304`](0304-report.md)); **AMBER, not merged** — it waits on his **check
session B** (0294 §5 + 0296 §4). The branch carries P4 as several commits
(foundation → minting → a 3D-extent fix → the dialog checkboxes + undo safety →
two render fixes he reported mid-phase → the weld).

## 1. THE WALL TYPE, AND MINTING (0296 §2)

A `dormer`-type `WallItem` is a real wall: `type: "dormer"` in the schema
(enum; `STD_T["dormer"] = 6.0`; no version bump, PR #98's precedent), with a
`bound_to: {roof, part}` object **required iff `dormer`** and forbidden
otherwise (a schema conditional). A dormer **mints its own three walls** — face,
`cheek_left`, `cheek_right` — as `dormer` walls on the storey **ABOVE** the host
(`_level_above`), from `_dormer_wall_lines()`, their vertices DERIVED through the
vertex API at every rebuild and still written. Minted on by default once that
storey exists; a one-layer plan mints nothing. **The L2 attic room now closes
against them** (`detect_room` finds it — the keystone for his #1 knee line and #2
wall-join). Read-only: not selectable; every write refused with the dormer
named; no openings of its own. `sync_dormer_walls` is called from `rebuild`;
`remove_with_dormers` / `remove_dormer_walls` take them with the dormer or the
level. Plan mark: the categorical dormer-blue dashed centreline (0288's
`EXTERIOR_T` band); solid on L2 active, the ordinary ghost on L1.

**Round-trip.** `bound_to` is serialized (resolved to the dormer's minted id in
`design_from_scene`'s cross-level pass, carried in the `Wall` model and
`_WALL_MODELLED`) and re-adopted on load by geometry, so a save/reload does not
duplicate. The dialog's three "Walls on <level>" checkboxes
(`dormer_wall_parts`) opt a wall out; the choice is written as the roof's
`dormer_walls` (omitted when all on, in the schema + `Roof` model) and read on
load.

## 2. THE WELD — deform-to-follow (0296 §2, his ask #2)

A hand-drawn L2 wall whose end lands on a cheek's **back end** (the up-slope
terminus where the cheek meets the host) SHARES that cheek's `Vertex` — the
existing draw-release weld (`weld_wall_ends` → `share_coincident_ends`), which
already sees `dormer` walls (`graph_from_scene` admits them; `nearest_wall_*`
snaps to any active-floor wall). The one thing P4 had to add is on the OTHER
side: when the dormer moves, `sync_dormer_walls` re-derives the cheek's vertices,
and it used `detach_end` — which lands the end on a FRESH corner and leaves every
sharer behind, stranding the knee wall. It now RELOCATES a shared corner instead
(`Vertex.relocated_to`, rebinding every holder via `set_end_vertex`), so the knee
wall follows; a free end still DETACHES to a fresh derived corner, byte-identical
to the pre-weld sync. **The knee wall tracks the cheek when the dormer moves, and
the weld survives a save/reload** (the shared vertex serializes to one document
vertex, re-shared on load, then relocated — not detached — by the next sync).

## 3. HIS TWO MID-PHASE RENDER REPORTS, FIXED ON THE BRANCH

* **The ceiling poked through the roof** (2026‑11‑07: "the ceiling of a floor
  needs to be the lesser of the roof or the ceiling height … the L2 ceiling
  pokes through the roof"). A room ceiling was a flat slab at the storey top.
  `fp3d.build_model` now builds ceilings AFTER the roof clips are known and
  clamps each to `min(ceiling line, roof underside)`: each room triangle is split
  along every covering roof's cut lines and its knee and follows the lower of the
  two (`_ceiling_pieces`), so an attic ceiling follows the slope and nothing
  pokes; flat where no roof stands over it.
* **The knee line / wall dashes vanished on L2** (2026‑11‑07: "you can see the
  knee wall on L2 only when the dormers are on L1"). `roof_clip_spans` and
  `room_ceiling_break_lines` read a roof's datum as `floor_elevation(rf.floor)`,
  but a dormer's `floor` is only its EDITING home — its heights are measured from
  the HOST's level. A promoted dormer shifted its clip a whole storey. New
  `_roof_datum_floor(rf)` returns the host's floor for a dormer; both functions
  compute and key off it (a non-dormer, and a dormer on its host's own level,
  stay byte-identical).

## 4. UNDO (0296 §2's demand, stated before the phase)

A dormer edit now writes derived AND serialized walls on another floor, so the
diff path (`apply_design_difference`) would leave a restored wall beside a
re-minted one (row 44's "resurrected wall"). A plan with dormer walls now
**declines the diff and reloads in full**, which adopts them; `sync_dormer_walls`
also dedups by grouping every scene dormer wall of this dormer and keeping one
per part. The 3D-extent fix he reported ("nothing renders"): a climb-band header
wholly above the roof hit `_wall_under_roofs`'s `_box` fallback and extruded to
the `_CLIMB_TOP_IN` sentinel; it now builds nothing (a latent P5 §3 bug).

## 5. RECEIPTS

Tests: `tests/test_p4_dormer_wall.py` (12 — minting, read-only, `bound_to`
round-trip, reload-no-duplicate, delete, the opt-out checkboxes, undo, **the
weld follows a move, the weld survives save/reload, a free end detaches**),
`tests/test_viewer_ceiling.py` (the ceiling does not poke through the roof),
`tests/test_roof_clip.py` (a dormer's knee line ignores its editing level),
`tests/test_p5_dormer_face_windows.py`. Gate: full mode, GREEN. His own
receipts (0296 §3) are check session B's to run on `little-dormer-test.json`
(now two dormers): tick the walls on, draw the L2 room against face + cheeks +
one knee wall (`check(deep=True)` clean), drag control C from L1 and watch the
L2 cheek, the welded knee wall and the room follow; a drag on the cheek itself
refused; promote the dormer and watch no wall move.

## 6. NEXT

**Check session B** (0294 §5). On his word, land P5 + P4. Then his **#1** (the
L2 knee line — now that the attic room closes, it is drawn where the roof
crosses that room's ceiling) and **#3** (a dimensioned gable-end window
elevation, a separate feature). The remote `p5-dormer-face-windows` ref awaits
his approved delete. Named, not ordered: 0248's items 8–9.

## 7. `fixtures/incoming/` (ruled 2026‑08‑09 — name each, with its age)

Today 2026‑11‑07. `little-dormer-test.json` (today — the P4/P5 check fixture,
two dormers, his edit), `wiscaway2026-11-01R1.json` and `wiscawayL2-fix.json`
(2 days — his R-files, P1's receipts ran on the L2-fix one), `dormer-test.json`
(6 days — byte-identical baseline), `wiscaway2026-10-13R1.json` (22 days, the
garage-knob fixture), `house_cutout*` and `wiscaway2026-10-07R1.json` /
`…-10-11R2.json` / `…-10-11R3.json` and the two `_work/` dirs (27–31 days). The
`house_cutout` set and the older wiscaway files have sat across several handoffs
untriaged — his working plans, kept by his standing word, not awaiting a test;
`README.md` (2026‑08‑23) carries the three exits.
