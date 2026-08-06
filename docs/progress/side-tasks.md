# Progress log — side tasks

> **Work that belongs to no migration phase**: tooling, packaging, the viewer
> track, documentation structure. Same rules as the phase logs — append one
> entry per task, newest at the bottom, never revise an entry (a correction is a
> later entry).
>
> **This file starts empty of history on purpose.** The log that was split on
> 2026-08-06 contained exactly one non-phase entry — the 3D view popup of
> 2026-08-04 — and it was left where it sits in
> [`phase-4-part-1.md`](phase-4-part-1.md), because its own text argues that its
> value is its position between P4.4 and P4.5. Lifting it here would have
> reordered contemporaneous history to tidy a filing system. See
> [`README.md`](README.md).

```
DOCS REFACTOR  2026-08-06  (branch docs-refactor)
         Requested after Phase 4 closed, with main clean and no task in
         flight. The register, the working agreement and the progress log
         come out of the two documents that had absorbed them.
         Ten steps, one sub-commit each, full-mode gate green at each.

step 0   THE REFERENCE AUDIT, FROZEN IN CODE BEFORE ANYTHING MOVED.
         tools/ref_audit.py holds the pattern set once, so the count taken
         now and the count taken at step 9 come from the same code rather
         than from a grep retyped at the end.
         baseline  413 references / 143 tracked text files / 53 carrying one
                   defect=307  row=81  artifact=22  mdlink=3  dnum=0
                   50 known ids (1-49 consecutive, plus 12a) / 0 unresolved
         findings  EXACTLY ONE reference in the repo resolved to nothing:
                   `defect 11a` at CODE_REVIEW_v2.md:76 -- 11a is a HALF
                   named in row 11's prose, never a row. Resolver now
                   resolves a lettered id to its numeric parent and SAYS SO.
                   dnum=0: the permanent-key spelling is used nowhere yet;
                   this refactor introduces it.
                   The register holds 50 rows, not 49.
                   48% of all references sit in the plan; the rest spread
                   over 51 files including ci.yml, CLAUDE.md, 20 modules
                   and 21 test files. Moving the register is not a
                   docs-only edit.
         evidence  docs/evidence/ref-audit-baseline.json

step 1   docs/README.md -- THE MAP, WRITTEN FIRST so the remaining steps
         had something to follow. States which documents decide things,
         which are the record, which are history; that superseded/ holds
         UNIQUE material; and that superseded/ is excluded from no lint,
         gate or search -- on this repo's own evidence, P0.1, where a
         hidden docs/_superseded/ rotted behind a ruff exclusion until it
         was deleted.
         measured  413 -> 427 refs, 4 unresolved, all forward references
                   declared in the document's own opening block.

step 2   FOUR DOCUMENTS TO superseded/, BODIES PROVED UNTOUCHED.
         CANVAS_ITEM_REFACTOR_PLAN, CODE_REVIEW, REFACTOR_PLAN, TODO --
         all four recorded by git as 100% renames.
         receipt   4/4 bodies byte-identical to HEAD's blob
                   34076 / 10427 / 11404 / 11499 bytes, unchanged
         Superseded by TWO different mechanisms, so not one header: by a
         DOCUMENT (the first two say so themselves) and by COMPLETION (the
         last two name no successor because the work shipped).
         The root-clutter attribution was corrected against disk: the
         finding is raised at CODE_REVIEW.md:88, not in TODO.md.
         One broken link left broken deliberately -- CANVAS's own line 3
         links relative to its old directory. Repairing it would have cost
         the 4/4 receipt; the new header carries the working pointer and
         the historical text stays as written.

step 3   WORKING_AGREEMENT.md EXTRACTED; the plan keeps a pointer.
         receipt   body vs plan lines 10-291: 38286 bytes / 282 lines,
                   IDENTICAL. Plan lines 1-8 and 292-end IDENTICAL.
         ONE CHARACTER changed in moved text, itemised: the heading was
         promoted from `## Working agreement` to `#`.
         plan      5,216 -> 4,936 lines
         SESSION_SNAPSHOT's reading order repaired in the same commit --
         a pointer and its target must never be split across commits.

step 4   THE PROGRESS LOG TO progress/, SPLIT BY PHASE, VERBATIM.
         receipt   log reassembled from its seven files and compared to
                   the plan's blob: 289,297 bytes / 4,351 lines either
                   way, IDENTICAL. Plan lines 1-579 IDENTICAL.
         plan      4,936 -> 586 lines (acceptance was ~900)
         Phases turned out to be CONTIGUOUS blocks, so every cut is at a
         column-0 task-entry start and nothing was reordered. Phase 3
         (1,861) and Phase 4 (1,417) exceeded the 1,200-line rule and were
         split in two; the parts are numbered rather than named for task
         ranges, because the log's APPEND order is not the phase's task
         order -- Phase 3 was written P3.1, P3.2, P3.3, P3.5, P3.8, P3.7,
         P3.6, P3.5-followup, P3.4, and a file called `P3.1-P3.5.md` would
         imply a range it does not hold.
         The log's own rule ("append one entry per task, newest at the
         bottom") lived in the heading block being replaced, and is
         carried verbatim into progress/README.md rather than dropped.
         The one non-phase entry in the whole log -- the 3D view popup,
         2026-08-04 -- was NOT lifted into this file. Its own text says
         its value is its position between P4.4 and P4.5.
```
