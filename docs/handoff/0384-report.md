# 0384 — report on 0376 / 0377 / 0378 (the furnishings lane). The schema keys declared, the kinds priced, the Qt-side editor tests written, the gallery brought current, the drop-on-save defect filed (D90). Gate GREEN. Patrick looked ("it looks very good") and gave the word; LANDED on `main`.

2026-11-27, Code. Branch `furnishings-0376`, rebased onto `main` `5c0828a` (the
dormer landing). No `fp3d.py` here. This files 0376 O6 / 0377's report and does
0378 step 3's owed work on `main`.

## 1. The orders, done

**O2 / 0377 O1 — regenerate.** `_gen_assets.py` runs; `git grep -l c2pa -- assets`
returns **nothing** (0377 §3's foreign-metadata fix holds). Content is
idempotent: ignoring line endings, a regeneration differs from the committed
tree only in the eight prices below. **But every asset shows modified — that is
line endings** (the generator writes LF; the working tree is CRLF): 159 files,
`git diff --ignore-all-space` empty on each. Per 0378 §4 I report it and do **not**
commit the churn; the committed SVGs are 0377 §3's byte-verified ones.

**O3 / 0377 O2 — the schema.** Eight keys declared in
`$defs.cabinet_state` of `design-schema.v6.json`: `tub_style` (alcove / insert /
walk_in / clawfoot), `shower` (none / single / multi), `enclosure` (none / glass
/ curtain), `art` (abstract / landscape / botanical / mono), `vase_fill`
(branches / empty), `trio_order` (ascending / descending), `trio_shape` (row /
stepped), `gap_in` (number). The object was `additionalProperties: true`, so this
documents and bounds them rather than enabling them.

**O4 / 0377 O3 — Qt-side tests (what they found).** New
`tests/test_furnishings_item_0376.py`, 23 tests, all GREEN:
- each of the **16** parametric kinds places as a `FurnishingItem`, opens its
  properties dialog (derived parts non-empty), accepts, and round-trips the
  edited state through the item AND the saved document; the footprint reproduces
  on reload.
- a placed `armchair` / `wicker_chair` / `corner_desk` with **no state** loads and
  saves with no state.
- the corner desk's and the picture arrangement's plan symbols **turn** when
  `hand` / `trio_order` is edited on the item; the umbrella table's footprint
  **grows** when `size_in` is edited on the item.
The geometry itself stays pinned Qt-free in `tests/test_furnishings_0376.py` (20
tests): the L on three legs, the E7L sizes, the weave in two tones, the tub
fittings, the 2:3:4 widths, the footprints.

**O5 / 0377 O4 — prices.** The eight new kinds, priced **by comparison** with the
catalog (like 0369 §O5; not the AI pricing tool, so Patrick may re-price):
`wicker_loveseat` 420 (vs loveseat 480), `picture_trio` 240 (~3× wall_art),
`plant_floor` 120, `wall_art` 90, `floor_vase` 90, `table_arrangement` 60,
`table_picture` 35, `plant_small` 35. Set in `manifest.json`; the generator
carries them across regeneration.

**Gallery.** `python docs/make_gallery.py` — the gallery was last cut at
`4d97705` (2026‑11‑16), **87 commits back**, so it was stale; this brings it
current (16 pages). `20-3d-view.png` alone is nondeterministic (it re-renders
differently every run) and is left at its committed bytes.

**D90.** `docs/defects/0090-…` filed for 0378 §5: an unknown furnishing kind is
skipped on load and so dropped on the next save (the wicker set, then four
cabinets). OPEN, no fix ruled.

## 2. 0378 §4 — the checklist

| Check | Result |
|---|---|
| catalog size | **127**; `test_viewer_model` pin passes |
| `git grep -l c2pa -- assets` | nothing |
| `_gen_assets.py` run twice | the second run changes no file (beyond the LF/CRLF churn above) |
| `git status` after regenerating | every asset shows modified = line endings; **reported, not committed**; the real content change is `manifest.json` (eight prices) |
| the 47 older presets | unchanged — the 611-case regression in `test_furnishings_0376` holds |
| a placed `armchair` / `wicker_chair` / `corner_desk` / `bathtub`, no state | loads, keeps its footprint, saves with no state (Qt-side test) |
| evidence | 16 PNGs, one per kind, from the real viewer, in `docs/evidence/0376-furnishings/` with an INDEX |
| gate | GREEN, ruff + OFF + ON |

## 3. The look, and the landing

The gate is GREEN. The evidence PNGs show one representative render per kind;
Patrick looked (0376 §6, 0377 §5) — *"it looks very good"* — and gave the word.
**Landed on `main` by this merge.** The eight new/reworked kinds (catalog 127),
their prices (by comparison; re-price with the AI tool at will) and D90 are on
`main`. Next in the dormer workstream: 0372 C (`compute_roof_clips` hang, open
the defect first), D (D89 skirt-not-live), E (two dialog advisories), and B2
(the hipped front-corner floor tabs) with them.
