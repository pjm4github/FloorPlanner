# The dormer as a furnishing — refactor plan

**Status:** DECIDED by Patrick 2026-11-16 (section 9). Phase 1 is built; phases 2-5 are ordered in `docs/handoff/0352-ruling.md`. Originally: a plan for review. Reviewer (Cowork),
2026-11-16, from Patrick's word of that evening and a read of the code at
`main`. Decisions wanted are in section 8.

## 1. The specification, read back

1. A roof stands on a level (say L1). It may be steep: the space under it is
   an attic.
2. A level above it (L2) is drawn like any other: exterior and interior
   walls, rooms, openings.
3. Where the roof is lower than L2's ceiling height, the plan shows the
   orange dashed **knee line**.
4. A **dormer is a furnishing**, dragged from the palette onto the roof, as a
   stair is dragged onto a floor.
5. The dormer has the control knobs the dormer has today (A-G of
   `docs/DORMER_CONROLS.md`) and a properties dialog.
6. Editing a dormer **computes no wall**. The only thing it recomputes is the
   knee lines, live, while it is moved or resized.
7. Getting the knee lines where the walls should go is the user's job.
8. Once it is placed, the L2 walls under it — drawn separately, by the user —
   rise to the dormer's roof or to the ceiling. Whether one is interior or
   exterior is whatever the user drew.
9. Every other L2 wall rises to the roof or the ceiling, whichever is lower.

The point: **the floor plan and the roof line stop writing to each other.**

## 2. What this replaces

The 1½-storey arc (0293-0297, merged) went the other way in its last two
phases. Phases 1-3 already hold the rule this plan needs; phases 4 and 5 are
what it retires.

| Today | Where | Lines | Under the plan |
|---|---|---:|---|
| Roof governs by absolute height; walls capped at the roof over them | `fp3d._wall_under_roofs` | — | **keep** — it is rule 9 |
| Knee line and wall dash | `roofs.roof_clip_trace`, `roof_clip_spans`, `room_ceiling_break_lines` | — | **keep**; add a drag-time path |
| Host roof cut away under a dormer | `roofclip.compute_roof_clips` | — | **keep** |
| A wall under a dormer climbs into it (0290, "no dormer walls of its own") | `fp3d._wall_under_roofs` | — | **keep** — it is rule 8, already built once |
| Dormer is a `roofs[]` record with a `host` | schema, `RoofItem`, `bridge` | — | **becomes a furnishing** |
| Knobs A-G | `RoofGripItem` | 239 | **move** to the dormer item |
| Dormer drawn with the H tool, shift-click | `view.py` | — | **retire** for palette drag |
| Minted face and cheek walls, `dormer` wall type, `bound_to`, the weld | `RoofItem.sync_dormer_walls` and around it; `walls.py`; `bridge.py` | 117 + | **retire** |
| Windows on the dormer face: `openings` on the roof record, `DormerWindowItem`, the dialog's window list, the sill datum | `roofs.py`, `dialogs.py` | 229 + | **retire** — a window is an opening in the wall the user drew |
| Generated face and cheeks in 3D, and their "yield to a house wall" logic | `fp3d._dormer_cheeks`, `_dormer_face` | 266 | **retire** |
| Dormer "edited on level", promote and demote | `levels.move_dormer_to_level`, `legal_dormer_levels`, `MOVEDORMER` | — | **retire** — it lives where it was dropped |

Tests that name dormers: 14 files, about 165 cases. Fixtures: 23 files hold 57
dormers, 72 `dormer`-type walls and 32 face windows.

**Two open defects go away with it.** 0350 §2 (minted dormer walls lose
`bound_to` on save and reopen) and the ten schema errors in Patrick's own
seed plans are both the minted-wall machinery. The design-loop candidates
already work the new way by hand: `dormer_walls: []`, with room walls as the
dormer's face and sides.

## 3. The target

### 3.1 The record

A furnishing, kind `dormer`, on the level it was dropped on:

```json
{"id": "f12", "level": "L2", "kind": "dormer", "pos": [534, 760],
 "rotation": 180,
 "state": {"form": "gable", "width_in": 192, "depth_in": 116,
           "eaves_h_in": 60, "pitch": 10, "ridge_offset_in": 0,
           "eave_overhang_in": [12, 12], "face_overhang_in": 12,
           "symmetric": true}}
```

- `pos` is the middle of the face line; `rotation` points the face.
- Heights are above **the dormer's own level** — the floor the user is
  standing on when they size it. (Today they are above the host's level, a
  storey down, which is why the dialog needed a datum correction.)
- **No `host` is stored.** The host is the roof whose surface is under the
  dormer, found by absolute height each time — the rule P1 already uses for
  walls. A dormer over no roof is drawn, reported, and cuts nothing.
- `furnishing.state` is already open in the schema; the keys are declared in
  a new `$defs/dormer_state`, as the stair's and cabinets' are.

### 3.2 The item

`DormerItem(FurnishingItem)`, built as `StairItem` is: its own paint, its own
`apply_params`, the generic properties dialog on double-click. It draws the
ridge, the two valley lines where it meets the host, the eave and rake
lines, and the knobs when selected. It draws **no wall**.

### 3.3 The knee lines

Three sources, one ink:

- the host roof against each room's ceiling plane, **minus the dormer's
  footprint** (built: 0307);
- the dormer's own planes against the same ceiling plane;
- nothing else.

While a dormer is dragged or a knob is down, only that dormer and its host
are recomputed, and the settle walk is held — the hold `roof_clips_held`
already provides. 0275 measured this trace at 214 ms a repaint before
caching; the drag path needs its own measurement before it is trusted.

### 3.4 The walls

One rule, in the 3D builder and the plan dash alike:

> A wall's top is the lower of its room's ceiling and the roof surface over
> it. Under a dormer, "the roof surface" is the dormer's.

This is `_wall_under_roofs` as it stands, with the generated face and cheeks
deleted and the climb kept. Section 8, decision 2 is the one open point.

### 3.5 Windows

A dormer window is an ordinary window in the wall the user drew under the
dormer's face. The gable-end elevation tab already reads walls (0311).

### 3.6 What the user is told

Because nothing closes the dormer automatically, a dormer with no wall under
its face or a side is open to the sky in 3D. The dormer's dialog and the
problems report say so (an advisory, not an error): "no wall under the face",
"no wall under the left side".

## 4. Migration

On load, an old plan is converted in memory and saved in the new form:

| Old | Becomes |
|---|---|
| `roofs[]` record with `host` | `furnishings[]` record, kind `dormer`, same geometry |
| `dormer`-type wall with `bound_to` | an ordinary `exterior` wall on the same two vertices |
| `dormer`-type wall with no `bound_to` (the seed defect) | the same |
| `openings` on the dormer record | a window in the converted face wall, at the same place and sill |
| `dormer_walls` narrowed to fewer than three | the walls that were off are simply not there |

So a migrated plan **looks the same**: the walls the app once minted are now
plain walls the user owns. A face window whose face wall was switched off has
nowhere to go; it is listed in the load report, not dropped silently.

The schema keeps accepting the old forms (version 6 documents exist); the
app stops writing them. Whether that is a version 7 is decision 5.

## 5. Phases

Each is its own branch and its own check. Old and new dormers both work
until phase 4.

| Phase | What | Who | Tier |
|---|---|---|---|
| 0 | Decisions (section 8). Measure: the drag-time knee recompute; which of the 165 tests pin rules 8 and 9 (keep), which pin minted walls (go) | Code | — |
| 1 | `floorplanner/parametric/dormer_geometry.py`, pure, no Qt: state to the roof geometry `roofclip` already takes; footprint, valleys, knee segments for a ceiling plane; `normalize_state`; the parametric kind, its dialog specs and findings | Reviewer, in the furnishings lane | GREEN |
| 2 | `DormerItem`: palette entry, drag-drop, knobs A-G moved from `RoofGripItem`, host found by height, live knee lines, save and load | Code | AMBER |
| 3 | 3D and clip read furnishing dormers through the phase-1 adapter; generated face and cheeks deleted; wall rule per decision 2; ceilings | Code | AMBER |
| 4 | Migration on load; the writer stops; delete minted walls, `bound_to` handling, `DormerWindowItem`, the dialog's window list, level promote and demote, the H tool, `MOVEDORMER`; fixtures re-saved; tests rewritten | Code | AMBER |
| 5 | `docs/DORMER_CONROLS.md`, `COMMANDS.md`, schema text, gallery | Code | GREEN |

## 6. What is lost, said plainly

- The app no longer closes a dormer for you. A dormer dropped on a roof with
  no walls drawn under it is a hole.
- The dormer-window editor (list, sill measured from the dormer floor,
  clamped under the ridge) goes; the ordinary window dialog replaces it and
  does not know about the ridge.
- A dormer can no longer be edited from the storey below.
- The knee wall no longer follows the dormer when the dormer moves (the 0296
  weld). That is the specification: rule 7.

## 7. Risks

- **Roof clipping.** The clipper already does not return on one main roof
  with two opposed cross gables (0350 §1). Furnishing dormers feed the same
  clipper. That defect should be understood before phase 3.
- **Undo.** The difference path declines plans with dormer walls today and
  reloads in full; after phase 4 a dormer is an ordinary furnishing and
  should take the fast path. To be shown, not assumed.
- **Shed dormers.** Their high edge lies on the host; the "meets the host"
  rules differ from a gable's (0256). The geometry module must carry both
  forms from the start.
- **Twenty-three fixtures** change on re-save. Each needs a before-and-after
  3D comparison, not a schema pass alone.

## 8. Decisions for Patrick

1. **A furnishing record, or a roof record that merely behaves this way?**
   Recommended: a furnishing, as you said. It gets the palette, the dialog,
   copy and paste, and undo for free, and it ends the special cases a
   "roof with a host" needs. Cost: the migration in section 4.
2. **How high does a wall under a dormer go?** Your words: "up to the dormer
   roof line (or ceiling)". Recommended: an EXTERIOR wall rises to the roof
   surface even above the ceiling line, so a gable face closes to its peak;
   an INTERIOR wall stops at the lower of roof and ceiling. The alternative —
   every wall stops at the ceiling — leaves each gable face open above
   ceiling height.
3. **Knobs C and D** move the dormer's side walls and face wall today. With
   no walls, recommended: they stay, as the lines where the dormer's roof
   ends (its eaves and its gable end), drawn as guides. They are what the
   user lines their own walls up against.
4. **Migration** as section 4: minted walls become ordinary walls, face
   windows become wall windows. Or: old plans keep old dormers until edited,
   as legacy stairs do. Recommended: convert — two dormer systems living
   side by side is the cost this refactor is meant to remove.
5. **Schema version.** Recommended: stay at 6 (the state object is open, old
   forms still read), with the retired keys marked deprecated.
6. **The Wiscaway design loop** uses dormers. Recommended: it carries on with
   hand-closed dormers, which are already this model, and moves to the
   furnishing when phase 2 lands.

## 9. Decided (Patrick, 2026-11-16)

1. **A furnishing record**, in the existing **Framing** palette group, with
   `stairs`, `elevator` and `post` (corrected 2026-11-16, ruling 0353: no new
   "Structure" group). He will tidy old plans by hand where the conversion
   cannot.
2. **Exterior walls rise to the gable face's peak.** Interior walls stop at
   the lower of roof and ceiling.
3. **Knobs C and D stay as guides.** They draw no wall.
4. **Convert on load where possible. Never abort.** What cannot be converted
   is listed in a WARNING dialog and the plan opens anyway. (Headless
   callers get the same list on `_import_errors`, no dialog.)
5. **Schema stays at version 6.**
6. **The Wiscaway loop is paused** (watcher stopped, ruling 0353) until the
   furnishing exists; it then resumes with furnishing dormers.

Consequences for sections above: section 4's table stands, with "listed in
the load report" now meaning that warning dialog; section 5's phase 1 is
done (`dormer_geometry.py`, `dormers.py`, `tests/test_dormer_geometry.py`,
`$defs/dormer_state`). One change from section 3.1's sketch: the state keys
are the flat ones in `dormer_geometry.STATE_DEFAULTS` (`span_left_in`,
`pitch_12`, ...), not `width_in` / `depth_in` pairs.
