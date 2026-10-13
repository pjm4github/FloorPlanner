# FloorPlanner — every command, with an example

Written 2026‑10‑12 against `main` (schema v6, [`0271-report.md`](handoff/0271-report.md)).
One place for "how do I …": the tools and keys, every menu and context menu,
the dialogs, both macro languages with their application commands, and every
command-line program. Positions everywhere are **scene inches** (1 unit = 1″;
`10'6"` is also accepted where a macro takes a number). Right-click menus are
written *right-click ▸ Item*; the menu bar *Menu ▸ Item*.

Contents: [Run it](#1-run-it) · [Tools](#2-the-tools-toolbar-and-keys) ·
[Keyboard](#3-keyboard) · [Menus](#4-the-menu-bar) · [Context menus](#5-the-context-menus) ·
[Dialogs](#6-the-dialogs) · [Macro language](#7-the-macro-language) ·
[Macro language v2](#8-macro-language-v2) · [Application commands](#9-application-commands) ·
[Command-line programs](#10-command-line-programs) · [Developer commands](#11-developer-commands)

---

## 1. Run it

| Command | What it does | Example |
|---|---|---|
| `python FloorPlanner.py` | Start the editor. | `python FloorPlanner.py` |
| `floorplanner` | The same, as the installed console script. | `pip install -e . && floorplanner` |
| `python FloorPlanner.py --verify-design` | Start with **shadow verification** on: every settle checks the live scene against the document invariants (also `FP_VERIFY_DESIGN=1`). | `python FloorPlanner.py --verify-design` |

Plans open and save by default in `Documents/FloorPlanner`; the app's own
settings file lives in the per-user config directory (**Help ▸ About** shows
both).

---

## 2. The tools (toolbar and keys)

Pick a tool from the toolbar or by its key. The tool stays until another is
picked (the Room and Datum tools hand back to Select after one use).

| Key | Tool | How to use it | Example |
|---|---|---|---|
| **S** | Select | Click an item; drag to move; drag an end-knob to stretch; **Ctrl**-drag a rubber band to add what it encloses; **Ctrl**-click toggles one item. | Press `S`, drag a sofa into the den. |
| **E** | Exterior wall | Press where the wall starts, drag, release. The end lands on the snap grid; **Shift** = off the grid at any angle; **Esc** cancels. An end released on another wall welds a T or L; one released a grid step short is left as a reveal. | `E`, drag from the corner to 20′ right. |
| **I** | Interior wall | As Exterior, 4½″ thick. | `I`, drag across the house for a partition. |
| **D** | Door | Click a wall, type the **WWHH** size code and the leaf type. | `D`, click the hall wall, `3680 RH`. |
| **W** | Window | Click a wall, type the WWHH code; the sill height comes from the plan default (36″) and can be changed in its properties. | `W`, click the north wall, `4048`. |
| **R** | Room name | Click inside an enclosed area, type the name. One-shot; **Ctrl**-pick the tool to keep it. | `R`, click the big area, `Living Room`. |
| **G** | Roof ridge | Press on the eaves wall, drag the ridge, release, then click the eaves wall the roof spans over; the heights dialog opens (*Roof ▸ Sketch ridge*). | `G`, drag along the house, click the far wall, set eaves 96″ / ridge 150″. |
| **M** | Roof dormer | Press on a roof plane (snaps to the orange clip trace), drag along it for the width (**Shift** = free direction), release, set the heights. | `M`, drag 60″ along the front slope. |
| **T** | Annotation (text) | Click where the text goes, type it. Drag to move; double-click to edit. | `T`, click above the porch, `North elevation`. |
| **L** | Measure | Press on the first point, drag to the second. Each end snaps to the datum, a corner, an opening's jamb or a wall's centreline; both ends on one wall and the measure runs along it. Drag the measure to set it off the wall; select it for its four knobs (points 1 and 2 move and snap — **Ctrl** rotates about the other point, **Shift** frees; knob 3 slides the line's end; knob 4 slides the label). | `L`, drag corner to corner: `20'-0"`. |
| **N** | Leader | Press on the thing to name (snaps as a measure's end does), drag to where the text goes, release, type the text. An arrow at the point, the text on a short shoulder; drag the body to move it; select it for its two knobs; double-click to edit. A click without a drag puts the text 24″ up and right. | `N`, press on the post, drag away, `Relocate this post`. |
| — | Datum | *Show ▸ Place datum*, click: this level's datum point, which the Measure tool snaps to (one per level; placing again moves it). | *Show ▸ Place datum*, click the south-west corner. |
| — | Delete | The toolbar's bin, or **Del**: delete the selection. | Select a chair, `Del`. |
| **F** | Zoom fit | Fit the view to the walls. | `F` |
| — | Shuffle | **Ctrl+H**: nothing merges, welds or binds while on (join rooms explicitly with *right-click ▸ Join room into plan*). | `Ctrl+H`, drag rooms about, `Ctrl+H`. |
| — | Undo / Redo | **Ctrl+Z** / **Ctrl+Y** (or the ↺ ↻ buttons). | `Ctrl+Z` |
| — | Record macro | The ● button: the macro recorder window (see §7). | ● then **Start**. |

---

## 3. Keyboard

| Keys | Action | Example |
|---|---|---|
| **Arrows** | Nudge the selection one wall-snap step (6″ by default). | `→ → ↑` |
| **Ctrl + Arrows** | Fine nudge, 1″. | `Ctrl+→` |
| **Del** / **Backspace** | Delete the selection (a room's wall **fractures**: the room-edge stretch stays). | `Del` |
| **Esc** | Cancel the wall, ridge, dormer, measure or leader in progress; otherwise back to Select. | `Esc` |
| **Ctrl+N / Ctrl+O / Ctrl+S / Ctrl+Shift+S** | New plan / Open / Save / Save As. | `Ctrl+S` |
| **Ctrl+Z / Ctrl+Y** (or **Ctrl+Shift+Z**) | Undo / redo. | `Ctrl+Y` |
| **Ctrl+X / Ctrl+C / Ctrl+V** | Cut / copy / paste the selection (paste lands at the cursor). | `Ctrl+C`, move, `Ctrl+V` |
| **Ctrl+Shift+V** | Paste a copied **room** (walls and openings with it). | `Ctrl+Shift+V` |
| **Ctrl+G / Ctrl+Shift+G** | Group / ungroup the selection. | `Ctrl+G` |
| **Ctrl+A** | Select every editable item. | `Ctrl+A` |
| **Ctrl+H** | Toggle shuffle mode. | `Ctrl+H` |
| **Ctrl+F / Ctrl+Shift+F** | The floor selector (the default floor first, **Enter** picks it) / New floor. | `Ctrl+F`, `↓`, `Enter` |
| **Ctrl+PgDown / Ctrl+PgUp** | Next / previous floor. | `Ctrl+PgDown` |
| **Ctrl+3** | The 3D view of the current plan. | `Ctrl+3` |
| **Ctrl+Q** | Quit. | `Ctrl+Q` |
| **Mouse wheel** / **middle-drag** / drag empty space | Zoom / pan. | wheel over the kitchen |
| **Shift** while drawing or dragging an end | Unconstrained: off the grid, any angle. | hold `Shift`, drag |
| **Ctrl** while dragging a wall end | Snap to 15° increments about the anchored end. | hold `Ctrl`, drag |
| **Ctrl** while rotating a furnishing or group | Snap to the rotation increment. | hold `Ctrl`, drag the handle |

---

## 4. The menu bar

### File

| Item | Action | Example |
|---|---|---|
| New plan | Clear the plan (Ctrl+N). | *File ▸ New plan* |
| Open… | Open a plan `.json` (Ctrl+O). A v1–v4 `floorplanner-json` file is **converted** on open and reported; a v5 or v6 design opens as it is. | *File ▸ Open…*, `wiscaway.json` |
| Import rooms from CSV… | Rooms from `Name,Type,X_ft,Y_ft,X_loc_ft,Y_loc_ft,Notes`; unlocated rooms auto-place; the canvas grows to fit (to 500′). | `examples/simple_house.csv` |
| Import from image (PNG)… | Drop a raster plan on the canvas as a backdrop; calibrate, crop and extract walls from its context menu (§5). | `plan.png` |
| Save / Save As… | Write the plan (Ctrl+S / Ctrl+Shift+S) as a version‑6 design document. | *File ▸ Save As…*, `house.json` |
| Export ▸ Rooms as CSV… | The rooms as the CSV above. | `rooms.csv` |
| Export ▸ Chief Architect (DXF)… | One DXF R12 + `.openings.json` sidecar per storey level for Chief's **CAD to Walls** (see the README's workflow). | pick a folder |
| Export ▸ PDF plan set… | One 11×17 sheet per level: walls, openings, rooms, the plan's **drawn** measurements in place of the auto rows when it has any, its texts and leaders while shown; a title block. Options dialog, then a Save As. | `house.pdf` |
| Export ▸ Legacy v4… | The old `floorplanner-json` v4 file, for the one release that still reads it. | `house-v4.json` |
| Load template room… / Save template room… | A one-room document: save a **floated** room as a template; load one onto the canvas as a floating room. | *Save template room…* with the bath floated |
| Settings… | The plan's settings dialog (§6). | — |
| Quit | Ctrl+Q. | — |

### Edit

| Item | Action | Example |
|---|---|---|
| Undo / Redo | Ctrl+Z / Ctrl+Y. | — |
| Cut / Copy / Paste | The selection; paste lands at the cursor. | — |
| Paste room | Ctrl+Shift+V: a copied room with its walls and openings. | — |
| Group / Ungroup | Ctrl+G / Ctrl+Shift+G. | — |
| Coalesce all walls now | Merge overlapping same-type walls and weld every T/L junction across the plan (auto-coalesce is a setting). | after an import |
| Review wall gaps… | A dialog listing ends left a grid step short of a wall; **Close selected gap** welds one. | — |
| Wall orthogonality report… | Every wall's heading and how far off axis it is — run this before a DXF export. | — |
| Repair wall orthogonality… | Snap the near-axis walls square, by band; **Apply**. | — |

### View · Show

| Item | Action | Example |
|---|---|---|
| View ▸ 3D view… | Ctrl+3: the current plan rendered in 3D, read-only. | — |
| Show ▸ Annotations | Show / hide the texts and leaders (a plan setting). | untick to print without notes |
| Show ▸ Measurements | Show / hide the measures and the datum. | — |
| Show ▸ Item callouts | Every item's session label (`W7`, `V12`, `O3`, `R2`, `F4`, `RF1`) and name, in one small font and one colour; on whenever a plan opens. | untick for a clean view |
| Show ▸ Measurements in feet and inches | Tick for `20'-6"`, untick for `246"`. | — |
| Show ▸ Item callout colour… | The callouts' ink (default blue). | pick green |
| Show ▸ Place datum | The Datum tool (§2). | — |

### Rooms

| Item | Action | Example |
|---|---|---|
| New concept room… | A named area with no walls (a concept, not buildable; quarantined on export). | `Future deck` |
| Combine (union) | Two selected rooms become one; the shared interior walls go. | select two, *Combine* |
| Fragment into pieces | Two overlapping rooms become three groups — each minus the overlap, plus the overlap — every piece fully walled. | — |
| Subtract (1st − 2nd) | Remove the second room from the first. | — |
| Intersect (overlap only) | Keep the overlap. | — |
| Align to grid | Snap the selected rooms' walls to the wall-snap grid, keeping them orthogonal. | — |
| Distribute horizontally / vertically | Equal gaps between three or more selected rooms; the outer two stay. | — |
| Refresh rooms (drop unwalled) | Re-scan the canvas and drop rooms whose walls have gone. | — |

### Floors

| Item | Action | Example |
|---|---|---|
| Select… | Ctrl+F: the floor popup. | `Ctrl+F`, `Enter` |
| New… | Ctrl+Shift+F: name a new floor (switches to it if it exists). | `Upper` |
| Next floor / Previous floor | Ctrl+PgDown / Ctrl+PgUp. | — |
| *‹floor›* ▸ Edit this floor | Make it the active floor (the others ghost beneath). | — |
| *‹floor›* ▸ Rename… | — | `Second` |
| *‹floor›* ▸ Elevation and height… | The level's base elevation and wall height (the 3D builder's and the roofs' inputs). | `96 / 96` |
| *‹floor›* ▸ Reference floor | Tick to make it a reference layer (a site or lot level: exported sheets skip it). | — |
| *‹floor›* ▸ Delete floor | (Enabled while more than one floor exists.) | — |
| *‹floor›* ▸ Move to front / back (display) | Order the ghosted floors beneath the active one. | — |
| Show other floors (ghosted) | Tick to see the other floors faintly. | — |

### Roof

| Item | Action | Example |
|---|---|---|
| Sketch ridge [G] | The ridge tool (§2). | — |
| Sketch dormer [M] | The dormer tool (§2). | — |
| Show roof | Draw the roofs on the plan. | — |
| Edit roof | Show the roofs' grips (implies Show roof). | untick to edit walls under a roof |

### Inventory · AI · Macro · Help

| Item | Action | Example |
|---|---|---|
| Inventory ▸ House (structure)… | Rooms, doors, windows and walls as an aligned table; **Copy to clipboard (TSV)**. | paste into Excel |
| Inventory ▸ Interior furnishings… / Yard items… / Total… | Furnishings by location with quantities and prices; the grand total with the building cost. | — |
| AI ▸ Update furnishing prices… | Ask an AI (Anthropic Claude) for current retail prices for the catalog; the reply fills each furnishing's `price`. Needs an API key (dialog or `ANTHROPIC_API_KEY`). | — |
| Macro ▸ Record / Debug… | The recorder window: **Start**, **Pause**, **Stop**, **Load…**, **Replay** (the selection or all), **Save As…** (`.fpm`); *New line after each mouse action*; *Record in the v2 format*. | record, edit, **Replay** |
| Help ▸ About FloorPlanner… | The version, the checkout, and buttons to open the plans and settings folders. | — |

---

## 5. The context menus

Right-click an item for its own menu. What is offered depends on what is under
the pointer.

| On | Item | Action |
|---|---|---|
| a wall | Properties… | The wall sheet: name, type, thickness, length, heading, level, rooms, openings, **Id** (the session label; the file's id beside it when they differ). Double-click opens it too. |
| | Delete wall | A room's wall fractures (the room-edge stretch stays). |
| | Detach wall from room | Unlock the wall's corners; it stays part of the room. |
| | Snap to Grid Orthogonal | Land its ends on the grid and square it. |
| | Snap to 15deg grid… | Re-angle to the nearest 15°. |
| a door or window | Properties… | Kind, **Size WWHH**, the window's **Sill height**. |
| | Flip swing side | Which side a door opens to. |
| | Delete | — |
| a room name | Properties… | Name, type, area, *Include in total square footage*, interior width / length / perimeter, corners, windows (with glazing area), doors, ceiling height and type, finishes, trim, crown, HVAC, notes. |
| | Rename… | — |
| | Show dimensions | Double-headed arrows along every enclosing wall (also drawn on the PDF's angled lanes). |
| | Inventory… | The room's properties and every furnishing and opening in it, copyable as TSV. |
| | Copy room / Paste room | With its walls and openings (Ctrl+Shift+V pastes). |
| | Extract room (float it) | Lift the room off the plan as a movable unit; **Join room into plan** puts it back and welds. |
| | Delete room | — |
| the blank canvas | New concept room… | A named area with no walls. |
| | Paste room | A copied room, with its walls and openings. |
| | Snap to Grid | Land every wall end on the grid. |
| a furnishing | Rotate 90° CW / CCW | — |
| | Delete ‹name› | — |
| stairs | Full flight / Half flight (landing) · Turn left / Turn right / End at landing · Going up / Going down · Delete stairs | The flight's shape, the landing's turn and the travel arrow; the step count follows the room's ceiling. |
| a group | Cut group / Copy group / Ungroup / Delete group | — |
| the floor selector (Ctrl+F) | 3D view… | The 3D view, from the floor popup. |
| a roof (while *Edit roof* is on) | Roof parameters… | The End-On dialog: ridge and eaves heights, pitch, **Form** (gable / hip / shed), eaves span and overhang per side, each end gable or hip with its **hip run**, a dormer's standing rule; the canvas draws the end-on section. |
| | Delete roof | — |
| the imported image | Calibrate scale (2 points)… | Click two points a known distance apart, type the distance. |
| | Crop to region | Drag-select the part to keep. |
| | Extract walls | Detect the walls (shown as a blue ghost): **Yes** adds them. |
| | Lock image / Unlock image | A locked backdrop cannot be moved, scaled, cropped or removed. |
| | Remove image | — |
| a measure | (the four knobs, §2) | — |
| a leader | (the two knobs, §2; double-click edits the text) | — |

---

## 6. The dialogs

| Dialog | Fields | Where |
|---|---|---|
| Settings | Wall snap (on centre, default 6″) · Rotation snap (15°) · Canvas width / height (100′ × 70′) · Building cost per sq ft ($150) · Auto-coalesce walls · Auto-weld ends · Item callout colour · Measurement units. Saved with the plan. | *File ▸ Settings…* |
| Opening properties | Kind · Size WWHH · Sill height (windows; plan default 36″). | double-click an opening |
| Wall properties | Name · Type · (thickness, length, heading, level, rooms, openings, document fields) · Id. | double-click a wall |
| Room properties | See §5. | right-click the name |
| Roof End-On | See §5 *Roof parameters…*. | the ridge / dormer tools, or right-click a roof |
| Malformed design file | The validator's findings as rows in the **session labels** (`W7`, `V12`); **Zoom to** takes the view to the row's item; while it is open a callout whose label differs from the file's id shows both. | opens on a plan that fails a check |
| PDF export options | Title · Subtitle · Author · Wall assembly note · Dimension note · Levels · Include concept rooms. | *File ▸ Export ▸ PDF plan set…* |
| AI pricing | The AI system, the key, the editable prompt. | *AI ▸ Update furnishing prices…* |
| Macro recorder | See §4. | *Macro ▸ Record / Debug…* |

---

## 7. The macro language

A macro drives the app with no GUI — from the recorder window, `fp_macro.py`,
or `MainWindow.run_macro(text)`. The original language is a flat list of
whitespace-separated tokens; `#` starts a comment; a double-quoted token may
hold spaces. A bad token is recorded in `errors` and skipped. The full
reference is [`macro_language.md`](macro_language.md).

| Token | Action | Example |
|---|---|---|
| `S` `E` `I` `D` `W` `R` `G` `M` `T` `L` `N` | Pick a tool (Select / Exterior / Interior / Door / Window / Room / Roof ridge / Dormer / Text / Measure / Leader). Also `TOOL <name>` (`select extwall intwall door window room roofridge roofdormer text measure leader`) and the digits `1`–`6`. | `I CLICK 120 120 DRAG 360 120` |
| `^N` `^Z` `^Y` `^+Z` `^X` `^C` `^V` `^G` `^+G` `^A` `^S` `^H` | New / undo / redo / cut / copy / paste / group / ungroup / select all / save / toggle shuffle. | `^C MOVE 300 300 ^V` |
| `^O "path"` / `^+S "path"` | Open / save that file. | `^O "plans/den.json"` |
| `^F "name"` / `^F` / `^+F "name"` | Switch to a floor / the default floor / create (or switch to) a floor. | `^+F "Upper"` |
| `^H "on"` / `^H "off"` | Shuffle mode, absolutely. | `^H "on"` |
| `LEFT` `RIGHT` `UP` `DOWN` / `^LEFT` … | Nudge the selection a snap step / 1″. | `UP UP ^LEFT` |
| `ESC` · `DEL` · `ENTER` | Cancel · delete the selection · Return. | `DEL` |
| `CLICK x y` · `^CLICK x y` | Left click · Ctrl-click. | `CLICK 240 180` |
| `CLICK x1 y1 DRAG x2 y2` · `^CLICK … DRAG …` | Press, drag, release (with Ctrl). | `E CLICK 0 0 DRAG 240 0` |
| `RCLICK x y` · `MOVE x y` · `PRESS x y` · `RELEASE x y` · `DRAG x1 y1 x2 y2` | Right click · move the pointer · hold · release · a stand-alone drag. | `MOVE 120 96` |
| `PUP x y [keys…]` | Pop the right-click menu at a point and drive it (and any dialog) with `UP DOWN LEFT RIGHT HOME END TAB BACKSPACE DELETE ENTER ESC` and `TYPE "…"`. | `PUP 120 0 DOWN DOWN DOWN ENTER TYPE "2868" ENTER` |
| `TYPE "text"` | Type into the focused field. | `TYPE "Den"` |
| `PLACE kind x y [rot]` | A furnishing centred at (x, y). | `PLACE sofa 120 140 0` |
| `WALL x1 y1 x2 y2 [ext\|int]` | A wall (default exterior). | `WALL 0 0 240 0 ext` |
| `DOOR x y code` · `WINDOW x y code` | An opening in the wall under (x, y). | `DOOR 120 0 3680` |
| `ROOM name x y` | Name the enclosed area at (x, y). | `ROOM "Living Room" 120 90` |
| `DORMER x y width eaves ridge [dx dy]` | A gable dormer on the roof plane at (x, y). | `DORMER 200 190 60 116 136` |
| `TEXT x y "text"` | A text annotation. | `TEXT 60 90 "North elevation"` |
| `LEADER x1 y1 x2 y2 "text"` | A leader: the arrow's tip, the text's end. | `LEADER 240 100 300 60 "Beam above"` |
| `DATUM x y` | The level's datum, placed or moved. | `DATUM 12 36` |
| `SELECT x y` · `SELECTALL` · `DESELECT` | Select the editable item at a point · all · none. | `SELECT 120 140` |
| `ROTATE deg` · `MOVETO x y` · `DELETE` · `ZOOMFIT` | Rotate the selected furnishings · move the selection · delete it · fit the view. | `ROTATE 90` |
| `OPEN path` · `SAVE path` · `NEW` · `SHOT path` · `WAIT` | Load · save · clear · snapshot (`.svg` vector, else PNG) · flush events. | `SHOT den.svg` |

A whole plan in one line:

```
WALL 0 0 240 0 ext  WALL 240 0 240 180 ext  WALL 240 180 0 180 ext  WALL 0 180 0 0 ext
ROOM Den 120 90  DOOR 120 0 3680  WINDOW 240 90 4848  PLACE sofa 120 140 0
L CLICK 0 0 DRAG 240 0  TEXT 60 -30 "Den, 20 x 15"  SAVE den.json  SHOT den.svg
```

---

## 8. Macro language v2

A macro whose first line is `; fpmacro 2` is **v2**: one command per line,
optionally after a tool letter; `;` starts a comment; every modifier is a real
key press; the whole file is checked before anything runs (the lines before
the first bad one run; it and the rest do not). Specified in
[`macro-spec/MACRO_SPEC.md`](macro-spec/MACRO_SPEC.md).

| Line | Action | Example |
|---|---|---|
| `S` … `N` | A tool letter, alone or before a command. | `I CLICK 120 120 DRAG 360 120` |
| `CLICK x y` · `RCLICK` · `MCLICK` · `DCLICK` · `XCLICK1` · `XCLICK2` | A click of that button (double for `DCLICK`). | `DCLICK 200 150` |
| `CLICK x y DRAG x y DRAG x y …` | A chain: press at the first point, release at the last. | `CLICK 10 10 DRAG 100 10 +DRAG 100 90` |
| `+` `^` `!` `#` before a segment | Shift / Ctrl / Alt / Meta for that segment only. | `I CLICK 120 240 +DRAG 355 253` |
| `MOVE x y` · `WHEEL dx dy` | Move the pointer · one wheel event (120 is a notch). | `^WHEEL 0 120` |
| `TYPE text` | Type the rest of the line literally. | `TYPE 2868` |
| `KEY strokes` | Keystrokes: `^c ^v`, `+^g`, named keys in braces. | `KEY ^z` · `KEY {Enter}` |
| `KEYDOWN key` / `KEYUP key` | Hold a key across lines. | `KEYDOWN {Shift}` |
| `WAIT ms` | Process events for that long. | `WAIT 250` |
| `@NAME args` | An application command (§9). | `@PLACE sofa 120 96 0` |

```
; fpmacro 2
E CLICK 0 0 DRAG 240 0               ; a wall with the Exterior-wall tool
D CLICK 120 0                        ; the Door tool: its dialog opens…
TYPE 3680
KEY {Enter}                          ; …and is answered
@ROOM "Living Room" 120 90           ; no input simulated: the command builds it
N @LEADER 240 100 300 60 "Beam above"
S KEY ^z                             ; a real Ctrl+Z
```

Convert an original-language file to v2 (the original is kept as `.bak`):

```bash
python fp_macro.py --convert edits.fpm other.fpm
```

---

## 9. Application commands

`@NAME arg …` in v2 — the original language's high-level words, run by the
same handlers, so the two cannot drift. A wrong argument count is a validation
error before anything runs.

| Command | Arguments | Action |
|---|---|---|
| `@PLACE` | `kind x y [rot]` | A furnishing centred at (x, y). |
| `@WALL` | `x1 y1 x2 y2 [ext\|int]` | A wall. |
| `@DOOR` / `@WINDOW` | `x y WWHH` | An opening in the wall under (x, y). |
| `@ROOM` | `name x y` | Name the enclosed area. |
| `@DORMER` | `x y width eaves ridge [dx dy]` | A gable dormer. |
| `@TEXT` | `x y "text"` | A text annotation. |
| `@LEADER` | `x1 y1 x2 y2 "text"` | A leader: the arrow's tip at (x1, y1), the text's end at (x2, y2). |
| `@DATUM` | `x y` | The level's datum, placed or moved. |
| `@SELECT` | `x y` | Select the editable item at a point. |
| `@SELECTALL` / `@DESELECT` | | Select everything / clear the selection. |
| `@ROTATE` | `deg` | Rotate the selected furnishings. |
| `@MOVETO` | `x y` | Move the selection so its first item is centred there. |
| `@DELETE` | | Delete the selection. |
| `@ZOOMFIT` | | Fit the view to the walls. |
| `@OPEN` / `@SAVE` | `path` | Load / save a plan. |
| `@NEW` | | Clear the plan. |
| `@SHOT` | `path` | Snapshot the canvas (`.svg` vector, anything else PNG). |
| `@FLOOR` | `name` | Switch to a floor. |
| `@NEWFLOOR` | `name` | Create a floor, or switch to it if it exists. |
| `@SHUFFLE` | `on\|off` | Set shuffle mode. |

The recorder writes these itself for every action whose value comes from a
dialog (a door's size, a room's name, a dormer's heights, a text, a leader, the
datum), so a replay never needs the dialog.

---

## 10. Command-line programs

All run from the repository root. Every script answers `--help`.

### `fp_macro.py` — the headless driver

| Option | Meaning |
|---|---|
| `-i / --in PLAN` | Plan JSON to load first. |
| `-o / --out PLAN` | Plan JSON to write after the macro (also the `^S` target). |
| `-m / --macro TEXT` · `-f / --file FILE` | The macro to run, inline or from a `.fpm` file. |
| `--svg PATH` · `--png PATH` · `--shot PATH` | Snapshots (repeatable; `--shot` picks the format by extension). |
| `--summary counts\|full\|none` | How much of the result to print as JSON (`full` is the whole model). |
| `--repl` | Read macro lines from stdin, one run per line. |
| `--convert FILE…` | Rewrite original-language files as v2, keeping `.bak`; runs nothing. |
| `--window` | A real window instead of offscreen rendering. |
| `-q` | No JSON on stdout. |

```bash
python fp_macro.py --out den.json --svg den.svg --macro "
  WALL 0 0 240 0 ext  WALL 240 0 240 180 ext  WALL 240 180 0 180 ext  WALL 0 180 0 0 ext
  ROOM Den 120 90  DOOR 120 0 3680  PLACE sofa 120 140 0"
python fp_macro.py --in den.json --file edits.fpm --out den2.json --summary full
```

### `fp_extract.py` — a PNG into walls

| Option | Meaning |
|---|---|
| `-i / --in PNG` (required) | Dark walls on a light background. |
| `-o / --out PLAN` · `--png PREVIEW` | The plan written, and a preview image. |
| `--width-ft FT` · `--px-per-ft N` | The scale, as the drawing's real width or directly. |
| `--threshold 128` · `--min-wall-px 24` · `--merge 3` · `--max-thick-px 40` | Darkness that counts as wall; shortest line kept; parallel lines merged within N px (raise to the wall thickness for double-line drawings); thickest block kept. |
| `--wall-type exterior\|interior` | The type of every extracted wall. |

```bash
python fp_extract.py --in plan.png --out plan.json --width-ft 40 --png preview.png
```

### `python -m floorplanner.export.fp2dxf` — Chief Architect DXF

| Option | Meaning |
|---|---|
| `design` | The plan JSON. |
| `-o / --outdir DIR` (`dxf_out`) | One `<level>.dxf` + `<level>.openings.json` per storey level. |
| `--level ID` | Only this level (repeatable; also unlocks site levels). |
| `--set TYPE=INCHES` | Override a wall thickness, e.g. `--set exterior=6.5`. |

```bash
python -m floorplanner.export.fp2dxf house.json -o chief --level L1
```

### `python -m floorplanner.export.fp2pdf` — the PDF plan set

| Option | Meaning |
|---|---|
| `design` · `-o / --out plans.pdf` | The plan and the PDF. |
| `--title` · `--subtitle` · `--author` · `--assembly-note` · `--dim-note` | The title block. |
| `--level ID` · `--set TYPE=IN` · `--include-concept` | Levels, thickness overrides, concept rooms. |

Drawn measurements print in place of the auto rows on any level that has them
while *Show ▸ Measurements* is on; texts and leaders print while *Show ▸
Annotations* is on. Needs `reportlab`.

```bash
python -m floorplanner.export.fp2pdf house.json -o house.pdf --title "Wiscaway" --author "P. Moran"
```

### `python -m floorplanner.viewer.fp3d` — the 3D viewer (pyqtgraph) and OBJ writer

| Option | Meaning |
|---|---|
| `design` · `--level ID` · `--list-levels` | The plan; the levels to show. |
| `--no-furnishings` · `--no-floors` · `--no-openings` · `--no-roofs` · `--wall-height IN` | What to build. |
| `--edges` · `--flat` · `--xray` | Mesh edges; the library's shader; translucent walls. |
| `--dump` · `-v` | Print the stats and the placement report, then exit. |
| `--obj PATH` | Write a Wavefront OBJ and exit. |
| `--shot PATH` · `--azimuth` · `--elevation` · `--distance` | Render to PNG from that camera and exit. |

```bash
python -m floorplanner.viewer.fp3d house.json --shot house.png --azimuth -60 --elevation 28
python -m floorplanner.viewer.fp3d house.json --obj house.obj
```

### `python -m floorplanner.viewer.fp3dq` — the same viewer on Qt Quick 3D

| Option | Meaning |
|---|---|
| `design` · `--level ID` · `--no-furnishings` · `--no-ao` · `--no-shadows` | The plan, the levels, the lighting. |
| `--check` | Report whether Qt Quick 3D resolves, then exit. |
| `--container` | Embed through `createWindowContainer` (more reliable on some drivers). |
| `--shot PATH` · `--yaw` · `--pitch` · `--zoom` · `--fov` · `--shot-delay MS` | Render to PNG from that camera (needs a real display). |

```bash
python -m floorplanner.viewer.fp3dq house.json --shot house.png --yaw 30 --pitch -20 --zoom 1.2 --fov 28
```

### `tools/validate_design.py` — schema and invariants

```bash
python tools/validate_design.py house.json            # the packaged v6 schema
python tools/validate_design.py house.json other.json # another schema file
```

Prints Schema PASS / FAIL, the invariant findings (I1–I16), and a derived
area / perimeter / accounting report.

### `tools/migrate_to_design_v5.py` — a legacy file, converted

```bash
python tools/migrate_to_design_v5.py old.json new.json           # faithful
python tools/migrate_to_design_v5.py old.json new.json --clean   # weld, re-trace, repair; writes provenance
```

(The app does the same on *File ▸ Open*; the name is historical — the output is
the current document.)

### `tools/plan-snap.py` — snap a plan to a grid

```bash
python tools/plan-snap.py -s 12 -i in.json -o out.json
python tools/plan-snap.py < in.json > out.json          # default 6"
```

`--keep-degenerate` keeps zero-length walls; `--indent N` sets the JSON indent.

### Asset and example generators

```bash
python _gen_assets.py              # every SVG under assets/ (icons, furnishings, manifest, groups)
python docs/make_gallery.py        # docs/gallery/ and docs/screenshot.png
python examples/make_examples.py   # the sample files and previews
python tools/make_site_demo.py     # examples/site_demo.json
python tools/demo_move_wall.py     # proves workflow E: move a wall, the neighbours resize
```

---

## 11. Developer commands

```bash
pip install -r requirements-dev.txt
python -m ruff check .                 # lint
pytest                                 # the whole suite, headless
pytest --quick                         # without the slow and gui markers
pytest -m "not gui"                    # by marker (see tests/README.md)
python tools/gate.py                   # THE GATE: ruff, census, the suite twice, the docs lane; writes .gate-result.json
python tools/gate.py --quick           # the same, quick
python tools/gate.py --docs            # the docs lane alone
python tools/gate.py --trailer         # print the census as a commit trailer
python tools/status_index.py          # regenerate docs/STATUS.md and the mailbox's pair table (--check in the gate)
python tools/defects_index.py          # regenerate docs/defects/INDEX.md (--check, --validate)
python tools/progress_index.py         # regenerate docs/progress/tasks/INDEX.md (--check)
python tools/ref_audit.py --strict-ids # every defect reference resolves (--json PATH, --compare BASELINE, -v)
python tools/negative_assertions.py    # count the suite's negative assertions (--json PATH)
python tools/record.py --verify FILE "text" …   # prove an anchored edit landed
python tools/gen_macro_parser.py       # regenerate the v2 parser from the ANTLR grammar (--check)
python tools/defects_to_github.py --dry-run     # the gh commands that would file the defects as issues
```

The commit discipline: `docs/SESSION_SNAPSHOT.md` first, then the mailbox
(`docs/handoff/`), then the gate GREEN before a commit — the hook in
`.claude/hooks/verify_gate.py` refuses one without it.
