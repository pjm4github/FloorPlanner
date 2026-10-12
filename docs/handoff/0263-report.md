# 0263 — report: his four features built on his word — annotations (text) on the plan, measurements that snap to items with a datum, the items' callouts in a settable colour, and a Show menu that switches each on its own; 0248's items 8 and 9 backlogged — on `annotations-measure`, AMBER, for his check

**Code, 2026‑10‑11.** No merge has happened since
[`0262`](0262-report.md). His word:

> *"Lets backlog those items. More features that I need to have added:
> 1) I want to have the ability to place annotations (text) on the
> drawing, 2) ability to draw a dimension measurement that can snap to
> an item. The measure should be a single thin solid line with slash
> marks "/" at the point of the callouts. The measurements should be
> selectable as feet and inches or in inches. Measures will always be
> parellel to the item being measured. I may want a datum that is used
> for one end of the dimentioning tool, 3) The ability to show the items
> (the callouts of each wall, vitext, etc.) on the plan in a settable
> color (dfault = blue). 4) These features should be menu items that are
> checkable from the "show" menu and should allow a) annotations, b)
> measurements, c) items to be independentaly checked. When they are
> checked the will be shown."*

**The backlog first:** 0248's items 8 (the porch's steps and stone base)
and 9 (a porch roof turning a house corner) are on the snapshot's
"named, not ordered" line as his backlog, not ordered.

Built on `annotations-measure`, ONE commit on `main`'s tip, pushed, PR
open. The checkout is on it.

## 0. WHAT IS BUILT

A new module, `floorplanner/annotations.py`, holds the three items; the
tools, the menu, the settings and the document round trip are wired
through the places that already own them.

**1. Annotations.** The **T** tool (toolbar, "Annotation"): click where
the text goes, type it in the dialog. A text is an item on its level:
drag to move, double-click to edit, Delete removes it, ghosted and hidden
with its level like a wall.

**2. Measurements.** The **L** tool ("Measure"): press on the first
point, drag to the second, release. Each end SNAPS TO AN ITEM within one
grid step: the level's datum first, then a corner (a wall end), an
opening's jamb, a wall's centreline (on the grid along it), else the grid.
Both ends on one wall and the measure runs along that wall — parallel to
what it measures, whatever the cursor's wobble across it. Drawn as ONE
thin solid line parallel to the measured segment, 18″ off it, a "/" slash
at each callout point, thin extension lines from the measured points,
the length written above the line, parallel to it, never upside down. The
units are the plan's: *Show ▸ Measurements in feet and inches*
(checked) or inches. Drag a finished measure and it slides along its own
normal, so it stays parallel while it moves off the wall. **The datum:**
*Show ▸ Place datum*, then a click: the level's datum point, a crossed
circle, one per level (placing another moves it); the Measure tool snaps
to it, so a run of measures can share one end.

**3. Item callouts.** The *Show ▸ Item callouts* layer draws every wall's
length and, when it has one, its name, and every named corner's name,
in the callout colour — *Show ▸ Item callout colour…* (also in File ▸
Settings), **default blue**, saved with the plan. The openings' size
codes, part of their symbol, draw as they always did and take the
callout ink while the layer is on. The layer is OFF until asked: a
dimensioned plan is a choice, and every existing plan reads as it did
(measured: switching it on by default broke a pixel test's bare wall,
which is exactly the change a user would see).

**4. The Show menu.** New, between View and Rooms: *Annotations*,
*Measurements*, *Item callouts* — three checkable switches, each its own
(a switch hides its kind whatever the level says; the level's own
visibility is applied first). Then the units switch, the colour, the
datum. All five are plan settings (`show_annotations`, `show_dimensions`,
`show_callouts`, `callout_color`, `dimension_units`), written in the
file's `settings` block and read back; the menu's checks follow a load.
A switch that hides the kind the active tool makes hands the tool back
to Select.

## 1. THE DOCUMENT

The schema's `annotations` block had no writer and no reader; it has
both now. `kind` gains `datum`; a `dimension` carries `p2` and
`offset_in`; `leader` stays reserved. The settings block names the five
keys. Additive optional: no version bump. `DEFAULT_SETTINGS` gains the
five, so `SETTINGS_VERSION` is 3 with its migration row (a v2
app-settings file gains them at their defaults on the next read; the
fingerprint pin moved with it). Undo, save and load go through the
bridge, so the items ride the same path as everything else. Not
exported to DXF or PDF — named, not built.

## 2. TESTS

`tests/test_annotations.py` (10): the three kinds round-trip through the
document and validate; the units; the dimension line's side and offset;
the Annotation tool places a text and Delete removes it; the Measure tool
snaps both ends to corners, leaves nothing on a press-release, and runs
along one wall when both ends are on it; the datum is one per level and
a measure snaps to it; the three switches hide each kind independently
and ride in the document; the units switch and the colour are plan
settings, a malformed colour falls back; a wall paints its callout in
the colour only while the layer is on. `test_config.py`'s version pin
and a v2→v3 migration test. `--quick` 1605 passed; the full gate GREEN.

## 3. TIER

**AMBER** — two new tools, a new menu, a new layer. For his check: place
a text; measure a wall end to end, a corner to the datum, and across a
room; switch the units; switch each layer; set the callout colour; save,
reload, undo.

## 4. `fixtures/incoming/`, with ages

Unchanged from [`0262`](0262-report.md), plus his rename of the dormer
file to `wiscaway2026-10-11R3.json`.

## 5. WHAT HAPPENS NEXT

His check of the PR. Named: DXF/PDF export of annotations; a leader
annotation (text with an arrow); 0248's items 8 and 9 on the backlog.

**Carried:** unchanged from [`0262`](0262-report.md).
