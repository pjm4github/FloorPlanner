# 0377 — ruling: one more Decor kind (a 2-3-4 picture arrangement) joins 0376's change set, and a correction to how 0376's SVGs were installed. AMBER.

2026-11-26, reviewer session, furnishings lane. Adds to `0376-ruling.md`; its
orders stand and now cover this too. Nothing is committed.

## 1. Patrick's words, and the reading taken

*"make a picture arrangement that has 3 complementary paintings that are
arranged on a wall in a 2-3-4 pattern."*

Built as kind `picture_trio`, "Picture Arrangement 2-3-4", in the Decor group:
three framed pictures hung as one item. Their WIDTHS share the arrangement's
width, less two gaps, in the ratio 2 : 3 : 4. Read that way because it is the
one reading the words fix; the other (sizes stepping in both directions) is a
setting, `trio_shape = stepped`.

| Setting | Values |
|---|---|
| width of the arrangement | 24–180 in (born 72) |
| height (the tallest picture) | 8–72 in (born 30) |
| gap | 0–12 in (born 3) |
| order | 2-3-4, or 4-3-2 |
| shape | one height, or stepped (heights 2 : 3 : 4 too, on one centre line) |
| pictures | the four `art` subjects, each as THREE pictures in one palette |
| frames, height from floor | as `wall_art` |

"Complementary": in the abstract set blue leads on the left and its
complement, ochre, on the right; the landscape is one view across the three.

## 2. What changed in the tree since 0376

| File | Change |
|---|---|
| `cabinet_geometry.py` | model `picture_trio`, its preset, keys `trio_order`, `trio_shape`, `gap_in`; `_picture` takes a name tag and a composition |
| `cabinets.py` | its dialog specs, plan symbol (three frames along the wall), summary |
| `_gen_assets.py`, `manifest.json`, `groups.json`, `picture_trio.svg` | the row, the SOLIDS row, the Decor group |
| `tests/test_viewer_model.py` | pin 126 → 127 |
| `tests/test_furnishings_0376.py` | 3 more tests (20 in all) |

Measured here: 246 pass on the Qt-free modules, the same 5 roof tests fail as
before; the 611-case regression of the 47 older presets still identical; ruff
clean; the live tree imports and builds the new kind.

## 3. Correction: nine SVGs were installed with foreign metadata

The nine SVGs I installed for 0376 at 16:15 local each carried an injected
`<metadata>` block and an `xmlns:c2pa` attribute (about 8 KB each). It was
added by the path I staged them through, not by the generator. I found it at
16:22 comparing bytes, and replaced all nine, plus `picture_trio.svg`, with the
generator's own output. Now, in `assets/`: no file contains `c2pa`, and the ten
match a regeneration here byte for byte:

`corner_desk` 64337236, `umbrella_table` 91be668a, `floor_vase` dd4dad5c,
`plant_floor` caf8ece1, `plant_small` bf601593, `table_arrangement` 71fa4181,
`table_picture` 5af2adb6, `wall_art` c0dfe3e9, `wicker_loveseat` e0650035,
`picture_trio` 2e50fe8f (md5, first 8).

If you ran anything against the tree between 16:15 and 16:24, run it again.

## 4. Orders (added to 0376's)

- **O1.** 0376 O2 (re-run `_gen_assets.py`) is now also the proof for §3: after
  it, `git grep -l c2pa -- assets` returns nothing. Say so in the report.
- **O2.** 0376 O3 grows by three keys: `trio_order`, `trio_shape`, `gap_in`.
- **O3.** 0376 O4 grows by one kind; add that its plan symbol turns with
  `trio_order`.
- **O4.** A price for `picture_trio`.

## 5. Patrick's look

One line more on 0376 §6: the arrangement on a wall, in each order and shape,
with at least two of the picture sets.
