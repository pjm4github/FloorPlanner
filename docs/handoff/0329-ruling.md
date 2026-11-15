# 0329 — ruling: parametric CABINETS, the room STYLE and appliance finishes are BUILT (phases 1-4 of the plan) — un-gated, the Qt side never run; the camera elevation (phase 5) is held behind camera Phase 2

**Reviewer (Cowork), 2026-11-14.** Patrick answered the plan's decisions the
same day (recorded in `docs/furnishing-spec/CABINETS_AND_ROOM_STYLE_PLAN.md`
§8), adding an appliance MATCH feature with matte / gloss / gel-coat finishes
in a colour, and extending the lane to the Room Properties dialog.
**Tier: AMBER.** This tree also still holds the un-gated vehicles of 0328 §5.

## 1. RUN, AND NOT RUN

| | status |
|---|---|
| `py_compile`, every new and changed file | clean |
| `test_cabinet_geometry` (16 fns), `test_cabinet_viewer` (9), with `test_viewer_model`, `test_vehicle_profile`, `test_stair_*`, `test_gen_assets` | **156 cases pass under the stand-in runner**; the one failure is the test that imports PyQt6 |
| `tests/test_cabinet_item.py` (13: item, both dialogs, Room Properties, document, undo) | **never run** |
| `cabinet_view.py`, the `items.py` and `dialogs.py` changes | **never executed** |
| `ruff`, pytest, the gate, the real 3D view | not run. An AST pass found and removed two unused imports and two assigned lambdas (E731); it is not ruff |
| the JSON schema | parses; **not** validated against the corpus (`test_schema.py` needs `jsonschema`) |

## 2. WHAT WAS BUILT

- **`floorplanner/parametric/cabinet_geometry.py`** (new, pure, no imports).
  The ONE source for: the style vocabulary (9 finishes, 9 countertops, 4
  hardware finishes, 4 door styles, 3 sheens, 10 colours), their 29 materials,
  the 20 PRESETS (15 cabinets, 5 appliances), `normalize_state`,
  `resolve_materials` (own choice -> room style -> default) and
  `cabinet_parts`. Loaded BY PATH by the viewer and by the generator.
- **`cabinets.py`** — one `CabinetKind` class registered for all 20 kinds;
  **`cabinet_view.py`** — a front elevation and plan inset painted from the
  parts, in their resolved colours.
- **`registry.py`** — `to_state` and `footprint` on the contract (defaults keep
  stairs unchanged).
- **`items.py`** — `FurnishingItem`: `_room_style`, `room_style` in the
  context, `_apply_footprint`, and `apply_params` now asks the kind what to
  write. `make_furnishing` resizes a cabinet loaded with a width.
- **`dialogs.py`** — `RoomPropertiesDialog`: four style rows (cabinet finish,
  door style, countertop, hardware). "(default)" writes nothing; an unstyled
  room keeps no `style` key, so no existing document changes.
- **`_gen_assets.py`** — loads the calculator, merges its materials, writes
  `cabinet` on every manifest entry, and REFUSES to write if a preset's
  footprint or height disagrees with the catalog.
- **`viewer/fp3d.py`**, furnishing region — `_load_parametric`, `CABGEO`,
  `build_cabinet`, the hook, `stats["cabinet_kinds"]`; `_colour` accepts a
  `material#rrggbb` name.
- **`design-schema.v6.json`** — `room_properties.style` -> `$defs/room_style`;
  `$defs/cabinet_state`, `appliance_state`, `stair_state` DECLARED and
  described; `furnishing.state` stays open. No version bump; every addition is
  optional, so a v5/v6 file validates as before — **Code: confirm on the
  corpus.**
- **`tests/test_viewer_model.py`** — one test (`test_elevation_places_an_item_off_the_floor`)
  now reads all of a cabinet's vertices, not its first mesh; a cabinet is
  several meshes.

## 3. MEASURED

All 20 presets build at exactly their catalog width, depth and height (the
generator enforces it; a base cabinet is 4.5 + 30 + 1.5 = 36.0, a wall cabinet
54 -> 84). A base cabinet went from 12 triangles in one material to 20 parts in
4. Every mesh of every kind encloses positive volume. Pulls are at world -y
(the front) and move to +y under a 180 degree rotation. One room style changes
every unoverridden cabinet in it; a cabinet's own finish wins; an unknown key
falls back to the default. Still: `docs/evidence/0329-cabinets/kitchen_runs.png`
— one run of 13 items in three styles (matplotlib painter, not the app).

## 4. KNOWN LIMITS

1. **Sheen is not yet seen by the Qt Quick view.** `fp3dq._pbr` looks the mesh
   name up whole, so `sheen_gel_coat#a3211c` gets the default roughness. The
   COLOUR is right in both viewers. One line fixes it — strip the `#...` suffix
   before the lookup — and it is in `fp3dq.py`, Phase 2's file. **Code's edit,
   not this lane's.**
2. **No countertop bridges an appliance** (decision D2): the dishwasher and the
   range show their own tops in a run. A countertop-run item is the remedy.
3. **A resized cabinet grows about its centre**; the user re-seats it.
4. **The plan symbol is stretched** to a new width, not redrawn.
5. **The camera elevation still draws labelled boxes**, and reads a cabinet's
   height from the catalog, not its parameters. Phase 5.
6. **Islands** (`kitchen_island`, `island_sink`) are untouched boxes.
7. The diagonal corner's door carries no pull; the L-shape's second door none.
8. `validate.py` has no cabinet-state invariant. Bad values are normalised to
   defaults at read; they are not REPORTED. A real gap against "the application
   validates" — say if it should be a defect record.

## 5. PATRICK'S CHECK — one batch, after the gate

1. Open a plan with a kitchen: cabinets have doors, toe kicks and tops in 3D,
   and nothing has moved.
2. Room Properties on the kitchen: set cabinet finish and countertop; reopen
   the 3D view — every cabinet in that room follows.
3. Double-click a base cabinet: elevation and plan preview; change width,
   front, door style; OK. Footprint and 3D follow. Ctrl+Z once undoes it.
4. Give one cabinet its own finish; change the room style; that one stays.
5. Double-click a wall cabinet: change Height from floor.
6. Double-click the dishwasher: Match the room's cabinets. The range: Custom,
   gel coat, red.
7. Sink base and a vanity: bowls in the top, a faucet.
8. Save, reopen: sizes, finishes and the room style are as left.

## 6. OWED

- **Code:** gate. Commit by path, separately from the vehicles (0328 §5):
  `floorplanner/parametric/` (three new files, `registry.py`, `__init__.py`),
  `floorplanner/items.py`, `floorplanner/dialogs.py`,
  `floorplanner/design/design-schema.v6.json`, the three `tests/test_cabinet_*.py`,
  `docs/furnishing-spec/`, `docs/evidence/0329-cabinets/`. **Four paths carry
  BOTH lanes' hunks and cannot be split without `add -p`:** `_gen_assets.py`,
  `assets/furnishings/` (manifest, materials, README), `floorplanner/viewer/fp3d.py`,
  and `tests/test_viewer_model.py`. Commit vehicles and cabinets together if
  need be, and say so. Report failures verbatim. Do not merge.
- **Code, when Phase 2 is in:** the one line in `fp3dq._pbr` (§4.1).
- **Reviewer:** fixes from the report; then phase 5, after Phase 2 lands. No git.
