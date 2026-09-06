# 0157 — report: R4b — the roof parameters dialog: overhang, hip ends, eaves bound to the room top

**Code, 2026‑09‑06, answering [`0154-ruling.md`](0154-ruling.md) §3's R4b row,
the tranche after R4a ([`0155`](0155-report.md)/[`0156-report.md`](0156-report.md),
closed and merged).**

---

## 1. WHAT'S BUILT

**One dialog, still.** `RoofEndOnDialog` (`floorplanner/dialogs.py`) is
now the parameters dialog — the same class, the same three doors
([`0140`](0140-ruling.md) §1's marker right-click / double-click, the ridge's
own context menu, now labelled *"Roof parameters…"*, and the ridge-sketch
tool's initial prompt). The three-way ridge/eaves/pitch recompute is
unchanged and every R2b test still passes against it. Added, per
[`0154`](0154-ruling.md) §3's own list:

* **Per-side overhang (requirement 1).** Two fields, left and right, plus a
  *"same overhang both sides"* link that opens ON whenever the two currently
  agree — which every sketched roof does — and mirrors an edit to the other
  side while it stays on. Untick it and the sides diverge. The End-On
  drawing draws BOTH sides from their own span and overhang now
  ([`0154`](0154-ruling.md) §2: *"the End‑On drawing shows both slopes when
  they differ"*), continues each slope past its wall line to the overhang
  tip, and labels the right side's pitch `P'` whenever the spans differ
  (nothing before R4c can make them differ; the display is ready for it).
* **Gable ↔ hip, per end.** Two combos. **The ends are named by the
  marker** — *"End with the marker"* / *"Other end"* — because the marker is
  the one physical way a user tells the two ridge ends apart on screen; the
  mapping to `gable[0]`/`gable[1]` goes through `marker_end` at open time.
  The combos open showing the stored flags.
* **The `room_top` binding (requirement 5).** A checkbox. While ticked the
  eaves field is **locked and derived** from the covered rooms' ceilings, so
  the three-way rule runs between ridge and pitch alone — the binding is an
  input that can never be the derived field (`_derived()` skips it). The
  measurement's own note — which rooms, whether they differ, whether nothing
  was found — sits live under the toggle, and the same line goes to the
  status bar on apply. A hip toggle re-measures it live, since a hip end
  extends the footprint and can bring a room into it.

**What the binding reads — `roofs.bound_eaves_height(scene, roof)`.** The
HIGHEST `ceiling_height_in` among rooms on the roof's own floor whose
outline overlaps the roof's **eaves-start footprint** (`eaves_start_polygon`:
the span, not the overhang — a room only under the overhang is not a room
the roof sits on; a sliver under 1″ on either axis is a shared wall face,
not coverage). Same datum as every roof height ([`0140`](0140-ruling.md)
§3, the level's base), so a room's top IS its ceiling height. Rooms of
differing heights: **the highest governs and the mismatch is reported**,
[`0154`](0154-ruling.md) §2's stated default, in the returned
`RoomTopBinding` record — `differs()`, `note()`, `status_line()` — one note
the dialog label and the status bar both use. No room at all: the default
ceiling, flagged as a fallback and said so in the note, not silently.

**"Change the room height, watch the roof follow" — one call at the edit.**
`roofs.sync_bound_roofs(scene, floor)` re-derives every `room_top` roof on
the floor and rebuilds it; `RoomItem`'s own Properties door
(`rooms.py`, the context menu) calls it after `RoomPropertiesDialog.apply()`
and puts the binding's line on the status bar. The derived number is
**written to `eaves_h_in`** on save exactly as ruled — the document stays
self-contained; `fp3d`, the exports and the loader never re-derive. **Load
never re-syncs** — the saved value is what the binding last produced; only
an edit (the dialog, or a room's height) does. A boundary named, not
silently crossed: a room *deleted* or *redrawn* under a bound roof does not
re-sync until the next dialog visit or room-height edit.

**A hip end now has geometry — it was a flag with no consequence.** Before
this tranche `gable[i] = False` drew no end line in 2D and left the 3D mesh
open with an INFO note ("not modelled until R4"). A dialog toggle that
changed nothing visible would have been a vacuity, so R4b gives it its
geometry, derived from what the document already stores:

* **`RoofItem.hip_extension(end)`** = `(run, overhang)` past that ridge end:
  the run is the **mean of the two spans** (the span itself on every
  symmetric roof, so all four faces share one pitch — the regular hip), the
  overhang the mean of the two overhangs. **Nothing new is stored**: `gable`
  is the whole document fact; the run is derived, the same discipline as
  pitch. The ridge stays where it was sketched.
* **2D:** the eave lines run past the end, an end eave line closes them, two
  hip lines run from the ridge end to its corners; `shape()` covers all of
  it (D85's rule, extended — a hip line's midpoint is selectable, and the
  same point beside a gable roof is empty air, tested as a pair).
* **3D (`fp3d.py`):** the hip face is the same apex-to-two-corners triangle a
  gable end already is, just tilted instead of vertical; each side plane
  becomes a trapezoid, still planar because the extended corner keeps its
  side's own perp offset and height. R3's placeholder test becomes the
  hip-face test plus a gable control.
* **R3b's clip line (`roof_clip_spans`):** the surface past a hip end is the
  LOWER of the side plane and the hip plane; the hip plane's drop is affine
  in `along` exactly as a side's is in `perp`, so it adds roots (the
  footprint end, the hip threshold) — still exact interval arithmetic, no
  sampling. A wall running out past the ridge end under the eaves line,
  which a gable roof does not reach at all, is clipped by a hip roof between
  two closed-form boundaries; the gable-end-wall case is unchanged by the
  hip code path (tested as the control).

`design-schema.v5.json`: `gable`'s and `eaves_bind`'s descriptions now say
what R4b made them mean. **No shape change, no version bump** — every R4a
document is byte-for-byte valid under the same schema.

## 2. THE CHECK — gate GREEN, stopped for Patrick's own

`tests/test_roof_params.py`, **29 new tests**: the hip footprint and its
gable control, the run rule, the eaves-start polygon and its preview
override, shape coverage of a hip line; the binding's no-room fallback
(with and without a scene), a single room, a room OUTSIDE the footprint
(the control — a taller room the roof does not cover must not govern),
another floor, highest-governs with the mismatch reported, and a hip end
changing which rooms are read; `sync_bound_roofs` moving only the bound
roof and only on its floor; the dialog's overhang link both ways, the
end-combo mapping through the marker end (both marker positions), the
binding locking / seeding / derived rule / unbinding / hip re-measure /
no-room label, both pitches on the drawing; a full document round trip
(schema-valid) of hip flags + per-side overhang + `eaves_bind` with
`eaves_h_in` written; the hip clip line in closed form with its gable
control; and **Patrick's own check end to end** — a room's ceiling edited
through the room's Properties door, the bound roof follows to 120″, and
the UNBOUND roof beside it does not (the control that proves the binding
moved it, not a coincidence of defaults). Plus the two rewritten `fp3d`
tests and the menu-label follow in `test_roof_end_on.py`.

Full suite **1191 passed**, 7 deselected (`perf` lane), collected 1198.
`ruff` clean. `python tools/gate.py` (full mode): **GREEN**.

The dialog and the hip-end plan overlay were both rendered offscreen and
looked at (ridge, both slopes to their overhang tips, the wall stack, the
bound wall-top reference at the rooms' height; in plan, the extended
footprint with its two hip lines at one end and the gable line at the
other).

## 3. DISPOSITION — AMBER, PR open, waiting

**R4b is AMBER** ([`0154`](0154-ruling.md) §3's row): built, gated, PR up on
branch `roofs-r4b-parameters`, **not merged until Patrick's own check** —
his words, the row's own cell: *set an overhang, bind eaves to room top,
change the room height, watch the roof follow.* Two things worth his eye
that the ruling did not specify and this report decided:

1. **The hip run is the mean of the two spans** (§1 above). For every roof
   the app can currently make (symmetric spans) that is simply the span,
   the regular hip. If he wants a settable hip run, it is a new field —
   named here, not built.
2. **The two ridge ends are named by the marker** in the dialog. If he
   would rather see them by compass direction or by coordinate, that is a
   label change, nothing structural.

**R4c stays next** (five grips: two eave edges, two gable ends, the ridge —
AMBER, its own PR after this one lands), then R5 (dormers, RED, own
ruling). Nothing in R4b pre-empts R4c: the per-side fields the grips will
drag already exist (R4a), and the dialog now shows them.

**Carried, unchanged:** D83/D84 (held); room-label rounding
([`0131`](0131-ruling.md) §2); delta-snap sites; D61-family; yard items.
