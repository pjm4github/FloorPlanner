# 0125 — report: [`0120`](0120-ruling.md)'s angled dimension lane built, AMBER, PR pending on `angled-dimension-lanes`

**Built exactly to [`0120`](0120-ruling.md) §2's spec, on top of the merged
[PR #44](https://github.com/pjm4github/FloorPlanner/pull/44)** (the GREEN
`dim_row_along` refactor). Branch `angled-dimension-lanes`.

---

## 1. The mechanics, as ruled

`floorplanner/export/fp2pdf.py`:

- `FAMILY_ANGLE_TOL = 1.0`, `_wall_angle_deg(dx, dy)` (undirected, folded
  into `[0, 180)`), `_near_cardinal(angle)` — new module functions,
  directly tested. `_near_cardinal` excludes BOTH near-0/180 (horizontal)
  and near-90 (vertical) — the X row already covers one, the Y row the
  other.
- `Sheet._angled_families()` — cycles `self.doc["rooms"]` on this level for
  `room["label"]["show_dimensions"]`, walks each show-dims room's outline
  edges, resolves the wall, skips near-cardinal ones, and clusters the
  survivors by angle (mod 180, `FAMILY_ANGLE_TOL`) into families — reusing
  [`0118`](0118-ruling.md)'s own clustering idea, rotated onto degrees. A
  wall visited twice (shared by two show-dims rooms) is deduplicated by id.
- `Sheet._lane_geometry(fam)` — the family's own axis `u` / perpendicular
  `n` / projection origin (member-vertex centroid) / **clustered stations**:
  every member wall's two endpoints plus every opening's centreline
  (`opening_span`, the same helper `draw_opening` uses), projected onto `u`,
  then `cluster_stations()` — closing [`0119`](0119-ruling.md) §1's measured
  gap (a door in an angled wall was absent from every dimension string).
  Split out from the drawing method so the station list is testable without
  a canvas.
- `Sheet._draw_angled_lane(fam)` — placement: outward perpendicular
  direction picked by which side of the **whole plan bbox's centre** the
  family's own centroid sits on (not just the family's local footprint);
  clearance computed by projecting all four bbox corners onto that outward
  direction and adding `DIM_LANE` — the SAME clearance the orthogonal rows
  sit at, past the WHOLE drawing, not just this family. Extension lines run
  from each station's own position on the family's zero-offset line out to
  the lane (the diagonal analogue of the orthogonal rows' "near-drawing to
  row-line" reach — a diagonal family isn't guaranteed to sit flush against
  one shared bbox edge the way an axis-aligned feature is, so each line
  reaches its own real position rather than a shared edge). Labels come from
  `_rounded_stations` + `ftin`, same telescoping machinery as the orthogonal
  rows; rotation uses the exact "never upside down" idiom already in this
  file (`draw_opening`, `draw_extras`): `rot = degrees(theta); if rot > 90 or
  rot <= -90: rot += 180`.
- `draw_angled_dims()` wired into `render()`, after `draw_dims()`.
- Scope, as ruled: a wall in no show-dims room, or a dims-off room, is never
  visited by `_angled_families()` at all — not a gap, the control surface.

## 2. Receipts

20 new tests (60 total in `tests/test_fp2pdf.py`, was 40): `_wall_angle_deg`
undirected both ways; `_near_cardinal` on both axes; family merging across
two rooms at the same angle; a dims-off room's wall excluded; a triangle's
two cardinal legs correctly ignored (only the hypotenuse joins a family);
station telescoping to the family extent (0120 §4's own named receipt); a
door on the family edge adds a station a same-shape doorless wall doesn't
(the RED-today gap, now closed); an end-to-end `convert()` render of a
synthetic show-dims angled room, no warnings.

**Manually verified against the real corpus file Patrick's own check
names** — `fixtures/wiscaway2026-08-09R.json`, `Garage`/`M Bath`/`MUD`
`show_dimensions` forced on: three families detected (a ~45° run across six
walls, a ~135° run across eight, and `M Bath`'s own `w25` at ~108° correctly
isolated as its own single-member family rather than merged into either
run), renders to a real PDF, no warnings, no exceptions.

Full suite `pytest -m "not gui and not slow"`: 929 passed. `ruff` clean.
Gate GREEN, full mode. Corpus telescoping census
(`docs/evidence/pdf_dimension_telescoping_census.py`) unchanged: 964→856.

## 3. Disposition

**AMBER, PR pending on `angled-dimension-lanes`.** Patrick's check, quoted
from [`0120`](0120-ruling.md) §4:

> Turn Show dimensions ON for the 45° rooms on Wiscaway's right side,
> export. One 45° dimension lane sits outside the drawing with those rooms'
> walls and doors in it, readable; turn one room's dimensions OFF,
> re-export, and its edges leave the lane.

**Carried, untouched:** the `L2.dxf` Chief recount, the two latent
delta-snap sites, D61-family — per [`0123`](0123-ruling.md) §"Carried".
