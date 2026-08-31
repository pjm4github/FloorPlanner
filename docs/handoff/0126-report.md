# 0126 — report: [`0127`](0127-ruling.md)/[`0128`](0128-ruling.md)'s three check findings fixed on `angled-dimension-lanes`, plus the global opening-station drop and footer note

**Built exactly to [`0127`](0127-ruling.md) §1–2 and [`0128`](0128-ruling.md) §1,
on the same branch (`angled-dimension-lanes`, still unmerged — check feedback
folded into the build it checked, per both rulings' own tier note).**

---

## 1. [`0127`](0127-ruling.md) §2 — snug + no crossing, one rule

`floorplanner/export/fp2pdf.py:Sheet._lane_geometry`/`_draw_angled_lane`
rewritten. The first cut sized the lane's clearance off the **whole plan
bbox** and ran extension lines from the family's own **centroid** — for a
diagonal wing that is not at the bbox edge, that meant every extension line
crossed straight through the wing before reaching open page space (the
`DIM45.png` screenshot's hatch of diagonal lines).

- `_lane_geometry` now also returns `reach`: the family's own farthest point,
  projected onto the OUTWARD perpendicular (same sign logic as before — which
  side of the plan bbox centre the family's centroid sits on). Local to the
  family, not the whole house.
- `_draw_angled_lane`'s extension lines now start at `reach + 4pt-equivalent`
  (the family's own outer envelope, the rotated analogue of the orthogonal
  rows' `ext_base`) and run straight out to `reach + DIM_LANE` (the lane
  itself) — never back across the family's own geometry, by construction:
  nothing in the family projects past its own `reach`.

## 2. [`0127`](0127-ruling.md) §1 / [`0128`](0128-ruling.md) §1 — opening stations dropped, globally

Patrick's first finding (angled lanes only) generalised by his own answer to
`0127`'s one open question: **all three row kinds** drop opening centrelines.

- `Sheet._features()` (the bottom/left rows) no longer collects opening
  centrelines — wall endpoints only.
- `Sheet._lane_geometry` (the angled lanes) never did, following `0127`.
- Openings still **draw** — symbols and W/H tags untouched, per
  [`0128`](0128-ruling.md) §1's own distinction.
- Title block footer: "Openings shown for reference; not dimensioned" added
  beside the existing dimension-reference note, per
  [`0128`](0128-ruling.md) §1's own instruction.

## 3. Fixture promoted, per [`0127`](0127-ruling.md) §2's own instruction

`fixtures/incoming/wiscaway2026-08-30R1.json` → `fixtures/wiscaway2026-08-30R1.json`
(exit 1), `fixtures/incoming/DIM45.png` → `docs/evidence/DIM45.png`. Entry
added to `fixtures/README.md` naming what it reproduces. **Load-bearing**:
`tests/test_fp2pdf.py::test_angled_lane_on_the_real_wiscaway_wing_stays_snug_and_off_the_geometry`
renders this file with the wing rooms' `show_dimensions` forced on and
asserts, per family: `reach` stays on the wing's own scale (< 500″, against
the file's own ~1360″ whole-plan bbox), no member wall's vertex projects past
`reach` (the no-crossing assertion), and the station count never exceeds
`2 × wall count` (no opening sneaks a station in) on a wing that genuinely
carries a door. Confirmed RED against the pre-fix code, GREEN after.

## 4. Full receipt

65 tests in `tests/test_fp2pdf.py` (was 62 after the prior build): the two
new geometry receipts above, plus the global opening-station-absent test on
both orthogonal rows and the footer-note presence check. `pytest -m "not gui
and not slow"`: 934 passed. `ruff` clean. Gate GREEN, full mode.

**Telescoping census re-run on the reduced station set**
(`docs/evidence/pdf_dimension_telescoping_census.py`), now walking the
promoted fixture too: **824 raw → 699 after clustering, 23 sheets, every
sheet telescopes.** Fewer, longer segments than before the opening stations
dropped — the feature [`0128`](0128-ruling.md) §3 named, not a regression.

## 5. Disposition

**AMBER, same branch (`angled-dimension-lanes`), same in-flight PR.** The
re-check, quoted from [`0127`](0127-ruling.md) §3:

> Lanes hug the red lines, nothing crosses the wing, no door positions — and
> one room's dimensions OFF still removes its edges.

And [`0128`](0128-ruling.md)'s added glance:

> The bottom row of the same export: fewer, longer segments, summing to the
> overall — and the opening W/H tags still on every door and window.

**Carried, per [`0127`](0127-ruling.md) §3:** the orthogonal-row door
question is now answered (§1, [`0128`](0128-ruling.md)), so nothing remains
open from that list except the `L2.dxf` Chief recount, the delta-snap sites,
D61-family — unchanged, untouched here.
