# Tests

Automated pytest suite for FloorPlanner. Tests run headless (Qt offscreen
platform); no display or `pytest-qt` is required — `conftest.py` owns the
`QApplication`.

## Setup

```
pip install -r requirements-dev.txt
```

## Running

```
pytest                     # everything
pytest --quick             # skip slow + gui tests (fast feedback loop)
pytest -m geometry         # only the geometry category
pytest -m "not gui"        # everything except synthetic-mouse tests
pytest -m "groups or io"   # two categories
pytest tests/test_rooms.py # one file
pytest -k inventory        # tests whose name matches "inventory"
pytest -q                  # quiet;  -v for verbose;  -s to see prints
python tools/gate.py       # THE GATE: lint, census, the suite twice, the docs lane
```

`tools/gate.py` is what a commit needs: it runs ruff, counts the collection,
runs the suite with the display mode off and on, reconciles every sum against
`--collect-only`, runs the documentation checks (`--docs` runs them alone),
and writes `.gate-result.json`. `--quick` passes the same flag to pytest.

## Turning tests off while developing a feature

Every module is tagged with a category marker (see the list in
`../pytest.ini`). To skip a category, deselect its marker:

```
pytest -m "not furnishings"
```

`--quick` is the everyday shortcut — it skips the `slow` and `gui` markers,
which are the only meaningfully slower tests, and keeps the rest as a fast
regression net. `perf` is a local lane (timing ratios flap on shared runners)
and is deselected by the gate.

## Layout

The markers, and the files that carry each (2026‑10‑12):

| Marker | Covers | Files |
|--------|--------|-------|
| `smoke` | module imports, app builds, canvas, default settings | `test_smoke.py` |
| `geometry` | `parse_feet`, `parse_wwhh`, `fmt_ftin`, snap helpers | `test_geometry.py` |
| `walls` | wall and opening geometry, coalescing, snapping, orthogonality, the roofs (clip, dormers, grips, forms, hip runs, params, the cost) and the annotations | `test_walls.py`, `test_coalesce.py`, `test_openings.py`, `test_opening_sill.py`, `test_orthogonality*.py`, `test_snap_to_grid*.py`, `test_roof_*.py`, `test_roofclip_cost.py`, `test_r6a_display.py`, `test_r6b_composition.py`, `test_hip_run_and_posts.py`, `test_annotations.py` |
| `rooms` | room detection, area, outline, open walls, floors, extract / join, concept rooms, self-intersection | `test_rooms.py`, `test_room_walls.py`, `test_outline.py`, `test_open_walls.py`, `test_floors.py`, `test_extract_join.py`, `test_concept_rooms.py`, `test_self_intersection.py` |
| `selection` | rubber-band enclosure selection and room-edge synthesis | `test_selection.py` |
| `editing` | arrow-key nudge of selected items | `test_nudge.py` |
| `furnishings` | catalog integrity, true-scale placement, framing, extrudability, inventories, AI pricing | `test_furnishings.py`, `test_framing.py`, `test_extrudability.py`, `test_inventory.py`, `test_ai_pricing.py` |
| `groups` | group / move / ungroup, the characterisation suite, floor scope | `test_groups.py`, `test_characterization.py`, `test_d67_floor_scope.py` |
| `io` | the design document (schema, model, bridge, problems, templates, corpus freeze, fixtures), JSON and CSV round trips, the exporters (DXF, PDF), the export menu, settings, levels, about | `test_io.py`, `test_schema.py`, `test_design_model.py`, `test_design_bridge.py`, `test_design_problems.py`, `test_template.py`, `test_corpus_freeze.py`, `test_fixture_layout.py`, `test_fp2dxf.py`, `test_fp2pdf.py`, `test_export_menu.py`, `test_config.py`, `test_levels_elevation.py`, `test_load_path.py`, `test_model.py`, `test_commands.py`, `test_gen_assets.py`, `test_shuffle.py`, `test_about.py` |
| `gui` | drives synthetic mouse events through the view (slower): the roof tools, the grid snap, the hit tests | `test_roof_ridge_tool.py`, `test_roof_dormer_tool.py`, `test_roof_end_on.py`, `test_roof_hit_testing.py`, `test_roof_visibility.py`, `test_r6c_roof_tool_levels.py`, `test_grid_snap_default.py` (and `gui`-marked tests inside other files) |
| `macro` | both macro languages, the recorder, the converter, the player, the spec's example | `test_macro.py`, `test_macro2_language.py`, `test_macro2_commands.py`, `test_macro2_convert.py`, `test_macro2_player.py`, `test_macro2_recorder.py`, `test_roof_dormer_macro.py` |
| `viewer` | the 3D viewers' Qt-free geometry core and the catalog's 3D data | `test_viewer_model.py`, `test_viewer_dormer.py`, `test_viewer_popup.py`, `test_viewer_wall_clip.py`, `test_roof_overhang_3d.py`, `test_gable_climb_level.py` |
| `extract` | PNG → floor-plan extraction (`fp_extract.py`) | `test_extract.py` |
| `slow` / `perf` | timing-ratio scaling tests, a local lane | `test_scaling.py` |
| `tooling` | the gate's own instruments | `test_gate.py`, `test_progress_index.py`, `test_status_index.py`, `test_verify_gate_hook.py` |

Files without a module-level marker (`test_undo.py`, `test_vertices.py`,
`test_view.py`, `test_wall_move.py`, `test_wall_properties.py`,
`test_zorder.py`, `test_topology*.py`, `test_verify_design.py`,
`test_version.py`) mark their tests individually or need none.

## Adding tests

As features land, add a test next to the closest category (or a new
`test_<feature>.py` with its own `pytestmark = pytest.mark.<name>`, and
register the marker in `../pytest.ini`).

Shared fixtures live in `conftest.py`:

- `fp` — the FloorPlanner module
- `scene` — a bare `QGraphicsScene` (fast; enough for geometry)
- `win` — a full `MainWindow` (for io / group / gui tests)
- `add_walls(scene, x, y, w, h)` / `make_room(scene, x, y, w, h, name)` — builders
- `first_furnishing` — a stable catalog id
- `drag(win, scene_pt, dx_px, dy_px)` — synthetic left-button drag through the view
- `counts(scene)` — `(walls, furnishings, rooms)` tallies

Prefer the bare `scene` fixture over `win` when you don't need the UI — it's
much faster. Tag any test that drives the view with synthetic mouse events
`@pytest.mark.gui`, and anything genuinely slow `@pytest.mark.slow`, so
`--quick` can skip them.

Three traps the suite has paid for:

- A Python exception inside any Qt virtual, slot, paint or event handler
  kills the process silently (exit 127, no traceback, the log just stops).
  Replay the handler's steps outside the event under `try/except` to find it.
- The offscreen platform's font engine draws nothing below five pixels; a
  pixel test of small text checks the 1× render, and a zoomed grab of a plan
  uses `QT_QPA_PLATFORM=windows`.
- A modal `QInputDialog` or `QMessageBox` hangs headless: monkeypatch
  `QInputDialog.getText`, or pass `interactive=False` where a method offers it.
