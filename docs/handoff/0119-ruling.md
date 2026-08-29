# 0119 — ruling: aligned dimensions for angled walls — tranche 2, on tranche 1's machinery

**Patrick:** callouts for walls on an angle — the Wiscaway right side is a run of
rooms aligned to 45°.

---

## 1. WHAT THE CODE DOES WITH AN ANGLED WALL TODAY — measured from `_features()`

* its **endpoints** land in the X and Y rows — as bare corner stations that
  dimension nothing about the wall itself;
* its **length appears nowhere** on the sheet;
* its **openings appear nowhere at all** — the opening-centreline code only
  fires for `abs(uy) < 1e-6` or `abs(ux) < 1e-6`. **A door in a 45° wall is
  simply absent from every dimension string.** That is a gap, not a style
  choice, and it is this ruling's second deliverable.

## 2. THE RULING — ALIGNED dimension strings, one per collinear run

**The standard drafting answer, and the one that fits this code:** a dimension
string **parallel to the wall**, offset perpendicular, text rotated to the
wall's angle.

* **Which walls qualify:** deviation from the nearest cardinal **> 1°** — the
  census's own near-axis boundary. A *drifted* wall (0.1° off) does **not** get
  its own aligned string; drift is [`0118`](0118-ruling.md)'s clustering's job,
  and giving it callouts would rebuild the mess this tranche exists to clean.
* **One string per collinear RUN, not per wall.** Group by (angle mod 180,
  perpendicular offset), both quantised with [`0118`](0118-ruling.md)'s same 1″
  cluster tolerance — Wiscaway's 45° room chain reads as **one string with
  stations**, not five overlapping ones.
* **Stations along the run:** every member wall's endpoints **plus every
  opening centreline**, projected onto the run's axis — then **clustered and
  whole-inch telescoped exactly as [`0118`](0118-ruling.md) §2 rules for the
  orthogonal rows.** Same machinery, rotated.
* **Placement:** offset by `DIM_LANE` on the side of the run **away from the
  plan's centroid** — deterministic, no collision logic. **Text never
  upside-down:** angles that would read inverted flip 180°.
* **The orthogonal rows keep angled endpoints** as corner stations —
  they bound real geometry, and [`0118`](0118-ruling.md)'s clustering already
  keeps them legible.

## 3. BUILD SHAPE — one generalisation, not a third copy

`dim_row_x` and `dim_row_y` are the same routine with the axis baked in.
**Refactor to one `dim_row_along(origin, unit, stations, offset)`; the two
orthogonal rows become calls of it; the aligned string is a third call with a
rotated unit.** Three transcriptions of ticks/extension-lines/label-fitting is
the thickness-table disease in drawing code.

## 4. TIER AND ORDER

| | | |
|---|---|---|
| 0 | **[`0118`](0118-ruling.md) first** — this ruling consumes its clustering and telescoping; building tranche 2 before tranche 1 lands means building the station machinery twice | order, not tier |
| 1 | **§3's `dim_row_along` refactor** | **GREEN** — no visible change, receipts are the existing dimension tests unchanged |
| 2 | **§2 — aligned strings + angled-wall openings** | **AMBER**, its own branch after `0118`'s merges |

**Receipts:** a two-wall collinear 45° run with one door → **one** aligned
string, stations telescoping to the run's overall; a drifted (0.2°) wall →
**no** aligned string; the door-in-angled-wall station RED against today's
`_features()` by construction.

**Patrick's check, one export:**

> **Export Wiscaway. The 45° rooms carry one parallel dimension string per run,
> readable without turning the page upside down, with the door positions in
> it — and the drifted walls still get no callout of their own.**

**Carried:** the `L2.dxf` Chief recount, the delta-snap sites, D61-family.
