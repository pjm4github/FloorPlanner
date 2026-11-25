# 0368 — ruling: four kitchen casework kinds are IN THE TREE (furnishings lane). Gate, test and commit them by path. AMBER.

2026-11-25, reviewer session. Written under the furnishings-lane exception
(Patrick, 2026-11-14: the reviewer session may edit furnishing files in place;
Code still commits). Nothing here is committed. Number 0368 is the next free
one; if a file of yours took it first, this ruling keeps its name and your
report takes the next.

## 1. Patrick's words, and the reading taken

1. "a tall kitchen cabinet, parameterized for width and number of doors … a
   standard height that would reach the top of a wall cabinet from the base unit"
2. "a kitchen desk, which is a counter top with surface that matches the
   kitchen countertop. It has a small, full width drawer under the top"
3. "a corner wall kitchen cabinet with parameterized depth and wing sizes"
4. "a suspended ceiling cabinet that would hang over an island. The height of
   the cabinet and width and number of doors and under cabinet lighting are all
   selectable"

Item 1 reads two ways (84 in from the floor; or 48 in standing ON a base unit).
Both are built: `tall_cab` is born floor-standing at 84 in, and its `stands`
parameter puts it on a counter (36 in up) with its top still at 84.

## 2. What is in the tree (uncommitted, written 2026-11-25 at 11:57 local)

| File | Change |
|---|---|
| `floorplanner/parametric/cabinet_geometry.py` | types `kitchen_desk`, `corner_wall`, `suspended`; presets `tall_cab`, `kitchen_desk`, `corner_wall_cab`, `ceiling_cab`; state keys `stands`, `wing_in`, `door_sides`, `under_light`; `doors` takes `"3"`, `"4"`; builders, plan-symbol prims, the ceiling cabinet's light source; `overall_height(st, ceiling_in=96.0)` |
| `floorplanner/parametric/cabinets.py` | dialog specs, plan symbols, findings (`suspended.clearance`, `desk.knee`, `wall.clearance`), summaries |
| `floorplanner/catalog.py` | the four ids join `_CASEWORK_PREFIX` |
| `_gen_assets.py` | three symbol helpers, four FURNISHINGS rows, four SOLIDS rows, Kitchen group, the preset check skips `suspended` as it skips `light` |
| `assets/furnishings/manifest.json`, `groups.json` | regenerated: 119 entries |
| `assets/furnishings/tall_cab.svg`, `kitchen_desk.svg`, `corner_wall_cab.svg`, `ceiling_cab.svg` | new, generated |
| `tests/test_viewer_model.py` | catalog pin 115 -> 119 |
| `tests/test_kitchen_casework.py` | new, 36 tests, no Qt |

A ceiling cabinet's top is its room's ceiling less `drop_in`; rods appear when
the drop is over 0.5 in. The pantries keep their catalog symbol and build the
same parts as before.

## 3. What was measured, and what was not

Measured on a staged copy (Python 3.13, pytest 9.1, no PyQt6):

- `tests/test_kitchen_casework.py`: 36 pass. On the tree before the change, the
  same file: 36 fail.
- The nine Qt-free test modules that could be staged: 226 pass, 5 fail. The
  same 5 fail before the change (they need fixtures and editor modules that
  were not staged), so the set changes none of them.
- Existing kinds: 43 presets x 13 state variants x 2 ceilings = 1,118 cases.
  Parts, footprint, overall height, trade code, light source, mounting and
  materials are identical before and after in all 1,118.
- `_gen_assets.py` on the staged copy: 119 symbols; against a fresh run of the
  old generator the only differences are `manifest.json`, `groups.json` and the
  four new SVGs.
- `ruff check`: clean.
- On the live tree after install (Python 3.10, stub package): every preset
  evaluates, and `fp3d.build_model` builds the four as parts with one light.

NOT run: the gate, the full suite, any Qt test (`tests/test_cabinet_item.py`,
`tests/test_cameras.py`), the app, a dialog. Nobody has looked at these on screen.

## 4. Orders

- **O1. Do not stash this set and do not switch branches over it.** Commit it
  first, by path, as its own commit. Reason: the wicker set was stashed during
  the 0365 landing, the app then skipped the wicker kinds on load, and Patrick's
  `wiscaway-c04.json` lost them on save.
- **O2.** Re-run `python _gen_assets.py`; the tree must not change (line endings
  aside). Then `ruff`, the full `pytest`, the gate.
- **O3.** Declare the new keys in `$defs.cabinet_state` of
  `design-schema.v6.json`: `doors` gains `"3"`, `"4"`; add `stands`
  (`floor`/`counter`), `wing_in`, `door_sides` (`both`/`one`), `under_light`,
  and name `drop_in`, `light_colour`, `lumens` for the ceiling cabinet. Add the
  four kinds to the description. Declared, not enforced; the schema stays 6.
- **O4.** Add the Qt-side tests this session could not: each of the four placed
  on the canvas, its dialog opened, its state saved and loaded; `is_casework`
  true for all four.
- **O5.** The four carry `price: 0.0`. Price them the way the catalog is priced.
- **O6.** Report in the next number: the gate result, and every line you had to
  change to get there.

This is independent of 0367. Do it before the next 0367 commit, because the
tree is dirty with it. Sonnet.

## 5. Tier and Patrick's check

AMBER: user-visible. One sitting, after O2 is green:

1. Place each of the four in a kitchen; open each dialog.
2. 3D: a tall cabinet on the floor and on a counter both top out at the wall
   cabinets (84 in); three and four doors draw.
3. The desk's top takes the room's countertop; change the room style and it follows.
4. Corner wall cabinet: diagonal and L-shape, left and right, unequal wings.
5. Ceiling cabinet over the island: it follows the room's ceiling; drop it on
   rods; doors on one side and both; light on and off.

His look is the merge condition.

## 6. Two things for the record

- **A stale lock was this session's doing.** A read-only `git diff --stat` from
  the reviewer side at 11:43 local created a zero-byte `.git/index.lock` and
  could not remove it (deletes are off for this session in the repo). Patrick
  was told at once. The reviewer side runs no `git diff` here again.
- **A reproduction to file against 0350 section 1.** One main roof with two gable
  dormer furnishings directly opposite each other (same station, opposite
  slopes) and `compute_roof_clips` does not return; the second dormer 72 in off
  the first builds in about a second. Reproduce with
  `Documents\FloorPlanner\wiscaway-c04-build\c04.py` and
  `C04_EAST_DORMER=852` (hangs) against `=780` (builds). The app would hang the
  same way if a dormer were dragged opposite another. File it; no fix is ordered here.
