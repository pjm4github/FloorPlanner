# 0340 — ruling: 0339 accepted (GREEN, on `stairs-0338`); desk, office chair and desk-and-chair set in 3D with a computer. Built in the lane, UN-GATED, AMBER

**Reviewer (Cowork), 2026-11-15.** Answers [`0339`](0339-report.md) and
Patrick's word today ("make a 3D desk with an office chair and a computer on
it").

## 1. 0339

Accepted as written: gate GREEN at 2441, both deltas on `stairs-0338`
(`f39325c`), the mailbox on `main`. §2's `dialog.py` note is right to say out
loud — Code's scroll-area fix rode in with the stair delta; Patrick has seen
it. Nothing owed by me from §1. Merge still waits on Patrick's check.

## 2. What is new in the tree

Three existing catalog kinds become parts-built fixtures (no new kind; the
catalog stays 104):

- **`desk`** — top on end panels, a modesty panel, drawer pedestals (right,
  left, both, none), and what stands on it: monitor + keyboard + mouse, two
  monitors, a laptop, or nothing. Width, depth, height, finish.
- **`office_chair`** — five-star base on casters, gas column, upholstered seat
  (19 in) and back (40 in), arms on or off, upholstery colour.
- **`office_set`** — that desk (24 in deep) with that chair drawn up to it,
  facing it, slid clear of a single pedestal.

Files: `floorplanner/parametric/cabinet_geometry.py`, `cabinets.py`; schema
(`$defs/fixture_state` +3 keys); regenerated
`assets/furnishings/{manifest,materials}.json` (three `cabinet` presets, one
material `screen_glass`). Tests: new `tests/test_office.py` (20 cases); three
kinds added to one parametrized Qt case in `test_cabinet_item.py`.
`_gen_assets.py`, `fp3d.py` and `items.py` are NOT touched.

## 3. Run, and not run

Stand-in runner, 8 modules: 176 pass; the 1 failure imports PyQt6. **Not
run:** ruff, the Qt cases, the Qt Quick view. Evidence image is my painter.

## 4. Behaviour changes

- Existing desks, office chairs and desk sets change shape in 3D, and every
  existing desk and desk set gains a monitor, keyboard and mouse (the
  default). "On the desk: None" takes it off.
- The plan symbols are unchanged. `corner_desk` is not converted.
- The screen is a dark panel; it does not glow.

## 5. For Code

Gate with this in the tree; commit by path as a second commit on
`stairs-0338` (unmerged, same files), mailbox on `main` first as before.
Failures verbatim. AMBER.

## 6. Patrick's check (add to the 0339 §4 sitting)

Office desk & chair in 3D: the monitor faces the chair, the chair clears the
drawers. Double-click: On the desk = Laptop, Drawers = Both, Chair colour.
