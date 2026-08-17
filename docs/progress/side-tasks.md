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

step 5   THE REGISTER SPLIT INTO 50 RECORDS; INDEX.md GENERATED.
         receipt   150 moved cells (Record/Site/Milestone x 50) compared
                   byte-for-byte against HEAD's register: 150 IDENTICAL.
                   Register sections 1-2 and 4-5 IDENTICAL.
         register  156 -> 103 lines, 107,749 -> 10,891 bytes
         The body is ## Record, NOT the five specified sections: the
         register wrote each row as one continuous argument in which
         symptom, mechanism, evidence, ruling and receipt are
         interleaved. The five sections are documented as the shape NEW
         records take and the shape a record takes when NEXT REVISED.
         38 DEFECTS, NOT 49. Nothing removed, nothing closed -- the
         categories got honest. 50 records: 38 defect, 6 gap, 1 limit,
         5 task.
         State came from the PHASE CELL, not the prose, and finding out
         why was the substance of the step. Struck-through text is
         superseded and must not vote (4 rows); the Defect cell is
         append-only prose that keeps overruled proposals (4 more); and
         15 terse early rows say nothing at all -- their state lives in
         the Status table's tick box, in another document.
         Checked against SESSION_SNAPSHOT: agrees on 49 of 50. The one
         disagreement is D3, whose cell still reads "is still open" --
         migrated as the register has it, deferred to step 10.
         handoff: 0001

step 6   tools/defects_to_github.py -- --dry-run emits 50 valid gh
         commands and exits 0; flags verified against gh 2.93.0 rather
         than assumed. Labels and milestones are emitted FIRST because
         `gh issue create --label X` fails if X does not exist.
         `--execute` was run BY ACCIDENT and reached the GitHub API,
         failing on exactly that ordering. Nothing was created (verified:
         empty issue list, no github_issue written, clean status). The
         fix is in the tool: --execute now requires --yes.

step 7   gate.py --docs, ITS OWN LANE, plus a CI job.
         fail-first  8 probes, 8 behaved as required, each PROVED on disk
                     before its red was believed.
                     docs/evidence/docs-gate-failfirst.txt + probe
         The probe-verification column earned itself on the first run:
         probe 1 reported MISSING while the gate went red -- the mutation
         had applied and the MARKER was wrong. Without that column the
         run would have read 8/8 with one probe unverified.
         Dangling KEYS fail; dangling LINKS do not. A broken key means
         the register lost a row; a link can be dangling and correct.
         ruff caught a py3.10 break (a 3.12-only f-string) before CI did.

step 8   .gitignore gains Screenshot*.png -- and nothing else happens.
         `_tot.png` needed no entry: `_*.png` already covered it, which
         corrects the read-back. No untracked file was touched. Proved on
         files that do not exist yet, the only way to test a rule whose
         subject is absent.

step 9   THE MAILBOX, and the reference count re-run from step 0.
         reference audit, same frozen module, same pattern set:
             413 -> 828 references (+415)
             tokens 55 -> 183:  LOST 0   gained 128   recount 5
             gained = 50 dnum (the permanent-key form, one per record)
                    + 78 mdlink (the first dense cross-linking)
             recount = 5, every one an INCREASE
             unresolved 0 -> 1: the historical link recorded at step 2
         NOTHING WAS LOST IN TRANSLATION -- lost=0 is the acceptance
         condition, and every difference above is an addition.
         handoff/ opens with 0001, the pair that produced this task.

step 10  TWO RECORDS CORRECTED, IN THEIR OWN COMMIT.
         The rule this step exists to establish: a content correction
         discovered during a structural move is NEVER folded into the
         move. It keeps the move's verbatim receipt intact and makes the
         correction visible instead of buried in a diff of relocations.
         Recorded in docs/defects/README.md, not just practised.
         D40  its condition was met 2026-08-03 and the row was never
              ticked. It required the message "3D view needs pip install
              -r requirements-viewer.txt" at the call site; that is
              mainwindow.py:532 (VIEWER_HINT), asserted at
              test_viewer_popup.py:139, guarded at app.py:27.
              closed_by 0a37581 (PR #8).
         D3   its Phase cell still read "is still open", written before
              P4.5 closed it -- the ONLY one of 50 records whose derived
              state disagreed with SESSION_SNAPSHOT.
              3 tests pass: test_group_survives_roundtrip (flipped
              xfail -> pass at P4.5, annotated "defect 3"),
              test_undo_after_grouping_restores_the_plan,
              test_group_move_undo_restores.
              closed_by 52a6aed (P4.5(19)).
         Neither record's Record, Site or Milestone was touched. They
         were true when written; the new ## Receipt section is the
         annotation. state_source: receipt marks the two.
         open records 13 -> 11.
         FINDING, reported not fixed: tests/test_characterization.py
         carries a stale comment above test 4 saying test 3 "stays
         xfail" -- test 3's own header two lines up says it flipped to
         PASS at P4.5. A contradiction inside one file, in test code
         rather than the record, so it is reported rather than folded
         into this commit for exactly the reason above.

POST-PR CORRECTIONS  2026-08-06  (PR #11 open, CI running)
         Later entries, not revisions -- this log is append-only and a
         correction is a later entry.

step 11  THE TWO FINDINGS FIXED, as their own commit per step 10's rule.
         test_characterization.py contradicted itself about test 3
         ("stays xfail" vs its own header two definitions above).
         DESIGN_MODEL_v5.md:3 pointed at docs/_superseded/, deleted at
         P0.1. ANNOTATED, not repointed: the named drafts were never
         committed, and docs/superseded/ is a different, later directory.
         Sending a reader there would have been worse than the dangling
         link.

step 12  THE AUDITOR HAD A BOUNDARY AND ITS DOCSTRING DID NOT SAY SO.
         Answer to the question asked at the report: NO, DESIGN_MODEL's
         dangling link was NOT in the pattern set -- it was found by eye.
         The step-1 commit message claimed the boundary was "stated in
         the tool"; it was not. That overclaim is corrected at source.
         docpath added (a backticked path under docs/) and MEASURED
         before being trusted: 108 refs, 23 targets, 6 unresolved -- and
         FIVE OF THE SIX ARE CORRECT (the P0.1 log naming the directory
         it deleted, this refactor's own explanation of that deletion,
         and two pre-P0.7 schema locations in historical text). So it is
         REPORTED, NEVER ENFORCED, like mdlink: enforcing would fail five
         correct records to catch one wrong one.
         The pattern set is now VERSIONED and --compare REFUSES a
         cross-version baseline -- a difference between two runs that is
         really an instrument change is the exact failure this tool
         exists to prevent. The set-1 baseline is kept byte-unchanged so
         step 9's lost=0 receipt stays reproducible.

step 13  THE --execute NEAR-MISS, RECORDED CORRECTLY, and the finding it
         produced.
         WHAT ACTUALLY PREVENTED IT: a missing-label ordering error. The
         IDEMPOTENCE GUARD DID NOT FIRE -- it only refuses records that
         already carry a github_issue, and none did. What stopped 50
         issues being created was the repository happening to lack a
         label. That is luck, not design, and attributing it to a guard
         would teach the wrong lesson.
         THE FINDING: none of the 15 labels or 20 milestones exist in
         GitHub, so the real migration would have failed the same way on
         the day it mattered. --create-labels added; --execute now CHECKS
         the precondition before creating anything and refuses with the
         list of missing labels and the remedy; the precondition is
         documented in docs/defects/README.md.
         Verified: 15 labels named, rc=1, nothing created.

step 14  THE UNTRACKED ROOT FILES -- observation upgraded to fact.
         Step 8 recorded that the eleven untracked scratch files were no
         longer on disk and declined to say why, having no way to see it.
         PATRICK CONFIRMS HE DELETED THEM, as the ruling anticipated.
         The earlier entry stands as written; this is the attribution.

COMMIT GATE ENFORCED  2026-08-06  (on main, after PR #11)
         THE ENFORCEMENT HALF OF "a green signal is only evidence about
         what it measures". The gate has always measured the right thing;
         nothing ever made RUNNING it unskippable. Four incidents sit
         behind that gap, and THREE OF THE FOUR were a claim ABOUT a gate
         rather than a gate -- a trailer transcribed without its
         ", 2 errors"; "515 collected" quoted after two more tests had
         landed; a reconciliation asserted against a number never
         computed. A guard reading the commit MESSAGE would have passed
         all three. So the hook reads the RESULT FILE.
         tools/gate.py now writes .gate-result.json (gitignored) at the
         end of a FULL-mode run -- verdict, census fields, timestamp and
         the trailer. --quick and --deep do not write it: each skips two
         of the three gates, and letting either satisfy the hook would
         make the guard weaker than the thing it guards. RED is written
         too, because "you did not run it" and "you ran it and it failed"
         are different states, and a guard that cannot tell them apart
         teaches people to delete the file.
         .claude/hooks/verify_gate.py blocks (exit 2) unless that file
         EXISTS, reads GREEN, and is NEWER THAN EVERY TRACKED FILE. The
         third condition is the one that matters: without it, a green
         result from an hour and six edits ago waves through the fourth
         incident.
         .claude/settings.json is COMMITTED, so the rule binds the
         project rather than one machine. No `if` filter: a prefix rule
         would miss the compound form (`git add -A` then git commit) and
         would not cover the PowerShell tool.
         fail-first  4 probes, 4 as required, each proved on disk first:
                     absent -> BLOCKS; RED -> BLOCKS; real green gate ->
                     PASSES; touch a source file -> BLOCKS (stale).
                     docs/evidence/commit-gate-failfirst.txt + 2 probes
         FINDING, found by the guard biting its own validation command:
         the first draft matched the phrase ANYWHERE in the command line,
         so an `echo` mentioning it was blocked -- and a `grep` for it
         would have been, in a repo whose documents are full of it. The
         match is now anchored to a COMMAND POSITION (start of line, or
         after ; && || |, optionally behind one prefix token). 7/7 on
         both classes: every real invocation form blocks, every mention
         passes.
         COST, recorded because it will surprise someone: a Bash command
         whose TEXT contains a command-position invocation -- a heredoc
         writing this very entry, for instance -- is itself blocked. It
         fails closed and the workaround is to put the content in a file,
         which is what produced this one.
         Stated boundary, because an unstated one reads as coverage: it
         does not catch `xargs`-fed commits, shell aliases, or a commit
         made outside these tools. It raises the floor; it is not a
         sandbox.
         Windows: plain `python` resolves on the PATH the hook inherits
         -- verified by firing the hook and watching it block, not by
         assuming. The settings file records the absolute-venv fallback
         for a machine where that stops being true.

COMMIT GATE -- A BOUNDARY MEASURED, 2026-08-06 (later entry, not a revision)
         Testing the LIVE hook end-to-end found a limit that reasoning
         about it had not. The check ran, approved, and an empty commit
         landed anyway -- because PreToolUse fires BEFORE the command
         runs, so the tree the hook inspects is the tree at APPROVAL
         time. The test command touched a source file and committed in
         ONE invocation; the touch happened after the verdict.
         So: a single call that edits tracked files and then commits is
         NOT covered by the freshness check. Splitting edit and commit
         into separate calls -- the normal working shape, and what every
         commit on this branch did -- is fully covered.
         NOT FIXED, and deliberately. Detecting "this command will modify
         the tree" means guessing which shell words write, which is
         fragile in both directions; and blocking compound commands
         outright would break `git add -A` followed by a commit, where
         staging changes no mtime. The honest move is the one the
         standing rule already prescribes: state the boundary at the
         instrument. It is in the hook's docstring beside the two limits
         already recorded there.
         The junk commit was local-only (the push had already happened),
         removed with `reset --soft`, tree clean, local and remote both
         at 7c628ba.
         The lesson is the rule this whole session keeps re-earning: a
         guard is only evidence about what it measures, and finding out
         what it measures takes a probe, not an argument.

A FABRICATED TRAILER, AND THE FIX  2026-08-07
         One commit into the GREEN batch (47f9675), two numbers in the
         gate trailer were WRONG. The gate had been run as
         `python tools/gate.py | tail -3`, so only the DEEP line and the
         verdict were ever on screen; the OFF and ON lines were typed
         into the commit message from an earlier run.
             quoted   OFF 17.28s   ON 20.55s
             recorded OFF 17.14s   ON 19.79s
         Everything that decides anything was correct -- collected=633,
         625/7/1 in all three modes, every sum reconciling, verdict
         GREEN, ruff clean, vacuous=0, end_assign=0 -- and the gate had
         genuinely passed. The fabricated part was two wall-clock
         durations, the least consequential figures in the block.
         THAT IS PRECISELY WHY IT IS THE SAME FAILURE as "515
         collected": a number copied from one moment into a sentence
         written at another, inside the one block whose whole purpose is
         to be beyond retyping. A trailer that is right about everything
         that matters and wrong about two numbers is still not a
         verbatim trailer, and the doctrine does not have a
         "close enough" clause.
         NEITHER EXISTING GUARD COULD CATCH IT. The commit hook checks
         that a fresh GREEN gate exists FOR THIS TREE; it does not read
         the message, and it was working correctly -- the gate really was
         green. gate.py printed the true block; it was truncated before a
         human read it. The hole was between the tool and the message,
         and nothing was watching there.
         FIX: `python tools/gate.py --trailer` re-prints the stored
         trailer verbatim from .gate-result.json, to be REDIRECTED into
         the message file rather than retyped:
             python tools/gate.py
             python tools/gate.py --trailer >> msg.txt
             git commit -F msg.txt
         The numbers stop passing through a human at all. This entry and
         the commit that carries it are the first to use it.
         NOT REWRITTEN: 47f9675 is pushed, and rewriting history is on
         the never-autonomous list. The commit stands and this is the
         correction, which is the same rule the register has always used
         -- annotate, do not rewrite.
         The incident is recorded in gate.py's own docstring beside the
         three it was built for, because a tool's failure history belongs
         at the tool.

G1 -- D43 NEGATIVE-ASSERTION COUNT  2026-08-07  (GREEN batch, item 1)
         The measurement the record asked for, and only the measurement.
         tools/negative_assertions.py, ast-based, evidence at
         docs/evidence/d43-negative-assertions.json.
             45 test files, 1598 assertions
             287 NEGATIVE (17% of all assertions)
             157 have a positive assertion earlier in the same test
             HIT RATE 54%
             130 bare assertions across 98 tests -- the read-first list
             shapes: not X=71 == empty=64 == 0=41 not in=36 == before=33 is None=30 !==12
         A CLASSIFIER FAULT FOUND BY SPOT-CHECKING BEFORE ANY NUMBER WAS
         QUOTED. The first draft counted `assert r.returncode == 0` as
         negative. `== 0` is two claims -- "this count is zero" (absence)
         and "this process exited zero" (success). test_model_imports_
         zero_qt was flagged for the success check while its REAL
         negative assertion lives in a string run in a subprocess, where
         no AST pass over that file can see it. Success probes excluded:
         291 -> 287 negative, 135 -> 130 bare.
         BOTH PROXY ERROR DIRECTIONS SPOT-CHECKED rather than asserted.
         Overcount NOT observed (3 of 3 sampled "established" rows
         asserted about the same subject as their negative claim).
         Undercount observed: test_ungrouped_walls_survive_gc establishes
         its precondition entirely BY CONSTRUCTION, which is not an
         assert, so the proxy calls it bare. The bare list is therefore a
         SUPERSET of the suspect ones -- the right error direction for
         sizing a read.
         PROPOSAL, sized by the number: read 130 assertions in 98
         tests, ~2 min each, a half-day; leave the other 157 alone.
         The list is enumerated, so it is a work-list, not a search.
         Still argued Phase 6. Nothing remediated here, by design.

G3 -- D27 WINDOWS CI LEG  2026-08-07  (GREEN batch, item 2)
         ci.yml gains a `windows` job: windows-latest, py3.13,
         QT_QPA_PLATFORM=offscreen, running the suite and the shadow-mode
         pass. The deep half closed at 65c4c02 (P3.8); this is the other
         one. UNTIL NOW NOTHING AUTOMATED HAD EVER RUN THIS SUITE ON THE
         PLATFORM THE APP IS PRIMARILY DEVELOPED AND USED ON -- every job
         in the workflow was ubuntu-latest. The register's own wording:
         the severity of a Windows-only fault does not drop with the
         repro environment, only the audience that sees it.
         ONE PYTHON VERSION, deliberately: the Linux matrix already
         covers the 3.10 floor and 3.13. What was missing is the
         PLATFORM, not another interpreter, and a second Windows entry
         would double the slowest job to re-test what is already tested.
         No Qt system libraries -- the PyQt6 wheels are self-contained on
         Windows, which is why the Linux jobs need six apt packages and
         this one needs none.
         Local evidence taken BEFORE the job ran anywhere, on this
         Windows machine, using the job's own two commands:
             pytest -m "not perf"                    625 passed, 7 desel, 1 xfail
             FP_VERIFY_DESIGN=1 pytest -m "not perf" 625 passed, 7 desel, 1 xfail
         Per the roadmap: a red Windows leg is A FINDING, not a failure of
         this task -- report and stop.
G2 -- D48 SCENE IDENTITY CHECK  2026-08-07  (GREEN batch, item 3)
         design.bridge.scene_identity_report -- REPORT-ONLY. It gates
         nothing, raises nothing, and no operation calls it.
         The question is the one WallItem.end_vertex already states: two
         ends are the same corner iff that returns the same OBJECT for
         both. For every pair of ends within WELD_TOL, are they?
         IT REPRODUCES THE REGISTER'S MEASUREMENT INDEPENDENTLY, from the
         live scene rather than from the walk:
             scene   16 walls, 20 distinct Vertex objects, 10 points
             split   4 points, carrying 4/4/3/3 vertices
             walk    20 -> 10 vertices, 16 -> 12 walls, merged=4,
                     unwelded_ends=0, check(deep) == []
         The register said 20 on 10 with corners of 3,4,4,3 and exactly
         that collapse. Same numbers, different instrument.
         The last two lines are the whole point: the corners are not
         shared AT ALL, the weld hides it, and all fifteen accept it.
         SCOPED THE WAY THE WALK IS SCOPED. Per floor, then per vertex
         namespace. A floating room has deliberately broken its sharing
         with the plan (I12), so its coincidences are correct, not
         faults -- a checker ignorant of that would report every parked
         float as broken. _partitions() was EXTRACTED from
         design_from_scene and is now called by both, so the walk and the
         check cannot disagree about which ends may be compared. One
         definition, not a second.
         differential  two walls meeting at (120,0), ends not shared ->
                       extra_vertices=1; after set_end_vertex -> 0.
         Two tests. The negative one ("silent on a clean plan") asserts
         its preconditions FIRST -- ends>0 and points<ends -- because an
         EMPTY scene is silent just as loudly. G1's finding applied on
         the day it was measured.
         A BUG THE FIXTURE HID: the first draft of the local fragment
         helper omitted win._sel_order, so room_boolean had no input and
         silently produced a scene with ZERO walls -- and the test failed
         on its own precondition rather than on its verdict, which is
         what a precondition is for.
         STILL OPEN. This record proposed running the check where
         --verify-design already runs. NOT done here: that changes what
         an operation produces (AMBER), and the corpus consequence the
         record names -- legacy loads arrive unwelded BY DESIGN, P2.1 --
         is the scoping question that must be answered first. G2 delivers
         the instrument; where it runs is a separate ruling.
G4 -- D42 DRAG-SIDE SELF-INTERSECTION REPORT  2026-08-07  (GREEN batch, item 4)
         WallItem._report_deformed_rooms, called at drag release. The
         SAME report_self_intersections the group bake calls -- same
         predicate, same words, same remedy. No new semantics; one new
         caller.
         AT RELEASE, NOT IN _DragVertex.apply. The record names the
         applier as the site and the applier is the wrong place: it runs
         on every mouse-move event, the view repaints everything on each,
         so an edges-squared check there is the per-event cost the drag
         was built to avoid -- and the message would fire and clear
         dozens of times inside one gesture. A fault is worth saying
         once, when the gesture ends.
         SCOPED BY IDENTITY (defect 30's lesson): rooms_holding over the
         corners this drag moved, from _vmoves (body) and _ep_move
         (endpoint), each holding its CURRENT vertex because apply
         rebinds it. self.rooms would have been the wrong gather -- a
         room can hold a moved corner while owning no wall in the run,
         and that room is exactly the one that deforms.
         measured  L-room (0,0)(200,0)(200,100)(100,100)(100,200)(0,200),
                   inner edge slid 150" left:
                   outline (100,100)(100,200) -> (-50,100)(-50,200)
                   edge (200,100)-(-50,100) now crosses (0,200)-(0,0)
                   "Ell's outline now crosses itself - undo, or extract
                    the room before moving it."
         A BODY drag, not an endpoint drag, and not incidentally: a wall
         bound to a room has LOCKED ENDS (_ends_editable), so sliding the
         run is the gesture actually available -- which is why the
         exposure was real rather than theoretical.
         THE SECOND TEST IS THE ONE WORTH HAVING. A wall drag is the
         commonest gesture in the app; a check that fired on ordinary
         work would be worse than no check. test_an_ordinary_drag_says_
         nothing asserts silence WITH the precondition that the drag
         really moved the room -- silence is otherwise satisfied by a
         gesture that did nothing.
         STILL OPEN, scope unchanged: three appliers are still three.
         This adds a caller, it does not unify them. The consolidation is
         the Phase 6 task the record argues for; MoveVertices is the seam.

A1 -- D47 FRAGMENT PRODUCES FLOATING ROOMS  2026-08-07  (AMBER, awaiting the
         manual check)
         room_boolean("fragment") now EXTRACTS each piece instead of
         wrapping its walls in a GroupItem. The op's own comment already
         named the property -- "moves as a self-contained, fully-enclosed
         unit" -- and was written before extract existed.
         differential, on the record's own two-room case:
             room_owns_walls   false for all 9 pairs -> true for all 3
             shared walls      the defect            -> 0 for all pairs
             drag +300/+300    4/4 walls, 0/16 corners -> 4/4 and 4/4
             open_edges after  {Ov 2, R1 1, R2 1}    -> {0, 0, 0}
             groups            3                     -> 0
             orphan walls      4                     -> 0
             vertices          20 on 10 points       -> 18 on 16
             check(deep)       CLEAN                 -> CLEAN
         THE SUITE'S LAST XFAIL IS GONE. The marker promised "flips when
         fragment converts to extract"; it flipped, and it is a hard pass
         now so it can regress. Census reads 632 passed, no xfailed.
         TWO THINGS THE FIRST CUT GOT WRONG, both found by measuring:
         (1) extract alone left 4 ORPHAN WALLS -- bind_room_walls binds by
         geometry and fragment builds one wall per region, so a room could
         be bound to a neighbour's coincident copy, which extraction then
         copy-trimmed, leaving the original bound to nobody.
         _claim_region_walls narrows the candidate set to the region's own
         list; geometry still decides which wall covers which edge.
         (2) a _weld_region_loop pass was written, measured (12 -> 6 on a
         six-wall loop, so it worked), and REMOVED -- it made no
         difference to the final state because bind_room_walls re-splits a
         corner downstream. Code that demonstrably does nothing is worse
         than none. The residual (18 vertices on 16 points, inside one
         floating room's own namespace) is recorded against D48, where the
         mechanism lives.
         AMBER: stops at the PR. The manual check is Patrick's --
         fragment a room, move a piece, confirm it carries its region and
         that no dashed edge lies over a real wall.

THE ONE-CALL RULE, REFINED BY USE  2026-08-08
         It blocked the intended workflow within a day of shipping.
         `gate.py --trailer` matched GATE_RUN_RE, so building a commit
         message and committing in one call was refused as "runs the gate
         AND commits" -- but --trailer RUNS NOTHING and WRITES NOTHING. It
         reprints the stored verdict so a message can quote it verbatim,
         which is the very mechanism that closed the fabricated-trailer
         hole, and it is exactly the command that BELONGS beside a commit.
         Exempted: GATE_RUN_RE now ignores an invocation carrying
         --trailer. Same shape of fault as the command-position fix a day
         earlier -- a guard right in principle and one case too broad --
         and found the same way, by the guard biting real work.
         The probe gains a seventh case, and it asserts the REASON rather
         than the exit code: --trailer beside a commit is still
         verdict-dependent (it can be refused for STALENESS, and was, on
         a tree edited after the last run), but it must NEVER be refused
         AS A RUN. A case that only checked rc would have passed while
         the exemption was broken.
         7 probes, 7 as required.

D72 -- THE IMPORT-TIME ASSET WRITE, FIXED  2026-08-15  (GREEN, auto-merged)
         files:   _gen_assets.py  tests/test_gen_assets.py (comments only)
         The module-level write-everything body -- the FURNISHINGS/SOLIDS/
         MATERIALS consistency check through the final print -- now lives
         in main(), called under `if __name__ == "__main__":`. Everything
         above stays importable with NO SIDE EFFECT: `import _gen_assets`
         writes nothing and creates no directories (the mkdir calls moved
         into main() too).
         THE OBVIOUS RECEIPT WAS THE WRONG ONE, AND SAYING SO IS THE
         FINDING. Hashing the checked-out assets/ tree before and after
         running the script reported 13 files differing -- every one a
         CRLF PHANTOM-DIFF (CLAUDE.md: .gitattributes forces LF in the
         repo, but this working tree still checks out CRLF), reproduced
         IDENTICALLY against the unmodified generator from HEAD. Chasing
         it further would have been chasing a fact about the checkout,
         not about the change.
         THE CONTROLLED RECEIPT: run the unmodified generator once and the
         modified one once, same session, both into a clean checkout, and
         diff the two OUTPUTS against each other rather than against a
         checked-out blob.
             diff -rq <old-code output> <new-code output>
             IDENTICAL: no output-content difference from the refactor
         That isolates the one variable the receipt is actually about.
         git diff --stat -- assets/ on the final tree is clean; D70's
         tests pass unchanged, because the wrap preserves statement order
         and only shifts indentation.
         D71 -- QSvgRenderer RENDERABILITY CHECK, filed alongside D72 and
         fixed in the same pass  2026-08-15  (GREEN, auto-merged)
         files:   tests/test_furnishings.py
         THE RECORD'S PROPOSED METHOD WAS WRONG, MEASURED BEFORE TRUSTING
         IT (the positive-control rule). isValid() was proposed as the
         check that catches "well-formed XML that draws nothing" -- and
         isValid() returns True for an <svg> with NO CHILDREN AT ALL, and
         for one whose only child is a tag Qt's SVG module does not
         implement. It only re-detects XML that fails to PARSE, which
         svg_error already refuses before writing -- so using it alone
         would have made the new test a second copy of D70's check, not
         new coverage.
         THE INSTRUMENT THAT ACTUALLY WORKS: render to a buffer, look for
         a painted pixel. A positive control proves it catches two
         synthetic blanks isValid() missed, and that a real symbol still
         passes.
         THE CONTROL THEN CAUGHT A SECOND BUG, IN ITS OWN FIRST DRAFT:
         sip.voidptr.__getitem__ returns a length-1 bytes per index, which
         is TRUTHY REGARDLESS OF VALUE (bool(b'\x00') is True) -- so the
         first cut of the pixel scan reported EVERY pixel as painted,
         including a genuinely blank image. bytes(ptr) first, then index,
         fixes it. The control is why this was caught before it shipped
         as an always-green check.
         test_every_catalog_symbol_renders_something then walks all 95
         catalog entries through furnishing_renderer, the PRODUCTION
         accessor, per the record's original (correct) half. FAIL-FIRST
         CHECKED by blanking a real symbol (glass_shower.svg -> an empty
         <svg/>) and confirming the sweep names it; restored from git.
         Both closed as filed, with D71's method corrected from what was
         proposed to what measurement showed was needed -- ordinary
         defect-closure prose, not a handoff ruling: neither record's
         technical shape needed a policy decision, only correct execution.
```

0028 -- SESSION_SNAPSHOT.md AND handoff/README.md TRIMMED TO THEIR STATED JOB  2026-08-16  (GREEN)
         handoff: 0028 (ruling)
         files:   docs/SESSION_SNAPSHOT.md  docs/handoff/README.md
         Differential receipt, measured before and after, per 0028's own
         instruction that a cut with no receipt is indistinguishable from
         a tidy-up nobody measured:
             SESSION_SNAPSHOT.md   600 lines / 41,093 B  ->  268 lines / 18,006 B
             handoff/README.md         -- / 26,906 B  ->  156 lines / 10,211 B
         No fragmentation (one file, one marker, one gate, as ruled). The
         queue sections collapse to current-item-plus-next-two with one
         link each into the ruling that owns them; "the rules that bind"
         becomes names and one link into WORKING_AGREEMENT.md, dropping
         the reasoning that document already carries in full; Phase 6's
         park collapses to its verdict plus a link to ROADMAP.md's own
         copy. Kept as-is: the gate-condition header, the state table,
         "how to read the record," and the traps list -- which gained
         three entries from this session's own findings (the commit
         hook's gate.py substring match, fp3d.py's GL/offscreen limit,
         and the shallow-fetch parent-hiding behaviour D78 measured).
         handoff/README.md's pair table goes from dense multi-sentence
         paragraphs to one line per exchange; the protocol prose at the
         top is untouched, per the ruling -- it is the channel contract,
         not a copy of anything.
```

D67-ADJACENT CROSS-FLOOR INVESTIGATION -- 0037's SUSPECT REFUTED  2026-08-17  (GREEN, measurement only, no code changed)
         handoff: 0035 (ruling, Patrick's report), 0036-ruling.md (ruling,
                  the snap-vs-paint discriminator -- COLLIDES with this
                  session's own 0036-report.md, both committed, not
                  renamed), 0037 (ruling, names a suspect), 0038 (report)
         files:   none -- inspection plus a headless probe against an
                  existing fixture, no assertion added

         0037 SS2 CLAIMED the v5 load path calls set_floor_state(active=...)
         and nothing else, so apply_floor_visibility (reachable only
         through _sync_floor_state()) never runs after a load -- and named
         that as the single cause of both the "wrong after release" and
         "light gray bleed through" symptoms.

         MEASURED, AND IT DOES NOT HOLD. apply_design_to_scene
         (floorplanner/design/bridge.py:1265-1266) already calls
         win._sync_floor_state() -- present since 2026-07-26 (git blame,
         commit 2678ff5), three weeks before the report. Loaded Patrick's
         own submitted plan (fixtures/incoming/crossfloor-snap-2026-08-17.json)
         headless through the real MainWindow.open_document(): with
         default settings, the upper floor comes out fully hidden and
         disabled (0/45 visible, 0/45 enabled), the default floor fully
         visible and enabled (106/106 each); with show_other_floors
         pre-set True (simulating carried-over session state), the upper
         floor ghosts correctly -- visible, gray, disabled. Neither run
         reproduces anything reported.

         REOPENS 0036's own document-diff discriminator (save before the
         gesture, make it, save after, diff the files), never run --
         still needed, and still blocked on facts neither ruling nor the
         intake file states: was show_others actually on when it
         happened, and did the wall stay moved after release. The intake
         file has no .txt companion note. Does not touch 0035's
         hypothesis A (a query path with no floor filter) at all --
         genuinely still open if geometry turns out to have moved.

         ALSO CHECKED SS5's more general claim (a derived property with
         one manual call site): all three bare set_floor_state() calls
         found (levels.py:50 -- inside _sync_floor_state itself;
         planio.py:236 in apply_project_to_scene, which also calls
         _sync_floor_state() at line 313; bridge.py:1134 in
         apply_design_to_scene, which also calls it at line 1265) are
         each followed, in the same function, by the complete sync. The
         enumeration is still worth finishing properly, but none of the
         three found here is the missing-invalidation case the rule
         warns about.
```
