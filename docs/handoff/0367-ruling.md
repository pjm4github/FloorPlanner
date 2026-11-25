# 0367 — ruling: a PYRAMID ROOF structure furnishing (gazebo / many-sided roof) is ORDERED. Four stages, AMBER; plus the wicker set to gate and commit

**Reviewer (Cowork), 2026-11-24.** New work on Patrick's word; answers no
report. Numbered 0367 because 0365 and 0366 are in use as work labels (PR #111;
branch `bathroom-vanity-mirror-0366`) whose reports are still to come. Not run
by me: the gate, pytest, the app. It does not jump the queue: it starts when
0365 and 0366 have landed (one AMBER at a time), or on his word.

## 1. What Patrick asked for

> "make another structure furnishing that will allow me to make a gazebo or
> multisided pyramid roof that can be dropped on a ceiling. [...] It should
> have a room that it sits on and it should be able to be welded into the
> existing roof."

- **R1** a furnishing, beside the other structure kinds (the Framing group:
  stairs, elevator, post, dormer). No new group.
- **R2** many-sided: a pyramid over a regular polygon.
- **R3** it is dropped on a ceiling and has a room it sits on.
- **R4** it can be welded into the existing roof.

**Why a new kind and not a roof form — measured, 2026-11-24,** on his
`wiscaway-c03-roofA-garage.json` with `fp3d.build_model`: a `roofs[]` record
is a ridge with at most four planes at right angles. A hipped record over the
NOOK is cut into two pieces by the main roof (`roofclip.py`'s anchor rule), on
L1 and on L2 alike; two pyramids turned 45 degrees to each other resolve 4 of
the 8 sectors. `roofs[]` stays closed: no third `form`.

## 2. The kind — reviewer's defaults, his to overturn at the stage 2 check

Kind `pyramid_roof`, palette name "Pyramid Roof", Framing group. `pos` is the
CENTRE (the apex in plan). `rotation` is the furnishing's own field; at 0 one
face's outward normal points up the screen. Heights are above ITS OWN level's
floor, as the dormer's are. State, declared in the schema as
`$defs/pyramid_roof_state`, not enforced; the schema stays at 6:

| key | meaning | default |
|---|---|---|
| `sides` | 3 to 12 | 6 |
| `inradius_in` | centre to the WALL line (the eaves-start line) | 72 |
| `eaves_h_in` | the eaves-start line | the ceiling of its room |
| `eaves_bind` | `room_top` or `manual` — the roof record's own words | `room_top` |
| `pitch_12` | rise per 12 of run, every face | 10 |
| `overhang_in` | eave past the wall line | 12 |
| `weld` | `auto` or `off` | `auto` |

Apex height is DERIVED (eaves + inradius x pitch / 12) and shown. Whether it
is also editable the dormer's way is Code's call; say which.

## 3. R3 — the room it sits on

`room` is the room it was dropped on: assigned at the drop, never re-derived,
carried when the room moves — the furnishing field's existing meaning. Under
`room_top` its eaves follow that room's `ceiling_height_in`, re-derived when
the ceiling is edited. Its room's walls rise to it by the dormer's wall rule
(0352 phase 3): exterior to the surface, interior to the lower of surface and
ceiling. A `post` under it rises to its underside.

Findings, none of which blocks: `pyramid.no_room` (WARNING: sits on no room,
eaves are manual); `pyramid.off_room` (ADVISORY: the wall-line polygon does
not lie on its room's walls, and by how much); `pyramid.buried` (ADVISORY:
wholly under another roof, nothing shows).

## 4. R4 — the weld

Where the pyramid and any roof overlap in plan (a `roofs[]` record or a dormer
furnishing, any level, by ABSOLUTE height), **each is drawn only where it is
the HIGHER surface.** The boundary is the equal-height line, exact: both
surfaces are planar by pieces, so it is interpolated, never sampled. The lower
surface is CUT there, in plan and in 3D, not merely hidden.

This is deliberately NOT `roofclip.py`'s anchor rule ("a roof stops at the
seam, on the side its own body is on"). That rule is right for two ridges
meeting at an L and is what cuts a pyramid in two today. Existing roof-to-roof
behaviour does not change. `weld: off` — it ignores every roof and every roof
ignores it.

## 5. Stages. Each its own branch

1. **Geometry and kind. GREEN.** `floorplanner/parametric/pyramid_geometry.py`
   — pure, no Qt, loadable by path as the stair's and dormer's are: state
   defaults and `normalize_state`, wall-line and eaves polygons, the face
   planes, `surface_height`, hips, the local-to-plan transform.
   `parametric/pyramids.py`, built and NOT registered. Tests. The schema def.
2. **The item, free-standing. AMBER.** Catalog entry and symbol
   (`_gen_assets.py`; the size pin goes to 115 after §8); `register`;
   drag-drop onto a room; the generic dialog; the plan symbol (wall-line
   polygon, eaves polygon, hips, apex); one knob for the radius, snapping to
   the grid unless Shift is held; 3D faces with the roof slab's thickness;
   §3's walls and post. No weld yet: it draws whole over whatever is there.
3. **The weld. AMBER.** Only after C2's read-back is ruled on.
4. **Documents. GREEN.** `COMMANDS.md`, schema text, gallery, a page under
   `docs/furnishing-spec/`.

## 6. Conditions

- **C1 — one geometry.** The plan symbol, the dialog, the 3D faces and the
  weld all read `pyramid_geometry.py`. No second formula in `items.py` or
  `fp3d.py`.
- **C2 — read-back before stage 3,** as a report: where the weld is computed
  (an extension of `roofclip.py`, or its own pass) and why; its cost on
  `wiscaway-c03-roofA-garage.json`; and proof that it RETURNS — 0350 §1's
  three-roof case with a pyramid added, timed.
- **C3 — differential receipt.** Every fixture with no pyramid builds the same
  before and after stage 3: triangle count and bounds, per file, every
  difference named.
- **C4 — fail-first.** The weld test must go red with the cut removed; show
  that it did.
- **C5 — never abort.** A pyramid that cannot be built still loads, draws red,
  and says why in its dialog and in `model.notes`.

## 7. Evidence — `docs/evidence/0367-pyramid-roof/`

One plan JSON and one image (plan + 3D, one camera per case) each, and an
`INDEX.md` with an empty `Patrick's check` column. E1 is owed with stage 2,
E2-E5 with stage 3.

- **E1** free-standing hexagon: an exterior room 12 ft across flats, six
  posts, `sides` 6.
- **E2** an octagon bay on an eave, mid-wall, under a plain gable roof.
- **E3** the NOOK — the picture he asked for. A COPY of
  `wiscaway-c03-roofA-garage.json` (his file is not edited) with the NOOK
  reshaped to the bay (144,402) (132,390) (132,330) (174,288) (234,288)
  (246,300); `sides` 8, centre (204,360), `inradius_in` 72, eaves 128,
  pitch 12, turned so faces lie on x = 132 and y = 288, and within 1/8 in of
  x + y = 462. Expected: three window walls under three facets, the rest
  welded into the main roof.
- **E4** `sides` 4 astride a ridge.
- **E5** E3 with `weld: off` — both drawn whole.

Patrick's checks, batched: after stage 2, E1 by eye plus drag, rotate and the
dialog in the app; after stage 3, E2-E5 by eye and E3 opened in the app.

**Not ordered here** — say so if it tempts: a roof that follows an irregular
room outline; truncated tops, lanterns, finials; a dormer hosted on a pyramid;
two pyramids welding to each other (draw both whole, advisory
`pyramid.overlap`); vaulting the room's ceiling into the pyramid.

**Model.** Opus for stages 1-3 and the C2 read-back; Sonnet for stage 4.

## 8. Also in the tree, uncommitted: the wicker sunroom set (reviewer's furnishings lane)

Patrick, 2026-11-24: wicker chairs smaller than the 33 in armchair. Edited in
place on `bathroom-vanity-mirror-0366`: `_gen_assets.py` (helper
`wicker_seat`; `wicker_chair` 27x28, `wicker_chair_small` 23x24,
`wicker_table` 20 round; their `SOLIDS` rows; material `wicker`; the Sunroom
group), the regenerated `manifest.json`, `groups.json`, `materials.json`,
three new SVGs, and the size pin in `tests/test_viewer_model.py`, 111 to 114.

Checked by me: the generator run on a copy writes 114 symbols and changes only
those files; `build_model` gives both chairs as prisms with back and arms and
the table as a slab; no `transform`, no stray `data-` attribute. **Not run:**
ruff, pytest, the gate. Do not fold it into 0366's commit: gate, then commit
by path as its own commit; failures verbatim. `wiscaway-c03-nook.json` and
his later plans use these kinds.
