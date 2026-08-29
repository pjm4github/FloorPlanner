# 0120 — ruling: Patrick's room-driven scheme replaces [`0119`](0119-ruling.md) §2's wall classifier — and it is measured to be document-backed

**Patrick's amendment:** cycle the rooms whose **Show dimensions** is on;
classify their angled edges into a "45° callout" family; project those rooms'
dimensions **onto a 45° lane outside the drawing**.

**Adopted, and it wins on three grounds. [`0119`](0119-ruling.md) §2's
per-run-string placement is superseded; everything else there stands.**

---

## 1. WHY HIS SCHEME IS BETTER — and the one fact that makes it legal

* **`show_dims` is persisted** — `label.show_dimensions`, schema line 287,
  round-tripped at `bridge.py:722/1239`. **The export depends only on the
  document**; had it been view-only state, this ruling would have refused it.
* **It is per-room OPT-IN.** The user chooses which rooms carry angled
  callouts, with a toggle that already exists — no threshold argument, no
  drift-vs-deliberate inference. The drifted-wall exclusion
  [`0119`](0119-ruling.md) §2 needed a boundary for **falls out for free**: a
  drifted wall is not an edge of a show-dims room at an intended angle.
* **The LANE mirrors the sheet's existing architecture.** The bottom X row
  already projects every vertical wall onto one line regardless of its y — his
  45° lane is the same convention rotated, not a new idea to get wrong.

## 2. THE MECHANICS, RULED

1. **Cycle rooms with `show_dimensions = true`.** For each outline edge:
   near-cardinal (≤ 1° — the census boundary) → already covered by the X/Y
   rows; otherwise → **its angle family** (angle mod 180°, clustered).
2. **One lane per family** — 45° and 135° are distinct lanes, exactly as X and
   Y are — drawn **outside the drawing extents**, offset `DIM_LANE` beyond the
   plan bbox on the corner facing the family, extension lines running back to
   the geometry like the orthogonal rows' do.
3. **Stations:** the family's edge endpoints **plus opening centrelines on
   those walls** ([`0119`](0119-ruling.md) §1's measured gap — still this
   tranche's second deliverable), projected onto the lane axis, then
   **clustered and whole-inch telescoped per [`0118`](0118-ruling.md) §2.**
4. **[`0119`](0119-ruling.md) §3's `dim_row_along` refactor stands** — the lane
   is one more call with a rotated unit. Text never upside-down.

**One consequence stated so it is not filed as a bug:** all of a family's rooms
project onto **one shared lane**, so stations from different 45° rooms
interleave there — **the same behaviour the bottom row already exhibits for
every vertical wall in the plan**, and the reason lanes stay legible is
[`0118`](0118-ruling.md)'s clustering, not per-room separation.

## 3. SCOPE EDGE — walls in no show-dims room

A 45° wall belonging to no room, or to a room with dimensions off, **gets no
angled callout. That is the feature, not a gap** — the toggle is the control
surface. If a stray angled partition needs dimensioning, the answer on this
scheme is *put its room's dimensions on*, not a second classifier.

## 4. TIER AND ORDER — unchanged from [`0119`](0119-ruling.md) §4

[`0118`](0118-ruling.md) first (the station machinery), then the `dim_row_along`
refactor (GREEN), then this (AMBER, own branch). **Receipts:** a two-room 45°
family → one lane, stations telescoping to the family extent; a show-dims room
with a door in a 45° edge → the door station present (RED today); a 45° wall in
a dims-off room → absent.

**Patrick's check, one export:**

> **Turn Show dimensions ON for the 45° rooms on Wiscaway's right side, export.
> One 45° dimension lane sits outside the drawing with those rooms' walls and
> doors in it, readable; turn one room's dimensions OFF, re-export, and its
> edges leave the lane.**
