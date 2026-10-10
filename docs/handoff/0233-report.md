# 0233 — report: the status board built — `docs/STATUS.md` generated from one `**Landed:**` line per merge, gate-checked; 77 PRs on the board from #1; the migration table frozen; the pair table generated; the mailbox is the record

**Code, 2026‑10‑10.** No merge has happened since
[`0231`](0231-report.md). His word to [`0232`](0232-report.md) §5:

> *"build it, the mailbox is the record now"*

Built on `status-board`, GREEN — no new semantics, nothing the user must
learn, no format change — so it goes up as a PR and merges on green CI
without his check, per the charter; this report and the one new mailbox
file land on `main` first, because the hook admits a new handoff file
nowhere else.

## 1. WHAT WAS BUILT, against 0232 §5's five items

| item | done |
|---|---|
| **1. the generator** | `tools/status_index.py` writes [`docs/STATUS.md`](../STATUS.md): every landing (PR, date, merge commit, tier, what it rested on, the report), the PRs closed unmerged, `ROADMAP.md` §3's RED table as *named, not landed*, the defect counts. `--check` runs in the gate's docs lane as `Docs-Status` beside `Docs-Index`, RED on drift, on a malformed line, **and on a first-parent commit of `main` whose subject names a `PR #N` with no landing line** — the cross-check 0232 §3 named. |
| **2. the backfill** | **33 `**Landed:**` lines in 31 merge reports** (0113 carries three), each from GitHub's own record — merge commit verified present in `main`'s history, merge date, the title's tier tag where the title had one (12 of 76) and `—` where it did not, the fifth field *"see this report"*. **`handoff/0000-landings.md`**, written once, holds the **44 lines no report records** — the 36 merges before the mailbox and the eight green-CI merges after it (#40, #41, #42, #44, #46, #48, #61, #63) — each with the PR's title and the handoff files that mention it, or *"not on the record"*; and the one `**Not landed:**` line, #59. **The nine PRs 0232 found named nowhere are on the board.** |
| **3. 0019's freeze and move** | `V5_MIGRATION_PLAN.md`'s Status table carries the frozen header; its six `☐` rows are gone, corrected once in the move: P5.2 landed (#26, #27), P6.1/P6.2 parked, P5.1/P5.3/P6.3 now rows of `ROADMAP.md` §3's RED table, which the board renders. **The entry 0019 called a lie is no longer anywhere.** |
| **4. the pair table** | `handoff/README.md`'s table is a generated region between `PAIRS:BEGIN`/`PAIRS:END` markers, one row per mailbox file from its own first line — 244 rows where the hand table had stopped at 0116. Same `--check`. |
| **5. his decision** | *"the mailbox is the record now"* is written into `progress/README.md` under its own dated heading: a unit is recorded by its handoff report, a merge by the `**Landed:**` line under that report's title; `tasks/` stays as built and receives nothing. |

The snapshot's two hand-kept closed-tranche tables (12 and 9 rows) are
now one pointer each at the board, as 0019 §4 and [`0028`](0028-ruling.md)
ordered; `docs/README.md`'s map gains the `STATUS.md` row.

## 2. THE LINE, so the next landing writes it right

```
**Landed:** PR #78 · <sha7> · YYYY-MM-DD · GREEN|AMBER|RED|— · <what the merge rested on>
```

Directly under a merge-recording report's title; five fields, ` · `
between them. The reader is strict (a field short, a date not ISO, a tier
outside the set, the wrong separator: MALFORMED, not skipped), a PR landed
twice is MALFORMED, and an example inside a code fence — like the one
above — is not a landing.

## 3. THE RECEIPT

`tests/test_status_index.py`, sixteen tests. On the real record: the board
and the pair table match a regeneration and every PR on `main` has its
line; PRs #1–#77 each have exactly one line with no gap in the run and
#59 the only *Not landed*; **every landed commit is on `main`** (no
invented hash); every merge-titled report carries its line; the pair
table lists every mailbox file; the board renders the RED table and the
defect counts. On a synthetic record: generation then a clean check; **a
hand edit to the board is RED; a landing commit with no line is RED**;
six malformed shapes are MALFORMED; a PR landed twice is MALFORMED and a
fenced example is not a landing; a README without the markers is
MALFORMED. `tests/test_gate.py` green with `Docs-Status` in the lane;
`ruff` clean; the docs lane GREEN; the full gate the branch's own run.

## 4. SAID PLAINLY

* The 33 backfilled lines say *"see this report"* in the fifth field and
  `—` for the tier where the PR title carried none: **the record did not
  say, and I did not fill it in.** New lines say it.
* The cross-check reads `git log --first-parent`; on a shallow clone it
  sees fewer subjects and can only pass more easily, never fail wrongly.
* `0000-landings.md` is a mailbox file by location only; it is neither a
  report nor a ruling and the pair table says so in its one line.

## 5. `fixtures/incoming/`, with ages

* **`wiscaway2026-10-07R1.json` — his own, arrived since [`0232`](0232-report.md)
  (file dated 2026‑10‑07), not read, not edited; no note with it, no defect
  named. Its exit is his to name ([`0205`](0205-report.md) §3's four).**
* `README.md`.

**Also in the working tree, not mine and not touched:** a `Claude outputs/`
folder beside `gen/` and `docs/macro-spec/grammar/gen/`.

## 6. WHAT HAPPENS NEXT

The PR merges on green CI; the merge's own `**Landed:**` line goes into
the report that records it. Then, his word: the evidence re-shot (his
display), the save-time violations report, the profile view.

**Carried:** unchanged from [`0232`](0232-report.md).
