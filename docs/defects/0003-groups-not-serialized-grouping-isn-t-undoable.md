---
# permanent key, independent of GitHub
id: 3
title: "Groups not serialized; grouping isn't undoable; undo dissolves groups"

# maps directly onto GitHub Issues fields
state: closed
state_reason: completed
labels:
  - type:defect
  - area:groups
milestone: null

# ours; becomes body prose after migration
opened: null
closed: 2026-08-04
closed_by: 52a6aed
rank: 3
related: [4]
state_source: receipt
github_issue: null
---

# D3 — Groups not serialized; grouping isn't undoable; undo dissolves groups

## Record

> **Moved verbatim** from the register (`docs/CODE_REVIEW_v2.md`, the row at its
> line 68) on 2026-08-06 — not reworded, not split, not
> reformatted. The register wrote each row as one continuous argument in which
> symptom, mechanism, evidence, ruling and receipt are interleaved, so dividing
> it into sections would have meant interpreting it. See
> [`README.md`](README.md) for the section shape new records take.

Groups not serialized; grouping isn't undoable; undo dissolves groups

## Site

`mainwindow.py:1042‑1083`

## Milestone

**P4.5** — *partly closed early: defect 4's fix made group→move→undo restore the plan correctly. The remaining half (the group itself surviving save/load and redo) is still open and is held by characterization test 3.*

## Receipt

**Closed 2026-08-06, in its own commit, after the docs refactor migrated it
open.** The refactor derived this record's state from its Phase cell, which
still says the remaining half *"is still open and is held by characterization
test 3"* — written before P4.5 closed it. That derivation disagreed with
`SESSION_SNAPSHOT.md` (which lists row 3 among those closed in Phase 4) on this
record and on no other: **49 of 50 agreed.** Migrated open, corrected here.

Three tests, all passing, together covering both halves:

| test | half |
|---|---|
| `tests/test_characterization.py::test_group_survives_roundtrip` | the group survives save/load — **flipped `xfail` → pass at P4.5, annotated "(defect 3)"** |
| `tests/test_undo.py::test_undo_after_grouping_restores_the_plan` | grouping is undoable |
| `tests/test_characterization.py::test_group_move_undo_restores` | undo does not dissolve the group |

    python -m pytest tests/test_characterization.py::test_group_survives_roundtrip         tests/test_characterization.py::test_group_move_undo_restores         tests/test_undo.py::test_undo_after_grouping_restores_the_plan -q
    3 passed in 0.14s

Closed by `52a6aed` — *P4.5(19) - defect 3: groups serialize, and grouping still
moves nothing*, authored 2026-08-04, which is the date recorded above; P4.5
itself merged at PR #10 on 2026-08-06.

**One declared change, quoted from the test itself:** the round trip goes through
`design_document()`, not `serialize()` — v4 has no `groups` collection and never
will, so asserting group survival through the legacy writer would be asserting
the impossible.
