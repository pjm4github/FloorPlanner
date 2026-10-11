# 0236 — report: PR #79 merged on green CI — the PDF and DXF exporters accept a plan with a roof; D87 closed

**Landed:** PR #79 · d90f8b4 · 2026-10-11 · GREEN · on green CI (pytest full gate, ruff); his check is saving a PDF of a plan with a roof

**Code, 2026‑10‑11.** The record ([`0197-ruling.md`](0197-ruling.md) §7).
[`0235`](0235-report.md) fixed D87 on `pdf-v6` and put it up as
[PR #79](https://github.com/pjm4github/FloorPlanner/pull/79), GREEN.
CI went green and the branch landed on `main` at **`d90f8b4`**,
fast-forward, under the standing GREEN authority. The branch is deleted,
local and remote, in the same step. **D87's `closed_by` is this commit**,
and the index is regenerated with it.

## 1. ONE THING ABOUT THE LANDING ITSELF

The PR's first CI run was RED on two tests and its second GREEN with no
change to the fix: the first run's merge-ref held the branch's
regenerated pair table and board, which name `0235-report.md` and D87's
record, before `main` held those files — the two-step landing the hook
imposes (a new mailbox file commits on `main` only) seen by the board's
own `--check`. **The order that avoids it: land the report and any new
record on `main` first, then merge `main` into the branch and push.**
Said here so the next GREEN tranche does it in that order; nothing in the
tool is wrong.

## 2. WHAT LANDED

On the merged tree: full gate GREEN, `ruff` clean, docs lane GREEN.

| | report | what it is |
|---|---|---|
| D87 | [`0235`](0235-report.md) | `SUPPORTED_VERSIONS = (5, 6)` in `fp2pdf.py` and `fp2dxf.py`: a plan with a roof, written as version 6, exports again; 7 still refused; the message names what it saw |

## 3. `fixtures/incoming/`, with ages

* `wiscaway2026-10-07R1.json` — his own, file dated 2026‑10‑07, not read,
  not edited; no note; exit his to name.
* `README.md`.

## 4. WHAT HAPPENS NEXT

His check: File ▸ Export ▸ PDF plan set on the plan that was refused.
Then his word, from what is named: the file in `incoming/`; the evidence
re-shot (his display); the save-time violations report; the profile view.

**Carried:** unchanged from [`0235`](0235-report.md).
