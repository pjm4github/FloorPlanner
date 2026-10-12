# 0267 — report: his annotation-display clean-up — ONE font size and ONE colour for every item annotation; the opening's label off its size code; the room's painted last so the fill does not tint it

**Code, 2026‑10‑12.** His words, with a screen capture, after
[`0266`](0266-report.md):

> *"I meant to say Item Annotations. See the attached screen capture: The
> green items are the Item Annotations. They are small for wall and
> vertices but are too big and clipped for doors, rooms, openings,
> furnishings, etc. Make the font size and color for all the Item
> annotations the same so that the clutter is reduced and the user can
> visually filter color and size for look at Item Annotations."*

Built on `item-annotations-font`, ONE commit on `main`'s tip, AMBER for
his check.

## 1. WHAT WAS THERE

Six paint paths, five fonts. [`0264`](0264-report.md) gave each item kind
its own callout, each written in that kind's own font: the wall's and
corner's in 11 view pixels at any zoom; the opening's in a 6‑INCH font
prefixed to the size code (so it grew with the zoom and the two ran
together); the room's in the room's own name font (the big one, clipped
to the label rect); the furnishing's in a 7‑inch font clipped to a
10‑inch‑tall box; the roof's in a 9‑inch font. His capture: the small ones
read, the big ones crowded and cut.

## 2. WHAT IS THERE NOW

* **One font, one size** — `CALLOUT_PX` (9) view pixels whatever the zoom
  and whatever the item: `callout_font(lod)` in `annotations.py` sizes the
  font by the painter's own scale, and `draw_callout(painter, lod, at,
  text, align)` draws one annotation unclipped (left, centred or
  right‑aligned at a point) in the one font and the one colour
  (`callout_colour()`, *Show ▸ Item callout colour…*). Every kind paints
  through it: wall, corner, opening, room, furnishing, roof.
* **The opening** — the size code (`3680 RH`) stays the symbol's own, in
  its grey, where it was; the SESSION LABEL (`O60`) is the item
  annotation, on the OTHER side of the wall from the code, so neither
  covers the other.
* **The room** — the label under the room's name, painted LAST so the
  room's translucent fill no longer tints it (it was painted first, under
  the fill).
* **The furnishing** — centred under the footprint, no clipping box.
* **The roof** — beside the ridge's middle, offset in view pixels.

Rendered on his `wiscaway2026-10-11R3.json` at 2× and 4× (the windows
platform): every label the same nine pixels, the same blue, at both zooms.

## 3. A TRAP MET

The **offscreen platform's font engine draws nothing below five pixels**:
a 3‑pixel font under a 3× painter (nine device pixels) paints no ink
headless, while the windows platform paints it with the same ink coverage
as a 9‑pixel font at 1×. The test checks the ink at 1× only and the size
arithmetic at both; a headless grab of a zoomed plan needs
`QT_QPA_PLATFORM=windows`.

## 4. RECEIPT

`tests/test_annotations.py` (19): the new test paints a wall, a corner,
a door, a room, a furnishing and a roof under 1× and 3× painters, spies
every `draw_callout`, and asserts one pixel size per scale across all six
kinds, each reading the painter's own scale, each painted in the one
colour. `--quick` passed; gate GREEN.

## 5. WHAT HAPPENS NEXT

His check. Then his further tuning of the annotation tool and the Show
menu, on his words. Named: DXF/PDF export of annotations; a leader
annotation; his backlog (0248's items 8 and 9).

**Carried:** unchanged from [`0266`](0266-report.md).
