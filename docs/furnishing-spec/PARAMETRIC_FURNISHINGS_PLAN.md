# Parametric furnishings — implementation plan

**Status:** PLAN, for Patrick's review. Nothing is built. Reviewer session, 2026-11-14.
**First use case:** stairs — [`STAIRS_FURNISHING_SPECIFICATION.md`](STAIRS_FURNISHING_SPECIFICATION.md).
**Lane:** furnishings (handoff 0319, 0321, 0322).

## 1. What is being added

A furnishing can carry **parameters**. Double-clicking a placed furnishing whose
kind is parametric opens a modal editor; accepting it changes that one
furnishing's plan symbol, footprint and 3D solid. The parameters are saved with
the furnishing in the plan file. Stairs are the first kind; the machinery is
kind-agnostic so the next kind is a new definition, not a new dialog.

## 2. What the repo already has (read 2026-11-14, on disk)

| fact | where | consequence |
|---|---|---|
| The furnishing record already has an optional, open `state` object, described in the schema as *"Per-kind extra state (stair flight/turn/direction, plant species, ...)"* | `design-schema.v6.json` `$defs/furnishing` | A parameter section already exists in the file format |
| `state` already round-trips: `extra_state()` writes it, `make_furnishing(kind, pos, rotation, state)` reads it; copy/paste uses the same pair | `items.py`, `design/bridge.py:934, 1603` | Save, open, paste and undo need **no change** to carry parameters |
| A `StairItem` already exists: full or half flight, left/right turn, up/down arrow, set from the right-click menu | `items.py:263-450` | The spec's stair is a rebuild of this item, not a new one |
| Its rise is the **ceiling height of the room it sits in**; riser count is `round(rise / 7.0)`; tread 10.5", width 36" are constants | `items.py:25-28, 322` | Differs from the spec on all four points — see §6 |
| Undo is a whole-document snapshot compared at each quiet point | `mainwindow.py:1977-1993` | "One undoable transaction" and "Cancel leaves no trace" come for free if the dialog only mutates on accept |
| In 3D, stairs are a 108" wooden box; the viewer reads the manifest only and ignores `state` | `_gen_assets.py` `SOLIDS`, `fp3d.py:3029+` | The 3D stair needs the viewer to read `state` |
| The viewer may not import `floorplanner`; it loads `roofclip.py` **by path** because that file is plain Python | `fp3d.py:92-111` | Stair maths must be plain Python (no Qt) so both sides share one calculator |
| Level elevations are available per floor | `config.floor_elevation()` | Floor-to-floor rise can be computed |
| Double-click-opens-dialog is an existing pattern | `cameras.py:329`, `roofs.py`, `walls.py` | No new event routing |

## 3. Design

### 3.1 The plan file

The furnishing record is the callout; `state` is its optional parameter section.
A furnishing with no parameters is written exactly as today.

```json
{ "id": "f7", "level": "L1", "kind": "stairs", "room": "r3",
  "pos": [412.0, 96.0], "rotation": 90,
  "state": {
    "flight": "full", "turn": "left", "direction": "up",
    "rise_mode": "linked", "to_level": "L2",
    "tread_depth_in": 11.0, "stair_width_in": 36.0,
    "riser_count_mode": "auto",
    "code_profile": "irc_residential_example"
  } }
```

Rules: only **controlling** values are stored — never riser height, tread
count, run or pitch. Values equal to the kind's default may be omitted. Unknown
keys are preserved on a round trip, so a newer file opened by an older build
does not lose them.

### 3.2 Modules

A new package, `floorplanner/parametric/`. Three layers, each usable without
the one above it.

| module | Qt? | role | reusable? |
|---|---|---|---|
| `params.py` | no | `ParamSpec` (key, label, type, unit, default, min, max, step, when-enabled); `resolve(kind, state)` fills defaults; `to_state(values)` drops them | yes |
| `findings.py` | no | `Finding(rule_id, severity, message, actual, limit, field)`; ERROR / WARNING / ADVISORY / PASS / NOT_EVALUATED; `blocks()`, `needs_ack()` | yes |
| `registry.py` | no | kind -> definition: its `ParamSpec`s, `derive(values, context)`, `validate(values, derived, context)`, plan primitives, solid primitives | yes |
| `stairs.py` | no | `StairInputs`, `StairGeometry`, `calculate_stair_geometry`, `validate_stairway`, `StairCodeProfile`; plan lines and 3D boxes from the **same** `StairGeometry` | stairs |
| `dialog.py` | yes | `ParametricDialog`: preview pane left, form built from the `ParamSpec`s, read-only calculated block, findings panel, acknowledgement checkbox, Reset / Cancel / OK | yes |
| `stairs_view.py` | yes | the side-elevation drawing for the preview pane | stairs |

`FurnishingItem` gains three things: a `params` dict, `apply_params()`, and a
`mouseDoubleClickEvent` that opens `ParametricDialog` when the kind is
registered. `StairItem` keeps its name and class (tests and the selection code
name it) and delegates its geometry to `stairs.py`.

Adding a second parametric kind then costs: one definition file (specs,
derive, validate, primitives) and, optionally, a preview painter. No dialog
code, no save/load code.

### 3.3 The stair calculation (spec §5, unchanged)

```
N = ceil(H / h_max)  (auto)  or the override
h = H / N      T = N - 1      R = T * d      pitch = atan(h / d)
```

`H` = `elevation(to_level) - elevation(from_level)` when linked, or the stored
detached rise. 108 / 11 / 36 gives 14 risers, 7.714", 13 treads, 143" run, 35.05 deg.

### 3.4 Validation and the OK checkpoint (spec §6)

Hard errors block OK and focus the offending field. Warnings and
not-evaluated items require the acknowledgement checkbox. Headroom, landings
and handrails are **NOT_EVALUATED** in this release — the status line reads
"Basic dimensions pass; additional checks pending", never "code compliant".
One built-in profile, `irc_residential_example` (7.75 / 10.0 / 36.0); no
profile editor yet.

### 3.5 The dialog graphic

Drawn by the application with `QPainter`, to scale from the current
`StairGeometry`: stringer, each tread with its nosing, each riser, both floor
lines, and dimension callouts for unit rise, unit run, total rise, total run
and the headroom line. It redraws on every edit, so the picture always shows
the real riser count. It is styled after the reference image Patrick supplied
(same content and callouts). **The supplied image itself is not added to the
repository** — it is a published illustration, and the spec (§2.1) says not to
copy a third-party image in. One label in it is also wrong for our purpose:
its bottom dimension reads "Total rise" where it measures total run; ours will
say "Total run".

### 3.6 Plan view and 3D

Plan: side boundaries, `N - 1` tread lines, UP/DN arrow — from `stairs.py`,
not from a second calculator. The bounding box and hit shape follow the
parameters.

3D: the viewer loads `parametric/stairs.py` by path (the `roofclip` pattern),
reads the furnishing's `state`, and builds one box per tread plus two
stringers, replacing the 108" block. A furnishing with no `state` builds as it
does today.

## 4. Phases

| # | what | user-visible? | tier | how it is checked |
|---|---|---|---|---|
| 1 | `params.py`, `findings.py`, `stairs.py` + unit tests (spec §9.1 items 1-7, 12) | no | GREEN | I run the maths in plain Python here; Code runs pytest and the gate |
| 2 | `registry.py`; `FurnishingItem.params`; `StairItem` on the new geometry; round-trip and legacy-load tests (§9.1 items 8-10) | plan symbol | AMBER | Code's gate; Patrick opens an existing plan and a new one |
| 3 | `ParametricDialog`, `stairs_view.py`, double-click, OK checkpoint, acknowledgement (§9.1 item 11, §9.2) | yes | AMBER | Code's gate; Patrick's batch check of the dialog |
| 4 | 3D treads and stringers in `fp3d.py` | yes | AMBER | mesh measured here; Patrick's look at the 3D view |
| 5 | docs: `design-schema.v6.md` stair `state` keys, a short usage note, gallery | no | GREEN | Code |

Each phase ends in one numbered handoff file for Code to gate and commit.

## 5. Files touched, and what that does to the lane

| file | change | in the lane today? |
|---|---|---|
| `floorplanner/parametric/*` (new) | everything in §3.2 | new |
| `floorplanner/items.py` | `FurnishingItem`, `StairItem`, `make_furnishing` only | **no — needs Patrick's yes** |
| `floorplanner/__init__.py` | export the new names if the shim needs them | **no — needs Patrick's yes** |
| `floorplanner/viewer/fp3d.py` | furnishing block only | yes |
| `tests/test_parametric_*.py`, `tests/test_stair_*.py` (new), `tests/test_framing.py` | tests | partly |
| `docs/furnishing-spec/*`, `docs/design-schema.v6.md` | docs | new |

**Not touched:** `design/bridge.py`, `design/model.py`, the JSON schema,
`mainwindow.py`, `dialogs.py`, `cameras.py`, `roofs.py` — under decision D1(a).
Code's dormer work is in `cameras.py`, the roof region of `fp3d.py`,
`fp3dq.py` and `scene.qml`; none of that is in this plan.

## 6. Decisions for Patrick

**D1. Where parameters live in the file.**
(a) *Recommended:* the existing `state` object. No schema change, no version
bump, save/load/undo/paste already carry it, and older builds still open the
file. (b) A new `params` key beside `state`: a cleaner name, but the schema
forbids unknown keys on a furnishing, so every older build rejects any file
that uses it, and `bridge.py`, `model.py` and the schema all change.

**D2. Stairs already in saved plans.** They have no stored tread, width or
rise. The old rule and the spec's rule give different stairs: a 96" rise is
14 risers and a 136.5" run today, 13 risers and a 132" run under the spec.
(a) *Recommended:* a stair with no stored parameters loads **frozen at its old
numbers** (detached rise, tread 10.5, manual riser count), so no existing plan
moves; it adopts the new rules the first time it is edited and accepted.
(b) Convert on load: simpler, but every existing stair changes length.

**D3. Where the rise comes from for a new stair.**
(a) *Recommended:* linked to the level above when there is one
(`to_level` elevation minus this level's); detached, default 108", when there
is not. (b) Keep the old rule (the room's ceiling height) as a third mode.
Ceiling height is not floor-to-floor rise — it omits the floor structure — so
(b) is kept only if you want it.

**D4. Half flights and turns.** The spec calls L and U stairs future work, but
the half flight with a landing and a left/right turn already exists and is in
saved plans. *Recommended:* keep it working exactly as it draws today, driven
by the same riser and tread values, with landing size reported NOT_EVALUATED.
No new stair types in this release.

**D5. Apply button.** *Recommended:* leave it out of the first release (the
spec allows this). OK and Cancel only.

**D6. Widen the lane** to `floorplanner/items.py` (furnishing classes only) and
`floorplanner/__init__.py` (exports only). Without this the feature cannot be
built in this session.

## 7. Deferred, stated so it is not assumed

Headroom, landing and handrail checks; fit-to-space; nosing projection; open
risers; a code-profile editor; stair-aware camera elevations (the elevation
camera keeps drawing a to-scale box); DXF/PDF stair detail beyond what those
exporters draw today; stale-level detection while the dialog is open (the
dialog is modal, so the levels cannot change under it).

## 8. Decisions — Patrick, 2026-11-14 (supersedes §6 where they differ)

| # | decision |
|---|---|
| D1 | Parameters live in the existing `state` object, for now. |
| D2 | Existing stairs stay frozen on their old numbers until edited. |
| D3 | A new stair links to the level above when there is one; otherwise a detached rise, 108 in. |
| D4 | **Changed from the recommendation.** The stair types are straight, **L** and **U**. The turn is +90 / -90 (L) or +180 / -180 (U). The **landing height is adjustable**, default half way between the floors, and it changes the plan footprint — a flight may overhang, the L or the rectangle changes shape. |
| D5 | No Apply button in the first release. |
| D6 | The lane is widened to whatever the feature needs. |

Built as decided: see `docs/handoff/0323-ruling.md` and
[`STAIRS_STATE_AND_USAGE.md`](STAIRS_STATE_AND_USAGE.md).
