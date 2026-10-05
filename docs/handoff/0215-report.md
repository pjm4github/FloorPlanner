# 0215 — report: application commands, `@NAME arg …` — v1's high-level commands carried into v2 on his word; his grammar and spec extended; built stacked on the player, no PR until #73 merges; his question on the check macro's step 3

**Code, 2026‑10‑04.** No merge has happened since PR #72
([`0214`](0214-report.md)). **PR #73, the player, is still open and
waiting on his check.**

## 1. HIS WORD, AND WHY THERE IS NO SECOND PR

[`0214`](0214-report.md) §7 left one question with him. His answer:

> *"Yes carry v1's high level commands as a single command uing the form
> @COMMAND"*

Built, on branch **`macro2-commands`**, which is **stacked on
`macro2-player`** — it needs the player's sink — and **pushed without a
PR**. The standing rule is never two AMBER tranches open at once
([`0186`](0186-ruling.md) §5), and #73 is open. When #73 merges, `main`
is merged into `macro2-commands`, its PR opens, and it stops for his
check. Gate GREEN on the branch.

## 2. HIS GRAMMAR AND HIS SPEC WERE CHANGED — on that word, and here is exactly how

The grammar is his and [`MACRO_SPEC.md`](../macro-spec/MACRO_SPEC.md) §1
says *"do not silently change the `TOOL` lexer rule."* `TOOL` is
untouched. What was added:

* **`MacroLexer.g4`** — one rule in the default mode,
  `APPCMD : '@' [A-Z] [A-Z0-9_]* -> pushMode(ARG_MODE)`, and a new
  `ARG_MODE` with a quoted string, a bare word, whitespace, a `;`
  comment and the newline that pops the mode.
* **`MacroParser.g4`** — `appCommand : APPCMD appArg*` with
  `appArg : ASTRING | AWORD`, added as the ninth alternative of `command`.
* **`MACRO_SPEC.md`** — a new **§14, "Application commands"**, dated and
  attributed to his instruction; one bullet in §2; one sentence in §3.2.
  Nothing existing was reworded.
* **`examples.macro`** — three lines appended after the existing last
  line, so every earlier line keeps its number.

The parser was regenerated; the hash test that pins it to the grammar
was red in between, which is what it is for. **The eleven rejection
cases of §12 still reject, and the example still parses with zero
errors.**

## 3. WHAT'S BUILT

```
@PLACE sofa 120 96 0
@ROOM "Living Room" 10' 12'6"
S @SELECT 120 96        ; a tool letter may lead; a comment may follow
```

* **The `@` is what makes it parse.** Without it `DOOR` is the tool
  letters `D O O R`, and two on a line is an error — tested.
* **An argument** is a bare word or a double-quoted string. A bare word
  may *contain* a quote, so the feet-inches length `12'6"` is one
  argument, as in the existing language.
* **Twenty commands** (`floorplanner/macro2/appcmd.py`): `PLACE WALL
  DOOR WINDOW ROOM DORMER SELECT SELECTALL DESELECT ROTATE MOVETO DELETE
  ZOOMFIT OPEN SAVE NEW SHOT`, and three that were caret commands with an
  argument: `@FLOOR name` (`^F`), `@NEWFLOOR name` (`^+F`),
  `@SHUFFLE on|off` (`^H`).
* **They are run by the existing language's own handlers.** The player
  hands the arguments to `MacroRunner._dispatch` as its token stream.
  Nothing about `PLACE` or `DORMER` is written twice; a test builds the
  same scene both ways and compares the documents.
* **Validation, before anything runs:** an unknown name, or a wrong
  number of arguments. **What an argument must *be*** — a number, a
  catalog id, a file that exists — is judged when the command runs; a
  failure there aborts the macro with its line, and nothing after it
  runs.
* **No input is simulated**: no event, no pointer move; a key held by
  `KEYDOWN` stays held across a command.

**Not carried, deliberately** (§14.2), because v2 already says them: the
existing `CLICK`, `RCLICK`, `DRAG`, `MOVE`, `PRESS`, `RELEASE` (a mouse
chain); `TYPE`, `WAIT`, `ENTER`, `ESC`, the arrows and `^Z`-style carets
(`KEY`); `TOOL` and the digits (a tool letter); `PUP` (`RCLICK` then
`KEY`). **One thing this loses, named:** the existing `PRESS` and
`RELEASE` hold a button *across* lines, and v2 by design never does
(§2: *"the mouse button is never held between lines"*).

**One second list, admitted.** [`0213`](0213-report.md) §4 said the
argument counts would be checked against `MacroRunner`'s own handler
table, *"not a second list."* The handlers carry no such table — each
takes what it needs from the token stream — so `appcmd.COMMANDS` holds
the counts. It is pinned three ways: every name must resolve to a
handler the existing language has; each command is run; and a handler
that does not consume every argument it was given is an error, so a
count the table lets through wrongly cannot pass silently.

## 4. THE CHECK — receipts

`tests/test_macro2_commands.py`, **39 tests**: the grammar (quoting,
feet-inches, comments, a leading tool letter, five malformed forms,
CRLF); eight positioned validation errors; the canonical form and round
trip; and through a window — §14.4's own example building a furnished
room with one wall drawn by input in the same macro; the same scene by
command and by the existing words, compared; selection, editing, save,
new and reopen; floors and shuffle; a dormer; a command failing at run
time; a wrong count stopping the macro before it starts; and the check
macro, verbatim.

Full suite **1552 passed**, 7 deselected (`perf` lane), `ruff` clean,
gate GREEN — the branch's own run. Every existing macro test and both
earlier v2 test files pass, the latter with one number changed (the
example is 26 lines now).

## 5. HIS QUESTION ON THE PLAYER'S CHECK MACRO

He ran `fixtures/macro2-player-check.fpm` and sent the screen: a wall
along y = 10′ with a door labelled *2868 LH*, a second wall sloping
slightly down to the right, a third running diagonally, the Select tool
active, *"Replay complete."* His question:

> *"Im curious if the MACRO actually correctly drew the correct wall
> using the example macro. In particular what should the step 3 in teh
> macro look like, should that be 2 visible segments?"*

**What his screen shows is correct, and step 3 is one wall, not two.**
`I CLICK 120 360 DRAG 300 364 +DRAG 301 451` is one press and one
release. The wall tool draws a single straight wall from where the
button went down to where the cursor is; the middle point (300, 364) is
only somewhere the cursor passed on the way. So the result is one wall
from (120, 360) to (301, 451) — the diagonal in his picture. What the
two segments change is not the shape but the **rule in force at the
release**: the second segment holds Shift, so the end is placed at the
cursor, off the grid, where a plain drag to the same point would have
been pulled square. Two visible walls need two chains, each its own
`CLICK … DRAG`.

**The fault was my comment, not the macro.** It read *"one press, two
segments: constrained to (300,..), then free to (301,451)"*, which
invites exactly the reading he gave it. Reworded in the fixture (on
`macro2-commands`) to say that it is one wall and why.

His screen is a result, **not a word**: he has not said the check
passed or to merge, and PR #73 stays open.

## 6. `fixtures/incoming/`, with ages

`single-floor-90-roof-gable-end-check.json` — his own, 2026‑10‑03, exit
not yet named ([`0205`](0205-report.md) §3). `README.md`.

## 7. WHAT HAPPENS NEXT

His word on PR #73. On it #73 merges, `main` is merged into
`macro2-commands`, **its PR opens**, and it stops for his check with
`fixtures/macro2-commands-check.fpm`. Then T3 — and with application
commands in the language, **the v2 recorder can write a door as
`@DOOR x y 3280`**, as the existing recorder does, and the legacy
converter can carry every one of the eight committed `.fpm` files.

**Carried:** unchanged from [`0214`](0214-report.md).
