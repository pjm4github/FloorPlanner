# Headless macro language & driver

FloorPlanner can be driven with **no GUI** so a script — or an AI system — can
load a plan, edit it, "see" the result, and save it. It's a two-part tool:

1. **The in-app hook** (`FloorPlanner.MacroRunner`, exposed as
   `MainWindow.run_macro(text)` plus `export_canvas`, `load_path`, `save_path`,
   `scene_summary`). This lives inside the app, so the editor and the headless
   driver run the *same* code paths.
2. **The driver** (`fp_macro.py`) — a standalone CLI that boots the app
   offscreen, feeds it a macro, snapshots the canvas (SVG/PNG), saves the plan,
   and prints a JSON summary of the result.

```
              fp_macro.py  ──drives──▶  MainWindow.run_macro()  ──▶  MacroRunner
              (Part 2, CLI)             (Part 1, in-app hook)        (token engine)
```

## Coordinates

Positions are in **scene inches** (1 unit = 1 inch), matching the saved JSON
model. `120` means 10 ft. A value may also be written in feet: `10'` or
`10'6"`. The canvas defaults to 100' × 70' with the origin at the top-left.

## Macro syntax

A macro is a flat list of **whitespace-separated tokens**; newlines are just
more whitespace. `#` starts a line comment. A token may be double-quoted to
include spaces (e.g. a room name `"Living Room"`). A bad token is recorded in
`errors` and skipped — one mistake doesn't abort the whole macro.

### Tools (the toolbar / number keys)

| Token | Action |
|-------|--------|
| `S` `E` `I` `D` `W` `R` | **S**elect / **E**xterior-wall / **I**nterior-wall / **D**oor / **W**indow / **R**oom tool |
| `TOOL <name>` | same, by name: `select extwall intwall door window room` |

(The legacy digit codes `1`–`6` are still accepted for older macros.)

### Shortcuts (Ctrl chords, written `^X`)

Spaces separate them, e.g. `^C ^V`. A `+` after the caret adds Shift.

| Token | Action |
|-------|--------|
| `^N` | new / clear plan |
| `^Z` / `^Y` (or `^+Z`) | undo / redo |
| `^X` `^C` `^V` | cut / copy / paste (paste lands at the last `MOVE` point) |
| `^G` / `^+G` | group / ungroup the selection |
| `^A` | select all editable items |
| `^S` | save to the current file (set by the driver's `--out`) |

### Keyboard

| Token | Action |
|-------|--------|
| `LEFT` `RIGHT` `UP` `DOWN` | nudge the selection one wall-snap step (default 6") |
| `^LEFT` `^RIGHT` `^UP` `^DOWN` | fine nudge (1") |
| `ESC` | cancel an in-progress wall draw |
| `DEL` (or `DELETE`) | delete the selection |
| `ENTER` | send Return |

### Mouse (synthesized through the view, like real capture)

| Token | Action |
|-------|--------|
| `CLICK x y` | left click at a scene point |
| `^CLICK x y` | **Ctrl**+click (e.g. toggle an item in/out of the selection) |
| `CLICK x1 y1 DRAG x2 y2` | press at the click point, drag to the DRAG point, release — one click-drag operation. The `DRAG` carries only the **end** point; the start is the preceding `CLICK` |
| `^CLICK x1 y1 DRAG x2 y2` | the same with **Ctrl** held (e.g. Ctrl-drag a room name to nudge just the label, or a Ctrl rubber-band additive select) |
| `RCLICK x y` | right click |
| `MOVE x y` | move the cursor (sets the paste target) |
| `PRESS x y` / `RELEASE x y` | hold / release the left button |
| `DRAG x1 y1 x2 y2` | a stand-alone drag with explicit start+end (no preceding `CLICK`) |

### Context (right-click) menus & dialog text

| Token | Action |
|-------|--------|
| `PUP x y [keys…]` | pop up the right-click menu at a scene point, then drive it — and any modal dialog it opens — with the keys that follow |
| nav / edit keys | `UP` `DOWN` `LEFT` `RIGHT` (sub-menus) `HOME` `END` `TAB` `BACKSPACE` `DELETE`, ending with `ENTER` (select / accept) or `ESC` (cancel) |
| `TYPE "text"` | type literal text into the active dialog's field (e.g. a new size code or room name) |

All the keys after `PUP` are consumed by it (the menu/dialog is only open
during that step). The menu is the app's real context menu, so its items
depend on what's under the point (a wall, opening, room name, furnishing or
stairs).

Examples:

```
PUP 120 96 DOWN ENTER                          # rotate the furnishing 90 CW
PUP 120 0 DOWN DOWN DOWN ENTER TYPE "2868" ENTER   # resize a door to 28x68
```

A `PUP` with no trailing `ENTER` just opens and cancels the menu. (Standalone,
`TYPE "text"` types into whatever currently holds focus.)

### High-level placement & editing (robust, dialog-free)

These build items directly — handy for an AI that knows *what* it wants, not
*where to click*.

| Token | Action |
|-------|--------|
| `PLACE kind x y [rot]` | add a furnishing centred at (x,y), rotation in degrees. `kind` is a catalog id (`sofa`, `bed_queen`, `range`, …) |
| `WALL x1 y1 x2 y2 [ext\|int]` | add a wall (default exterior) |
| `DOOR x y code` / `WINDOW x y code` | cut an opening into the wall under (x,y); `code` is `WWHH` inches (e.g. `3680`) |
| `ROOM name x y` | name the enclosed area containing (x,y); the room then owns its walls |
| `SELECT x y` | select the editable item at a point (prefers furnishing/wall over a room label) |
| `SELECTALL` / `DESELECT` | select all / clear selection |
| `ROTATE deg` | rotate selected furnishings by `deg` |
| `MOVETO x y` | move the selection so its first item's centre is at (x,y) |
| `DELETE` | delete the selection |
| `ZOOMFIT` | fit the view to the walls |

### Files & snapshots

| Token | Action |
|-------|--------|
| `OPEN path` | load a plan JSON |
| `SAVE path` | save a plan JSON |
| `NEW` | clear the plan |
| `SHOT path` | snapshot the canvas; `.svg` → vector, anything else → PNG |
| `WAIT` | flush pending events |

## The driver: `fp_macro.py`

```
python fp_macro.py [options]

  -i, --in PATH       plan JSON to load first
  -o, --out PATH      plan JSON to write after (also the ^S target)
  -m, --macro STR     macro string to run
  -f, --file PATH     file containing a macro to run
      --svg PATH      write an SVG snapshot (repeatable)
      --png PATH      write a PNG snapshot (repeatable)
      --shot PATH     write a snapshot, format by extension (repeatable)
      --repl          read macro lines from stdin, one run per line
      --window        show a real window instead of rendering offscreen
      --summary {counts,full,none}   how much layout to print (default counts)
  -q, --quiet         suppress the JSON result on stdout
```

It prints a JSON result, e.g.:

```json
{ "ok": true, "steps": 6, "errors": [], "saved": "plan.json",
  "exports": [{"path": "after.svg", "ok": true}],
  "counts": {"walls": 4, "rooms": 1, "furnishings": 2} }
```

Use `--summary full` to get the entire parseable layout (`scene`: the full
`floorplanner-json` model — walls with openings, rooms, furnishings with kind /
position / rotation / size / price) so a downstream tool can read exactly what
changed.

### Examples

Build and furnish a room, then snapshot it:

```bash
python fp_macro.py --out den.json --svg den.svg --png den.png --macro "
  WALL 0 0 240 0 ext   WALL 240 0 240 180 ext
  WALL 240 180 0 180 ext   WALL 0 180 0 0 ext
  ROOM Den 120 90
  DOOR 120 0 3680
  PLACE sofa 120 140 0
  PLACE bed_queen 60 60 90
"
```

Apply an edit file to an existing plan and re-render:

```bash
python fp_macro.py --in den.json --file edits.fpm --png after.png --out den.json
```

Interactive, one macro line at a time (the AI loop: edit → look → edit):

```bash
python fp_macro.py --in den.json --repl
> PLACE armchair 180 140 0
{"ok": true, "steps": 1, "errors": [], "counts": {...}}
> SHOT step1.svg
{"ok": true, "steps": 1, "errors": [], "counts": {...}}
> QUIT
```

## Recording macros in the GUI

Rather than writing tokens by hand, open the **Macro ▸ Record / Debug…** window
(or the ● Record toolbar button). It's a non-modal recorder/debugger:

- **Start** — begins capture; switch to the plan window and interact. Mouse
  clicks/drags become `CLICK`/`DRAG`, tool changes become `1`–`6`, palette
  drops become `PLACE kind x y`, and keys (arrows, `^C`/`^V`/…, `DEL`, `ESC`)
  become their tokens. Actions whose parameters come from a **dialog** rather
  than keystrokes are captured as self-contained tokens with the value baked
  in — placing a door/window records `DOOR x y WWHH` / `WINDOW x y WWHH`, and
  naming a room records `ROOM "name" x y` — so replay never needs the dialog.
  A right-click context menu records `PUP x y` followed by the keys you press
  to drive it, all on one line — including any text you type into a dialog it
  opens, captured as `TYPE "..."` (e.g.
  `PUP 120 0 DOWN DOWN DOWN ENTER TYPE "2868" ENTER`). Inside an open menu or
  dialog only keystrokes are recorded, not mouse clicks, so playback can push
  them straight back to the modal.
  With **New line after each mouse action** ticked, a `\n` is added after every
  mouse/place action so the macro reads one action per line.
- **Pause / Resume** — temporarily stop/continue capturing.
- **Stop** — end capture. Now edit the text freely.
- **Replay** — select a portion of the text (or all) and replay it one line at
  a time so you can watch it run. Enabled only when text is selected.
- **Save As…** — write the macro to a `.fpm` file for later use with
  `fp_macro.py --file`.

Typical debug loop: record an action, **Stop**, clear the canvas (`Ctrl+N`),
select the recorded lines, **Replay**, and watch it rebuild — tweaking the text
between runs.

## Why SVG + the JSON summary

The **SVG** snapshot is a vector render an AI can both rasterise to "look at"
and parse structurally. The **`--summary full` JSON** is the authoritative,
machine-readable layout (the same model that is saved to disk). Together they
let a downstream system visualise a change and reason about it precisely, then
issue the next macro.
