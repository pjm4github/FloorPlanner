# 0333 — ruling: the parametric ISLAND (slots + seats), a range HOOD and over-range MICROWAVE, gloss LAUNDRY finishes and LIGHTS are built — un-gated; and the lights need one piece that is Code's to build

**Reviewer (Cowork), 2026-11-15.** Patrick, today: the island must take the same
parameter dialog as the other cabinets, with the number of seats a parameter
and "the items under the island a placeholder of cabinets and appliances";
cabinets on one side, short-backed stools on the other; a stove hood and a
microwave mountable over the stove; washer and dryer in gloss white, silver or
black; and light components that "provide a light source, shape and color that
can be adjusted". **Tier: AMBER.**

## 0. THE TREE AS FOUND

`HEAD` is `combined-walk-test` with 34 paths STAGED and nothing committed since
`432d82e`. This session edited working files on top of that — so
`cabinet_geometry.py`, `cabinets.py`, `items.py`, `_gen_assets.py`, `fp3d.py`,
the manifest and three test files now show as staged AND modified. The staged
content is untouched; this work is the unstaged delta. No git was run beyond
`status` / `log` with optional locks off.

## 1. RUN, AND NOT RUN

Stand-in runner: `test_island_and_lights` (new, 12 fns), `test_cabinet_geometry`,
`test_cabinet_viewer` (+5), `test_viewer_model`, `test_vehicle_profile`,
`test_gen_assets` — **129 cases pass**; the one failure is the PyQt6 import.
**Never run:** the three new Qt tests appended to `tests/test_cabinet_item.py`,
every dialog path, pytest, ruff, the gate, the real 3D view.

## 2. WHAT WAS BUILT

All in `cabinet_geometry.py` (the calculator the viewer and generator load by
path) unless noted.

- **Island** (`kitchen_island`, `island_sink`, now type `island`). Six SLOTS,
  each a code from `ISLAND_SLOTS` — base 12-36, drawer base 18-30, sink base
  30/36, dishwasher 24, or empty. Each slot is built by the SAME code that
  builds that cabinet against a wall, turned to face out; slot 1 is at the
  left as you face the doors. The island's length is the sum of its slots
  (derived, never stored). `seats` (0-8) puts short-backed stools along the
  other side, under the overhang. ONE countertop covers all of it — so a
  dishwasher in an island is under the counter — and opens over a sink's bowls.
- **`range_hood`** and **`microwave_otr`** — two new catalog kinds, wall-mounted
  appliances with `floor_to_bottom_in` (66 and 54) and the standard / match /
  custom finish.
- **Washer and dryer** — gloss, in white (default), silver or black; nothing
  else is offered or accepted.
- **Lights** — five new kinds (`light_recessed`, `light_flush`, `light_pendant`,
  `light_linear`, `light_sconce`), one definition. Parameters: shape (six),
  size, light colour (four whites by colour temperature, five colours),
  output in lumens, beam, pendant drop, sconce height. A ceiling fixture hangs
  from THE CEILING OF THE ROOM IT IS IN. The lens is drawn in the light's
  colour (`light_emit#rrggbb`).
- **`cabinets.py`** — the dialog specs, advisories and summaries for the above.
  **`items.py`** — `_owning_room`, `_room_ceiling`, `ceiling_in` in the context.
- **`_gen_assets.py`** — seven new symbols, their `SOLIDS` rows, a `Lighting`
  palette group, the hood and microwave in `Kitchen`; the catalog is now 103.
- **`viewer/fp3d.py`** — `Model.lights`; `build_cabinet` takes the ceiling and
  returns the light; `stats["lights"]`.
- **`tests/test_viewer_model.py:75`** — the pinned catalog size, 96 -> 103.

## 3. THE LIGHT SOURCES — CODE'S PIECE, AND THE CONTRACT FOR IT

A fixture is geometry; this lane built that. **Light is the renderer's**, and
the renderer is `fp3dq.py` / `scene.qml`, which are Code's (and Phase 2's).
`build_model` now reports what to light with:

```
model.lights = [ {"id": <furnishing id>,
                  "pos": (x, y, z),          # WORLD frame, inches, z up
                  "colour": (r, g, b),        # 0..1
                  "lumens": 800.0,
                  "kind": "point" | "spot",   # a spot aims straight DOWN
                  "cone_deg": 60.0 | 180.0}, ... ]
```

**Ruled for Code to build (AMBER):** in the Qt Quick view, one `PointLight` or
`SpotLight` per entry, positioned through the SAME recentre and z-up -> y-up
remap the meshes take (`pos - ctr`, then `(x, z, -y)`), coloured from `colour`,
brightness scaled from `lumens`. Conditions:

1. **Measure before choosing the scale.** Report what brightness an 800 lm
   point at 8 ft gives against the existing three directional lights, and pick
   the lumens -> brightness factor from that, not from a guess.
2. **Cap what casts shadows.** Shadow-casting lights are the expensive ones;
   start with none of these casting, and say what the frame cost of N lights is.
3. **A plan with no lights renders exactly as today** (`model.lights == []`).
4. The lens mesh (`furnishings:light_emit#...`) should read as lit regardless
   of scene lighting — an emissive factor, or unshaded. Until then it is just
   a pale box.
5. While in `_pbr`: the one-line sheen fix 0329 §4.1 asked for (strip the
   `#rrggbb` before the materials lookup). The laundry now uses it by default,
   so every washer currently gets the default roughness in the Qt Quick view.

## 4. MEASURED

- `kitchen_island` at its preset: 72 x 39 x 36, two B36 slots, three stools —
  inside the catalog box. Pulls at f < 3 (the door side), stools beyond the
  cabinet backs, nothing outside the footprint.
- DW24 + B36 gives a 60 in island; the dishwasher's parts are appliance roles,
  the base's are cabinet roles, slot 1 at +x.
- Hood 66 -> 84 in, microwave 54 -> 71 in.
- Washer: `sheen_gloss#f2f2ee`; `colour: red` normalises back to white.
- A pendant in a 108 in room: fixture top at 108, source below the lens, the
  source reported at world (50, -70) for a plan position of (50, 70).
- Still: `docs/evidence/0333-island-lights/island_hood_lights.png` (matplotlib
  painter; its triangle-sort artefacts on the countertop are the painter's).

## 5. KNOWN LIMITS

1. **The island's PLAN SYMBOL does not follow its parameters.** It is the
   catalog SVG stretched to the new length: the stools drawn on the plan stay
   three whatever `seats` says, and the door ticks do not track the slots.
   3D and (later) elevations are right; the plan is not. The fix is a painted
   plan symbol from the parts, and it belongs with phase 5.
2. A slot holds a base, a drawer base, a sink base or a dishwasher. No range,
   cooktop, wine cooler or open shelving yet.
3. Stools are fixed counter height (24 in seat) and tuck to fit a short
   overhang; under 6 in of room none are drawn.
4. A light's footprint on the plan is small; nothing draws its throw.
5. `washer` / `dryer` in existing plans change from stainless to gloss white.
   That is the request, and it is a visible change to old plans.
6. The hood and microwave are not tied to a range: they are placed over one by
   hand, and nothing checks the clearance.

## 6. PATRICK'S CHECK

1. Double-click an island: set "Under the island" slots to a dishwasher and a
   base; set Seats. 3D: cabinets one side, short-backed stools the other, one
   countertop.
2. Place a Range Hood and an Over-Range Microwave above a range; change
   Height from floor.
3. Washer and dryer: white by default; set silver, black.
4. Lighting palette group: place each light; change shape, colour, output.
   (The fixtures appear now. They will LIGHT the room once §3 is built.)

## 7. OWED

- **Code:** gate; commit this lane's delta by path, apart from Phase 2; then
  §3 on a branch. Report in the next number, failures verbatim.
- **Reviewer:** fixes from the report. No git.
