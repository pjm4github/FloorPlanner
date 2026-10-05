# 0218 — report: the legacy converter and the v2 docs built, with two things he asked for mid-session — replay takes whole lines top down, and the recorder window numbers its lines

**Code, 2026‑10‑05.** No merge has happened since
[`0217`](0217-report.md). The work is on branch `macro2-convert`, one PR,
for his check. His words, in order:

> *"continue with where we left off be reading the snapshop"*

— which the snapshot answers with the two things [`0217`](0217-report.md)
§4 left owed: the converter and the docs. Then, while that was being
built:

> *"when I select the lines from the bottom up and then replay the macro,
> it doesnt replay corectly. If I select ftom the top down it works
> correctyly. Check to find the problem - I think you need to make sure
> that when the lines are selected (for replay) that they always play from
> the top down."*

> *"I also want to show line numbers in the macro recorder window so an
> error can highlight the broken line number with an error indicator (when
> that feature is added)"*

## 1. THE CONVERTER — `MACRO_SPEC.md` §11

`floorplanner/macro2/convert.py`, and `python fp_macro.py --convert FILE …`.
It follows `MacroRunner._dispatch` token by token and writes v2 canonical
form; it runs nothing and needs no window. The original is kept beside
the file as `FILE.bak`. A file already in v2 is left alone, so running it
twice is safe; a file whose `.bak` already exists is refused, because
that copy may be the only original.

**Every token of the existing language has a rule**, and a test holds the
converter's word list equal to the engine's own `_cmd_*` handlers, so a
word added there cannot go unconverted unnoticed. The mapping is the
module's docstring; what is not obvious:

| existing | v2 | why |
|---|---|---|
| `^CLICK a b DRAG c d` | `^CLICK a b ^DRAG c d` | the engine put Ctrl on every event of the drag |
| `PRESS … MOVE … RELEASE …` | one chain | v2 never holds the button between lines |
| `^N`, `^A` | `@NEW`, `@SELECTALL` | **measured:** Ctrl+N's action asks before discarding, and the app has no Ctrl+A action at all; `KEY ^n` / `KEY ^a` would not do what the engine did |
| `^+Z` | `KEY ^y` | **measured:** Ctrl+Shift+Z is not a Redo shortcut on Windows |
| `PUP x y keys…` | `RCLICK x y`, then `KEY` / `TYPE` lines | §14.2's own reading |
| `TYPE "a  "` | `TYPE a`, `KEY {Space} {Space}` | §6.1 |
| `# comment` | `; comment` | |

**What has no v2 form is reported and stays in the file** (§11: *"report
it and do not drop it silently"*): a `; NOT CONVERTED (line N): … — reason`
comment where it stood, the same line in the JSON report, exit code 1.
Those are a `PRESS` with no `RELEASE` after it, a `RELEASE` alone, a bare
`^F` (`@FLOOR` needs the name), and anything the engine itself would have
refused. The file is still rewritten and is still a valid v2 macro.

**Two conversions are reported as notes, because they are now real
input:** `^S` (with no current file Ctrl+S opens Save As, where the engine
skipped it) and `RCLICK` (v2's right click opens the context menu; the
engine sent the button alone).

**One thing the converter cannot know, said as a limit:** `PUP` closed
whatever menu or dialog was still open when its keys ran out. Whether
anything is cannot be told without running it, so a closing `KEY {Esc}`
is written only where the key list did not end in `ENTER` or `ESC`.

### The receipt

All **eight** committed existing-format `.fpm` files convert with nothing
unconverted and no note ([`0217`](0217-report.md) §4 expected eight; a
test asserts the table is every such file in `examples/` and `fixtures/`).
Each is then replayed twice — the existing engine on the file as
committed, the v2 player on its conversion, each on its own window — and
**the two plans are byte-identical** (`snapshot()`, canonical JSON), with
the wall count pinned so the equality is not two empty plans. One of the
eight, `disappearingroof.fpm`, does end at zero walls on both: it closes
with `S ^Z`, and with no pause between steps the undo takes all of it.

**The committed `.fpm` files are not converted and not touched** — the
plan's own line ([`0212`](0212-report.md) §4), and tests pin them as they
are.

## 2. THE DOCS

`docs/macro_language.md` gains a *Macro language v2* section (the line
forms in one table, what differs in behaviour, converting), the
`--convert` option, and the recorder's v2 tick-box. **The "three stale
lines" of [`0217`](0217-report.md) §4 were never enumerated on the
record**, so what was fixed is what could be checked against the code:
`TOOL <name>` listed six of the eight names; the recorder was said to
write tool changes as `1`–`6` (it writes letters); and the shortcut table
omitted the five that carry a value (`^O`, `^+S`, `^F`, `^+F`, `^H`).

## 3. REPLAY FROM THE BOTTOM UP — his report

**What the code did:** `replay()` took `cursor.selection().toPlainText()`.
Qt returns that in document order whichever way the selection was
dragged, so **the lines were never played in reverse**. What a bottom-up
drag changes is where the selection *ends*: at wherever the mouse stopped
in the top line, which is rarely its first column. Half a line is a
different macro — `LICK 120 120 DRAG …` is three tool letters and an
error, and in v2 one error stops the whole macro. A top-down drag has the
same fault at its other end; it is only less often hit.

**I did not reproduce it on his screen; this is the mechanism the code
has, and the fix covers his own reading as well:** `_selected_lines`
takes **every line the selection touches, whole, in document order**. A
selection that stops at the very start of a line does not take that line.
Both formats. Four tests, all RED against the code as it was — three
selections of the same two lines (top-down mid-line, bottom-up mid-line,
bottom-up to a line start) must replay the same text.

If it still misbehaves selected bottom-up, the mechanism is something
else and I need the macro text and what it did.

## 4. LINE NUMBERS — his request

The recorder window's editor is now `MacroEdit`: a gutter on the left,
one number per macro line, 1-based — **the way a v2 error already counts**
(`line 3:0 …`), which a test ties together. It widens with the count and
follows the scroll. Wrapped lines keep wrapping as before; the number
sits at the line's first row.

**Not built, as he said it:** the error indicator. The gutter is where it
goes, and a v2 error carries its line; the existing language's errors
carry a token, not a line, so that half needs a decision when it is
built.

## 5. STATE

Macro suites green; `ruff` clean; the full gate is this commit's own run
and the PR's. `MacroRunner` is untouched: every change in
`floorplanner/macro.py` is in the recorder dialog.

**For his check (AMBER):** in Macro ▸ Record / Debug — the numbers in the
gutter; select some lines from the bottom up and Replay; and, if he
wants, `python fp_macro.py --convert` on a copy of a macro of his.

## 6. `fixtures/incoming/`, with ages

`single-floor-90-roof-gable-end-check.json` — his own, 2026‑10‑03, exit
not yet named ([`0205`](0205-report.md) §3). `README.md`.

**Untracked, not mine, untouched:** `gen/` and
`docs/macro-spec/grammar/gen/`; and my own uncommitted draft
`docs/WORKING_AGREEMENT.proposed.md`. A `git stash` entry from an earlier
session (`WIP on main: 863204a`) is still in the stash list; not touched.

## 7. WHAT HAPPENS NEXT

His check of the PR. With it the spec's six tasks are done. Behind it,
untouched since [`0211`](0211-report.md) §4: the error indicator he named
here, the D67 pair, the four-way crossing fault, parallel walls 6″ apart
merging, the status board, and the plan in `incoming/`.

**Carried:** unchanged from [`0217`](0217-report.md).
