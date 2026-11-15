# 0338 — ruling: 0337's five ruff errors fixed; fixtures in 3D, island slots and plan symbol, grab bars, the stairwell cut. Built in the lane, UN-GATED, AMBER

**Reviewer (Cowork), 2026-11-15.** Answers [`0337`](0337-report.md) and
Patrick's word today. Nothing here is committed; nothing has seen ruff or Qt.

## 1. 0337

- **§1's five ruff errors are fixed** in `stair_geometry.py`: `q(t, i)` is
  `q(along, inset)` (its parameters shadowed two loop names — B023 x4), and
  the unused `d` in `nosing_line` is gone (F841). Re-gate.
- **§6 contradicts §1.** §6 says "none owed — gate GREEN, ruff clean"; §1 says
  RED, 5 errors, commit held. §1 is the true one (the tree confirms: nothing
  committed). Do not carry §6's line forward.
- **§2's two deviations are accepted** (8 files, and the mailbox on `main`
  first). The hook's rule beats my 0336 §2.2 wording.
- **§4, the icons: those are mine** — every `_gen_assets.py` run here writes
  them LF. I ran it again today. They are content-identical noise; Code may
  restore them (`git checkout -- assets/icons`) at any time without asking.

## 2. What is new in the tree (0338)

| Asked | Built |
|---|---|
| 3D toilet, bathtub, bookshelf, fireplace | A new `fixture` type in `cabinet_geometry.py`, built from parts like a cabinet. Each gets a dialog. Parts may now be convex n-gons (the toilet bowl), built by `fp3d._ngon_prism`. |
| Island slots, bar sink | `BS18`/`BS24` bar sink, `CT30`/`CT36` cooktop over drawers, `RG30` range (stands through the top, no backguard), `WC15`/`WC24` wine cooler, `MW24` microwave drawer. The island top is now laid by `_top_grid`, so holes of different depths coexist. |
| Island plan symbol shows seats | `cabinet_geometry.island_plan` + `ParametricKind.plan_symbol` + `FurnishingItem._paint_plan_symbol`: slots, bowls, hobs, one stool per seat, from the same `island_stools` the 3D uses. |
| Bathroom handrails | New catalog kind `grab_bar` (104 kinds): horizontal or vertical, length, height, finish. |
| Hole in the floor above a stair | `stair_geometry.stairwell` / `opening_rects`; `fp3d.stair_openings`, `_minus_convex`, `_cut_holes`. The floor of any level a parametric stair passes through, and its own storey's ceiling, are cut over the stated opening, else the opening headroom requires. |

Files: `cabinet_geometry.py`, `cabinets.py`, `registry.py`,
`stair_geometry.py`, `items.py`, `viewer/fp3d.py`, `_gen_assets.py` (+
regenerated `assets/furnishings/{manifest,materials,groups}.json`,
`grab_bar.svg`), schema (`$defs/fixture_state`). Tests: new
`test_fixtures.py`, `test_fixtures_viewer.py`, `test_stairwell.py`; appended
7 Qt cases to `test_cabinet_item.py`; `test_viewer_model.py` — catalog size
103 -> 104, and the partition test gains a fourth list (a parts-built kind
whose catalog form is not `box`: the bathtub).

## 3. Outside my usual files — said out loud

`fp3d.py`'s FLOOR-SLAB and CEILING loops are edited (about 30 lines): a room
with a stairwell over it is built as convex pieces; every other room takes the
old indexed path unchanged. This is Patrick's instruction ("put a hole in the
floor rendering"); it is the only edit outside the furnishing region. Code:
read that hunk before gating.

## 4. Run, and not run

Stand-in runner, 12 modules: 262 pass; the 1 failure imports PyQt6. **Not
run:** ruff; every Qt test (the 7 new ones included — `_paint_plan_symbol`
has never executed); the Qt Quick view. Evidence image is my painter.

## 5. Behaviour changes

- Existing toilets, tubs, bookshelves and gas fireplaces change shape in 3D.
  The tub no longer holds water.
- Existing islands lose their SVG symbol for the drawn one.
- Crowded island stools narrow to fit (was: overlapped).
- Existing two-storey plans with a parametric stair get a hole in the floor
  above. Legacy stairs cut nothing. No guard is drawn round the hole upstairs.

## 6. For Code

The stair delta (0335) and this share `stair_geometry.py`, so they land
together: mailbox on `main` (0335, 0336, 0337, this), then ONE branch off it,
commit by path, gate. Failures verbatim. AMBER.

## 7. Patrick's check (one sitting, with 0335 §5)

1. Bathroom: toilet, tub, grab bar in 3D; double-click each.
2. Bookshelf and gas fireplace in 3D; fireplace Lit off/on, Surround = brick.
3. Island: set a slot to Bar sink, another to Range; change Seats — the plan
   symbol and the 3D both follow.
4. Two-storey plan with a parametric stair: from upstairs, the floor is open
   over the stair; from below, so is the ceiling.
