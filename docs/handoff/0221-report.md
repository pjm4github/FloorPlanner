# 0221 — report: his ruling on a v2 error — the lines before it run, it stops there, the error stays on show; §8.3 of his spec amended; folded into PR #75

**Code, 2026‑10‑06.** No merge has happened since
[`0220`](0220-report.md). The change is a second commit on
`macro2-error-marker`, PR #75, which waits on his check. His word, with
the macro he ran — the commands check with `@WALL 0 300 0` put in as its
line 11:

> *"the runner should play as many lines as possible and stop on the
> error line and keep the error message on the bottom of the macro window
> (instead of filling in replay complete). This macro has an error on line
> 11 so the mark should appear on that line but lines 7 through 10 should
> show on the canvas"*

## 1. WHAT THIS CHANGES — his spec, by his ruling

`MACRO_SPEC.md` §8.3 said: *"Validate the whole macro before executing
anything. Report every error with its line and column, then abort."* The
player did exactly that, and [`0220`](0220-report.md) §1 described it:
*nothing of a v2 macro runs when a line is bad*. His ruling is the other
reading, and it is now the rule:

* **The whole macro is still checked first, and every error is still
  reported** — a macro with three bad lines names all three.
* **The lines before the first bad line run. It and everything after it
  do not.**

§8.3 carries the amendment, dated and quoting him; §14.3's *"found before
anything runs"* is reworded to match; `docs/macro_language.md`'s v2
section says the new rule. The spec's own test 6 (*"nothing is
executed"*) is now *nothing from the first bad line is executed*, and
three tests that pinned the old rule are rewritten to pin this one, each
saying why.

**How:** `Player.run` takes the first error's line, re-checks the text
cut just before it, and runs that; a prefix that does not check clean
(it cannot — a syntax error lives on its own line, and validation is
per line) or has no command lines runs nothing. `steps` is the number of
command lines run.

## 2. THE STATUS LINE

A replay that met an error no longer ends with *"Replay complete."* The
message — *"Replay stopped: line 11:0 @WALL takes 4 to 5 arguments, not
3"* — stays until the next Replay or Start, which is when the gutter's
marks clear too.

## 3. HIS CASE, PINNED

`test_his_macro_with_a_bad_line_11_draws_lines_7_to_10`: his macro,
built from `fixtures/macro2-commands-check.fpm`'s first ten lines plus
his line 11 and the three after it, replayed in the dialog — **four
walls on the canvas, line 11 the only mark, the error on the status
line, "complete" nowhere in it.**

## 4. STATE

Branch `macro2-error-marker` at `62dc27d`, two commits, pushed; PR #75
open. Full gate GREEN on it: **1691 passed**, 7 deselected (`perf`
lane), `ruff` clean. `main` is this commit; the branch's snapshot was cut
against its own tip and will be resolved to the merged state when it
lands, as every AMBER branch's has been.

**For his check:** the same macro, in Macro ▸ Record / Debug, Replay.

## 5. `fixtures/incoming/`, with ages

Unchanged from [`0220`](0220-report.md) §4.

## 6. WHAT HAPPENS NEXT

His check of PR #75. Behind it, unchanged from [`0219`](0219-report.md)
§6.

**Carried:** unchanged from [`0220`](0220-report.md).
