# 0308 — report: #3 the gable-end window elevation — the End-On dialog's Elevation tab, built on a branch

**Code, 2026‑11‑09.** The record ([`0197-ruling.md`](0197-ruling.md) §7). His
standing item **#3** (the dimensioned gable-end window elevation — [`0294`](0294-ruling.md)
§4, named-not-ordered), begun on his word "Start #3." Built on branch
`gable-elevation`, cut from `main` (69dcefa, the #1 merge, [`0307`](0307-report.md));
AMBER, **MERGED** into `main` 2026-11-09 by a two-parent local merge on his word
("Merge #106, and sweep in the schema_viewer.py and the corrected pyproject.toml"),
which also swept in his orthogonal `tools/schema_viewer.py` and its `schema-viewer`
optional dependency. (No `**Landed:**` line: a two-parent merge's landing commit is
not on `main`'s first-parent chain.)

## 1. HIS ORDER (2026‑11‑09)

The elevation view is his to order parameter by parameter ([`0294`](0294-ruling.md)
§4); its door is the plan double-click on a window, already wired (§2). He
ordered this first cut: a **new TAB in the End-On dialog** (not a standalone
dialog, not a PDF sheet); covering **both a dormer face AND a plain gable end**;
with the **minimal locating set** — per window its size (W×H), its sill above the
floor, and its centre's offset from the gable centreline.

## 2. WHAT IT DRAWS

`RoofItem.gable_elevation()` (new) returns the drawing data, or `None` when there
is no gable to draw:

* a **dormer**: its own face gable (`_dormer_wall_lines()[0]` width, eaves/ridge
  above the dormer's own floor via `dormer_sill_floor_in`) and its `openings` —
  the windows the dialog edits, placed by `face_window_span`;
* a plain **gable** roof: the gable-end triangle (the two eaves spans wide, the
  eaves/ridge heights) and the gable-end WALL's windows — the exterior wall
  perpendicular to the ridge at a live gable end, found by `_gable_end_wall`
  (prefers the end whose wall carries windows, else `marker_end`).

Heights are measured from the elevation's own floor; `floor_abs_in` labels it. A
window's `centre_in` is its offset from the gable centreline, `sill_in`/`head_in`
its heights; `apex_in` is the ridge peak's offset (0 when symmetric).

`_ElevationCanvas` (dialogs.py) paints it to scale: the gable outline (walls to
the eaves, roof to the ridge apex), a dashed centreline, each window a glazed
rectangle with its size label, a vertical sill dimension and a horizontal
centreline-offset dimension. `RoofEndOnDialog` is now **tabbed** — "Parameters"
(every prior field, unchanged) and "Elevation"; the tab reads the roof's stored
geometry on open and when shown. Live spinbox tracking is a later parameter, his
to order.

## 3. RECEIPTS (instrument `docs/evidence/0308-gable-elevation/render.py`)

Renders: a 366″-wide gable with three located windows, and a dormer face with its
window — both read as an architect's elevation (outline, centreline, glazed
windows, sill and offset dimensions). On `wiscawayL2-fix.json` the gable-end walls
are found with their windows (36×48, 30×48, 110×80; sills at the default 36″); on
`little-dormer-test.json` each dormer face draws its 30×30 window. (Headless text
renders as tofu — the offscreen font has no glyphs; `fmt_in` is ASCII and draws on
the real display.)

## 4. TESTS

`tests/test_gable_elevation.py` (7): the plain-gable outline, an asymmetric apex,
a located gable-end window, an off-centre offset, an interior stub NOT mistaken
for the end wall, a dormer face window, and a gui test that the dialog grows an
"Elevation" tab that paints. Gate: full mode, GREEN.

## 5. NEXT

Checked and MERGED (his word). More elevation parameters are his to order ([`0294`](0294-ruling.md)
§4): live tracking of the spinboxes, head-below-ridge, offsets from the corners,
the pitch, the second gable end. 0248's items 8–9 named, not ordered.
