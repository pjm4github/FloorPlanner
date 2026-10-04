# 0212 — READ-BACK: macro language v2 — the existing macro feature surveyed, ten conflicts with the v2 grammar, his three answers, and the plan in three tranches

**Code, 2026‑10‑04.** No merge has happened since
[`0211`](0211-report.md). No code is changed by this commit.

## 0. HIS INSTRUCTION

The four files staged under `docs/macro-spec/` since
[`0210`](0210-report.md) §7 are his: a specification
([`MACRO_SPEC.md`](../macro-spec/MACRO_SPEC.md)), two ANTLR grammars and
an example macro. His instruction:

> *"Implement the macro language described in @docs/macro-spec/MACRO_SPEC.md,
> using the grammar in @docs/macro-spec/grammar/MacroLexer.g4 and
> @docs/macro-spec/grammar/MacroParser.g4. Follow the tasks in Section 1
> in order. Start with Task 1 (survey the existing macro feature) and
> Task 2 (conflict check), and report what you find, including the
> current tool-letter table and file format, before proposing an
> implementation plan."*

The spec's own Task 2: *"Check for conflicts and stop if you find any …
list the conflicts and ask before proceeding."* There were conflicts; I
stopped and asked; §3 is what he answered.

**Why this exists, in this arc's own terms:** today's macros cannot
express a Shift-drag — the recorder never records Shift on the mouse —
which is why [`0210`](0210-report.md) §1 could not reproduce his
grid-snap report from the macro he recorded.

## 1. TASK 1 — the existing macro feature

| | |
|---|---|
| engine | `floorplanner/macro.py`, `MacroRunner` (line 56); entry `MainWindow.run_macro(text)` (`mainwindow.py:2068`); CLI driver `fp_macro.py` |
| recorder | `MacroRecorderDialog` (`macro.py:695`): an application-wide `eventFilter` that never consumes events, **plus** eleven semantic hooks the app calls — `on_tool`, `on_place`, `on_popup`, `on_opening`, `on_dormer`, `on_open`, `on_save_as`, `on_shuffle`, `on_floor`, `on_new_floor`, `on_room` |
| documented in | [`docs/macro_language.md`](../macro_language.md) |
| **file format** | **`.fpm`, UTF‑8, no header line, no version marker, no version detection anywhere** |
| syntax | a **flat stream of whitespace-separated tokens** (`_tokenize`, `macro.py:168`). Lines exist only to cut `#` comments; several commands share a line (`S ^Z`). A token may be double-quoted. Command words are upper-cased before dispatch, so they are case-insensitive |
| numbers | decimal inches, or feet-inches: `10'`, `12'6"` (`_num`, 177) |
| errors | a bad token is logged and **skipped**; the macro carries on (`run`, 149) |
| coordinates | scene inches through `view.mapFromScene` — the same as the spec's §5.1 |
| mouse delivery | `QMouseEvent`s sent to the viewport (`_mouse`, 290); a drag is press, **2** moves, release; a modifier is a **flag on the mouse events only** — no key event is sent |
| keyboard | shortcuts and arrows **call app methods** (`CARET_SHORTCUTS`, `nudge_selected`); only `ENTER` and the keys of a `PUP` are real key events |

**The tool-letter table** (`_TOOL_CODES`, `macro.py:120`):

| letter | tool | | letter | tool |
|---|---|---|---|---|
| `S` | select | | `W` | window |
| `E` | exterior wall | | `R` | room |
| `I` | interior wall | | `G` | roof ridge |
| `D` | door | | `M` | roof dormer |

Also accepted: the legacy digits `1`–`6` (`_DIGIT_TOOLS`) and
`TOOL <name>` with eight names. The recorder emits letters only.

**The vocabulary**, 25 `_cmd_*` handlers and the dispatch: `CLICK`,
`^CLICK`, `RCLICK`, `MOVE`, `PRESS`, `RELEASE`, `DRAG` (two numbers
after a `CLICK`, or four on its own), `PLACE`, `WALL`, `DOOR`, `WINDOW`,
`DORMER`, `ROOM`, `SELECT`, `SELECTALL`, `DESELECT`, `ROTATE`, `MOVETO`,
`ZOOMFIT`, `PUP` with its key list, `TYPE "text"`, `OPEN`, `SAVE`,
`NEW`, `SHOT`, `WAIT`, the arrows, `ESC`, `ENTER`, `DEL`; the caret
commands `^N ^Z ^Y ^X ^C ^V ^G ^+G ^A ^S`, and five that take a quoted
argument: `^O "path"`, `^+S "path"`, `^F "name"`, `^+F "name"`,
`^H "on|off"`.

**What depends on it:** 8 committed `.fpm` files, which between them use
only `CLICK`/`DRAG`, tool letters, `^Z`, and in two files `^O`, `^F`,
`^+F`; and 12 test files with about 85 `run_macro` calls
(`tests/test_macro.py` alone 55).

**ANTLR:** none in the repository. `requirements.txt` pins PyQt6 and
numpy; CI installs `requirements-dev.txt`.

**The recorder does not record Shift on the mouse** — only Ctrl, at
press time, as `^CLICK`. A Shift wall-drag is lost.

## 2. TASK 2 — conflicts

**The spec's own stop conditions are met:**

1. **Digits and a multi-character tool code exist**: `1`–`6` and
   `TOOL <name>`. The eight tool letters are single uppercase letters and
   do not conflict.
2. **Three words collide with a v2 keyword of a different meaning:**
   `TYPE "text"` (quoted; v2 types the quotes), `WAIT` (no argument; v2
   requires milliseconds), a stand-alone `DRAG x1 y1 x2 y2` (v2 allows
   `DRAG` only inside a chain).

**Beyond those:**

3. `#` is the comment character today; in v2 it is the Meta modifier and
   `;` is the comment.
4. Many commands per line today; one per line in v2.
5. About thirty commands have no v2 form: the whole high-level and file
   vocabulary, and the five caret commands that take an argument.
6. **v2 §7 requires real modifier key events, and `CLAUDE.md` forbids
   them**: *"never synthesize Ctrl-modified key events — it leaks
   `QApplication.keyboardModifiers()`; route shortcuts/arrows through
   app methods (as `MacroRunner` does)."* Separately, a key press
   delivered by `sendEvent` does not reach a `QAction` shortcut, so
   `KEY ^z` would not undo without more work.
7. **Modal dialogs.** Today's recorder bakes a dialog's result into one
   token (`DOOR x y 3280`) so replay never opens it. A raw-input replay
   must drive `QDialog.exec()`, which blocks the caller.
8. Skip-and-continue today; validate-everything-then-abort in v2.
9. A new dependency: the ANTLR tool (Java) and its Python runtime.
10. Small: the spec names `grammar/examples.macro`; the file is at
    `docs/macro-spec/examples.macro`. Its last line uses tool `X`, which
    no tool has — it parses and fails validation, as §8.3 intends.

## 3. HIS THREE ANSWERS

Asked as three questions, each with a recommendation; he chose:

| question | his answer |
|---|---|
| How should v2 relate to the existing language? | **Side by side.** v2 is a second format, detected by its first line `; fpmacro 2`. Files without it run on today's engine unchanged |
| v2 §7 against `CLAUDE.md`: which wins? | **Follow the spec, guard the leak.** Real modifier key events, always released, with tests that the modifier state is clean afterwards; `CLAUDE.md`'s rule is amended to name the v2 player as the one sanctioned place |
| How should the parser be built? | **ANTLR, generated code committed**, so CI and users need the pinned runtime and not Java |

He then approved the plan below.

## 4. THE PLAN — three tranches, one open at a time

A new package, `floorplanner/macro2/` (the spec's suggested `macro/`
would sit beside `floorplanner/macro.py`): generated parser, AST,
validation, a pure expansion to abstract input events, a serializer, a
Qt event sink, a player, a recorder state machine and a legacy
converter. `MacroRunner` and the committed `.fpm` files are not touched.

* **T1 — the language, no Qt delivery (GREEN).** Commit his four spec
  files as they are; generate and commit the parser; AST, validation,
  expansion, serializer; the spec's tests 1–8 and a test that the
  generated code matches the grammar's hash, so a grammar edit without
  regeneration goes red without CI needing Java.
* **T2 — the player (AMBER, his check).** Delivery to Qt, the modifier
  guard, `run_macro` choosing the engine by the first line, the
  `CLAUDE.md` amendment. The receipt this arc wants: **a Shift-drag
  macro lands off the grid.**
* **T3 — the recorder, the converter, the docs (AMBER, his check).**

**Named in the plan and to be measured, not assumed:**

* **The ANTLR version.** The spec says 4.11.1. I believe that runtime
  imports `typing.io`, which Python 3.13 removed, and this repository
  requires 3.13. T1's first step checks it; if it does not import, 4.13.2
  for both tool and runtime, said in the report.
* **Shortcut strokes.** Whether `QTest.keyClick` both fires a `QAction`
  shortcut and leaves the modifier state clean; if not, the sink resolves
  the stroke to the action with that shortcut and triggers it.
* **Dialogs.** The player delivers events from a timer inside a local
  event loop — the mechanism `PUP` already uses — so that `TYPE` and
  `KEY {Enter}` reach a dialog a mouse release opened. If a dialog cannot
  be driven, that is reported as a limit.
* **The eight committed `.fpm` files stay legacy**; tests pin them.

## 5. `fixtures/incoming/`, with ages

`single-floor-90-roof-gable-end-check.json` — his own, 2026‑10‑03, exit
not yet named ([`0205`](0205-report.md) §3). `README.md`.

## 6. WHAT HAPPENS NEXT

T1, on branch `macro2-language`.

**Carried:** unchanged from [`0211`](0211-report.md).
