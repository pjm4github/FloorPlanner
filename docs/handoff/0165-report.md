# 0165 — report: R4d — roof intersection clipping, the valley seam

**Code, 2026‑09‑07, answering [`0164-ruling.md`](0164-ruling.md) — the item
named-not-ordered since [`0139`](0139-ruling.md), ordered as R4d. Patrick's
instruction was *"continue with R5, and look at the new ruling too"*; the
ruling itself puts R4d first and keeps R5 RED behind its own ruling, so R4d
is what was built. R5 has not been started.**

---

## 1. WHAT'S BUILT

**A pure function of the roofs, nothing stored** ([`0164`](0164-ruling.md)
§1). `floorplanner/roofclip.py` takes the live roofs of one floor and
returns, per roof, the visible part of its own footprint, the seam segments
where its surface meets another's, and any pair it had to give up on. The
schema does not change; the roof's own rectangle stays the document's
truth, which is exactly what his select rule needs — the grips edit the
true rectangle, and it survives underneath.

**The geometry, as ruled** (§2):

* **The seam is the equal-height locus, constructed exactly.** Each roof is
  a piecewise-planar surface (two side planes, plus a hip plane past a hip
  end — `surface_height()`). The overlap of two footprints is cut into
  convex cells by every line along which either surface changes plane
  (each ridge line, each hip end's two equal-height lines); inside a cell
  the height difference is linear, so the seam is where it crosses zero on
  the cell's edges, by exact interpolation. Never sampled. Drawn **solid**,
  a real edge, distinct from the dashed eave/gable/hip lines.
* **A roof draws only up to the seam.** It keeps the part of a cell where
  it is the higher surface. Then the connected-component rule: a kept
  piece that no longer touches the roof's own body outside the overlap —
  the wing poking out the *far* side of the main, where the main's far
  slope has dropped below the wing again — is dropped, **and the other
  roof shows through it**, not a hole. Dropped from the paint AND from
  `shape()`: what paints is what hits (D85's lesson, carried).
* **Selected = unclipped.** `RoofItem.is_clipped()` is "a clip exists and
  the roof is not selected"; selecting shows the whole rectangle, outline
  and grips on true geometry; deselecting repaints re-clipped. The re-clip
  also runs after any grip drag or dialog apply (`rebuild` →
  `sync_roof_clips`), on a roof entering or leaving a scene, and never
  from `paint()`.
* **Same floor only.** Cross-level clipping is his one line if ever
  wanted; not assumed.
* **Degenerate pairs** (coplanar over a cell) draw unclipped and report
  it — `RoofClip.warnings`, carried onto the item as `clip_warnings`,
  `Sheet.warnings`-style: named in the result, never a crash. No `Sheet`
  class exists in the editor; the PDF converter's `Sheet.warnings` list
  ([`0121`](0121-report.md)) is the pattern the ruling names, and that is
  the pattern followed.
* **3D stays interpenetrating**, as ruled. Mesh-level clipping and seam
  lines in the exports stay named, not ordered.

**A decision worth his eye:** the clip is all our own convex-polygon
arithmetic on plain point lists (Sutherland–Hodgman against a value field,
Cyrus–Beck segment clipping, shared-boundary adjacency), not
`QPainterPath` booleans. The first cut used the booleans and *looked*
nondeterministic; the measured cause was different and is recorded in the
module docstring: **iterating a temporary `QPolygonF` yields points that
alias its buffer, and once the polygon is collected they read another
polygon's memory** — the same class as `fp_extract.py`'s `QImage` buffer
trap in CLAUDE.md. `footprint_polygon()` returns copies for that reason.
The own-arithmetic design stayed because it makes paint, hit shape and
tests read one exact geometry.

## 2. THE CHECK — receipts

`tests/test_roof_intersection.py`, **21 tests**, on a closed-form
miniature of the ruled case (main ridge along x at 150″ over 96″ eaves,
span 100; wing ridge along y at 130″, span 60, running into the main's
side): the seam apex is at `200 + 20/0.54 = 237.037` and the two valleys
run from it to the wing's eave-start corners on the main's eave line —
asserted as exactly two straight segments of known endpoints and length;
**every seam vertex at equal height on both roofs** (§3's receipt,
literally); no seam around the dropped island; the wing keeping its body
and the valley pocket only; the main losing exactly the pocket and
showing through the island; the two regions **partitioning the union of
the footprints by area** with the seam separating them; a no-overlap pair
left alone; coplanar roofs unclipped with a warning naming both; pairwise
folding per roof; on the item — derived not stored, the **select →
whole rectangle → deselect → re-clipped round trip** (§3), the hit shape
stopping at the seam and including it, a grip drag re-clipping live,
removing the main un-clipping the wing, another floor not clipping, the
warning reaching the item; the paint — seam ink present, no ink past the
far side, no ink under the main, ink in the pocket; and **the 45° wing**
— seam heights equal, area partition, the wing's ridge hidden where it
starts inside the main and visible at its far end, the item round trip.

Full suite **1247 passed**, 7 deselected (`perf` lane), collected 1254.
`ruff` clean. `python tools/gate.py` (full mode): **GREEN**.

Rendered offscreen and looked at, an orthogonal wing and a 45° wing each
running into a main roof, clipped and then selected: the wing's ridge
stops at the seam apex, the valley is a solid V, the main's eave line is
hidden under the wing between the valley feet, nothing pokes out the far
side; selected, each wing shows its full rectangle with its grips.

## 3. DISPOSITION — AMBER, PR open, waiting

**R4d is AMBER** ([`0164`](0164-ruling.md) §3): one branch, `roofs-r4d-clip`,
PR up, then stop. **His check, his words:** run the wing's roof into the
main roof. The valley seam draws as a real edge; nothing pokes out the far
side; selecting the wing shows its whole rectangle; deselecting re-clips it.

**R5 (dormers) stays RED behind this**, its own ruling when wanted — per
[`0164`](0164-ruling.md) §3, not started here.

**Carried, unchanged:** D83/D84 (held); room-label rounding
([`0131`](0131-ruling.md) §2); delta-snap sites; D61-family; yard items;
the stash entry (his call).
