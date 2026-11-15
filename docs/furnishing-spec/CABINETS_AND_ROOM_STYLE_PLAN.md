# Parametric cabinets and a room style — plan

**Status:** PLAN, for Patrick's review. Nothing is built. Reviewer session, 2026-11-14.
**Builds on:** the parametric machinery of handoff 0323 (`floorplanner/parametric/`).
**Goal:** a kitchen or a bathroom that reads correctly in a camera elevation and
in the 3D view — doors, drawers, toe kicks, countertops, in the room's finishes.

## 1. Where the cabinets are today (read on disk)

| fact | consequence |
|---|---|
| 19 cabinet kinds, each a FIXED size: `base_cab_24/36`, `drawer_base_18`, `sink_base_36`, `corner_base_36`, `wall_cab_24/30/36`, `pantry_18/24/36`, `vanity`, `vanity_24/36/48`, `kitchen_island`, `island_sink` | a 27 in or 33 in cabinet cannot be placed at all |
| In 3D every one is a plain wood box, 12 triangles | no door, drawer, toe kick or countertop |
| In a camera elevation each is a translucent to-scale rectangle with its name | a run of cabinets is a row of labelled boxes |
| A base cabinet is 36 in high in the catalog — the countertop height, with no countertop | the top and the box are one block |
| A wall cabinet's height off the floor is a catalog constant, 54 in | it cannot be moved per cabinet |
| Cabinetry is told from furniture by id prefix (`catalog._CASEWORK_PREFIX`) | new kinds must keep the prefixes |
| A room has free `properties` (`room_type`, `floor_finish`, `wall_finish`, ...); the schema's `room_properties` allows extra keys | a room style fits without breaking any existing file |
| A furnishing's `state` is open, round-trips, and already carries stair parameters | cabinet parameters have a home |

## 2. Dimensions the industry already agrees on

These become the DEFAULTS and the choices offered, not hard limits.

| | standard | source |
|---|---|---|
| Base cabinet box | 34.5 in high (30 in box + 4.5 in toe kick), 24 in deep | Kitchen Cabinet Kings; Houlte |
| Toe kick | 4.5 in high, 3 in deep (3.5-4.5 seen) | Houlte; House Plans Helper |
| Countertop | 1.5 in thick, giving 36 in finished | Houlte; Coohom |
| Widths | 9 to 42 in, in 3 in steps | Coohom; QuikCabinets |
| Wall cabinet | 12 in deep; 30, 36 or 42 in high; 18 in above the counter (underside 54 in) | QuikCabinets; Kitchen Cabinet Kings |
| Over-fridge / bridge wall cabinet | 12-24 in high, 12 or 24 in deep | QuikCabinets |
| Tall / pantry | 84, 90 or 96 in high; 12 or 24 in deep | Kitchen Cabinet Kings |
| Vanity | 21 in deep, 34.5 in high | QuikCabinets |
| Sink base | 30, 33, 36 in (24-42 made); a false drawer front, open inside | QuikCabinets; MFS spec book |
| Corner | blind corner 24 in deep; lazy-Susan 33 or 36 in; diagonal sink 36-42 in; corner wall 24-27 in | QuikCabinets; Kitchen Cabinet Kings |
| Top drawer / door split | 6 in drawer over a 24 in door | Kitchen Cabinet Kings |
| Face frame | 1.5 in stiles and rails, 0.75 in thick | KCD / Rugby catalog; MFS |
| Five-piece door | 2.25-2.75 in stiles and rails, 0.75 in thick | Shenandoah spec guide; KCD |
| Overlay | full (door covers the frame) or partial (about 1 in of frame showing); or frameless | Shenandoah; Chadwell |
| Trade codes | `B24`, `SB36`, `W3030` (width, then height), `W3618-24` | QuikCabinets; KCD |

CAD libraries parametrise the same things: Microvellum's face-frame library
lists width / height / depth / toe-kick height, left and right end conditions,
fillers, overlay and gap, a top-drawer option, and stile and rail widths.

## 3. Design

### 3.1 Five parametric kinds, and the old kinds as presets

| kind | what it is | parameters beyond the common set |
|---|---|---|
| `base_cabinet` | doors, drawers, or both | front layout: doors / drawer-over-door / all drawers (2-4) |
| `sink_base` | false front over doors | sink: none / single / double bowl; the bowl is cut into the top |
| `corner_base` | an L in plan | type: blind / lazy-Susan / diagonal; the two leg lengths; which side is blind |
| `wall_cabinet` | hung on the wall | **height from the floor** (default 54); height 12-42; depth 12 or 24 |
| `tall_cabinet` | pantry / utility | height 84 / 90 / 96; door split |

**Common set:** width, depth, height, toe-kick height and depth, number of
doors, hinge side (single door), door style, overlay, pulls, finished ends
(left / right), and a **countertop** block: on/off, thickness, front overhang,
side overhangs, backsplash height.

The 19 existing kinds stay in the palette as PRESETS — `base_cab_36` is a
`base_cabinet` born 36 wide. Their ids do not change, so no saved plan needs
converting, and `_CASEWORK_PREFIX` keeps working. A vanity is a `sink_base`
preset at 21 deep; an island is a later kind (§7).

### 3.2 Doors are a parameter, not a furnishing

"Cabinet doors" are edited inside each cabinet's dialog: count, style
(slab, shaker / recessed panel, raised panel, glass), overlay, hinge side,
pull type. A door is not placed on the plan on its own — it has no footprint.

### 3.3 The room style

A new object in the room's `properties`, edited in the Room Properties dialog:

```json
"style": {
  "cabinet_finish": "maple",
  "door_style": "shaker",
  "countertop": "quartz",
  "hardware": "brushed_nickel",
  "backsplash": "tile"
}
```

- `cabinet_finish`: modern white, maple, cherry, oak, walnut, painted grey,
  painted navy, espresso — an extensible list, each a material.
- `countertop`: marble, tile, quartz, granite, soapstone, laminate, butcher
  block, concrete, stainless — likewise.
- Offered for every room; it MEANS something in kitchens and baths today, and
  is where other furnishings can look later (a sofa's fabric, a bed's frame).

**Resolution, one rule:** a cabinet's own value, else its room's style, else the
application default. A cabinet stores a finish only when the user overrides it
— so restyling a room restyles every cabinet in it that was not overridden.
The room is the furnishing's owning `room`, which the plan file already records.

### 3.4 The plan file

```json
{ "id": "f12", "level": "L1", "kind": "base_cab_36", "room": "r4",
  "pos": [120.0, 12.0], "rotation": 0,
  "state": { "width_in": 33.0, "front": "drawer_over_doors", "doors": 2,
             "countertop": { "on": true, "overhang_front_in": 1.0 } } }
```

Only what differs from the kind's defaults need be written. A cabinet with no
`state` is the preset at its catalog size.

### 3.5 One calculator, three pictures

`floorplanner/parametric/cabinet_geometry.py`, plain Python like
`stair_geometry.py`, returns the cabinet as named PARTS — carcass, toe kick,
face frame, each door, each drawer front, pulls, countertop, backsplash, sink
bowl — each with a box and a material ROLE (`cabinet`, `countertop`,
`hardware`, `sink`). From that one list:

- **3D:** each part a box in its resolved material (`fp3d.py`, loaded by path).
- **Camera elevation:** the front-facing parts drawn as real lines — door and
  drawer outlines, toe kick, counter edge, pulls — in place of the labelled
  rectangle.
- **Plan symbol:** footprint, counter-nosing line, door ticks, at the true
  width.

### 3.6 The dialog

The generic `ParametricDialog` of 0323, unchanged. Its preview pane shows a
front elevation and a plan inset of the one cabinet, redrawn on every edit.
Validation is light — there is no code to satisfy — and advisory: a door wider
than 24 in, a wall cabinet whose underside is under 15 in above a counter, a
sink bowl wider than its base, a width off the 3 in module.

## 4. The schema

| change | where | effect on old files and old builds |
|---|---|---|
| `room_properties.style` declared, with its five keys | `design-schema.v6.json` | none — the object already allows extra keys; this documents and type-checks it |
| the cabinet and stair `state` keys declared as `$defs` and described | same | none if descriptive; see D5 |
| new materials: finishes, countertops, hardware | `materials.json` (generated) | none |
| `docs/design-schema.v6.md` updated | docs | — |

No version bump is needed for any of it.

## 5. Phases

| # | what | tier | needs |
|---|---|---|---|
| 1 | `cabinet_geometry.py` + unit tests; materials | GREEN | lane only |
| 2 | room `style`: schema, `DEFAULT_ROOM_PROPS`, Room Properties dialog, round trip | AMBER | `config.py`, `dialogs.py`, schema |
| 3 | cabinet kinds registered; item footprint from parameters; dialog + preview | AMBER | `items.py`, `_gen_assets.py`, `catalog.py` |
| 4 | 3D parts in room materials | AMBER | `fp3d.py` (furnishing region) |
| 5 | camera elevation draws the fronts | AMBER | **`cameras.py`, `dialogs.py`** — after camera Phase 2 lands |
| 6 | docs, gallery | GREEN | Code |

## 6. Decisions for Patrick

**D1. Existing cabinets in saved plans.** Unlike the stairs, the new look does
not change a preset's size. *Recommended:* existing cabinets take the new
appearance automatically (doors, toe kick, top), at exactly their catalog
footprint — nothing moves. Alternative: frozen as boxes until edited.

**D2. The countertop.** *Recommended:* each base cabinet carries its own top;
adjacent tops abut and read as one run, with a seam at each joint.
Alternative: a separate "countertop run" furnishing drawn over several
cabinets — seamless and able to bridge a dishwasher, but a new item to place
and keep aligned. (The dishwasher and range gaps are the real argument for it;
it could be a later phase.)

**D3. Base height.** Today a base cabinet is 36 in. *Recommended:* 34.5 in box
plus a 1.5 in top = 36 in, so nothing changes height in existing plans.

**D4. Where the style lives.** *Recommended:* `properties.style` on the room,
as §3.3. Alternative: flat keys (`cabinet_finish`, `countertop`) beside
`floor_finish` — simpler, but they multiply as furnishings learn to read them.

**D5. How strict the schema is about `state`.** *Recommended:* declare and
describe the keys, validate them in the application (as the stair dialog
does), and leave `state` open in JSON Schema. A strict per-kind schema would
reject a file from a newer build that added one parameter.

**D6. Appliances.** The range, dishwasher and refrigerator stay as they are in
this work; they are the next realism pass. Say if you want the dishwasher
panel-matched to the room style now.

**D7. The lane widens** to `config.py` (room defaults and the finish lists),
`dialogs.py` (Room Properties, and the wall elevation in phase 5),
`cameras.py` (phase 5 only), `catalog.py`, and the JSON schema.

## 7. Deferred

Islands as a parametric kind; countertop runs (D2); crown and light-rail
moulding; fillers and end panels as separate pieces; appliance panels;
interior shelves; a cut list or cabinet schedule with trade codes (`B33`,
`W3030`) — cheap once the parameters exist, and worth doing next.

## Sources

- [Standard Kitchen Cabinet Sizes and Dimensions Guide — Kitchen Cabinet Kings](https://kitchencabinetkings.com/kitchen-cabinet-sizes)
- [Kitchen Cabinet Sizes: Complete Guide to Standard Dimensions — QuikCabinets](https://quikcabinets.com/blogs/kitchen-remodeling-guides/kitchen-cabinet-sizes-standard-dimensions-guide)
- [Kitchen Cabinet Types & Sizes — QuikCabinets](https://quikcabinets.com/blogs/kitchen-remodeling-guides/cabinet-types-sizes-guide)
- [How Tall Are Standard Kitchen Cabinets — Houlte](https://houlte.com/blogs/news/how-tall-are-standard-kitchen-cabinets-dimensions-guide)
- [Kitchen Cabinet Dimensions — House Plans Helper](https://houseplanshelper.com/kitchen-cabinet-dimensions.html)
- [Standard Kitchen Cabinet Sizes Chart — Coohom](https://www.coohom.com/article/standard-kitchen-cabinet-sizes-chart-pdf-quick-reference)
- [Shenandoah Cabinetry digital spec guide](https://shenandoahcabinetry.com/content/dam/shenandoah-site/en/for-the-pros/guides/287%20LW%20PE%20Digital%20Spec%20Guide_2024.pdf)
- [Rugby / KCD product catalog](https://res.cloudinary.com/hdi/image/upload/v1652903946/Suppliers/Kitchen_Cabinet_Distributors/Documents/Brochures/Rugby_KCD_Product_Catalog_MPNW.pdf)
- [MFS Supply cabinetry spec book](https://www.mfssupply.com/web-assets/downloads/MFS%20Supply%20-%20Cabinetry%20Spec%20Book%20-%20v2025.2.pdf)
- [Chadwell Supply cabinet selection and styles](https://www.chadwellsupply.com/globalassets/service-images/cabinets/cabinetselectionandstyles.pdf)
- [Microvellum face-frame expansion overview](https://intercom.help/microvellum-knowledge-base/en/articles/13919573-face-frame-expansion-overview)

## 8. Decisions — Patrick, 2026-11-14 (supersedes §6 where they differ)

| # | decision |
|---|---|
| D1 | Existing cabinets take the new look automatically, at their catalog footprint. |
| D2 | Each base cabinet carries its own countertop. |
| D3 | 34.5 in box + 1.5 in top. |
| D4 | The style is one `style` object in the room's properties. |
| D5 | The keys are declared in the schema; the application validates. |
| D6 | **Added:** an appliance MATCH feature, and special finishes — matte, gloss, gel coat — in a colour. |
| D7 | The lane extends to the Room Properties dialog. |

Built as decided, phases 1-4: `docs/handoff/0329-ruling.md`. Phase 5 (the
camera elevation drawing the fronts) waits for camera Phase 2.
