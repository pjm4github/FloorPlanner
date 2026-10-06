# 0222 — report: PR #75 merged on his word, after his check — the error indicator in the recorder window's gutter, and the stop-at-the-error rule

**Code, 2026‑10‑06.** The record ([`0197-ruling.md`](0197-ruling.md) §7).
[`0220`](0220-report.md) and [`0221`](0221-report.md) put the branch to
him for his check. He ran it and said:

> *"perfect, I checked the macro error message and the replay and that
> looks. The message shows on teh status bar and the error line has a
> RED mark. Go ahead and land # 75"*

Done as said. `main` (where [`0221`](0221-report.md) had landed) was
merged into `macro2-error-marker`, the snapshot resolved as the merged
state, the gate run GREEN, and the branch landed on `main` at
**`48a9fe4`**, fast-forward. GitHub shows
[PR #75](https://github.com/pjm4github/FloorPlanner/pull/75) MERGED. The
branch is deleted, local and remote, in the same step.

## 1. WHAT HIS WORD RESTS ON

**He checked both commits on his own screen**, with the macro he wrote
for it: the red mark on the failing line, the error on the status line
in place of *"Replay complete."*, and — the ruling of 0221 — the lines
before the error on the canvas. This is the first tranche of the macro
arc checked by him in every part before its merge; the record says so
because the earlier ones ([`0217`](0217-report.md) §1,
[`0219`](0219-report.md) §1) had to say otherwise.

## 2. WHAT LANDED

On the merged tree: **1691 passed**, 7 deselected (`perf` lane), `ruff`
clean, gate GREEN.

| | report | what it is |
|---|---|---|
| the indicator | [`0220`](0220-report.md) | the failing line's number white on red, the line tinted, the error as the gutter's tooltip; marks ride the text block through edits and clear on the next Replay or Start |
| the rule | [`0221`](0221-report.md) | a v2 error lets the lines before it run and stops there; every error still reported; `MACRO_SPEC.md` §8.3 amended, dated, quoting him; the error kept on the status line |

With this the macro arc has nothing named and unbuilt: his spec's six
tasks ([`0219`](0219-report.md) §3), the indicator, and the rule.

## 3. `fixtures/incoming/`, with ages

Unchanged from [`0220`](0220-report.md) §4.

## 4. WHAT HAPPENS NEXT

Nothing is open on a branch. On his word, from [`0211`](0211-report.md)
§4 as it still stands: the D67 pair, the four-way crossing fault,
parallel walls 6″ apart merging, the status board, and the plan in
`incoming/`.

**Carried:** unchanged from [`0221`](0221-report.md).
