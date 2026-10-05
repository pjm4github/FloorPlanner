# 0216 — report: the v2 recorder, built on his report that Shift is not captured; the commands check ran on his screen; three branches stacked, one PR open

**Code, 2026‑10‑04.** No merge has happened since PR #72
([`0214`](0214-report.md)). **PR #73, the player, is still open.**

## 1. HIS REPORT

He ran `fixtures/macro2-commands-check.fpm`, then recorded more on top
of it, and sent the screen:

> *"here is the result of replaying the macro then I added more objects,
> an interior wall and an exterior wall. The one issue I see is that the
> shift key is not captured in the recorder"*

**What the screen shows.** The commands check did what its comments say:
four exterior walls, the room named *Living Room*, a door labelled
*3680*, a sofa and an armchair, the free-angle interior wall, *"Stopped."*
Below the macro, the lines he then recorded:
`I CLICK 212 87 DRAG 395 84`, `E CLICK 393 2 DRAG 409 179`, and a run of
plain `CLICK`s — **no `+` anywhere.**

**Why, exactly.** That recording was made by the *existing* recorder.
[`0214`](0214-report.md) §4 said *"Not yet: the v2 recorder"*; what it
did not say is what would happen in the meantime, which is what he hit:
the existing recorder records only Ctrl on the mouse
([`0212`](0212-report.md) §1), and it was **appending its own format to
a v2 macro**. Those lines happen to be valid v2, so nothing complained,
and the Shift he held was simply gone. His report is correct and the
gap was mine to have named.

His screen is a result, **not a word**: no merge has been asked for.

## 2. WHAT'S BUILT — on branch `macro2-recorder`, stacked on `macro2-commands`

**`floorplanner/macro2/recorder.py`** — the state machine of
[`MACRO_SPEC.md`](../macro-spec/MACRO_SPEC.md) §9, **Qt-free**: it is
handed plain values (a button name, scene coordinates, a set of
modifiers, a key) and writes canonical v2 lines. So each rule is tested
without a window.

| what he does | what is written |
|---|---|
| drags a wall | `I CLICK 120 120 DRAG 360 120` |
| holds Shift for the whole drag | `I +CLICK 120 120 +DRAG 355 133` |
| **presses Shift partway through** | `I CLICK 120 240 DRAG 300 244 +DRAG 355 253` — the segment closes where the pointer was, with the modifiers it had |
| releases a modifier partway | `^CLICK 10 10 ^DRAG 100 10 DRAG 100 90` |
| clicks with a wobble of a few pixels | `CLICK 50 50` — at the press point; the threshold is `startDragDistance()` in **view pixels**, so it does not depend on zoom |
| double-clicks | the `CLICK` just written becomes `DCLICK`; a drag after it becomes its segments |
| middle-drags, right-clicks, turns the wheel | `MCLICK … DRAG …`, `RCLICK x y`, `MOVE x y` then `WHEEL dx dy` |
| changes tool | the letter prefixes the next line; one still pending at Stop gets a line of its own |
| types in a menu's dialog | `TYPE 28 68`, the trailing space as `KEY {Space}`, sharing its line with the stroke that follows |
| places a door, names a room, sketches a dormer, opens a file, switches floor | **one application command** — `D @DOOR 120 0 3280`, `@ROOM "Living Room" 120 90` — from the app's own hooks, so replay opens no dialog |

**The dialog.** Macro ▸ Record / Debug feeds the recorder from the event
filter it already had; the careful key de-duplication of the existing
recorder is reused, not rewritten, and v2 branches off only where a
line is written.

* **v2 is the default** when the application opens the dialog; a
  checkbox says so and turns it off.
* **A macro already in the editor keeps its own format.** Load a v2 file
  and record: v2. Load a legacy one: the existing recorder, unchanged.
  One file is one language — which is exactly what went wrong on his
  screen, and is now a test.
* On the canvas a key is a `KEY` stroke — except a tool's own key (the
  tool hook writes the letter) and Open, Save As, floor and shuffle
  chords (their hooks write `@OPEN "path"` and the rest, with the value
  a bare `^o` could not carry). `Ctrl+N` is written `@NEW`.
* Coordinates keep the precision a pixel has: whole inches at an
  ordinary zoom, a decimal when zoomed in.

## 3. THE CHECK — receipts

`tests/test_macro2_recorder.py`, **29 tests**. Twenty-one drive the
state machine with plain values — the rules of §9 one by one, the last
of them asserting that everything it writes parses and is already
canonical. Eight go through the dialog with real events:

* **His report:** Shift pressed partway through a wall drag is recorded
  as a `+DRAG` segment, and **replaying the recording on a fresh plan
  draws the same off-grid wall** (§12 item 9, both halves).
* A string typed with a trailing space, in a dialog a right click opened.
* **A recording added to a v2 macro stays v2**; a legacy macro in the
  editor keeps the legacy recorder.
* The hooks write application commands; a double click and the wheel;
  canvas keys; the application opens the dialog in v2.

Every existing recorder test passes unmodified (the constructor's
default is still legacy). Full suite **1581 passed**, 7 deselected
(`perf` lane), `ruff` clean, gate GREEN — the branch's own run.

**A slip of mine in a test, found and fixed:** my first version released
the mouse somewhere the pointer had not been moved to, and the replay
disagreed with the recording by 15″. A real mouse cannot do that; the
app places a wall's end on *move*, not on release. The test now moves
there first. The recorder and the player were right.

## 4. NAMED — limits, none hidden

* **The roof ridge's End-On dialog is not recorded.** Its values are set
  by clicking in the dialog, and clicks inside dialogs are not recorded
  (nor were they before). A recorded ridge replays the sketch and then
  the player closes the open dialog with a warning. A door, a room and a
  dormer do not have this problem — their hooks bake the value in.
* **Hover is off, waits are off.** Both are in the recorder
  (`hover=True`, `wait_ms=…`) and neither has a control in the dialog.
* **Zoom is recorded** (the wheel, the middle-button pan). It replays,
  and it means a recording carries the view changes made during it.
* **Still owed of T3:** the legacy converter (`fp_macro.py --convert`)
  and the v2 section of `docs/macro_language.md`.

## 5. THE STACK — said plainly, because it is unusual

| branch | holds | state |
|---|---|---|
| `macro2-player` | T2, the player | **PR #73, open, AMBER** — CI green |
| `macro2-commands` | application commands | pushed, stacked on the player, no PR |
| `macro2-recorder` | the v2 recorder | pushed, stacked on commands, no PR |

One AMBER tranche open at a time ([`0186`](0186-ruling.md) §5), so the
upper two wait. On his word each lands in turn — #73; then `main` into
`macro2-commands`, its PR, his check; then the same for the recorder.
**Or, if he would rather check them as one**, his word to fold the three
into #73 does that; I have not presumed it.

The working checkout is left on **`macro2-recorder`**, which contains
all three, so what he runs is the whole of it.

## 6. `fixtures/incoming/`, with ages

`single-floor-90-roof-gable-end-check.json` — his own, 2026‑10‑03, exit
not yet named ([`0205`](0205-report.md) §3). `README.md`.

**Also in the working tree, not mine and not touched:** two new
untracked directories, `gen/` at the repository root and
`docs/macro-spec/grammar/gen/` — the default output folder of an IDE's
ANTLR plug-in, by the look of them. The parser this project uses is the
committed one in `floorplanner/macro2/_generated/`.

## 7. WHAT HAPPENS NEXT

His word on the stack (§5). Then the converter and the docs.

**Carried:** unchanged from [`0215`](0215-report.md).
