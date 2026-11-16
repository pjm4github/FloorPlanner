# 0341 — ruling: pedal bin, dog crate, sofa table and table lamp — four new kinds in 3D. Built in the lane, UN-GATED, AMBER. Lands with 0340

**Reviewer (Cowork), 2026-11-15.** Patrick's word today. No report since
0339; the 0340 office delta is still uncommitted in the tree, and this sits
on top of it in the same two files — so **0340 and 0341 are one delta now.**
If a gate was running while these files changed, discard it and re-run.

## 1. What is new

Four NEW catalog kinds (104 -> 108), each parts-built with a dialog:

- **`pedal_bin`** (Kitchen) — round body, base ring, domed lid, hinge, pedal.
  Diameter, height; stainless or a colour + sheen.
- **`dog_crate`** (Living) — tube frame, wires at 2.5 in, three hoops, wire
  top, pan, door and latch in the +x end, a bed (on/off, colour). Length,
  width, height.
- **`sofa_table`** (Living) — top, apron, four legs, 0-3 low shelves; finish
  from the room's style.
- **`table_lamp`** (Lighting, Living) — a LIGHT (`fixture: table`): foot,
  body, stem, a glowing three-tier shade, and a point source in
  `model.lights`. `floor_to_bottom_in` is the surface it stands on (30 by
  default — a sofa table's top); `drop_in` is the lamp's own height.

Files: `cabinet_geometry.py`, `cabinets.py`, `_gen_assets.py` (4 rows, 4
solids, 3 groups) + regenerated `assets/furnishings/` (4 SVGs, manifest,
materials, groups), schema (`fixture_state` +3 keys). Tests: new
`tests/test_living_items.py` (19 cases); catalog size pinned 108 in
`test_viewer_model.py`; three kinds added to the parametrized Qt case in
`test_cabinet_item.py`. `fp3d.py` and `items.py` NOT touched.

## 2. Run, and not run

Stand-in runner, 8 modules (0340's included): 189 pass; the 1 failure imports
PyQt6. **Not run:** ruff, Qt, the Qt Quick view. Evidence is my painter.

## 3. To know

- A table lamp does not find the table under it: its height is a number.
  Placed on the bare floor it floats at 30 in until that is set to 0.
- "Table lamp" also appears in every light's Shape list.
- The lamp shade is three stacked rings, not a smooth cone (parts are
  vertical prisms).
- The crate is about 1,100 triangles; the largest size about 1,500.
- Nothing existing changes shape in this delta.

## 4. For Code

Gate with 0340 + 0341 in the tree; mailbox on `main`; one more commit by path
on `stairs-0338`. Failures verbatim. AMBER.

## 5. Patrick's check (same sitting as 0339 §4 and 0340 §6)

Place a sofa table and two table lamps on it: lamps sit on the top and light
the room. Dog crate and pedal bin in 3D; double-click each.
