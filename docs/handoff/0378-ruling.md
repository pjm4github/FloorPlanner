# 0378 — ruling: how the furnishings of 0376 / 0377 reach `main`. After the dormer branch, on their own branch, behind Patrick's look. AMBER.

2026-11-26 (17:05 local), reviewer session. 0376 and 0377 say WHAT is in the
tree and what to add to it; this says the ORDER it lands in. Their orders stand.

## 1. Patrick's words

*"give me the instructions to CC so that it can incorporate these furnishings
into the main line code once all the branches are merged."*

## 2. Where things stand, as read from disk

- You are on `dormer-climb-floor-0372` at `2f39c90`, with `fp3d.py` and
  `tests/test_viewer_dormer.py` modified: 0375's item A, in progress.
- In the same working tree, uncommitted, mine: 4 modified source files, 1 new
  test file, 8 new SVGs, 3 changed JSON and 2 changed SVG under `assets/furnishings`.
  Not one of them is a file the dormer branch has touched.
- 0376 and 0377 are on disk, not yet filed.

Fingerprints as I left them (md5, first 8), so you can prove nothing was lost:
`cabinet_geometry.py` f51dfc2f, `cabinets.py` 9ab70fd0, `_gen_assets.py`
a4d615a9, `tests/test_viewer_model.py` af221683, `tests/test_furnishings_0376.py`
f679445e, `manifest.json` 4e5e81c6, `groups.json` 53f354b2, `materials.json`
f71a4170. The ten SVGs are in 0377 §3.

## 3. The order

1. **Before anything is switched, merged or reset: get the furnishing files
   into a commit.** Branch `furnishings-0376`, cut from `main`, the files of §2
   added BY PATH and nothing else. No stash. How you get there with 0375's
   work open is yours; the test is that afterwards the eight fingerprints above
   read the same in that commit, and `fp3d.py` and `test_viewer_dormer.py` are
   not in it. If `tests/test_viewer_model.py` also needs an edit for 0375, the
   two edits go in by hunk, each to its own branch.
2. **Finish 0375 on the dormer branch.** Report, Patrick's look, merge. The
   furnishings do not wait inside that PR and do not block it.
3. **When `main` holds the dormer work,** bring `furnishings-0376` onto it and
   do the owed work there:
   - 0376 O2: re-run `_gen_assets.py`, ruff, pytest, the gate.
   - 0376 O3 with 0377 O2: declare the 8 keys in `$defs.cabinet_state`:
     `tub_style`, `enclosure`, `shower`, `art`, `vase_fill`, `trio_order`,
     `trio_shape`, `gap_in`.
   - 0376 O4 with 0377 O3: the Qt-side tests, 15 kinds.
   - 0376 O5 with 0377 O4: prices for the 8 new kinds.
   - `python docs/make_gallery.py`.
4. **Open the PR and stop.** AMBER: Patrick's look is the merge condition
   (0376 §6 and 0377 §5, one sitting).
5. **On his word, merge, file the report, re-cut the snapshot.**

## 4. What the report must show

| Check | Expected |
|---|---|
| catalog size | 127; the pin in `test_viewer_model.py` passes |
| `git grep -l c2pa -- assets` | nothing |
| `_gen_assets.py` run twice | the second run changes no file |
| `git status` after regenerating | only `manifest.json`, `groups.json`, `materials.json`, `corner_desk.svg`, `umbrella_table.svg` and the 8 new SVGs. If every asset shows modified, that is line endings: report it, do not commit the churn |
| the 47 older presets | their parts unchanged (I measured 611 cases identical; say how you checked) |
| a placed `armchair`, `wicker_chair`, `corner_desk`, `bathtub` with no state | loads, keeps its footprint, saves with no state |
| evidence | one PNG per new or changed kind from the real viewer, in `docs/evidence/0376-furnishings/`, with an INDEX |
| gate | the result line, both modes |

## 5. Recorded, not ordered

Twice now a running app that did not know a new kind has dropped it from
Patrick's plan on save (the wicker set, then four cabinets). An unknown
furnishing is skipped on load and so is gone on save. Open a defect record for
it with both instances. No fix is ruled here.
