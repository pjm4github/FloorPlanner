# 0376 — ruling: eight furnishing changes are IN THE TREE (furnishings lane). Gate, test and commit them by path, apart from 0375. AMBER.

2026-11-26, reviewer session, under the furnishings-lane exception (Patrick,
2026-11-14). Nothing here is committed. Written while you were on
`dormer-climb-floor-0372` with `fp3d.py` open; none of these files is `fp3d.py`.

## 1. Patrick's words, and the reading taken

| # | He asked | What is built |
|---|---|---|
| 1 | "The Corner desk should render as an actual corner desk" (FlexiSpot E7L link) | `corner_desk` is an L on a three-leg frame. Side, return, board depth, height 23.5–49.5, return left or right. Born 60 x 60 as before, so placed desks do not move; 63 x 47 is the E7L top |
| 2 | "Make the armchair H-W-D parameterized" | `armchair`: width 26–44, depth 28–42, back height 28–44, upholstery colour |
| 3 | "an umbrella table with 4 chairs and a parasol umbrella over a square table. The size of the table should be parameterized" | `umbrella_table`: square table 30–72, four chairs, pole and parasol. Footprint = table + 54 |
| 4 | "The bathtub should have a shower option, and a tub style option" | `bathtub`: three selectors. Tub: alcove / fiberglass wall insert / walk-in / on feet. Shower: none / showerhead / multiple. Enclosure: open / glass / curtain. Plus which long side stands on a wall |
| 5 | "The wicker chairs should look like wicker material" | the weave is GEOMETRY: rows of strands in two tones, alternately proud, over dark stakes. No texture is used |
| 6 | "a wicker loveseat" | `wicker_loveseat`, 50 x 29, 1–3 cushions |
| 7 | "a hanging flat-screen TV with adjustable size" | the existing `large_tv` made parametric by its diagonal (19–110) and its height off the floor; renamed "Wall TV 75\"". No new kind |
| 8 | "an artwork and plant (decorations) category" | palette group **Decor**: `wall_art`, `table_picture`, `plant_floor`, `plant_small`, `table_arrangement`, `floor_vase` |

Catalog 119 → 126. Seven kinds that were catalog solids are now parametric
fixtures: `corner_desk`, `armchair`, `umbrella_table`, `large_tv`,
`wicker_chair`, `wicker_chair_small`, `wicker_table`.

## 2. What is in the tree (uncommitted)

| File | Change |
|---|---|
| `floorplanner/parametric/cabinet_geometry.py` | 12 fixture models, 14 presets, 5 state keys (`tub_style`, `enclosure`, `shower`, `art`, `vase_fill`), 14 materials, roles; `_bathtub` rewritten, its alcove default unchanged |
| `floorplanner/parametric/cabinets.py` | dialog specs, two plan symbols (`corner_desk`, `umbrella_table`), summaries |
| `_gen_assets.py` | 7 rows, 7 SOLIDS rows, the Decor group; corner desk and umbrella table thumbnails redrawn |
| `assets/furnishings/` | `manifest.json`, `groups.json`, `materials.json`, `corner_desk.svg`, `umbrella_table.svg`; 7 new SVGs |
| `tests/test_viewer_model.py` | pin 119 → 126 |
| `tests/test_furnishings_0376.py` | new, 17 Qt-free tests |

## 3. Measured here (no Qt on this side)

- The Qt-free modules I can run: 243 pass. The same 5 fail before and after;
  all 5 are roof tests in `test_viewer_model.py` that need fixtures or Qt I do
  not have here.
- 47 presets that existed before, 13 state variants each, 611 cases: parts,
  footprint, height, trade code and materials identical.
- Generator: only the files in §2 differ from a regeneration of the old tree.
  Prices carried over; the 7 new kinds have none.
- Ruff clean on the changed files. The live tree imports; Patrick's plan builds
  with no `unknown` material. Its furnishing triangles go 38,868 → 43,804.

**Not checked, because it cannot be from here:** every Qt path. The dialogs, the
painted plan symbols, the palette, the item tests, the full gate.

## 4. Orders

- **O1.** Do not stash these. Keep them out of the 0375 commits: commit them by
  path on their own branch. If your gate goes red on a furnishings test while
  you are on 0375, that is this change set: report it, do not fix it forward.
- **O2.** Re-run `_gen_assets.py` on your machine, then ruff, pytest, the gate.
- **O3.** Declare the 5 new keys in `$defs.cabinet_state`.
- **O4.** Qt-side tests: each of the 14 kinds opens its dialog and round-trips;
  a placed `armchair` / `wicker_chair` / `corner_desk` with no state loads and
  saves with no state; the corner desk's plan symbol turns with `hand`; the
  umbrella table's footprint follows `size_in`.
- **O5.** Prices for the 7 new kinds.
- **O6.** Report as the next number. Say what O4 found.

## 5. Known gaps, recorded

- The tub's PLAN symbol does not change with its style, shower or enclosure.
- The wall TV keeps a 4 in depth whatever its size.
- Art is four fixed compositions in flat colour.

## 6. Tier and Patrick's look

AMBER. His look, in the 3D view, one of each: the corner desk (turn the return,
raise it); an armchair resized; the umbrella table at two sizes; the tub in each
style with a shower and an enclosure; a wicker chair and the loveseat up close;
the wall TV at two sizes; one of each Decor item on a table and on a wall.
