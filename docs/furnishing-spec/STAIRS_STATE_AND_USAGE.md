# Stairs — what is stored, and how to use it

Built 2026-11-14 (handoff 0323) from
[`STAIRS_FURNISHING_SPECIFICATION.md`](STAIRS_FURNISHING_SPECIFICATION.md) and
the decisions in [`PARAMETRIC_FURNISHINGS_PLAN.md`](PARAMETRIC_FURNISHINGS_PLAN.md) §8.

## Using it

1. Drag **Stairs** from the Framing section of the palette. A new stair is
   straight, 36 in wide, 11 in treads. It links to the level above when the
   plan has one; otherwise its rise is 108 in.
2. **Double-click** the stair (or right-click ▸ *Stair properties…*).
3. Change the type, turn, rise, tread depth, width, riser count or landing
   height. The side elevation, the plan inset and the calculated block follow
   every edit.
4. **OK** runs the checkpoint. An error keeps the dialog open with the cursor
   on the field. Unresolved checks need the acknowledgement box ticked.
   **Cancel** changes nothing. An accepted edit is one undo step.

A stair saved before this feature keeps drawing exactly as it did. Opening its
properties shows its own numbers; it becomes a parametric stair only when you
click OK.

## The furnishing record

The furnishing record is unchanged; the parameters are its optional `state`.

```json
{ "id": "f7", "level": "L1", "kind": "stairs", "room": "r3",
  "pos": [412.0, 96.0], "rotation": 90,
  "state": {
    "type": "L", "turn_deg": 90, "direction": "up",
    "rise_mode": "linked", "total_rise_in": 108.0,
    "tread_depth_in": 11.0, "stair_width_in": 36.0,
    "riser_count_mode": "auto", "riser_count": 14,
    "landing_mode": "half", "landing_height_in": 54.0,
    "code_profile": "irc_residential_example",
    "acknowledged": ["code.profile", "handrail.guard", "headroom.min", "landing.top_bottom"],
    "flight": "half", "turn": "right"
  } }
```

| key | values | meaning |
|---|---|---|
| `type` | `straight`, `L`, `U` | its presence is what makes a stair parametric |
| `turn_deg` | `0`; `90`, `-90`; `180`, `-180` | positive turns to the walker's left going up |
| `direction` | `up`, `down` | the plan arrow only |
| `rise_mode` | `linked`, `detached` | linked = the rise to the next level above this one |
| `total_rise_in` | number | used when detached, and as the fallback when linked finds no level above |
| `tread_depth_in`, `stair_width_in` | number | the two direct controls |
| `riser_count_mode`, `riser_count` | `auto` / `manual`, integer | the count is used only when manual |
| `landing_mode`, `landing_height_in` | `half` / `custom`, number | the height is used only when custom; it snaps to a whole number of risers |
| `code_profile` | id | which limits were checked |
| `acknowledged` | list of rule ids | the unresolved checks the user accepted |
| `flight`, `turn` | as before | still written, so an older build opens the file and draws a stair on the same side |

**Never stored:** riser height, tread count, run, pitch, footprint. They are
recalculated on load, by `floorplanner/parametric/stair_geometry.py`.

`pos` is the **centre of the footprint**, as for every furnishing. Editing a
stair keeps its foot (the first riser) where it was, so `pos` moves when the
footprint changes.

## Counting

`N` risers; a flight that ends at a floor or a landing has one fewer tread than
risers. Straight: `N - 1` treads. L or U: `N - 2`, split at the landing.

## Not checked in this release

Headroom, top and bottom landings and door swings, handrails and guards. They
are reported as NOT CHECKED and the dialog never says "code compliant".
The limits are IRC-derived example defaults (7.75 in riser, 10 in tread, 36 in
width, 151 in rise between landings), not a determination for a jurisdiction.

## Adding another parametric furnishing

1. A definition: subclass `ParametricKind` (`floorplanner/parametric/registry.py`),
   give its `ParamSpec` list, `normalize`, `evaluate` and `summary`, and
   `register()` it.
2. Optionally a preview widget with `set_data(values, derived, context)`.
3. If its shape depends on the parameters, override `apply_params` on its item
   and, for 3D, add its solid beside `build_stair` in `fp3d.py`.

The dialog, the double-click, save, load, copy/paste and undo need no change.
