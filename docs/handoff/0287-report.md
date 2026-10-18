# 0287 — report: PR #97 merged on his word — the plan's annotations in the DXF, and the second-floor procedure; a gate deadlock of my making, and how it was cleared

**Landed:** PR #97 · ea5a4bc · 2026-10-18 · AMBER · checked by Patrick in Chief: "The DXF import into Chief Architect works well"; landed on his choice "Land #97 now"

**Code, 2026‑10‑18.** The record ([`0197-ruling.md`](0197-ruling.md) §7).

## 1. WHAT LANDED

`main` fast-forwarded to **`ea5a4bc`**, ONE commit on `05b6154`:

* [`0285`](0285-report.md): drawn dimensions on `FP-DIMENSIONS`, texts and
  leaders on `FP-ANNOTATIONS`, by the plan's Show switches; the dimension
  geometry shared with the PDF through `floorplanner/export/_annot.py`.
* [`0286`](0286-report.md): the README's step 10, importing `L2.dxf` onto a
  second Chief floor (a floor, not a layer), with his own edits to steps
  1–9 and four screenshots.

## 2. THE DEADLOCK, AND THE SLIP BEHIND IT

`05b6154` (0286's record on `main`) named **"PR #97"** in its subject while
#97 was still open. `tools/status_index.py --check` reads every
first-parent subject on `main` as a landing claim and wants a `**Landed:**`
line for each, so the gate went RED, and the commit hook refused every
commit, including a reword and the landing commit itself, because that
line can only name a commit that already exists. The hook was right; the
slip was mine. Earlier records named the **branch**, never an open PR
number, in a `main` subject, and that is the rule from here.

Offered the choice, he chose to land #97 and made the one branch commit
himself (`ea5a4bc`, its message prepared here and saying why it was made
by hand). This record then names it, which turns the check green the
ordinary way. Nothing was bypassed and `main`'s history was not rewritten.

## 3. HIS CHIEF QUESTIONS, ANSWERED IN CHAT

How to move between floors (Up/Down One Floor) and how to ghost the other
floor (Reference Display, Select Reference Floor). These follow Chief's
standard controls and were not verified in his X17; if his menu names
differ, step 10 gets corrected.

**On GitHub, #97 reads CLOSED, not merged:** once `main` had `ea5a4bc`, the PR's head was
force-moved onto it (his command), and GitHub closed the PR without recording a merge. A
comment on the PR points to `ea5a4bc` and this record. The branch is deleted, local and remote.

**Nothing is open on a branch.** Named, not ordered: his backlog (0248's
items 8 and 9).

**Carried:** unchanged from [`0286`](0286-report.md).
