# 0214 — report: PR #72 merged (GREEN, on green CI); macro language v2, T2 — the player; the modifier leak measured exactly and guarded; AMBER, stopped for his check

**Code, 2026‑10‑04.** The record ([`0197-ruling.md`](0197-ruling.md) §7):
**PR #72, macro v2 T1, is merged** — GREEN tier, so on green CI rather
than on his word ([`ROADMAP.md`](../ROADMAP.md) §1): CI's `ruff` job and
its full-gate job both passed on the PR, and `macro2-language` was landed
on `main` at **`504d6d7`**, fast-forward, the branch deleted local and
remote in the same step.

His next word: *"proceed with the second tranche."* Branch
`macro2-player` off `main` at `504d6d7`,
[PR #73](https://github.com/pjm4github/FloorPlanner/pull/73) open, gate
GREEN, **stopped for his check** (§5).

## 1. WHAT'S BUILT

A macro whose first non-blank line is `; fpmacro 2` now **runs**.
Anything else runs on `MacroRunner` exactly as before — `run_macro`
chooses by that line and changes nothing else.

```
text ─► parse ─► AST ─► validate ─► expand ─► [InputEvent] ─► QtEventSink
```

* **`floorplanner/macro2/sink.py`** turns an abstract event into a
  `QMouseEvent`, `QKeyEvent` or `QWheelEvent` and sends it: mouse and
  wheel to the canvas viewport, keys to whatever holds the keyboard.
  Coordinates are scene inches through `view.mapFromScene`, so the same
  macro draws the same wall at 0.25× and 2× (tested).
* **`floorplanner/macro2/player.py`** validates the whole macro first —
  *nothing runs unless it is valid* ([`MACRO_SPEC.md`](../macro-spec/MACRO_SPEC.md)
  §8.3) — then delivers. It returns the dict `run_macro` always
  returned, plus `warnings`.
* **`CLAUDE.md`**'s rule against synthesizing Ctrl-modified key events
  names the v2 sink as its one sanctioned exception, as he ruled
  ([`0212`](0212-report.md) §3).
* **The recorder dialog** replays a v2 macro as **one** macro, where it
  replays the existing language a line at a time: in v2 a `KEYDOWN` holds
  across lines and a dialog one line opens is driven by the next.

## 2. FOUR THINGS MEASURED AT THE BUILD — each changed the design

**(a) The modifier leak, exactly.** `CLAUDE.md` says only that
synthesizing Ctrl-modified key events *"leaks
`QApplication.keyboardModifiers()`."* With `sendEvent`, to any widget:

| event sent | global modifier state afterwards |
|---|---|
| KeyPress of a **modifier key itself** (`Key_Control` carrying Ctrl) | unchanged |
| KeyPress of an **ordinary key** carrying Ctrl (`Z` + Ctrl) | **Ctrl — and it stays** |
| its KeyRelease; the modifier's KeyRelease; a mouse event with flags | unchanged — **none of them clears it** |
| a later KeyPress carrying no modifier | cleared |

So the leak is one event, and one event undoes it. **The guard**
(`_sync_global`): after every key event the sink compares the global
state with the modifiers the macro actually holds and, when they
differ, sends one KeyPress of `Key_unknown` carrying the right set to a
**private widget that is never shown**. Two consequences, both wanted:
the global state is clean when a macro ends or aborts; and during the
macro it **follows** it — a widget reading `keyboardModifiers()` inside a
`+DRAG` sees Shift, which §7 asks for (tested from inside the app).
Removing the guard leaks Ctrl, checked by mutation.

**(b) A drag came out 18″ long instead of 240″.** The spec says to call
`processEvents()` after each delivered event; doing so between a drag's
interpolated moves let the pump's next timer fire mid-drag, and the
release arrived after the first move. Each interpolated move is now its
own pump step and nothing is delivered between them.

**(c) `KEY ^z` straight after a drag did nothing.** Two reasons. A key
press delivered with `sendEvent` never reaches Qt's shortcut map; and
Undo is disabled until the app's 180 ms settle timer commits the
gesture, which a person's hand always outlasts and a macro never does.
The sink now does, in Qt's own order, what Qt does for a real key
press: offer the widget a `ShortcutOverride`; if it declines, find the
window's enabled `QAction` with that shortcut and trigger it; otherwise
deliver the KeyPress — and it settles the pending gesture first.

**(d) Delivery is a timer-driven pump.** A click that opens a door's size
prompt does not return until the prompt closes. The pump schedules the
next step before delivering the current one, so `TYPE 2868` and
`KEY {Enter}` are delivered from inside the dialog's own loop — the
mechanism `PUP` has always used. A macro that ends with a dialog or a
menu still open has it closed, with a warning, instead of hanging.

## 3. THE CHECK — receipts

`tests/test_macro2_player.py`, **21 tests** (`macro`, `gui`). An autouse
fixture asserts **after every one** that no modifier is left down.

* **The Shift-drag lands off the grid** — `I CLICK 120 120 +DRAG 355 133`
  ends at the cursor, to within a pixel; the same line without `+` ends
  at (354, 120). This is the gesture [`0210`](0210-report.md) §1 could
  not get from a recorded macro.
* A modifier that changes partway through a chain; `KEYDOWN {Shift}`
  doing what a `+` prefix does; a drag being many small moves.
* `KEY ^z` undoes and `KEY ^y` redoes; an arrow reaches the canvas and
  nudges a furnishing; **a door placed by driving its size dialog**; a
  dialog left open is closed and reported; a right click opens the
  context menu and keys drive it; the wheel zooms.
* The spec's own §13 example, verbatim, runs clean.
* An aborted macro — a failure mid-chain with Ctrl held and Shift down —
  reports its line, delivers nothing more, and leaves nothing down.
* A macro without the header still runs on the existing engine, two
  commands on a line and a `#` comment included; the existing words are
  errors in v2, and nothing runs.
* The check macro (§5), replayed verbatim.

**Every existing macro test passes unmodified.** Full suite **1513
passed**, 7 deselected (`perf` lane), `ruff` clean, gate GREEN — the
branch's own run.

## 4. NAMED

* **A shortcut is a shortcut.** `KEY ^o` opens the real Open dialog and
  `KEY ^n` clears the plan, as the keys do. With the canvas focused,
  `TYPE Select` presses `S`, `E`, … and so changes the tool — again as the
  keys do. `TYPE` is for a text field.
* **Mouse precision is one pixel.** A point is mapped to a viewport pixel
  and back, so a Shift-drag's end is the cursor to within a pixel — 2″ at
  the default zoom — exactly as a hand's would be. A constrained drag
  lands on the grid regardless.
* **The spec's `examples.macro` cannot be run**: its last line uses tool
  `X` ([`0213`](0213-report.md) §2). §13's example is what the test runs.
* **Not yet:** the v2 recorder and the legacy converter — T3.

## 5. HIS CHECK

On an **empty plan**: Macro ▸ Record / Debug ▸ **Load…**
`fixtures/macro2-player-check.fpm` ▸ **Replay**. The file's own comments
say what each step must do:

1. a wall on the grid along y = 10′;
2. a Shift-drag whose end is off the grid and not square;
3. one press, a constrained segment and then a free one;
4. a door on wall 1, its size dialog opened, typed into and accepted;
5. the Select tool.

Then anything of his own — a macro only needs `; fpmacro 2` as its
first line.

## 6. `fixtures/incoming/`, with ages

`single-floor-90-roof-gable-end-check.json` — his own, 2026‑10‑03, exit
not yet named ([`0205`](0205-report.md) §3). `README.md`.

## 7. WHAT HAPPENS NEXT

His check (§5). On his word PR #73 merges, branch deleted in the merge
step, the merge recorded in the report that follows. Then T3: the v2
recorder, the legacy converter and the docs. **Still his to answer**
before T3 is shaped: whether v1's high-level commands come into v2, and
in which form ([`0213`](0213-report.md) §4) — it decides whether the v2
recorder records a door as raw input or as one command.

**Carried:** unchanged from [`0213`](0213-report.md).
