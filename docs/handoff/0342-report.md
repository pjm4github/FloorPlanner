# 0342 — report: the 0340 + 0341 furnishing delta (desk / office chair / office set, and pedal bin / dog crate / sofa table / table lamp) gated GREEN and landed by path on `main`, catalog 104→108

**Code (Claude Opus 4.8), 2026-11-16.** Answers [`0340-ruling.md`](0340-ruling.md)
and [`0341-ruling.md`](0341-ruling.md), and Patrick's word ("the desk/office
components look good. go ahead and merge all the outstanding branches into
main."). Tier: **GREEN, LANDED** — one delta, gated, committed by path on `main`.

## 1. The gate — the whole 0340 + 0341 delta in the tree

```
Gate-Census: collected=2485 ruff=clean vacuous=0 end_assign=0 snapshot=current
Gate-OFF: 2478 passed, 7 deselected, 3 warnings in 102.49s (0:01:42)  -> sum 2485  OK
Gate-ON:  2478 passed, 7 deselected, 11 warnings in 122.22s (0:02:02)  -> sum 2485  OK
Gate-Verdict: GREEN (every sum reconciles against --collect-only)
```

2485 collected = 2441 (last cycle) + 44 from `test_office.py` (20),
`test_living_items.py` (19) and the expanded parametrized Qt / catalog cases;
OFF and ON both reconcile; 2478 pass, 7 deselected (perf lane). Re-run after
`0341`'s files settled (its ruling warned: "if a gate was running
while these files changed, discard it and re-run" — so this is a fresh full run
with both deltas final). No failures, ruff clean.

## 2. One delta, not two (and the report number)

`0341-ruling.md` §0 states it plainly: `0341` sits on top of `0340` in the same
two files (`cabinet_geometry.py`, `cabinets.py`), so **`0340` and `0341` are one
delta** and land together. `0340` was ruled + Patrick-checked (desk, office
chair, office set); `0341` rules the four I had earlier (in my withdrawn draft)
mis-called "un-ruled" — **they are ruled**: `pedal_bin`, `dog_crate`,
`sofa_table`, `table_lamp`. Because Cowork's `0341-ruling.md` took the `0341`
number, this report is **`0342`** (the draft `0341-report.md` was removed to
avoid the collision the commit hook would have refused).

## 3. What landed, and how — direct on `main` by path

`0340`/`0341` §4/§5 said "one more commit on `stairs-0338` (unmerged)," but that
branch was already MERGED and PUSHED (`95a96c1`). Its base is identical to
`main`, so there was nothing to branch: the delta landed **by path directly on
`main`** — the precedent for checked, GREEN, reviewer-built work. One commit
carrying the delta and the records; no merge commit.

What landed:
- **`0340`** — `desk` (top on end panels, modesty panel, drawer pedestals, and
  a monitor+keyboard+mouse / dual / laptop / nothing on top), `office_chair`
  (five-star caster base, gas column, upholstered seat + back, optional arms),
  `office_set` (desk + chair drawn up, cleared of a pedestal). Existing kinds,
  now parts-built; a `screen_glass` material.
- **`0341`** — four NEW catalog kinds: `pedal_bin` (round body, domed lid,
  pedal), `dog_crate` (tube frame, wire hoops, pan, door, optional bed),
  `sofa_table` (top, apron, legs, 0–3 shelves), `table_lamp` (a `fixture:
  table` LIGHT — glowing shade + a point source in `model.lights`;
  `floor_to_bottom_in` is the surface it stands on, 30 in default). Catalog
  **104 → 108**.

By path (nothing else): `floorplanner/parametric/cabinet_geometry.py`,
`cabinets.py`, `floorplanner/design/design-schema.v6.json`, `_gen_assets.py`,
`assets/furnishings/{manifest,materials,groups}.json`,
`assets/furnishings/{dog_crate,pedal_bin,sofa_table,table_lamp}.svg`,
`tests/test_cabinet_item.py`, `tests/test_viewer_model.py`,
`tests/test_office.py`, `tests/test_living_items.py`,
`docs/evidence/{0340-office,0341-living}/`. Mailbox on the same commit:
`0340-ruling`, `0341-ruling`, this report, the snapshot re-cut, the status board.
**Not touched** (both rulings, and the tree, agree): `fp3d.py`, `items.py`.
**Not committed:** `docs/gallery/*`, `docs/screenshot.png`, `fixtures/incoming/*`,
`gen/`.

## 4. To know (from `0341` §3)

A table lamp's height is a number, not found from the table under it — on the
bare floor it floats at 30 in until set to 0. "Table lamp" also appears in every
light's Shape list. The shade is three stacked rings (vertical prisms), not a
smooth cone. The crate is ~1,100–1,500 triangles. Nothing existing changes shape
in the `0341` half; in the `0340` half, existing desks/chairs/sets re-shape and
gain a default monitor.

## 5. Patrick's check

Desk & chair in 3D (monitor faces the chair, chair clears the drawers) — **done,
his word.** The four `0341` furnishings (`0341` §5: a sofa table with two lamps
lighting the room; dog crate and pedal bin in 3D) landed on his "land everything"
word and were not individually walked — eyeball at leisure.

## 6. Owed

- **Reviewer (Cowork):** any fix from §1 (none — GREEN). No git.
- **Code:** push `main` on Patrick's word; delete the merged `stairs-0338`.

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01XVitzXNKQWS64xhKKpacra
