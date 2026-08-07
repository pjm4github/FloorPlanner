---
# permanent key, independent of GitHub
id: 51
title: "The census depends on the working tree, not the repository"

# maps directly onto GitHub Issues fields
state: open
state_reason: null
labels:
  - type:defect
  - area:tests
milestone: null

# ours; becomes body prose after migration
opened: 2026-08-07
closed: null
closed_by: null
rank: 52
related: [50]
state_source: row
github_issue: null
---

# D51 — The census depends on the working tree, not the repository

## Symptom

`collected=` moved from 637 to 638, and the gate went RED, because of a file
that **is not in any commit**. An untracked or merely staged `.json` dropped into
`examples/` changes the collected count and can fail the suite.

## Mechanism

`tests/test_schema.py` globs `examples/*.json` **off the filesystem** and
parametrizes over what it finds:

    DESIGN_FILES = _design_files()
    CLEAN_FILES  = [p for p in DESIGN_FILES if p.name != CORRUPT]

    @pytest.mark.parametrize("path", CLEAN_FILES, ids=lambda p: p.name)
    def test_clean_design_validates(path): ...

So the parametrization — and therefore the census — is a property of **the
working tree**, not of the repository. Two machines with the same commit, or two
agents on the same branch, legitimately disagree about `collected=`.

## Evidence

Measured 2026-08-07, on `examples/farmplaceBIGmultifloor.json` (present on disk,
staged, in no commit):

    with the file      collected=638   1 failed   Gate-Verdict: RED
    deselecting it     collected=637   0 failed   629 passed

**And it is worse than a count.** With `.claude/hooks/verify_gate.py` in place,
a red gate blocks every commit — so **a file that is not in the repository can
stop all work in it**. That is this record's sharpest form: the census is not
merely inaccurate across machines, it is a hole through which an unversioned
file reaches the guard.

The census-reconciliation doctrine exists precisely so a number cannot mean two
things at two moments. This makes it mean two things in two *places*, which the
doctrine never considered.

## Ruling

*(Open — a proposal, not a decision. Nothing is implemented.)*

**The instrument should read the repository, not the tree.** Three shapes, in
increasing cost:

1. **Parametrize from `git ls-files examples/*.json`** rather than a glob. The
   census then describes the commit, which is what every consumer of it assumes.
   Cheapest, and it fixes the count and the red together.
2. **Keep the glob, and make the gate report the discrepancy** — a
   `Gate-Census: … untracked=N` field, so an unversioned file is visible rather
   than silently priced into the total.
3. **A frozen manifest** of corpus files, with the glob asserted against it. The
   strictest, and the closest in spirit to `test_corpus_discovered`, which
   already guards the opposite failure (a rename silently emptying the corpus).

(1) and (2) compose and are probably the right pair: read the repository, and
say so when the tree disagrees with it.

## Receipt

*(Open.)* Acceptance: with an unversioned `.json` present in `examples/`, the
collected count and the verdict are unchanged from the same commit without it.
