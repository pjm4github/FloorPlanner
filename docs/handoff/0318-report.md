# 0318 — report: the whole-house-side elevation now spans ALL LEVELS with the ROOF, DORMERS and GABLE ENDS — built COMPOSITIONALLY, the eave overhang the roof's own geometry — on branch `full-elevation`

**Code, 2026‑11‑12.** The follow‑on 0317 §5 named: *"the whole‑house‑side
elevation across ALL LEVELS, with the ROOF, the DORMERS and the GABLE ENDS."*
His direction 2026‑11‑11, a DIFFERENT APPROACH from the 3D‑projection /
hidden‑line path first sketched: *"lets take a different approach … I can get
each wall one by one … assemble all the walls that are part of a complete side
of the building … one floor first then … the second floor on the first floor
then … the roof elevation on that image then compose the entire elevation view.
The dormer already has an elevation view from the gable end."* Built on branch
`full-elevation`; **his word: "land it"** — report on `main`, the one branch
commit, then merged.

## 1. WHAT HE ORDERED

0317 capped the house‑side elevation at the flat ceiling of one storey. He
wanted the FULL exterior elevation — every storey's walls stacked by their floor
elevation and the roof / dormer / gable geometry above, drawn to the roofline —
but reached **compositionally**, not by a 3D model and a depth buffer: each wall
and each roof a flat 2‑D piece on one shared plane, assembled and painted. Then,
checking the first wiring, four tweaks (2026‑11‑11): (a) a PURE FRONT‑ON look
(the main gable end read slightly sloped); (b) the main roof must OVERHANG the
walls at the eaves; (c) rear windows / doors / dormers must not show on the
front; (d) the garage roof STACKING corrected — *"look at roof elements in
relation to the walls that are being rendered then figure out the stacking when
viewed from the front."* Then (2026‑11‑12): the eave overhang must be the roof's
OWN geometry — *"determine the overhang based on the roof dimension: the eave
height, roof angle and the overhang … Make sure that the overhang and all roof
parameters are stored in the plan (and make the schema match)."*

## 2. WHAT IT DOES (`CameraItem._house_elevation`, `cameras.py`)

- **Compositional 2‑D pieces, painted far → near.** Each exterior wall and each
  roof face is a flat polygon on one plane: horizontal axis `u` = the
  camera‑right projection, vertical axis = ABSOLUTE world height
  (`floor_elevation(floor) + height`). Because every exterior wall is a vertical
  plane, whole‑piece painter order by depth is an EXACT hidden‑surface removal —
  no per‑pixel z‑buffer. ~17 ms on his wiscaway plan, against ~2 s for the 3D
  build‑and‑project path it replaces. `dialogs._paint_house_elev` draws each
  piece as a white‑filled polygon with a dark outline, openings on their walls,
  the dormer face windows frontmost, a baseline + floor label + height dimension.
- **(a) Front‑on snap.** The projection axis is aligned to the dominant
  exterior‑wall direction (the facade), so a camera a few degrees off square no
  longer skews the roof — the main roof's eave and ridge read exactly horizontal.
- **Rake‑aware wall clip.** Each top‑of‑stack wall's top follows
  `min(roof surface above it)` sampled across its length (`_roof_surface_z`); a
  wall with a storey stacked on it stops flat at the next floor base
  (`higher_base_over`). The gable wall climbs toward the ridge.
- **(c) Rear culled.** A roof face whose outward normal turns away from the
  camera is dropped; a DORMER whose face gable turns away is dropped WHOLE (roof
  + its windows), so only the front dormers show. Rear wall openings never enter
  (a front wall must separate camera‑side outdoors from an interior room).
- **(d) Stacking.** Roofs and walls sort by their NEAREST edge
  (`min` depth over the piece), so a wing / garage roof that comes forward stacks
  IN FRONT of a roof set behind it.
- **(b)+(overhang) The eave is the roof's OWN geometry, not a drawn‑in constant.**
  `overhang_in[side]` is the soffit's plan‑perpendicular reach past the eaves
  line; `end_overhang_in` is the RAKE past each GABLE end; the fascia drops below
  the eaves height by **the true slope × that soffit reach**
  (`slope = (ridge_h − eaves_h) / span`). A roof that stores a real overhang laps
  over the wall below and projects past it; a roof that stores 0 sits flush —
  the faithful picture of its parameters. A near‑vertical stub side (a
  half‑gable's degenerate span, whose pitch would be all but vertical) carries no
  soffited eave, guarded by `MAX_EAVE_PITCH = 3.0` (36:12, steeper than any real
  roof), so an overhang set on such a side projects nothing instead of dropping
  the fascia hundreds of inches off the drawing.

## 3. STORAGE & SCHEMA — VERIFIED COMPLETE, NOT CHANGED

Every roof parameter the elevation reads already ROUND‑TRIPS and is already in
the schema; this was verified, not altered. `design/bridge._roofs_of` writes
`ridge`, `eaves_h_in`, `ridge_h_in`, `overhang_in`, `span_in`, `eaves_bind`,
`gable`, `marker_end`, `form`, `hip_run_in`, `end_overhang_in`, `wall_span_in`,
`box_half_in`, `openings`, `dormer_walls`, `host`, `uid`; `_build_roofs` reads
them back; `design-schema.v6.json`'s `roof` object describes each. Proven on his
plan: `overhang_in [16,16]` / `end_overhang_in [12,12]` set on the three main
gable roofs wrote into `design_document()` and reloaded identically (the shed's
dead side correctly clamps to 0). So the overhang the elevation now draws is
exactly the value stored in the plan and set from the roof‑parameters dialog /
the soffit grips.

## 4. RECEIPTS (instrument `docs/evidence/0318-full-elevation/render.py`)

A two‑storey house (L1 at 0, L2 at 108) with a gable roof on L2, a camera at a
GABLE END and another at an EAVE side. `gable_end.png` (mode `house_elev`, 5
pieces, 4 openings) composes the gable wall climbing to the ridge, the roof
faces, and both storeys' openings; `eave_side.png` (3 pieces) is the long eave
side. The receipt roof stores overhang 0, so the eaves read flush — the
parameter faithfully drawn.

## 5. TESTS

`tests/test_cameras.py` (28, up from 27): the full elevation is a `house_elev`
composite of wall + roof pieces to the gable; only the camera‑facing openings
draw; and the new
`test_a_roof_overhang_is_its_own_geometry_and_degeneracy_is_guarded` — a stored
overhang drops the fascia below the eaves and projects past the wall, a stored 0
sits flush at the eaves height, and a half‑gable's degenerate stub side with a
16″ overhang leaves the extent bounded (the guard). Gate: full, GREEN.

## 6. NEXT — NAMED, NOT ORDERED

His plan's main roofs (rf1/rf2/rf3) currently store `overhang [0,0]`, so they
render flush until he gives them an eave overhang. 0248's items 8–9 (the porch
steps / base, a porch roof turning a corner) still stand. A small near‑edge‑on
dormer‑rake sliver remains cosmetic.
