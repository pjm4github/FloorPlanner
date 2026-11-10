# 0311 — report: the gable-end Elevation tab reads the walls under the gable and draws their doors AND windows, to scale with measurements — on a branch

**Code, 2026‑11‑11.** The record ([`0197-ruling.md`](0197-ruling.md) §7). A
follow-on to his either-gable-end elevation (#3, [`0309`](0309-report.md),
merged `486f13f`), on his word 2026‑11‑11: *"I need to have the roof gable end
tab show the windows that are part of the gable on that part of the wall under
the roof. There needs to be a way that we can read the walls under the gable end
and show them in the elevation view. The elevation viewer must read the walls and
display any doors and windows that are under them in the correct scale with
measurements."* Built on branch `gable-end-openings`, cut from `main`; AMBER,
**awaiting his check**. (No **Landed:** line — AMBER.)

## 1. WHAT WAS MISSING

The Elevation tab already drew a plain gable end to scale and located the
openings on its gable-end wall ([`0308`](0308-report.md)), but with two faults
his order names:

1. **Doors were not doors.** Every opening was drawn as a glass window floated at
   the window sill default (`DEFAULT_SILL_IN`, 36″). A door in the gable end sat
   36″ off the floor as glass, and its height came out 0 whenever its code did
   not parse as `W×H`.
2. **Only ONE wall was read.** `_gable_end_wall` returns a single wall and
   rejects any wall shorter than half the eaves width — so a gable end built from
   more than one wall piece, or a gable wall split into segments by a tee,
   dropped every opening that was not on the one chosen wall.

## 2. WHAT IT DOES NOW

`RoofItem.gable_elevation()` gains `_gable_end_openings(primary, end_pt, axis,
apex_in, width)`, which reads the gable-end wall AND **every collinear segment of
it** (same perpendicular line, within the gable's width), and returns **two
SEPARATE lists — `windows` and `doors`** (his word 2026‑11‑11, so a reader never
has to tell them apart by a tag; a gate rides with the doors, sitting on the
floor and drawing the same). Each opening is located in the elevation's own frame:

- **list + kind** — a window in `windows`, a door/gate in `doors`; each entry
  also keeps its `OpeningItem.kind` (`window` | `door` | `gate`).
- **size** — `w_in`/`h_in` from `OpeningItem.width/height`, which `set_code`
  fills for every kind, so a door's height is real (80″), never 0.
- **height above the floor** — a window keeps its own sill (its record's, else
  `DEFAULT_SILL_IN`); a **door or gate sits ON the floor** (sill 0, head = its
  height).
- **centre offset** — the opening centre projected onto the width axis, measured
  from the gable centreline (+ toward the primary wall's p2). The formula
  reduces exactly to the old `s − length⁄2` for a single wall centred on the
  ridge, so #3's located-window tests are unchanged; for segments it places each
  opening by its own wall's geometry.

`_gable_end_wall`'s length bar dropped from ½·width to `max(24″, 0.30·width)`, so
a gable wall split by a door (two ~0.4·width segments) still resolves a primary;
a 24″ stub is still rejected. The dialog's `_ElevationCanvas` now draws a
**window** as glass with a muntin cross (sill dimension), and a **door/gate** as
a panel on the floor with a leaf stile (head-height dimension); the centre-offset
dimension is drawn for both. The dormer-face branch is unchanged but tags its
windows `kind: "window"`.

## 3. RECEIPTS (instrument `docs/evidence/0311-gable-end-openings/render.py`)

Case 1 — one gable-end wall on an asymmetric gable (apex 20″ right of centre)
carrying a window, a door and a window — renders `gable_openings.png`: the two
windows float at their 36″ sills with a muntin cross, the door stands ON the
floor as a tan panel to its 80″ head, each dimensioned — the data in SEPARATE
lists (`windows` 2, `doors` 1):
`window 30×48 sill 36 centre −40`, `door 36×80 sill 0 head 80 centre +20`,
`window 24×36 sill 36 centre +80`. Case 2 — a gable end built from TWO collinear
exterior segments — renders `gable_segments.png` and reads an opening from BOTH:
`window 24×30 centre −60` (lower segment) and `door 30×80 centre +58` (upper).
Offscreen text renders as tofu; `fmt_in` is ASCII and draws on the real display.

## 4. TESTS

`tests/test_gable_elevation_ends.py` gains three: a door in the gable end is read
as a door into the `doors` list (sill 0, real height), the `windows` list empty; a
door and a window in one wall go to their OWN lists; two collinear segments are
both read (one window, one door, each inside the gable half-width). The #3 suites
(`test_gable_elevation.py` 7,
`test_gable_elevation_ends.py` existing) are untouched and green — the located
single-window cases (centre 0, offset 40) hold under the new projection. Gate:
full mode, GREEN.

## 5. NEXT

AMBER — his to check (open the End-On dialog on a gable end with a door and
windows, flip to each end, read the Elevation tab). Known limit, named for his
word: a gable end split into three or more SHORT segments (each below 0.30·width)
resolves no primary wall and shows nothing — raise it to a coverage sum if he
hits it. More #3 parameters remain his to order ([`0294`](0294-ruling.md) §4):
live spinbox tracking, head-below-ridge, corner offsets, pitch. 0248's items
8–9 named, not ordered.
