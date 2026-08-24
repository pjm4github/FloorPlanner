# 0098 — ruling: the report names walls the user cannot find — two id namespaces, one label shape

**Patrick, 2026‑08‑23, on `wiscaway2026-08-08.json`:** *"I have Wall 19 selected
which appears to be almost 90 degrees not 45 as the report says. Am I doing
something wrong?"*

**No. He selected a different wall from the one the report names, and nothing in
the application could have told him that.**

---

## 1. MEASURED — they are two different identifiers

| | |
|---|---|
| **status bar** `Wall W19: V28(97.50, 43.50)ft -> V30(97.50, 50.50)ft len 7.00ft` | `WallItem.uid` — **session-local**, minted lazily in the order items are first read ([`0064`](0064-report.md), `5d85b09`) |
| **report** `wall w19 (interior) is 45.00 degrees off axis` | the **document** id from the saved v5 JSON |

**The document's `w19` is `v16(46.50,35.50)ft -> v17(48.00,34.00)ft`, 2.12 ft
long, heading 315°, deviation 45.0000°** — a two-foot diagonal stub on the other
side of the plan. **The wall he selected sits at x = 97.50 ft and is the document's
`w71` region.**

> ### `WallItem.uid`'S OWN DOCSTRING SAYS IT: *"NOT the id a saved document assigns … this is for a live editing session only (the status bar, debugging)."*
>
> **Both render as a W and a number, in the same window, at the same time, with
> nothing to tell them apart.** The warning is in the code where only Code reads
> it. **The collision is on screen, where only Patrick does.**

**The report itself is correct.** Its two entries — 45.0000° and 18.4349° — are
[`0055`](0055-ruling.md) §3's own independent measurement of this exact file
(*"103 walls, 2 off-axis (45.0000, 18.4349 — both deliberate)"*), reproduced to
four decimals by the shipped instrument. **The instrument works. The naming
does not.**

## 2. THIS BLOCKS THE PR #37 CHECK, NOT JUST THIS ONE

The repair's preview lists moved and refused walls **by document id too**
([`0079`](0079-report.md) §2(d)). **Patrick cannot verify a single line of it**
— and "does the drawing still look like your drawing?" is not answerable when he
cannot locate the walls the dialog is talking about.

**OWED before the #37 check, and the cheap half is enough:**

> **Every wall the report or the preview names carries its endpoints in feet**,
> the same form the status bar already prints. `wall w19 (interior) at
> (46.50, 35.50) -> (48.00, 34.00)ft — 45.00 degrees off axis`. **A number he
> cannot look up is not a report.**

**The right answer is click-to-select** — click a row, the wall selects in the
scene. **Named, not ordered**: it is a dialog change with its own read-back, and
coordinates unblock the check today.

## 3. TWO SMALLER THINGS

**The report says 104 walls; the file has 103.** One extra. Not investigated — I
cannot run the app. **Name the source of the count before the next report is
trusted**; a census that cannot reproduce its own denominator is
[`0059`](0059-ruling.md) §1 again.

**[`0093`](0093-ruling.md) §4's named question now has a live instance, and it
argues itself.** Both entries in this report are **deliberate diagonals**. Under
the 15° intended-angle grid, `w19` at exactly 45.00° has deviation **zero** and
leaves the report entirely; `w25` shows 3.43° off the nearest increment.

> **The report's whole content today is two walls Patrick drew on purpose.**
> That is the separation [`0055`](0055-ruling.md) §2 had to make by hand, and
> the 15° grid makes it by construction. **Still not ordered — it moves item C's
> candidate set and item C is at PR — but the question is no longer theoretical.**

## 4. TIER

**§2's coordinates: GREEN** — a report gains a column, no behaviour changes.
**Ahead of the #37 check.**

**§3's count: GREEN**, a measurement.

**Click-to-select and the 15° report grid: RED**, both named, neither started.

**Patrick did nothing wrong, and the confusion is the finding.** A check that
cannot be performed is a defect in the thing being checked, not in the checker.
