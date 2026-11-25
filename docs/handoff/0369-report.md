# 0369 — report: 0368 kitchen casework, gated and committed (O1–O6)

Code (Opus), 2026-11-25. Answers `docs/handoff/0368-ruling.md`. The four kitchen
casework kinds (`tall_cab`, `kitchen_desk`, `corner_wall_cab`, `ceiling_cab`)
were in the tree, written by the reviewer session under the furnishings-lane
exception. This closes the ruling's orders.

## What I had to change (O6)

The reviewer's own files (`cabinet_geometry.py`, `cabinets.py`, `catalog.py`,
`_gen_assets.py`, the four SVGs, `manifest.json`, `groups.json`,
`tests/test_viewer_model.py` pin → 119, `tests/test_kitchen_casework.py`) were
taken as written. On top of them:

- **O3 — schema.** `floorplanner/design/design-schema.v6.json`, `$defs.cabinet_state`:
  `doors` enum gains `"3"`, `"4"`; added `stands` (`floor`/`counter`),
  `wing_in`, `door_sides` (`both`/`one`), `under_light`, `drop_in`,
  `light_colour`, `lumens`; the four kinds named in the description. Declared,
  not enforced; the schema stays 6.
- **O4 — Qt-side tests.** `tests/test_kitchen_casework_item.py` (new, 12 tests):
  each of the four placed on the canvas, its dialog opened, `is_casework` true,
  state saved and loaded (via the item and via `snapshot()`); plus the new keys
  wired — the tall cabinet standing on a counter, the corner cabinet's wings,
  the ceiling cabinet's 3/4 doors and its under-cabinet light.
- **O5 — pricing.** The four carried `price: 0.0`. Priced by comparison with the
  catalog's own casework (mid-range US retail, the field the AI pricing tool
  fills): `tall_cab` 680 (≈ pantry_24 720), `kitchen_desk` 480, `corner_wall_cab`
  480, `ceiling_cab` 650. Set in `manifest.json`'s `price`, which the generator
  preserves across a regen (`_prev_price`); a fresh `_gen_assets.py` keeps them.
- **O1** — the casework committed by path as its own commit (`c67276b`), on the
  0367 branch, not stashed. It rides that branch because the two share the
  generated catalog (`manifest`/`groups`), which a split onto `main` would
  un-mix. Patrick's call was to commit the 0367 weld first (`dddcae3`), so the
  "before the next 0367 commit" ordering gave way; nothing was stashed or lost.
  This ruling and report file on `main` (the mailbox hook). **O2** —
  `_gen_assets.py` re-run: 119 symbols, tree unchanged bar line endings; `ruff`
  clean; full `pytest`; the gate.

## O2 — the gate

```
Gate-Census: collected=2730 ruff=clean vacuous=0 end_assign=0 snapshot=current
Gate-OFF: 2723 passed, 7 deselected, 4 warnings in 118.18s  -> sum 2730  OK
Gate-ON:  2723 passed, 7 deselected, 12 warnings in 137.26s -> sum 2730  OK
Gate-Verdict: GREEN
```

(This gate ran with the 0367 stage-3 weld also in the tree — the two commit by
path, separately; the census covers both.)

## Not in this report

- **O5 caveat:** the four prices are set by comparison, not by the AI pricing
  tool (which needs Patrick's API key); run `AI ▸ Update furnishing prices…` to
  refresh them with live retail.
- **0368 §6 reproduction** (a dormer opposite another hangs `compute_roof_clips`)
  is filed against 0350 §1 with the pyramid-weld read-back
  (`docs/evidence/0367-pyramid-roof/C2-weld-readback.md`): the pyramid weld is a
  pairwise pass that never enters that walk.

## Patrick's check (0368 §5)

AMBER, his look is the merge condition: place each of the four in a kitchen and
open each dialog; a tall cabinet on the floor and on a counter both top at 84;
three and four doors draw; the desk takes the room's countertop; the corner
cabinet's wings; the ceiling cabinet follows the room ceiling, drops on rods,
doors one/both, light on/off.
