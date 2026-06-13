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
```

## Turning tests off while developing a feature

Every module is tagged with a category marker (see the list in
`../pytest.ini`). To skip a category, deselect its marker:

```
pytest -m "not furnishings"
```

`--quick` is the everyday shortcut — it skips the `slow` and `gui` markers,
which are the only meaningfully slower tests, and keeps the rest as a fast
regression net.

## Layout

| File | Marker | Covers |
|------|--------|--------|
| `test_smoke.py` | `smoke` | module imports, app builds, canvas, default settings |
| `test_geometry.py` | `geometry` | `parse_feet`, `parse_wwhh`, `fmt_ftin`, snap helpers |
| `test_walls.py` | `walls` | wall geometry, opening sizing, garage-door defaults |
| `test_rooms.py` | `rooms` | room detection, area, inventory, naming, region-follow |
| `test_furnishings.py` | `furnishings` | catalog integrity, true-scale placement, groups |
| `test_io.py` | `io` | JSON + CSV import/export round-trips |
| `test_groups.py` | `groups` (+`gui`) | group / move / ungroup, incl. the GC + wall-drag regressions |

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
