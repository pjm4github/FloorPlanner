# 0220 — report: the error indicator in the recorder window's gutter, built on his word; both languages mark the failing line

**Code, 2026‑10‑06.** No merge has happened since
[`0219`](0219-report.md). The work is on branch `macro2-error-marker`,
one PR, for his check. His word:

> *"add the error indicator to the line number gutter"*

— the feature he named when he asked for the line numbers
([`0218`](0218-report.md) §4), and 0219 §4 carried as *named, not built*.

## 1. WHAT IT DOES

When a Replay fails, **the number of the line that failed is drawn white
on red in the gutter, the line itself is tinted, and hovering the marker
shows the error** — the same text the status line shows. Marks clear when
the next Replay or a recording starts. A mark is carried by the text
block, so it stays on its line when lines are inserted or deleted above
it.

## 2. THE DECISION 0219 §4 SAID THIS NEEDED — taken, and here is how

A v2 error names its line (`line 4:0 unknown tool letter 'B'`), counted in
the text that was RUN. The dialog puts the `; fpmacro 2` header back on a
selection that lacks it, so the editor's line is the error's plus the
selection's first line, less one more when the header was added; the
mapping is `_replay_doc_lines`, and a test selects lines 3–5 of a macro
with the fault on 4 and finds the mark on 4.

**The existing language's errors name a token and no line** (`FOO: unknown
command`) — the engine is a flat token stream. But the dialog replays that
language **one line at a time**, so the line is known at the moment of the
error: the one just run. That is what is marked, and its message is the
step's errors joined. `MacroRunner` is not changed to carry a line.

Blank lines are skipped by the replay and counted by the gutter; the
mapping accounts for them, and a test puts a blank line before the fault.

## 3. STATE

`floorplanner/macro.py` (the editor and the dialog only — `MacroRunner`
untouched), `tests/test_macro2_player.py` (+5), one paragraph in
`docs/macro_language.md`. Macro suites green; `ruff` clean; the full gate
is this commit's own run and the PR's.

**For his check (AMBER):** in Macro ▸ Record / Debug, put a bad line in a
macro (`BOGUS 1` in a v2 one; `FOO` in an old one), Replay, and look at
the gutter; hover the red number.

## 4. `fixtures/incoming/`, with ages

`single-floor-90-roof-gable-end-check.json` — his own, 2026‑10‑03, exit
not yet named ([`0205`](0205-report.md) §3). `README.md`.

**Untracked, not mine, untouched:** `gen/`, `docs/macro-spec/grammar/gen/`,
my draft `docs/WORKING_AGREEMENT.proposed.md`, and the old stash entry.

## 5. WHAT HAPPENS NEXT

His check of the PR. Behind it, unchanged from [`0219`](0219-report.md)
§6.

**Carried:** unchanged from [`0219`](0219-report.md).
