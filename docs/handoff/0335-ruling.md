# 0335 — ruling: stair U-gap, handrails and guards, stated headroom and landings. Built in the lane, UN-GATED, AMBER

**Reviewer (Cowork), 2026-11-15.** Patrick's word today: a U stair needs a
separation between its flights so a wall can stand there; add handrails "and
other missing requirements" so the validation box carries fewer open items.
Read 0334 first: the furnishing delta is on `main` (`0a73b94`); `lights-3d`
is Code's, AMBER, untouched by this.

## 1. What changed (all in the stairs lane; no viewer file edited)

- `floorplanner/parametric/stair_geometry.py` — `flight_gap_in` (U only: the
  landing is `2W + gap`, the second flight starts `gap` further over);
  `rail_solids`, `landing_edges`, `side_treatment`, `clear_width`,
  `guard_opening`, `nosing_line`, `required_opening`; eight new state keys;
  ten new profile limits (defaulted). `solids()` now ends with the rails, so
  `fp3d.build_stair` draws them with no change.
- `floorplanner/parametric/stairs.py` — eight new `ParamSpec`s;
  `handrail.guard` (NOT_EVALUATED) is gone, replaced by `handrail.required`,
  `handrail.height`, `guard.required`, `guard.height`, `guard.opening`,
  `width.clear`; `headroom.min` and `landing.top_bottom` are evaluated when
  the user states the opening / the landings and stay NOT_EVALUATED until then.
- `stair_view.py` (rail line in the elevation; headroom caption), `dialog.py`
  (size 1000x760 only), schema `$defs/stair_state` (+8 declared keys),
  `docs/furnishing-spec/STAIRS_STATE_AND_USAGE.md`.
- Tests: new `tests/test_stair_rails.py` (29 cases); one assertion changed in
  `test_stair_validation.py`, two in `test_stair_viewer.py` (the tallest
  vertex is now the rail, `rise + 36`).

## 2. Run, and not run

Stand-in runner, no Qt: `test_stair_geometry`, `test_stair_validation`,
`test_stair_viewer`, `test_stair_rails` — 81 pass, 0 fail. **Not run:** ruff,
`test_stair_item.py`, the dialog, the preview paint, the real viewer. The
picture in `docs/evidence/0335-stair-rails/` is my painter, not the app.

## 3. Behaviour changes to know

- **Every parametric stair already in a plan gains guards and two rails in
  3D** (defaults `guard` / `guard` / `both`). Plan symbol and footprint are
  unchanged. Legacy stairs (no `type`) are untouched.
- A default stair's open checks go from 4 to 3 (`headroom.min`,
  `landing.top_bottom`, `code.profile`); with the opening and both landings
  stated, 1 (`code.profile`, a WARNING by spec sec 6.2 — left alone).
- Headroom PASS rests on a STATED opening and a floor thickness of
  `rise - ceiling_in` (12 in when that is not 4..36). The app has no floor
  openings, so nothing measures it; the message says so.
- Rails are not drawn on the plan symbol. `handrail.required` and
  `guard.required` are WARNINGs, not ERRORs.

## 4. For Code

Gate; commit by path on a branch off `main`, apart from `lights-3d` and
Phase 2. Report failures verbatim — I fix them. AMBER: do not merge before
Patrick's check.

## 5. Patrick's check (one sitting)

1. Stair, double-click, Type U: set Gap between flights 4.5 — plan symbol
   widens by 4.5, flights part, footprint foot stays put.
2. Left side = Wall on a left U: 3D shows a wall handrail inside, guard outside
   and round the landing.
3. Validation box: no "handrails not modelled"; enter Stairwell opening =
   the "Opening needed" figure and both landings 36 — only the code notice
   remains.
4. An existing parametric stair in a saved plan now shows rails in 3D.
