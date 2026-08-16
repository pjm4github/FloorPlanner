# 0026 — report: pushed, PR #31 open, CI is red — and it is a finding, not a re-run

**Per [`0025-ruling.md`](0025-ruling.md) §2 — "push the branch, open the PR,
merge on green CI plus this check."** The branch was already pushed and PR #31
already open before `0025` was written (its "never pushed" measurement was
stale by the time it landed — `git ls-remote` now shows
`d74-vessel-enclosure-split` at this session's own last commit). CI ran. It is
not green. **This report is that disagreement, per `0025`'s own instruction
not to resolve it by re-running.**

---

## 1. PR #31, and what CI actually says

[`https://github.com/pjm4github/FloorPlanner/pull/31`](https://github.com/pjm4github/FloorPlanner/pull/31),
`d74-vessel-enclosure-split` → `main`. Six jobs; **four pass** (`ruff`,
`pytest` on 3.10/3.13/windows), **two fail**: `records (gate --docs)` and
`pytest deep invariants (py3.13)`.

**Both failures are the same one line**, and nothing else in either job:

```
Docs-Snapshot: RED -- docs/SESSION_SNAPSHOT.md was cut against bf22ee2,
which is neither HEAD (ce8a98a) nor its parent.
```

`Gate-DEEP: 720 passed, 7 deselected` — identical to the local, GREEN run.
`Docs-Defects`, `Docs-Index`, `Ref-Audit` all report clean. **The snapshot
line is the only thing that differs from local.**

## 2. Why, and it is not this branch's content

[`D78`](../defects/0078-the-snapshot-staleness-gate-cannot-pass-on.md), filed.
`actions/checkout@v5` on a `pull_request` trigger checks out the
synthetic merge ref by default (`refs/pull/31/merge`), not the branch tip.
Fetched and inspected directly:

```
git log -1 --format="%H %P" refs/pull/31/merge
ce8a98a...  0680c80... (main)  1960025... (this branch's own tip)
```

**`HEAD~1` on that ref is always `main`'s tip, by construction — never the
branch's own previous commit.** The snapshot re-cut rule and this checkout
model are in direct conflict: correctly re-cutting the marker for this
branch's own work is exactly what makes CI's copy of the check unsatisfiable,
because CI is not looking at this branch's history at all. A branch that
never touched the marker would coincidentally pass, for the wrong reason.

**Not a flake, not a real invariant failure, not anything about the vessel/
enclosure split, the evidence render, or D75/D76/D77.** All of that content
is exactly what the local gate and Patrick's check already confirmed.

## 3. What this report does NOT do

**It does not merge PR #31.** The merge condition per `0025` §6 is Patrick's
check plus green CI, and CI is not green. **It does not touch
`.github/workflows/ci.yml` or `tools/gate.py`** — D78 names three candidate
remedies without choosing one, because the checkout step and the gate check
are shared infrastructure this task did not ask to redesign, and `0025`'s own
instruction was to report a CI disagreement, not to make it go away by
editing around it.

**One consequence worth stating plainly: this commit's own re-cut of
`SESSION_SNAPSHOT.md`'s marker (§0/§1, below) will very likely fail CI the
identical way, for the identical reason.** That is expected, not a new
problem — it is the same structural mismatch D78 names, reproduced by the
report that names it. Filing this report and D78 does not require the
marker to be left un-re-cut; leaving it stale would be curing CI's symptom
by breaking the rule the marker exists to enforce.

## THE STATE, AS IT NOW STANDS

**PR #31 is open, Patrick's check passed (0025), CI is red on one structural
line (D78), and nothing merges until that is ruled.** Tier unchanged: AMBER.

## Gate

Local: `ruff` clean; `python tools/gate.py` full mode — `collected=727
ruff=clean vacuous=0 end_assign=0 snapshot=current`, OFF/ON/DEEP each `720
passed, 7 deselected`, `Gate-Verdict: GREEN`. `python tools/defects_index.py
--validate` — 79 records (D78 added), front matter valid. CI: see §1 — four
of six green, two red on `Docs-Snapshot` only, explained by D78.
