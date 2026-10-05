# 0217 — report: PR #73 merged on his word, three tranches folded into it — macro language v2 runs, takes application commands and is recorded

**Code, 2026‑10‑05.** The record ([`0197-ruling.md`](0197-ruling.md) §7):
[`0216`](0216-report.md) §5 put two ways to land the stack to him and
presumed neither. His word:

> *"fold all three into #73 and merge"*

Done as said. `macro2-player` was fast-forwarded to the tip of
`macro2-recorder` (`eef0ef5`), which carries all three tranches in order
— the player `0f1837e`, application commands `8d7fb17`, the recorder
`eef0ef5` — so **PR #73 held all of them**, and the branch was landed on
`main` at **`7cf8ca3`**, fast-forward. GitHub shows PR #73 MERGED with
four commits. `macro2-player`, `macro2-commands` and `macro2-recorder`
are deleted, local and remote, in the same step.

## 1. WHAT HIS WORD RESTS ON — recorded as it is

He **ran two of the three** and sent the screens: the player's check
macro ([`0215`](0215-report.md) §5 — the three walls, the door, the
Select tool) and the commands check ([`0216`](0216-report.md) §1 — the
furnished room). **The recorder he has not reported on.** It was built
in answer to his own finding that Shift was not captured, it was the
last thing put in front of him, and his next message was the merge
word. So the recorder is merged on his instruction and on its tests —
29, one of which records a Shift pressed mid-drag and replays it to the
same wall — **not on a check of his that is on the record.** If it
misbehaves in his hands, that is the first place to look, and it is its
own small tranche.

## 2. WHAT LANDED

On the merged tree: **1581 passed**, 7 deselected (`perf` lane), `ruff`
clean, gate GREEN.

| | report | what it is |
|---|---|---|
| the player | [`0214`](0214-report.md) | a macro whose first line is `; fpmacro 2` runs: mouse chains with per-segment modifiers, `TYPE` / `KEY` into dialogs, shortcuts, the modifier guard |
| application commands | [`0215`](0215-report.md) | `@NAME arg …`, twenty of them, run by `MacroRunner`'s own handlers; his grammar and spec gained §14 |
| the recorder | [`0216`](0216-report.md) | Macro ▸ Record / Debug records v2 by default: Shift and Alt on the mouse, a modifier changing mid-drag, double clicks, the wheel; dialog-driven actions as one command |

Anything without the `; fpmacro 2` first line still runs on the existing
engine, and every test of it passes unmodified.

## 3. `SESSION_SNAPSHOT.md` — and a rule of mine I had broken again

[`0203`](0203-report.md) wrote into the snapshot: *when a tranche
closes, REPLACE its entry with one line and a link; do not append.*
Over reports 0212–0216 the macro paragraph in §0 had grown by exactly
that appending — four tranches, four bolted-on paragraphs, forty lines.
It is replaced whole by one paragraph in this merge's re-cut. The rule
was right and I did not follow it while the work was in flight; said
here because the file's staleness is how this project lost sessions
before.

## 4. STILL OWED OF THE SPEC

* **The legacy converter** — [`MACRO_SPEC.md`](../macro-spec/MACRO_SPEC.md)
  §11: rewrite an existing-format macro as v2, keeping a `.bak`, and
  report anything with no v2 form rather than drop it. With application
  commands in the language, every one of the eight committed `.fpm`
  files can now be carried, where two could not before.
* **The docs** — a v2 section in `docs/macro_language.md`, and its three
  stale lines ([`0212`](0212-report.md) survey).

**Named limits carried from the three reports,** unchanged: a roof
ridge's End-On dialog is not recorded; zoom and pan are; a shortcut in a
macro is a real shortcut; mouse precision is one pixel.

## 5. `fixtures/incoming/`, with ages

`single-floor-90-roof-gable-end-check.json` — his own, 2026‑10‑03, exit
not yet named ([`0205`](0205-report.md) §3). `README.md`.

**Untracked, not mine, untouched:** `gen/` and
`docs/macro-spec/grammar/gen/` (Java output of an IDE's ANTLR plug-in,
[`0216`](0216-report.md) §6), and my own uncommitted draft
`docs/WORKING_AGREEMENT.proposed.md`.

## 6. WHAT HAPPENS NEXT

The converter and the docs, on his word. Behind them, untouched since
[`0211`](0211-report.md) §4: the D67 pair, the four-way crossing fault,
parallel walls 6″ apart merging, the status board, and the plan in
`incoming/`.

**Carried:** unchanged from [`0216`](0216-report.md).
