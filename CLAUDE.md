# CLAUDE.md

Guidance for Claude Code in this repo. **Traps only** — things the code would
get you WRONG, not things you'd only get slowly (structure is in the
imports; history is in `handoff/` and `docs/V5_MIGRATION_PLAN.md`; the full
module layout, phase history, extract/join and floors mechanics, and the
performance measurements behind these traps all live in
`docs/ARCHITECTURE.md`).

## Starting a session

Read **`docs/SESSION_SNAPSHOT.md`** first — where the work stands, what to
read in what order, the traps that waste time. It is an index, not a second
copy of the record; where it points elsewhere, that document wins.

Then **`docs/handoff/`** — the channel between Code and the reviewer.
Highest number is current; read every ruling since the snapshot's own head
before doing anything the snapshot names as owed.

Before changing walls/rooms/items/mainwindow, read
**`docs/V5_MIGRATION_PLAN.md`** — it says what's scheduled for deletion and
in which phase, so you don't build on top of something about to go.

## Traps

- `import FloorPlanner` (the compatibility shim) **re-exports the whole
  `floorplanner/` package API** — `fp.WallItem`, `fp.SETTINGS`, etc. resolve
  regardless of which submodule they actually live in; no need to import
  from the specific submodule.
- Scene units are **inches** (1 unit = 1 inch); canvas size comes from
  `SETTINGS` via `canvas_rect()`.
- `planio.py`/`csvio.py`/`imageio.py`/`levels.py` are **mixins, not
  delegating wrappers** — add a method to the module that owns its concern,
  not to `MainWindow`.
- Use a **late (function-local) import only to close a genuine cycle**
  (`walls↔rooms`); otherwise keep imports acyclic (`items ← walls ← rooms`;
  UI imports the scene layer).
- `snapshot()` (canonical v5 doc), `design_document()` (what gets written:
  snapshot + provenance + settings + `active_floor`), and `serialize()`
  (legacy v4, only for File ▸ Export legacy v4) are **three different
  payloads** — don't reach for one expecting another.
- **Everything under `assets/` is generated** by `_gen_assets.py` — never
  hand-edit; edit the generator and re-run it.
- **A corner is one shared `Vertex`** (`walls.py`/`rooms.py`) — moving it
  moves every wall and room outline that holds it.
- Headless: **never synthesize Ctrl-modified key events** — it leaks
  `QApplication.keyboardModifiers()`; route shortcuts/arrows through app
  methods (as `MacroRunner` does).
- `fp_extract.py`: a `QApplication` must exist before `QImage` decodes a
  PNG; keep it in a **module global** (a local gets GC'd and crashes
  `MainWindow`); **copy `QImage` buffers** (`arr.copy()`) — a view into a
  freed `QImage` segfaults.
- **Don't memoize the wall path build** (profiled as already cheap) and
  **don't move junction-clip work into `paint()`** (path booleans per
  repaint stalls) — see `docs/ARCHITECTURE.md` for the measurements.
- Mouse-wheel zoom is **coalesced** (one `scale()` per 16 ms, not per
  event) — keep any new per-event view work off that synchronous path.
  `tests/test_view.py` guards it.
- `ruff.toml` suppresses **E402 in headless scripts**, because
  `QT_QPA_PLATFORM` must be set before the Qt imports it would otherwise
  flag as out of order.

## Linting and tests

Run `python -m ruff check .` after edits. `pytest` (headless; conftest owns
the `QApplication`) runs everything; `pytest --quick` skips `slow`+`gui`
markers for fast feedback; `pytest -m "not gui"` selects/skips by category
(`geometry`, `walls`, `rooms`, `groups`, `io`, … — see `tests/README.md`).
Prefer the bare `scene` fixture over `win` (full `MainWindow`) when the UI
isn't needed. When fixing a bug, add a regression test.

## Headless scratch-script pattern

- Set `os.environ["QT_QPA_PLATFORM"] = "offscreen"` before importing PyQt6;
  create `QApplication([])` before `import FloorPlanner`.
- A modal `QMessageBox` hangs headless — pass `interactive=False` where a
  method offers it (errors land in `self._import_errors`).
- Console is cp1252 — never print non-ASCII in test output.
- Pixel assertions on antialiased 1px lines need a lenient threshold
  (`< 190`, not `< 100`).
- `QTest.mouseMove` doesn't synthesize button-held drags — build
  `QMouseEvent`s with `buttons=Qt.MouseButton.LeftButton` and send via
  `QApplication.sendEvent`.
- Delete throwaway scripts when done.

## Other

- Regenerate the gallery with `python docs/make_gallery.py` after a UI
  change — don't hand-edit the PNGs.
- Commit and push **only when explicitly asked**. Never commit the user's
  plan files (`floorplan*.json`, `layout_wiscaway.csv` — gitignored).
- `gh` is not on PATH here: call it as
  `& "C:\Program Files\GitHub CLI\gh.exe"`.
