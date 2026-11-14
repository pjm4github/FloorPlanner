# 0323 — ruling: parametric furnishings are BUILT (stairs: straight, L, U, adjustable landing) — UN-GATED, no Qt line of it has ever run, and Code's gate is the first real test

**Reviewer (Cowork), 2026-11-14.** Follows 0322. Patrick ruled on the plan's six
decisions the same day (recorded in `docs/furnishing-spec/PARAMETRIC_FURNISHINGS_PLAN.md`
§8) and widened the lane: *"widen your lane to use what you need to implement
this."* **Tier: AMBER** — user-visible throughout. Nothing merges before the gate
is green AND Patrick's check in §6.

## 1. WHAT WAS RUN, AND WHAT WAS NOT — read this first

The device shell has no PyQt6, no pytest, no ruff, and cannot install them.

| | status |
|---|---|
| `py_compile` on every new and changed file | clean |
| `tests/test_stair_geometry.py`, `test_stair_validation.py`, `test_stair_viewer.py` | **52 cases pass — under a stand-in runner** (a stub `pytest`, the package's `__init__` bypassed), NOT under pytest |
| `tests/test_stair_item.py` (16 tests: item, dialog, save/load, undo) | **never run** |
| `dialog.py`, `stair_view.py`, every change in `items.py` | **never executed** — written against the Qt API from reading, nothing more |
| `ruff check .` | not run; an AST pass found no unused imports and no line over 100 |
| the full gate | not run |

So: the arithmetic and the 3D mesh are measured; the editor side is unproven.
A red gate comes back as a report (0319 §4), not a fix-up in place.

## 2. WHAT WAS BUILT

- **`floorplanner/parametric/`** (new, 8 files). `params`, `findings`,
  `registry` are kind-agnostic. `stair_geometry.py` is the one calculator and
  imports only `math` and `dataclasses`. `stairs.py` is the STAIRS kind
  (parameters, validation, summary). `dialog.py` is ONE generic properties
  dialog built from a kind's parameter list; `stair_view.py` is the to-scale
  side elevation and plan inset. Importing the package imports no Qt.
- **`items.py`** — `FurnishingItem`: `params`, `draft_state`, `apply_params`,
  `make_properties_dialog`, `open_properties`, and a double-click that opens
  the dialog for a registered kind only. `StairItem`: a `params` mode beside
  the untouched legacy mode. `make_furnishing(..., new=False)`.
- **`view.py:1326`** — one line: a palette drop passes `new=True`.
- **`viewer/fp3d.py`**, furnishing region only — `_load_stair_geometry`
  (by path, the `roofclip` pattern), `_prism8`, `build_stair`, and the hook in
  the furnishing loop.
- **Storage:** the furnishing record's existing `state`. **No schema change,
  no change to `design/bridge.py`, `design/model.py`, `planio.py` or
  `mainwindow.py`.** Keys and usage: `docs/furnishing-spec/STAIRS_STATE_AND_USAGE.md`.

## 3. THE THREE STAIRS `make_furnishing` NOW TELLS APART

| saved with | becomes |
|---|---|
| a `state` carrying `type` | a parametric stair |
| nothing, and `new=True` (a palette drop) | a parametric stair on the defaults |
| anything else — every stair in every existing plan | the legacy stair, byte-for-byte the old code path |

`test_framing.py` and `test_undo.py` are not edited and should pass unchanged;
that is the receipt for "existing stairs frozen". If either goes red, the
freeze is broken and that outranks everything else here.

## 4. MEASURED (through `build_model`, one stair, levels at 0 and 120)

| stair | triangles | solid volume, cu in | top, in |
|---|---:|---:|---:|
| legacy (no parameters) | 12 | 466,560 (the 36 x 120 x 108 box) | 108 |
| straight, detached 108 | 348 | 11,903 | 107 |
| straight, linked (120) | 396 | 13,643 | 119 |
| L, +90 | 420 | 15,683 | 107 |
| U, -180 | 420 | 17,627 | 107 |

Volumes are positive, so every face is wound outward. An L stair at 30 degrees
lands on the same world extents the editor's own transform gives (x 30.333 to
136.667, y -269.667 to -130.333) — not mirrored, not mis-centred.
The spec's example checks out: 108 / 11 / 36 gives 14 risers of 7.7143, 13
treads, 143 run. **One number in the spec is off:** it gives the pitch as
35.05 degrees; atan(7.7143 / 11) is 35.04. The test asserts the arithmetic.

## 5. KNOWN GAPS — named, not hidden

1. **Macro `place stairs` still makes a LEGACY stair** (`macro.py:401` does not
   pass `new=True`), so a recorded drop replays as a different stair than the
   user placed. Deliberately not changed: it would alter every existing macro's
   output. Patrick's call.
2. **A linked stair resizes about its CENTRE when a level's elevation
   changes** — its foot moves by half the change in run. Keeping the centre is
   what guarantees a saved stair reloads where it was saved.
3. **`direction: down` flips the arrow only**; the 3D solid always climbs from
   the stair's own level.
4. **One addition beyond the spec:** a WARNING when a single flight rises more
   than 151 in without a landing (IRC 2021 R311.7.3). The spec's table says not
   to invent a riser-count limit; this is a rise limit, and it is a warning,
   not an error. Remove it if unwanted.
5. Not done: `docs/design-schema.v6.md` stair keys, `tests/README.md` marker
   table, the gallery, `docs/progress/furnishings.md`. Code's files.
6. Camera elevations still draw a stair as a to-scale box.

## 6. PATRICK'S CHECK — one batch, after the gate is green

1. Open an existing plan with stairs. Nothing has moved; right-click still
   offers Flight / Half-flight direction.
2. Drag a new Stairs in. Double-click it: the dialog opens, elevation on the
   left, plan inset under it.
3. Change tread depth: run and footprint follow, rise does not.
4. Type -> L, then U; flip the turn; set a custom landing height low and high.
   The plan inset and, after OK, the plan symbol change shape.
5. Riser count -> Manual -> 13 on a 108 rise: OK is refused, cursor on Risers.
6. A valid stair: OK is refused until the acknowledgement box is ticked.
7. Cancel after edits: nothing changed, nothing to undo.
8. OK, then Ctrl+Z once: the stair is back as it was.
9. Save, reopen: the stair is where it was, same shape.
10. Open the 3D view: treads, risers, stringers and (L / U) a landing on posts.
11. Double-click an existing (legacy) stair, change nothing, Cancel: unchanged.

## 7. OWED

- **Code:** run the full gate. Commit by path on a branch — `floorplanner/parametric/`,
  `floorplanner/items.py`, `floorplanner/view.py`, `floorplanner/viewer/fp3d.py`
  (its diff is this lane's four hunks only, as of writing), the four new
  `tests/test_stair_*.py`, `docs/furnishing-spec/`. Report the gate in the next
  number, failures verbatim. Do not merge: AMBER.
- **Reviewer:** fixes for whatever the gate finds, in the next ruling.
