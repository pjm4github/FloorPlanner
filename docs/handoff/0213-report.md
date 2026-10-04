# 0213 — report: macro language v2, T1 — the language is built, no Qt delivery; ANTLR 4.11.1 stands (my doubt about it was wrong); his question on carrying v1's features into v2, answered as a proposal

**Code, 2026‑10‑04.** No merge has happened since
[`0211`](0211-report.md). Branch `macro2-language` off `main` at
`86cc70f`, [PR #72](https://github.com/pjm4github/FloorPlanner/pull/72)
open, gate GREEN. **GREEN tier** — nothing a user sees changes — so it
merges on green CI without waiting ([`ROADMAP.md`](../ROADMAP.md) §1).
His four spec files went onto `main` with [`0212`](0212-report.md).

## 1. WHAT'S BUILT — `floorplanner/macro2/`

The pipeline of [`MACRO_SPEC.md`](../macro-spec/MACRO_SPEC.md) §8.1 as
far as the abstract events:

```
text ─► parse ─► AST ─► validate ─► expand ─► [InputEvent]        (T1)
                                               └─► Qt sink        (T2)
```

| module | what it is |
|---|---|
| `_generated/` | the parser ANTLR 4.11.1 generated from his two `.g4` files, **committed**, and `GRAMMAR.sha256` |
| `parse.py` | text → AST through the generated parser; syntax errors collected with line and column, never printed; **no AST is built from a tree ANTLR had to repair** |
| `validate.py` | §8.3: unknown tool letter, unknown `{Name}`, repeated modifier, negative `WAIT` — every error, positioned, in source order |
| `expand.py` | AST → abstract input events, **pure** (§5.3's six steps, §7's press and release order, the `KEYDOWN` baseline, the end-of-macro release with its warnings) |
| `serialize.py` | the canonical form of §10 |
| `keys.py` | the §6.2 key table, one definition for validation, expansion and writing |
| `ast.py` | the dataclasses; nothing downstream sees an ANTLR type |

`tools/gen_macro_parser.py` regenerates the parser — in the grammar's
own directory, so the generated header carries no machine path — and
`--check` compares the grammar's hash to the recorded one.
**Regenerating is byte-identical**, checked.

`antlr4-python3-runtime==4.11.1` is added to `requirements.txt` and
`pyproject.toml`; `floorplanner/macro2/_generated` is excluded from
`ruff`. `MacroRunner`, the recorder, `run_macro` and every `.fpm` file
are untouched.

## 2. MEASURED — and one belief of mine corrected

[`0212`](0212-report.md) §4 said: *"I believe that runtime imports
`typing.io`, which Python 3.13 removed."* **Wrong, and measured before
anything was built on it.** The 4.11.1 runtime does name `typing.io`,
but behind `if sys.version_info[1] > 5: … else:`, so on 3.13 it never
runs. Both 4.11.1 and 4.13.2 import on Python 3.13.9. **The spec's
version stands: ANTLR 4.11.1, tool and runtime.**

His grammar, as written, with no change:

* `examples.macro` parses with **zero errors**, 23 lines.
* **All eleven** of §12's rejection cases produce at least one error.
* The example fails **validation** on exactly one line, the last:
  `X MOVE 1.5 -2.25` — no tool has the letter `X`. That is §8.3 working,
  and it means the example cannot be *run* as it stands; T2's check uses
  §13's example instead.

## 3. THE CHECK — receipts

`tests/test_macro2_language.py`, **76 tests** (`macro`), none of which
opens a window:

| §12 item | |
|---|---|
| 1 acceptance | the example, zero errors; and its one validation error |
| 2 rejection | the eleven bad lines, each positioned |
| 3 `TYPE` literalness | the four listed, plus `TYPE` followed by one space |
| 4 expansion | **all seven rows of §5.4**, in the table's own notation; and beyond the table — each event carries its own segment's modifiers, modifiers press and release in §7's order however they were written, the six head verbs and their buttons, a double-click-drag, `MOVE`, `WHEEL`, `WAIT`, `KEY` strokes |
| 5 `KEYDOWN` baseline | a held Shift rides the press with no extra key events; a key left held is released at the end with a warning; a doubled `KEYDOWN` and a stray `KEYUP` warn and do nothing |
| 6 validation | seven positioned cases; every error reported, not only the first |
| 7 round trip | the example; twelve canonical-form cases |
| 8 CRLF | the same AST, no `\r` in any text |

and format detection (§11's first-line rule), and the grammar-hash
test, which also pins the runtime's version to the tool's.

**One thing in §5.4 the table does not say and the expansion does:**
§5.3 step 2 moves the pointer to the head point *before* the press, with
no button. The table's rows begin at the press. The abstract list names
that pre-press move `hover`, distinct from a drag's `move`, and the
row-by-row test leaves it out — said here so the test is not mistaken
for the spec.

Full suite **1492 passed**, 7 deselected (`perf` lane), `ruff` clean,
gate GREEN — the branch's own run.

## 4. HIS QUESTION — "How do I extend the V2 (once it passes tests) to include features of V1?"

Asked while T1 was being gated. **A proposal; nothing of it is built.**

What v1 has and v2 lacks is the vocabulary that *builds things or
drives the app directly* rather than moving the mouse: `PLACE`, `WALL`,
`DOOR`, `WINDOW`, `ROOM`, `DORMER`, `SELECT`, `ROTATE`, `MOVETO`,
`ZOOMFIT`, `OPEN`, `SAVE`, `NEW`, `SHOT`, and the caret commands with an
argument (`^O "path"`, `^F "name"`, `^H "on"`). It is the "superset"
option of [`0212`](0212-report.md) §3, deferred rather than refused —
and the pipeline was layered so it can be added without redoing T1–T3.

**The grammar is his, so the change starts there.** Two ways:

* **One escape form — recommended.** A single new line shape, an
  *application command*: a marker, a name, and arguments, e.g.
  `@PLACE sofa 120 96 0`, `@DOOR 120 0 3280`, `@OPEN "plans/den.json"`.
  One lexer rule that switches to an argument mode (quoted strings,
  numbers including feet-inches, bare words) and one parser rule. The
  marker is what keeps `DOOR` from being read as the tool letters
  `D O O R`. New high-level commands later need **no grammar change**.
* **A keyword per command.** `PLACE`, `WALL`, … each added to the lexer
  with its own typed rule. The grammar then checks arity itself, at the
  cost of a grammar edit and a regeneration for every command ever added.

**Then, the same five steps either way**, each small because of the
layering:

1. Edit the two `.g4` files and `examples.macro`; run
   `python tools/gen_macro_parser.py`. Until that is done the hash test
   is red — which is the point of it.
2. `ast.py`: one node, `AppCommand(name, args)`.
3. `validate.py`: the name must be one the application has, with the
   right number of arguments — checked against `MacroRunner`'s own
   handler table, not a second list.
4. `expand.py` passes it through as one abstract event; the Qt sink
   (T2) calls **`MacroRunner`'s existing handler**. Nothing about
   `PLACE` or `DORMER` is written twice.
5. `serialize.py` writes it; the legacy converter (T3) then maps the
   high-level commands straight across, and **all eight committed
   `.fpm` files become convertible**, where today two are not.

**What it would also settle:** the dialog problem. T3's v2 recorder
records raw input, so a door placement replays by driving the size
dialog. With application commands the recorder can go on emitting
`@DOOR x y 3280`, as the v1 recorder does, and replay never opens a
dialog.

**When:** after T2, as part of T3 or as a fourth tranche — it needs the
sink. It is a change to his grammar and his spec, so it waits on his
word and on which of the two forms he wants.

## 5. `fixtures/incoming/`, with ages

`single-floor-90-roof-gable-end-check.json` — his own, 2026‑10‑03, exit
not yet named ([`0205`](0205-report.md) §3). `README.md`.

## 6. WHAT HAPPENS NEXT

PR #72 merges on green CI; the merge is recorded in the report that
follows. Then T2, the player, on its own branch — AMBER, his check.

**Carried:** unchanged from [`0212`](0212-report.md).
