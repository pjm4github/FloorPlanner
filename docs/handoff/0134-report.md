# 0134 — report: the cleanup tranche built — [`0129`](0129-ruling.md) §3(a)-(c) and [`0130`](0130-ruling.md)'s family exclusivity, on `dimension-cleanup-tranche`

**Built exactly to [`0129`](0129-ruling.md) §3 and [`0130`](0130-ruling.md),
against the check file [`0132`](0132-ruling.md) names — `wiscaway2026-08-30R2.json`.**

---

## 1. (a) Grid-aware station filtering

`Sheet.wall_snap_in` — read from `doc["settings"]["wall_snap_in"]`,
defaulting to 6.0 (`config.py:WALL_SNAP_DEFAULT`) only when the document's
own settings block omits it. `grid_filter_stations()` — a second declutter
pass after `cluster_stations`'s 1″ merge: adjacent stations still closer
than the document's own grid step keep only the on-grid one (within 0.1″ of
a `wall_snap_in` multiple); an all-off-grid crowd keeps clustering's own
mean, unchanged. Applied to both orthogonal rows (`_features()`) and every
angled lane (`_lane_geometry`) — the lane's own "on-grid" is a distance
along the family's axis from its centroid, not an absolute coordinate (a
correctly-snapped 45° wall's raw x/y is never a round number: 6″ along a
45° ray is `dx = dy = 6/√2`), the only grid concept that applies there at
all — flagged in the code's own docstring for visibility, not silently
assumed correct.

**Receipt that the value is actually read, not defaulted into matching**
(0132 §2's own instruction): a pair 8″ apart is untouched at the default 6″
step but collapses to its on-grid member at a 12″ step — passes only
because `grid_filter_stations` reads `snap_in`.

## 2. (b) Lane labels already feet-and-inches — confirmed

No code change needed; a receipt proves it rather than assuming: rounded
lane-station differences run through `ftin`, which only appends a
fractional suffix when one exists, so its absence over every adjacent pair
on a real family confirms whole-inch feet-and-inches output.

## 3. (c) Centerline note

Title text (module docstring, CLI `--dim-note` default, and
`PDFExportOptionsDialog`'s default) changed to **"All dimensions to wall
centerlines"**, matching the document's own `area_basis: centerline`.
**No station was actually face-derived** — `_features()`/`_lane_geometry`
both already read vertex coordinates directly; confirmed with a source
guard (neither references `wall_t`/`self.th`) rather than assumed from
the text alone.

## 4. (d) Openings — reaffirmed, no work

Already out everywhere since [`0126-report.md`](0126-report.md) §2.

## 5. [`0130`](0130-ruling.md) — family exclusivity

`_features()` now skips any wall whose angle isn't within 1° of
horizontal/vertical before collecting its endpoints — withdraws
[`0119`](0119-ruling.md) §2's "corner stations" bullet. A shared corner
between an orthogonal and an angled wall still appears in both families,
**once from each wall** (proven with a two-wall fixture: the shared vertex
present in both the X row and the lane; the diagonal-only vertex present
in neither the X nor Y row). Row 2's overall now telescopes within the
orthogonal family's own extent **automatically** — `fx`/`fy` are scoped
correctly at the source, so `draw_dims()`'s existing `[fx[0], fx[-1]]`
needed no change.

## 6. Fixture promoted, per [`0132`](0132-ruling.md) §2

`wiscaway2026-08-30R2.json` / `R2g.pdf` promoted from `fixtures/incoming/`
(exit 1), superseding R1 as the tranche's baseline — two levels, 15 rooms
with `show_dimensions` already on (Patrick's own state, nothing forced),
`wall_snap_in: 6.0` in its own settings. `R1` untouched, its own tests
still run. Entry added to `fixtures/README.md`; the R1 entry's own stale
`0124` citation corrected to `0127` in the same pass (the renumbering
0127's own file already documents).

## 7. Full receipt

78 tests in `tests/test_fp2pdf.py` (was 65): 24 new — the grid filter's
pure-function behavior, `Sheet.wall_snap_in` reading the document, the
centerline note in both places, the face-offset source guard, lane-label
fraction absence, a lone diagonal wall producing zero orthogonal stations,
the shared-corner two-family receipt, and a real-corpus regression against
the promoted R2 fixture. `pytest -m "not gui and not slow"`: 947 passed.
`ruff` clean. Gate GREEN, full mode.

**Corpus telescoping census rewritten** (`docs/evidence/pdf_dimension_telescoping_census.py`)
to isolate both declutter stages (disabling `cluster_stations` AND
`grid_filter_stations` for the "raw" column — the old script only disabled
the first, which had gone silently misleading now that `_features()` also
angle-filters unconditionally) and to check EVERY angled lane's own
telescoping independently, per [`0130`](0130-ruling.md) §2's re-pointed
invariant. Corpus-wide: **25 sheets, 733 raw → 574 after declutter, every
sheet telescopes; 4 angled lanes across the corpus, every lane telescopes.**

## 8. Disposition

**AMBER, branch `dimension-cleanup-tranche`, PR to follow.** The check,
quoted from [`0129`](0129-ruling.md) §4 + [`0130`](0130-ruling.md) §3:

> Export Wiscaway once more. Every orthogonal callout lands on the 6″ grid
> or is gone; the 45° lanes read in feet-and-inches; the title block says
> centerlines; and rows still sum to their overalls. No 45° corner appears
> in the bottom or left rows; no orthogonal corner appears in a lane; each
> row's segments sum to its own family's overall.

**Carried:** the room-label rounding question ([`0131`](0131-ruling.md)
§2, Patrick, one line), the `L2.dxf` Chief recount, the delta-snap sites,
D61-family.
