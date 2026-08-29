# 0121 — report: [`0118`](0118-ruling.md) built — station clustering, telescoping
whole-inch labels, and door_type-keyed symbols; [`0119`](0119-ruling.md)/[`0120`](0120-ruling.md) read, queued next in order

**Built exactly to [`0118`](0118-ruling.md)'s spec, on branch
`pdf-dimension-and-door-fix`.** `0119`/`0120` (aligned dimension lanes for
angled walls) landed on disk mid-build; both read in full before this report
was written. `0119` §1's gap-measurement and §3's `dim_row_along` refactor
stand; §2's per-run placement is superseded by `0120`'s room/`show_dimensions`
scheme. **Neither is started here** — `0118` §0's own ordering note ("building
tranche 2 before tranche 1 lands means building the station machinery twice")
means `0118` merges first.

---

## 1. D82 — station clustering + whole-inch telescoping labels

`floorplanner/export/fp2pdf.py`:

- `cluster_stations(values, tol=1.0)` — new module function. Merges dimension
  stations closer than 1″ into their mean, chaining transitively. `_features()`
  now returns `cluster_stations(sorted(fx))` / `cluster_stations(sorted(fy))`
  instead of the raw per-vertex sets.
- `_rounded_stations(coords)` — new module function, `[round(c) for c in
  coords]`. `dim_row_x`/`dim_row_y` compute this once per call and label
  adjacent pairs with `ftin(rounded[b] - rounded[a])` instead of `ftin(b - a)`
  on the raw stations. Row 2's overall call (`[fx[0], fx[-1]]`) rounds the
  same two endpoints the same way, so row 1's segments telescope to row 2's
  overall **by construction** — proven with a naive-vs-fixed contrast in
  `tests/test_fp2pdf.py` (stations 0.0/10.4/20.6/31.0: naive per-segment
  rounding gives 10+10+10=30, one inch short of round(31)=31; rounding the
  stations first gives 10+11+10=31, exact).
- `ftin` itself is untouched — whole-inch input already prints with no
  fraction (`frac == 0`), so nothing else that calls it changed shape.

**Corpus receipt:** `docs/evidence/pdf_dimension_telescoping_census.py`, new.
Walks `examples/` + `fixtures/` (21 sheets), asserts telescoping on both axes
for every one (all pass), and reports the clustering count: **964 raw stations
→ 856 after clustering, 108 merged.** `wiscaway2026-08-09R.json` — the exact
file `0118`'s own check names — goes from 190 to 156 (34 merged), the largest
single-file collapse after `crossfloor-snap-2026-08-17.json` (134→103,
45→27). 3 zero-wall levels skipped, a pre-existing limitation (`_frame()`
needs at least one wall), unrelated to this fix.

## 2. D81 — door symbols keyed off the real catalog

`_door_symbol(kind, door_type)` — new module function, pure and directly
tested. Dispatches on `floorplanner/config.py:DOOR_TYPES`' vocabulary
(`LH`/`RH`/`FRENCH`/`BIFOLD`/`POCKET`/`SLIDER`/`DOORWAY`/`GARAGE-*`), not
imported (config.py pulls in PyQt6 and `floorplanner.model`, which would drag
the Qt editor through `floorplanner/__init__.py`'s star-import — the same
constraint `_stdt.py`'s own docstring names) — the vocabulary is transcribed
as literal string comparisons instead, same as `walls.py:_paint_door` itself
has no shared "shape catalog" to import from.

`draw_opening` now draws a distinct symbol per catalog value: `LH`/`RH`/`""`
keep the existing single swing-leaf-plus-arc (unchanged shape, still reading
`hinge`/`swings_toward`, not `door_type` — v5's own reason for splitting those
fields from the leaf-type name); `FRENCH` is two half-width leaves from each
jamb; `BIFOLD` two connected V-folds; `POCKET` a dashed panel slid into the
wall plus a solid stub at the opening; `SLIDER` two overlapping panels;
`DOORWAY` two dashed face lines, no leaf; `GARAGE-*` a closed panel plus a
dashed overhead outline (a centre divider added for `GARAGE-2`). Any other
`door_type` string — including the literal `"sliding"` D81 found — draws the
generic swing **and** appends
`f"opening {code}: unrecognized door_type {door_type!r}, drawn as a generic
swing"` to a new `Sheet.warnings` list, collected into `ConvertResult.warnings`
by `convert()` (mirrors `fp2dxf.py`'s existing `Ctx.warn` pattern).

**Receipts:** `_door_symbol` tested directly, one case per catalog value plus
`"sliding"`/an unknown string (confirms both map to `"unknown"`, not silently
`"swing"`) plus the gate/window/cased fallthrough. End to end: `convert()`
exercised once per catalog value on a synthetic one-door plan — renders
without raising, `warnings == []` — and once each for `"sliding"` and a
made-up type — renders, and the returned `ConvertResult.warnings` names the
opening and the bad string.

## 3. Full receipt

39 tests in `tests/test_fp2pdf.py` (was 8), all new ones fail-first verified
against the pre-fix code where the ruling names a concrete regression (the
telescoping contrast, the drift-pair collapse). `pytest -m "not gui and not
slow"`: 908 passed. `ruff` clean. Gate GREEN, full mode.

## 4. Disposition

**One branch, one check, per `0118` §4's own table.** [PR pending] on
`pdf-dimension-and-door-fix`. Patrick's check, quoted from `0118` §4:

> Export the drifted `wiscaway2026-08-09R` plan set. The bottom dimension row
> reads as separated whole-inch strings — no overlapped labels; row 1 sums to
> row 2 on both axes; and the French and pocket doors on your own plan look
> like French and pocket doors.

**Next, in order, once this merges** (not before — `0118`'s own station
machinery is what `0119`/`0120` build on): `0119` §3's `dim_row_along`
refactor (GREEN, no visible change) is queued first, then `0120`'s
room-driven angled-dimension-lane feature (AMBER, its own branch).
