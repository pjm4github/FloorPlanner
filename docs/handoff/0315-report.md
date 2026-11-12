# 0315 — report: the plan CAMERA now SHOWS the furnishings and/or the cabinetry it faces, as to-scale silhouettes — on branch `camera-content`

**Code, 2026‑11‑11.** The record ([`0197-ruling.md`](0197-ruling.md) §7). The
third increment of the plan-cameras feature ([`0313`](0313-report.md),
[`0314`](0314-report.md)), on his order after the room elevation landed. His
order 2026‑11‑11: *"Now I want to add the ability to show the furnishings and/or
the cabinetry. These should all be checkable switches that are set by
right‑clicking on the camera icon on the plan. When each mode is selected then
the icon should change its shape so the user can see what will be shown."* Two
blocking choices he settled by question: **cabinetry = casework, the rest
furnishings** (disjoint sets), and the content drawn as **to‑scale silhouettes
on the wall**. Built on branch `camera-content`; **his word: "land it and
merge"** — report on `main`, the one branch commit, then merged.

## 1. WHAT HE ORDERED

The camera already elevations the room wall it faces. He wants to switch ON, per
camera, the things standing against that wall — the **furnishings** and/or the
**cabinetry** — as two checkable switches reached by RIGHT‑CLICKING the camera
glyph, and he wants the GLYPH ITSELF to change shape so he can see at a glance
what a camera will show. The split he chose: **cabinetry is the casework** (base
and wall cabinets, vanities, islands, …), **furnishings is everything else**, the
two disjoint; the content drawn **to scale on the wall**, at each item's real
width and mounting height.

## 2. WHAT IT DOES

- **Two per‑camera switches** (`CameraItem.contextMenuEvent`). Right‑click the
  camera ▸ **Show furnishings** / **Show cabinetry**, each a checkable toggle
  reflecting the camera's own state; `set_show_furnishings` /
  `set_show_cabinetry` flip the flag, `prepareGeometryChange` + `update()` so the
  glyph and any open elevation follow. The flags default OFF.
- **The glyph changes shape** (`CameraItem.paint`, `_badges`). Each active switch
  grows a small BADGE in a row under the camera body — an **armchair** pictogram
  for furnishings (teal), a **cabinet** pictogram for cabinetry (wood) — so a
  glance at the plan says what the camera shows. The badges are drawn
  **counter‑rotated** (`painter.rotate(-self.rotation())`) so they stay upright
  at any camera aim; `boundingRect` opens to a disc that covers them.
- **The content split** (`catalog.is_casework`). Casework is classified by
  manifest id — the prefixes `base_cab`, `wall_cab`, `drawer_base`, `sink_base`,
  `corner_base`, `pantry`, `vanity` plus the exact `kitchen_island` /
  `island_sink` (17 catalog items); furnishings is every other catalogue item,
  the two disjoint. `furnishing_spec` now also surfaces each item's `height_in`
  and `elevation_in` (mounting height off the floor; a wall cabinet at 54″),
  which were in all 96 manifest entries but never exposed.
- **Against the wall, to scale** (`CameraItem._items_against`). With a switch on,
  the elevation scans the floor's `FurnishingItem`s, keeps those of the right
  class, and projects each one's (possibly rotated) footprint onto the faced
  wall: its along‑wall span becomes the silhouette's run, its perpendicular
  clearance decides whether it stands **against** this wall (within 12″, on the
  camera's side). Each kept item comes back with its run `x0..x1` and its
  vertical band `sill..head` = `elevation_in .. elevation_in + height_in`.
- **Drawn in the elevation** (`dialogs._WallElevationCanvas`). Each item is a
  **translucent to‑scale box** at its real width and mounting height (clamped to
  the ceiling), outlined in its class ink — **cabinetry wood, furnishings teal** —
  named where it fits. A base cabinet sits on the floor, a wall cabinet rides at
  54″, a sofa on the floor. The dialog's note appends "Against the wall: N
  furnishing(s), M cabinet(s)." when a switch is on.
- **Saved with the plan.** `CameraItem.to_record` writes `show_furnishings` /
  `show_cabinetry` only when true; `from_record` reads them. The v6 schema's
  camera object gains both (boolean, default false); `design/model.Camera` gains
  the two fields. The optional‑when‑default rule keeps a plain camera's record
  unchanged.

## 3. RECEIPTS (instrument `docs/evidence/0315-camera-content/render.py`)

The receipt builds a kitchen room whose far wall is two coplanar segments split
by a doorway, stands a **base cabinet** and a **wall cabinet** against it and a
**sofa** on the other wall, turns both switches on, and renders.
`camera_content_elevation.png` draws the base cabinet on the floor and the wall
cabinet at its 54″ mounting height, both in wood, with the sofa in teal — each a
translucent to‑scale box over the elevation. `camera_glyphs.png` is the plan
glyph in its three states side by side — plain, +furnishings, +both — showing the
badges that grow on the icon. The elevation print confirms the projection: the
base cabinet `y[0..36]`, the wall cabinet `y[54..84]`, the sofa `casework=False`.
(Offscreen text renders as tofu; the shapes and bands are what the receipt
asserts, and the labels draw on the real display.)

## 4. TESTS

`tests/test_cameras.py` (21, up from 13): the split (`is_casework` divides
cabinets from furniture); the toggles off show nothing; the cabinetry toggle
shows only casework; the furnishings toggle shows only free‑standing; a wall
cabinet sits at its mounting height; an item away from the wall is not shown; the
two switches round‑trip through save/load; the glyph grows a badge per active
switch. Gate: full, GREEN (2118 collected, 2111 passed OFF and ON, ruff clean).

## 5. NEXT

**His word was "land it and merge"** — this increment lands. Still named, not
ordered: a per‑item depth cue (nearer items drawn over farther); a legend or
count by room; more per‑camera actions (save a named view, open in 3D, a
section). The next ordered work is the **annotation‑number persistence + a find
tool** he asked for in the same message — a separate increment.
