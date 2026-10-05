# FloorPlanner Input Macro Language — Specification v2

This document specifies version 2 of the FloorPlanner macro language. It is
written as an implementation brief for Claude Code. It covers the language
itself (syntax and semantics), how macros are recorded and replayed in a
PyQt6 application, and the work needed to migrate the existing macro feature.

The formal grammar lives in `grammar/MacroLexer.g4` and
`grammar/MacroParser.g4`. Where this document and the grammar disagree on
syntax, the grammar wins. This document is authoritative for semantics.
`grammar/examples.macro` contains a macro that exercises every construct and
must parse without errors.

---

## 1. Tasks for Claude Code

Do these in order.

1. **Survey the existing macro feature before changing anything.** Find the
   current macro parser, recorder, player, file format and extension, and
   the table that maps tool letters to tools (for example `I` = wall tool,
   `S` = select tool). Identify how mouse and keyboard input are currently
   represented.
2. **Check for conflicts and stop if you find any.** The v2 grammar assumes
   that tool letters are single uppercase ASCII letters `A`–`Z` and appear
   first on a line. If the existing format uses lowercase letters, digits,
   multi-character tool codes, or any word that collides with a v2 keyword
   (Section 3.2), list the conflicts and ask before proceeding. Do not
   silently change the `TOOL` lexer rule.
3. **Add the grammar** to the repository (suggested location:
   `macro/grammar/`). Generate the Python target with
   `antlr4 -Dlanguage=Python3 -visitor MacroLexer.g4 MacroParser.g4`. Pin
   `antlr4-python3-runtime` to the same version as the ANTLR tool; the
   grammar was validated with ANTLR 4.11.1 and uses nothing newer. If the
   repository already has a convention for generated ANTLR code (committed
   vs. generated at build time), follow it.
4. **Implement the pipeline** described in Section 8: parse → AST →
   validate → expand to abstract input events → deliver to Qt. Also
   implement the recorder (Section 9) and serializer (Section 10).
5. **Handle legacy macros** (Section 11).
6. **Write the tests** listed in Section 12.

---

## 2. Design summary

- One command per line, optionally preceded by a single-letter tool selection.
- Modifier prefixes follow AutoHotkey: `+` Shift, `^` Ctrl, `!` Alt, `#` Meta.
- A mouse **chain** (`CLICK x y DRAG x y DRAG x y …`) presses at the first
  point and releases at the last. The mouse button is never held between lines.
- Modifiers are scoped to a single segment. They are never sticky across
  segments or lines; `KEYDOWN`/`KEYUP` are the only way to hold a key
  across steps.
- `TYPE` takes the rest of the line literally. `KEY` sends keystrokes with
  modifiers and `{Named}` keys.
- An **application command** (`@PLACE sofa 120 96`) makes the application
  act directly instead of simulating input (Section 14).

---

## 3. Lexical structure

### 3.1 Lines, whitespace, comments

- Encoding is UTF-8. Readers accept LF or CRLF line endings; writers emit LF.
- Tokens are separated by spaces or tabs. Blank lines are allowed anywhere.
- `;` starts a comment that runs to end of line, in ordinary lines and in
  `KEY`/`KEYDOWN`/`KEYUP` lines. **`TYPE` lines cannot contain comments**:
  everything after `TYPE ` is text. On a `KEY` line, the semicolon key is
  written `{;}`.
- `#` is the Meta modifier, not a comment character.

### 3.2 Keywords

Keywords are case-sensitive and uppercase:

`CLICK` `RCLICK` `MCLICK` `DCLICK` `XCLICK1` `XCLICK2` `DRAG` `MOVE`
`WHEEL` `TYPE` `KEY` `KEYDOWN` `KEYUP` `WAIT`

An application command is not a keyword: it is `@` followed by an
uppercase name (Section 14).

### 3.3 Tool letters

A tool letter is a single uppercase letter `A`–`Z`. Keywords take
precedence by longest match, so `CLICK` is never read as tool `C`.

### 3.4 Numbers

`-?[0-9]+(\.[0-9]+)?`, for example `100`, `-120`, `1.5`. A leading `+` is
not allowed, because `+` is the Shift modifier.

### 3.5 Modifiers

| Char | Modifier | Qt                               |
|------|----------|----------------------------------|
| `+`  | Shift    | `Qt.KeyboardModifier.ShiftModifier`   |
| `^`  | Ctrl     | `Qt.KeyboardModifier.ControlModifier` |
| `!`  | Alt      | `Qt.KeyboardModifier.AltModifier`     |
| `#`  | Meta     | `Qt.KeyboardModifier.MetaModifier`    |

Several prefixes can be combined in any order (`+^CLICK`). Repeating a
prefix (`++CLICK`) is a validation error. On macOS, Qt maps
`ControlModifier` to Cmd; this implementation accepts that Qt behavior.

---

## 4. Line structure

```
line := [TOOL] [command]
```

| Example                        | Meaning                                      |
|--------------------------------|----------------------------------------------|
| `S`                            | Select the select tool                       |
| `I CLICK 100 100 DRAG 400 100` | Select the wall tool, then draw a wall       |
| `CLICK 50 50`                  | Click with whichever tool is currently active |

- The tool is selected **before** the command on the same line runs.
- The selected tool persists until another tool letter is executed.
- Tool selection must invoke the same `QAction` (or equivalent handler) that
  the toolbar and the keyboard shortcut use. Do not synthesize a key press
  for it.
- An unknown tool letter is a validation error (Section 8.3).

---

## 5. Mouse commands

### 5.1 Coordinates and targets

All mouse commands target the floor-plan canvas. If the canvas is a
`QGraphicsView`, coordinates are **scene coordinates**: the player converts
them with `view.mapFromScene()` and the recorder with `view.mapToScene()`,
so macros survive zoom and pan. If the canvas is not a `QGraphicsView`,
coordinates are logical pixels local to the canvas widget. Check which
applies and document it in the code.

The player tracks a **current pointer position**, updated by every mouse
command. It starts at the canvas center.

### 5.2 Chains

```
chain   := [mods] HEAD x y { [mods] DRAG x y }
HEAD    := CLICK | RCLICK | MCLICK | DCLICK | XCLICK1 | XCLICK2
```

| Head      | Button                         |
|-----------|--------------------------------|
| `CLICK`   | Left                           |
| `RCLICK`  | Right                          |
| `MCLICK`  | Middle                         |
| `DCLICK`  | Left, double click             |
| `XCLICK1` | `Qt.MouseButton.BackButton`    |
| `XCLICK2` | `Qt.MouseButton.ForwardButton` |

The button chosen by the head is held for the whole chain.

**Rules:**

1. The press happens at the head point. The release happens at the endpoint
   of the last segment. A head with no `DRAG` segments is a click: press and
   release at the same point.
2. Each segment's modifiers apply only while moving to that segment's
   endpoint. The head's modifiers apply only to the press.
3. The final segment's modifiers stay held through the release. The mouse
   is released first, then the modifiers.
4. `DCLICK` with drag segments is a double-click-drag (word-wise selection
   in text editors). The button stays held after the second press.

### 5.3 Execution of a chain

Let the segments be `S0` (the head) through `Sn`, each with a modifier set
`Mi` and a point `Pi`. Let `K` be the set of modifiers held by `KEYDOWN`
(Section 6.3).

1. Transition the modifier state to `M0 ∪ K` (Section 7).
2. Move the pointer to `P0`, with no buttons held.
3. Press the button at `P0` with modifiers `M0 ∪ K`. For `DCLICK`, send the
   sequence Press, Release, DblClick, leaving the button held after the
   DblClick event.
4. For each segment `i = 1 … n`: transition the modifiers to `Mi ∪ K`, then
   send interpolated `MouseMove` events from `P(i-1)` to `Pi` (Section 8.5).
   Each move carries `buttons() = button`, `button() = NoButton`, and
   modifiers `Mi ∪ K`.
5. Release the button at `Pn` (or at `P0` if `n = 0`) with modifiers
   `Mn ∪ K`.
6. Transition the modifiers back to `K`.

### 5.4 Expansion examples

| Macro                                 | Events                                                                 |
|---------------------------------------|------------------------------------------------------------------------|
| `CLICK 10 10`                         | press(10,10) → release(10,10)                                           |
| `CLICK 10 10 DRAG 200 10`             | press(10,10) → move… → release(200,10)                                  |
| `CLICK 10 10 +DRAG 200 80`            | press → Shift↓ → move… → release(200,80) → Shift↑                       |
| `+CLICK 10 10 DRAG 200 80`            | Shift↓ → press → Shift↑ → move… → release(200,80)                       |
| `+CLICK 10 10 +DRAG 200 80`           | Shift↓ → press → move… → release(200,80) → Shift↑                       |
| `CLICK 10 10 DRAG 100 10 +DRAG 100 90`| press → move to (100,10) → Shift↓ → move to (100,90) → release → Shift↑ |
| `^CLICK 10 10 +DRAG 200 80`           | Ctrl↓ → press → Ctrl↑ → Shift↓ → move… → release → Shift↑               |

### 5.5 MOVE

`[mods] MOVE x y` moves the pointer with no buttons held, for hover
effects and previews. The modifiers are applied for the duration of the
move and then released.

### 5.6 WHEEL

`[mods] WHEEL dx dy` sends one `QWheelEvent` at the current pointer
position, with `angleDelta = QPoint(dx, dy)` in Qt's units: eighths of a
degree, so 120 is one notch. Use `MOVE` first if the wheel event needs to
happen somewhere else.

---

## 6. Keyboard commands

Keyboard events go to `QApplication.focusWidget()`. If no widget has focus,
they go to the canvas.

### 6.1 TYPE

```
TYPE <text>
```

- The lexer consumes exactly one space after `TYPE`. Everything after that,
  up to the end of the line, is typed literally. Additional leading spaces
  are part of the text.
- No characters are special: quotes, `+ ^ ! # ; { }` are all typed as written.
- `TYPE "Hello World"` types the quotes too. `TYPE +DRAG 10 10` types
  `+DRAG 10 10`.
- Newlines and trailing whitespace can't be expressed; use `KEY {Enter}` and
  `KEY {Space}` instead.
- A bare `TYPE` (no text) is valid and does nothing.
- Each character becomes a KeyPress/KeyRelease pair carrying that character
  as `text()`, as `QTest.keyClicks` does.

### 6.2 KEY

```
KEY stroke { stroke }
stroke := { + | ^ | ! | # } ( char | {Name} )
```

Each stroke is sent in this order: press its modifiers, press the key,
release the key, release the modifiers. Strokes may be separated by spaces
(`KEY ^c ^v`) or run together (`KEY ^cv` means Ctrl+C, then V).

- A single character names a physical key. **Letters are
  case-insensitive**: `^A` and `^a` both mean Ctrl+A. Shift must always be
  written explicitly (`^+a`).
- The Qt key for a character `ch` in the Latin-1 range is
  `Qt.Key(ord(ch.upper()))`. Qt key codes equal Unicode code points in that
  range.
- `+ ^ ! # ; { }` cannot appear bare, because they are syntax. Escape them
  in braces.

**Named keys.** Names are matched case-insensitively; the writer emits the
spelling shown here.

| Name                                    | `Qt.Key`                                  |
|-----------------------------------------|-------------------------------------------|
| `{Enter}`                               | `Key_Return`                              |
| `{Tab}`                                 | `Key_Tab`                                 |
| `{Esc}`                                 | `Key_Escape`                              |
| `{Space}`                               | `Key_Space`                               |
| `{Backspace}`                           | `Key_Backspace`                           |
| `{Delete}`                              | `Key_Delete`                              |
| `{Insert}`                              | `Key_Insert`                              |
| `{Up}` `{Down}` `{Left}` `{Right}`      | `Key_Up` `Key_Down` `Key_Left` `Key_Right` |
| `{Home}` `{End}`                        | `Key_Home` `Key_End`                      |
| `{PgUp}` `{PgDn}`                       | `Key_PageUp` `Key_PageDown`               |
| `{F1}` … `{F24}`                        | `Key_F1` … `Key_F24`                      |
| `{Shift}` `{Ctrl}` `{Alt}` `{Meta}`     | `Key_Shift` `Key_Control` `Key_Alt` `Key_Meta` |
| `{+}` `{^}` `{!}` `{#}` `{;}` `{{}` `{}}` | The literal character's key             |
| `{x}` (any single character)            | Same as the bare character `x`            |

An unknown name is a validation error.

### 6.3 KEYDOWN / KEYUP

```
KEYDOWN key
KEYUP key
```

Each takes exactly one key with no modifier prefixes. Typical use is
holding Space to pan the canvas while dragging:

```
KEYDOWN {Space}
CLICK 100 100 DRAG 300 250
KEYUP {Space}
```

- The player keeps a set of held keys. When a modifier key is held this
  way (`KEYDOWN {Shift}`), it joins the baseline modifier set `K` used in
  Section 5.3 and is included in every subsequent event until `KEYUP`.
- `KEYDOWN` for a key that is already held, or `KEYUP` for a key that is
  not held, logs a warning and is otherwise ignored.
- When the macro ends, whether normally or by abort, all held keys are
  released, and a warning is logged for each one.

---

## 7. Modifier state transitions

Whenever the active modifier set changes from `A` to `B`:

- For each modifier in `A − B`, send a `KeyRelease`. Release in the order
  Meta, Alt, Ctrl, Shift.
- For each modifier in `B − A`, send a `KeyPress`. Press in the order
  Shift, Ctrl, Alt, Meta.
- Each key event's `modifiers()` reflects the state *after* that key
  changes, which matches what Qt delivers for real hardware input.

Real key events are required, not just modifier flags on mouse events.
Some widgets react in `keyPressEvent` (live constraint previews, for
example), and some read `QGuiApplication.keyboardModifiers()`. Sending
real events keeps both kinds of widget consistent.

---

## 8. Player architecture

### 8.1 Pipeline

```
text ─► ANTLR parse ─► AST (dataclasses) ─► validate ─► expand ─► [InputEvent] ─► QtEventSink
```

- **AST.** Build plain dataclasses with an ANTLR visitor, and keep the rest
  of the code independent of ANTLR types. Suggested node types:
  `Line(tool: str | None, command: Command | None, lineno: int)`,
  `Chain(button, double: bool, segments: list[Segment])`,
  `Segment(mods: frozenset[Mod], x: float, y: float)`,
  `Move`, `Wheel`, `TypeText(text)`, `KeyPress(strokes)`,
  `KeyDown(key)`, `KeyUp(key)`, `Wait(ms)`.
- **Expand** is pure: it turns the AST into a list of abstract
  `InputEvent`s (key down/up, mouse press/move/release/dblclick, wheel,
  wait, select-tool), using scene coordinates and no Qt objects. Unit tests
  cover this step without needing a GUI.
- **QtEventSink** converts the abstract events into `QMouseEvent`,
  `QKeyEvent`, and `QWheelEvent`, maps coordinates, and delivers them with
  `QApplication.sendEvent` to the canvas viewport (for mouse events) or the
  focus widget (for key events).

### 8.2 TYPE text extraction

The `TEXT` token contains exactly the text to type; the separator space has
already been consumed by the lexer. A `TYPE` with no `TEXT` child means
empty text.

### 8.3 Validation

Validate the whole macro before executing anything. Report every error
with its line and column, then abort. Validation errors:

- Syntax errors from ANTLR. Install an error listener that collects errors
  instead of printing them.
- Unknown tool letter.
- Unknown `{Name}`.
- A repeated modifier prefix within one token group (`++CLICK`).
- A negative `WAIT`.

### 8.4 WAIT

`WAIT ms` processes events for that many milliseconds, using
`QTest.qWait` or a `QEventLoop` with a timer. Do not use `time.sleep`.

### 8.5 Drag interpolation and pacing

- Split each drag segment into moves of at most `step_px` (default 8)
  view pixels, measured after mapping to view coordinates, with at least 2
  moves per segment. Without this, `QApplication.startDragDistance()` and
  rubber-band logic don't behave as they would with a real mouse.
- Call `QApplication.processEvents()` after each delivered event.
- Make `step_px` and an optional per-event delay (default 0 ms)
  configurable in the player.

---

## 9. Recorder

Install an application-wide event filter while recording. The filter must
never consume events.

### Tool changes

Record the tool letter when the active tool changes, by hooking the
tool-change signal rather than input events. Emit it as the prefix of the
next line. If recording stops with a tool change still pending, emit the
letter on its own line.

### Mouse

- A press on the canvas opens a chain. The head's modifiers are those
  active at the press.
- While the button is held, track the pointer. When the modifier state
  changes, close the current segment at the current pointer position,
  using the *previous* modifiers, and start a new segment.
- The release closes the final segment at the release position, using the
  modifiers active at the release.
- If the total movement is less than `startDragDistance()` and the
  modifiers never changed, emit a plain click at the press position. This
  drops hand jitter.
- When a `MouseButtonDblClick` arrives, replace the preceding `CLICK` at
  the same position with `DCLICK`. If a drag follows the double click, it
  becomes the chain's segments.
- Record hover moves only if hover recording is enabled (off by default).
  Moves during a drag are folded into the segments as described above.
- Wheel events become `WHEEL` lines.

### Keyboard

- Collect consecutive key presses whose `text()` is printable and whose
  modifiers are a subset of {Shift} into a single `TYPE` buffer. Shift is
  already reflected in the text, so `H` is recorded as `H`.
- Flush the buffer on any other recorded event. If the buffer ends with
  spaces, strip them from the `TYPE` line and emit them as a following
  `KEY {Space}` line, repeated once per space. A buffer consisting only of
  spaces becomes `KEY {Space}` strokes.
- Any other key press becomes a `KEY` stroke. Consecutive strokes can be
  merged onto one `KEY` line.
- Don't record modifier keys pressed on their own. They show up as prefixes
  on the events they affect.

### Timing

The recorder does not emit `WAIT` by default. Add an option to emit
`WAIT` for gaps longer than a configurable threshold.

---

## 10. Serializer (canonical form)

Writers always produce this canonical form. Readers also accept
non-canonical spacing that the grammar allows, such as `+ CLICK` or
`ICLICK`.

- The tool letter is followed by one space: `I CLICK 1 2`.
- Modifiers are attached to their keyword, in the order `+ ^ ! #`: `+^DRAG`.
- Tokens are separated by single spaces.
- Numbers are written with up to 2 decimal places, with trailing zeros and
  any trailing `.` removed. `-0` is written as `0`.
- Named keys use the spellings in the table in Section 6.2. Bare
  characters in `KEY` lines are written in lowercase.
- Line endings are LF, and the file ends with a final newline.
- The first line is the comment `; fpmacro 2`, used for format detection
  (Section 11).

Round-trip requirement: `serialize(parse(serialize(ast))) == serialize(ast)`.

---

## 11. Legacy macros

- A file whose first non-blank line is `; fpmacro 2` is v2.
- Any other file is checked against the existing format. If it parses as
  legacy, convert it to the v2 AST through a converter module that maps
  the existing commands onto v2 commands.
- Provide a command-line or menu action that rewrites legacy macro files
  in v2 canonical form. Keep a `.bak` copy of each original.
- If a legacy construct has no v2 equivalent, report it and do not drop it
  silently.

---

## 12. Tests (pytest)

1. **Grammar acceptance.** `grammar/examples.macro` parses with zero errors.
2. **Grammar rejection.** Each of the following produces at least one
   error:
   `DRAG 10 10`, `KEY +`, `KEY }`, `CLICK 10`, `I S CLICK 1 1`,
   `FOO 1 2`, `KEYDOWN ^a`, `KEYDOWN a b`, `TYPEx`, `CLICK 1 1 TYPE hi`, `+`.
3. **TYPE literalness.** `TYPE "Hello World"` yields `"Hello World"`;
   `TYPE +DRAG 10 10` yields `+DRAG 10 10`; `TYPE   x ; y` yields
   `  x ; y`; a bare `TYPE` yields empty text.
4. **Expansion.** Every row of the table in Section 5.4 produces exactly
   the listed event order. Test against the abstract event list, without
   Qt.
5. **KEYDOWN baseline.** `KEYDOWN {Shift}` followed by `CLICK 1 1` produces
   a press carrying Shift and no extra Shift key events. An unreleased key
   at the end of the macro is released and a warning is logged.
6. **Validation.** Unknown tool letters, unknown key names, repeated
   modifiers, and negative `WAIT` each produce a positioned error, and
   nothing is executed.
7. **Round trip.** For every example, the serializer output is stable, as
   defined in Section 10.
8. **CRLF.** A CRLF copy of `examples.macro` parses to the same AST, with no
   `\r` in any `TEXT` token.
9. **Recorder (pytest-qt, if available).** Use `qtbot` to record a
   Shift-constrained drag that changes modifiers partway through, and a
   typed string with a trailing space. Assert the recorded text, then
   replay it and assert the resulting canvas state.

---

## 13. Complete example

```
; fpmacro 2
; Draw two walls, select one, label it
I CLICK 100 100 DRAG 400 100
I CLICK 400 100 +DRAG 400 300
S +CLICK 250 100
DCLICK 200 150
TYPE Hello World
KEY {Enter}
KEYDOWN {Space}
CLICK 300 300 DRAG 500 400
KEYUP {Space}
```

---

## 14. Application commands

*Added 2026-10-04 on Patrick's instruction: "carry v1's high level commands
as a single command using the form @COMMAND".*

```
appCommand := @NAME { argument }
argument   := "quoted text" | bare-word
```

An application command makes the application **act directly** — place a
furnishing, cut a door, open a file — where every other line of this
language simulates input. It is how a macro says *what it wants* rather
than *where to click*, and how a recorder writes down an action whose
parameters came from a dialog without having to replay the dialog.

### 14.1 Syntax

- `@` and an uppercase name (`[A-Z][A-Z0-9_]*`), then arguments separated by
  spaces or tabs, to the end of the line. The `@` is what keeps a name such
  as `DOOR` from being read as the tool letters `D O O R`.
- An argument is a **bare word** or a **double-quoted string**. Quotes are
  needed only when the text is empty, starts with a quote, or contains a
  space, a tab or a semicolon. There are no escapes; a quoted string cannot
  contain a double quote.
- A bare word may *contain* a quote, so the feet-and-inches length `12'6"`
  is one argument. Numbers are plain inches (`120`) or feet-inches (`10'`,
  `12'6"`); they are the application's to read, not the grammar's.
- `;` starts a comment, as on an ordinary line.
- A tool letter may precede it: `S @SELECT 120 96`.

### 14.2 The commands

These are the existing macro language's own commands
(`docs/macro_language.md`), run by its own handlers, so `@PLACE` here and
`PLACE` there cannot drift apart.

| Command | Arguments | Action |
|---|---|---|
| `@PLACE` | `kind x y [rot]` | add a furnishing centred at (x, y) |
| `@WALL` | `x1 y1 x2 y2 [ext\|int]` | add a wall (default exterior) |
| `@DOOR` / `@WINDOW` | `x y WWHH` | cut an opening into the wall under (x, y) |
| `@ROOM` | `name x y` | name the enclosed area containing (x, y) |
| `@DORMER` | `x y width eaves ridge [dx dy]` | add a gable dormer on the roof plane at (x, y) |
| `@SELECT` | `x y` | select the editable item at a point |
| `@SELECTALL` / `@DESELECT` | | select everything / clear the selection |
| `@ROTATE` | `deg` | rotate the selected furnishings |
| `@MOVETO` | `x y` | move the selection so its first item is centred at (x, y) |
| `@DELETE` | | delete the selection |
| `@ZOOMFIT` | | fit the view to the walls |
| `@OPEN` / `@SAVE` | `path` | load / save a plan |
| `@NEW` | | clear the plan |
| `@SHOT` | `path` | snapshot the canvas (`.svg` is vector, anything else PNG) |
| `@FLOOR` | `name` | switch to a floor |
| `@NEWFLOOR` | `name` | create a floor, or switch to it if it exists |
| `@SHUFFLE` | `on\|off` | set shuffle mode |

**Not carried, because this language already says them:** the existing
`CLICK`, `RCLICK`, `DRAG`, `MOVE`, `PRESS`, `RELEASE` (a mouse chain,
Section 5); `TYPE`, `WAIT`, `ENTER`, `ESC`, the arrows and the shortcut
carets such as `^Z` (`KEY`, Section 6); `TOOL` and the digit tool codes (a
tool letter, Section 4); and `PUP` (`RCLICK`, then `KEY`).

### 14.3 Semantics

- No input is simulated: no mouse, key or modifier event is sent, the
  pointer position does not change, and a key held by `KEYDOWN` stays held
  across the command.
- **Validation** (Section 8.3) adds two errors, found before anything runs:
  an unknown command name, and a wrong number of arguments.
- What an argument must *be* — a number, a catalog id, a file that exists —
  is judged when the command runs. A failure there **aborts the macro** and
  is reported with its line; nothing after it runs, and every held key is
  released.
- Canonical form (Section 10): `@NAME`, a single space between arguments,
  each argument bare unless it must be quoted.

### 14.4 Example

```
; fpmacro 2
@WALL 0 0 240 0 ext
@WALL 240 0 240 180 ext
@WALL 240 180 0 180 ext
@WALL 0 180 0 0 ext
@ROOM "Living Room" 120 90
@DOOR 120 0 3680
@PLACE sofa 120 140 0
I CLICK 60 90 +DRAG 177 133     ; and a free-angle wall, by input
@SHOT den.svg
```
