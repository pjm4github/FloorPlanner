# 0231 — report: PR #77 merged on his word with three tranches folded in — the parallel-walls merge rule, the violations report that zooms to each problem, the wall-properties dialog

**Code, 2026‑10‑10.** The record ([`0197-ruling.md`](0197-ruling.md) §7).
[`0228`](0228-report.md), [`0229`](0229-report.md) and
[`0230`](0230-report.md) put three stacked branches to him under one PR.
His word:

> *"wall properties look right, fold all three into #77 and land"*

Done as said. `parallel-walls-6in` was fast-forwarded to
`wall-properties`'s tip (`1ab7600`), `main` (where 0230 had landed)
merged into it, the snapshot resolved as the merged state, the gate run
GREEN, and the branch landed on `main` by that merge commit,
fast-forward. GitHub shows [PR #77](https://github.com/pjm4github/FloorPlanner/pull/77)
MERGED. The three branches are deleted, local and remote, in the same
step.

## 1. WHAT HIS WORD RESTS ON — recorded as it is

He **checked the wall-properties dialog** on his own screen: *"wall
properties look right."* **The other two he has not reported on** — the
parallel-walls rule ([`0228`](0228-report.md): a gesture merges at 3″)
and the violations report ([`0229`](0229-report.md)) — and they are
merged on his instruction and on their tests. If two walls he meant as
one stop merging, 0228's tests are where to start; if a violation row
zooms to the wrong place, `design/locate.py`'s.

## 2. WHAT LANDED

On the merged tree: **1742 passed**, 7 deselected (`perf` lane), `ruff`
clean, gate GREEN.

| | report | what it is |
|---|---|---|
| parallel walls | [`0228`](0228-report.md) | a draw or drag release merges a same-type parallel wall within `GESTURE_WELD_IN` (3″), not the grid step; the explicit passes keep the grid step |
| the violations report | [`0229`](0229-report.md) | "Malformed design file" is a non-modal list of every violation; a row switches level and fits the view to the place it names, resolved against the opened document |
| wall properties | [`0230`](0230-report.md) | double-click a wall: name, type, end points corner by corner in inches or feet-and-inches, the joined-corners checkbox, cancel reverts, one undo step, a profile placeholder |

**The format changed with it** ([`0230`](0230-report.md) §2): walls and
vertices carry an optional `name`. Said again here because it landed on
his word for the dialog, not on a word about the schema; a document
without names is unchanged byte for byte.

## 3. THE QUEUE, as it now stands

Of [`0211`](0211-report.md) §4's four items only **the status board**
remains ([`0019`](0019-ruling.md), read-back first). Beside it: the
`roofs-r3-planes-gables.png` evidence re-shot ([`0224`](0224-report.md)
§4, his display); the save-time violations report, the profile view
and the catalog-symbol items named in earlier reports, each his to
order.

## 4. `fixtures/incoming/`, with ages

Empty.

## 5. WHAT HAPPENS NEXT

Nothing is open on a branch. His word.

**Carried:** unchanged from [`0230`](0230-report.md).
