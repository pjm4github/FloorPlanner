# Progress log - Phase 4 - rooms as durable movable units (part 1)

> **Moved verbatim** from `V5_MIGRATION_PLAN.md` (its lines 3519-4360 as of
> commit 2f232bd) on 2026-08-06. Nothing was reworded, reordered, tidied or
> reformatted; the entries appear in the order they were appended. The code
> fence below is the one the log has always been written inside - it is
> reopened here and closed at the end, because a fence cannot be split.
>
> Index: [`README.md`](README.md) - Plan: [`../V5_MIGRATION_PLAN.md`](../V5_MIGRATION_PLAN.md)

```
P4.1  done   (branch p4.1-delete-wall, 3 sub-commits: 0df3aa5 census
         corrections + the three rulings; a0e1b95 delete_wall + both call
         sites + 2b flip; this commit, corpse + tests + docs)
ruff:    clean
pytest:  514 passed, 7 deselected, 5 xfailed (OFF/ON/DEEP each, sum 526 OK)
files:   walls.py (delete_wall added; fracture_delete_wall + _merge_intervals
         DELETED, 66 lines; context-menu call site), mainwindow.py
         (delete_selected), rooms.py (docstring corrected),
         tests/test_characterization.py (2b marker off),
         tests/test_walls.py + tests/test_room_walls.py (fracture trio
         renamed/replaced), CLAUDE.md, docs/CODE_REVIEW_v2.md (defect 17
         closed with coda; defect 25 -> P4.1b ruled; carried census note),
         this file.
notes:   CENSUS DOCTRINE APPLIED at task open, and it earned its keep a third
         time: _perimeter_span does NOT die here -- _copy_spec (unowned) and
         _privatize_shared_walls (P4.2's) both outlive fracture -- so the
         deletion is 66 lines, not the ~90 the task-line record implied.
         Stated as a contingency in the register (authoritative copy) so
         P4.2's read-back inherits a question, not a claim.
         RECEIPT, fail-first: 2b re-measured xfailing against main@5a7711c
         this session, then flipped green on exactly the call-site switch --
         513 passed / 6 xfailed -> 514 / 5, nothing else moved. Census 526
         unchanged across all three sub-commits (tests replaced 1:1).
         VISIBLE-LIE CODA now in defect 17's closing entry: post-P3.7 the
         fracture no-op measured 4 bound walls + 1 OPEN edge (the outline
         still naming the dead wall fracture replaced), i.e. a dashed open
         cue painted over an edge a wall actually covers. The silence had
         aged into misinformation -- the final argument for deletion over
         repair.
         TESTS CHANGED -- all four declared at the read-back, approved before
         work began: characterization 2b (marker off; IS the acceptance);
         test_delete_free_wall_removes_whole (behaviour preserved through the
         new delete_wall entry point); test_delete_overhanging_wall_goes_
         whole_room_keeps_area and test_delete_shared_wall_keeps_both_rooms
         (INTENTIONALLY replace the fracture-era pair: the wall genuinely
         goes; each bordering room keeps its area with one open edge -- the
         party-wall numbers measured at the read-back: 100.0 sf, 3 bound +
         1 open each).
         Defect 25 deliberately NOT touched here: P4.1b branches the moment
         this task's PR merges, message-only scope per its task text.

P4.1b done   (branch p4.1b-doorway-message: 1d3eaa6 mechanism + tests;
         this commit, docs)
ruff:    clean
pytest:  516 passed, 7 deselected, 5 xfailed (OFF/ON/DEEP each, sum 528 OK)
files:   walls.py (report_gesture_fault / drain_gesture_faults /
         report_doorway_landings + the endpoint-drag release hook),
         view.py (draw-release hook), mainwindow.py (_commit_if_changed
         drains the new list beside the defect-6 report), tests/
         test_walls.py (two gui tests), docs/CODE_REVIEW_v2.md (defect 25
         closed), this file.
notes:   REPORT ONLY, per the ruling -- no change to what the gesture DOES;
         decline/split/weld policy stays P4.3's with the auto_* flags (the
         dissent's surviving kernel). The straddle question is asked of
         plan_split_edge -- one planner, no second definition of "a junction
         lands inside this opening" (P3.4 point 1). The body search runs at
         ON_SEG_TOL, not JOIN_TOL, so a deliberate reveal (a wall stopped
         short of another) never nags -- only an end ON the body, whose
         junction is genuinely owed a split, reports. The drag checks only
         the end it moved (ends=(mode,)), so an old landing on the far end
         is not re-announced by an unrelated drag.
         CHANNEL: the defect-6 discipline exactly (scene-filed, drained at
         the debounce, said once, the sentence naming the edit and the
         thing in the way) as its OWN list -- nothing failed to be PLACED,
         so draining through "Could not place ..." would misblame a door
         that is fine. Drained after the opening report so the gesture the
         user just made wins the status bar.
         RECEIPT, fail-first and mechanism-proving: both tests run UNCHANGED
         against pre-fix main@708dc2e in a worktree, reach their
         preconditions (the drawn/dragged end measurably rests on the
         host's centreline inside the door span -- the defect-28 vacuity
         lesson applied), and FAIL on the message assert, the status bar
         holding only the generic tool hint. Both pass on the branch.
         Census 526 -> 528 (the two gui tests), every sum reconciling.
         The walk's report path (R2c) is untouched and stays as the
         load-path safety net, exactly as the register entry planned.

P4.2  done   (branch p4.2-extract-join, 7 sub-commits: dfd30af core,
         4cf67e8 label-drag rewire, 9821571 defect 30, 5c8795e the P2.3
         refutation, 7dbd740 defect 13, 216e755 defect 34, + this docs
         commit. AWAITS THE PATRICK MINI-GATE before its PR merges.)
ruff:    clean
pytest:  525 passed, 7 deselected, 4 xfailed (OFF/ON/DEEP each, sum 536 OK)
files:   extract.py (NEW: extract_room/join_room/capture_floating_
         furnishings), rooms.py (placement modelled; label-drag =
         extract->move->join; _privatize_shared_walls DELETED, 51 lines;
         floating paint cue; context menu Extract/Join), design/bridge.py
         (placement emit/apply; stash retired for placement; per-floating-
         room vertex namespaces in the level walk), design/validate.py
         (I14 floating exemption; near_vertex_gaps), walls.py (defect-30
         gather; defect-13 stick; close_gap), dialogs.py (GapReviewDialog),
         mainwindow.py (Review wall gaps... action), CLAUDE.md, register,
         tests: test_extract_join.py (NEW), test_groups.py (party-wall
         flip), test_room_walls.py, test_wall_move.py, test_walls.py.
notes:   CORE FIRST, HARVEST AFTER, per the ordering constraint -- each
         piece its own sub-commit at a full green gate.
         ACCEPTANCE MET: extract -> move 500" -> join, check() clean at
         EVERY step, I12 while floating, furnishings and openings intact;
         the party-wall round trip fuses back to ONE shared wall; the
         party-wall regression test flipped xfail -> hard pass via the
         real extract (P0.5 Known-regressions row closes).
         TWO MODEL CONSEQUENCES, not workarounds: the level walk folds
         each floating room in its OWN vertex namespace (coincident-is-one-
         corner is exactly the sharing I12 breaks), and I14 exempts
         floating-vs-plan pairs (closure within a floating room still
         holds) -- same exemption class as I11.
         RULINGS EXECUTED: (a) label-drag rewired, behaviour-preserving by
         construction (the old path already WAS extract->move->join in old
         clothes); (b) defect 30 fixed as a BUG (holders of the corner via
         vertex identity; 23-vs-30 boundary stated for P4.5); (c) defect 34
         closed as the review op (list, never auto-close); (d) defect 13's
         drag half closed (stick -> scene-space WALL_PROJECT_STICK, 9",
         == join_tol_in; catch radius stays screen-space); (f)
         _perimeter_span re-argued to P4.4 in the register, contingent,
         not counted in this census.
         RULING (e) REFUTED BY THE TREE, reverted, recorded: the vertex-
         adjacency run gather turned P3.3's anti-shear pins red --
         _tee_scene is topologically IDENTICAL to the undo-split segments,
         and "split first, shear never" owns that topology with three
         tests. The P2.3 row's SECOND predicted fix to fail on its own
         terms; the row now needs a carry-vs-stay RULING, pinned by the
         xfail test_a_roomless_split_wall_body_drags_as_one_run.
         TESTS CHANGED, all declared: the party-wall flip (route only,
         assertions unchanged); test_moving_a_room_does_not_distort_its_
         neighbour drives extract_room (follows the mousePress it always
         mirrored). Census 528 -> 536 (3 acceptance + 1 conflict pin +
         1 zoom pin + 3 gap tests), xfails 5 -> 4 net (party-wall and
         defect-30 flips out, P2.3 conflict pin in).

         THE PATRICK MINI-GATE (P4.2 is the first task under the ruling --
         the PR does NOT merge until this passes; ~15 min, stated
         expectations, Gate-3 style):
         1. EXTRACT: open planc1TestV5.json, right-click a room with
            shared walls -> Extract room. Expect: room reads floating
            (warm fill, dashed boundary, "(floating)" under the name); the
            plan keeps every wall; neighbours unchanged; no warning.
         2. FLOAT-MOVE: drag it ~500" away by its name. Expect: walls +
            doors + furnishings + region move as one unit; nothing else
            moves; nothing welds in passing.
         3. JOIN: place it beside existing walls -> right-click -> Join
            room into plan. Expect: coincident walls merge, no doubled
            wall, no duplicated openings; room reads placed.
         4. THE OLD WORKFLOW UNCHANGED: plain label-drag a PLACED room one
            bay over. Expect: exactly the old behaviour -- party wall
            stays with the neighbour, room re-merges on drop, furnishings
            stay put.
         5. UNDO back through all of it. Expect: each step reverses
            cleanly.
         6. DEFECT 30: body-drag a party wall at a 4-way corner. Expect:
            every room touching that corner follows; no stranded dashed
            outline.
         7. DEFECT 34: Edit > Review wall gaps... on planc1TestV5.json.
            Expect: the known 1.53"/6.003" pairs listed with distances;
            closing one 1.53" pair welds it; the 6" pairs left alone stay;
            the saved file is otherwise unchanged.
         8. FLOATING ROUND-TRIP: save while a room is floating -> close ->
            reopen. Expect: still floating, everything intact, and
            tools/validate_design.py on the saved file -> PASS/PASS.

P4.2+ mini-gate finding: DEFECT 30's FIRST CUT CORRECTED (item 6 caught it)
ruff:    clean
pytest:  527 passed, 7 deselected, 4 xfailed (sum 538 local; CI sees 536 --
         the two extra are Patrick's untracked examples/symmetricP2/P3.json
         picked up by the corpus validation, both green, not committed)
files:   walls.py (_plan_vertex_moves steps 1+4), tests/test_wall_move.py
         (pin revised), docs/CODE_REVIEW_v2.md (row 30 corrected), this file.
notes:   Patrick ran item 6 on symmetricP3 and the blanket follow tore a
         DIAGONAL across Foyer and Great Room -- their boundary at the
         corner is the CONTINUATION, which the anti-shear split holds
         still, so dragging their corner off it was the first cut's own
         error, screenshot on file (Screenshot 2026-08-01 162708.png).
         CORRECTED: the split makes the old corner TWO corners, and each
         room's corner goes with ITS OWN BOUNDARY -- run-bordered rooms
         follow the moved vertex; continuation-bordered rooms re-point to
         the stationary twin the split mints (now recorded in step 1).
         The pin is revised to the corrected expectation and renamed
         (test_a_dragged_corner_splits_by_each_rooms_own_boundary), with a
         no-diagonal assertion so the tear cannot come back. Fail-first:
         red against the first cut in a worktree ("borders the continuation
         but was dragged off it"), green on the correction. Verified on
         pristine symmetricP1: Foyer/Great Room outlines unchanged through
         a 24" down-drag, Dining/Kitchen resize, zero new off-axis edges
         (the four flagged are a pre-existing 0.3" skew at (582.3, 483.6)
         in the shipped example itself, below the weld band, identical
         before and after).
         NOTE for the re-run: symmetricP3.json still CONTAINS the damage
         from the bad-drag session -- re-cut it from symmetricP1 before
         re-running item 6, or drag and undo on the fixed build.

P4.2+ mini-gate finding 2: CLOSE_GAP STRANDED OUTLINES (item 7 + a drag)
ruff:    clean
pytest:  528 passed, 7 deselected, 4 xfailed (sum 539 local; CI 537 -- the
         two extra remain Patrick's untracked example files)
files:   walls.py (close_gap), tests/test_walls.py (invariant pin),
         docs/CODE_REVIEW_v2.md (row 34 corrected), this file.
notes:   Patrick closed symmetricP1's reviewed gaps, then dragged the
         M Bath/Lounge wall down -- and M Bath, Hall and Lounge drew dashed
         DIAGONALS to corners their walls no longer held (Screenshot
         2026-08-01 170311.png). Not deferred recalculation -- there is no
         later recalculation since P3.5, by design; outlines follow walls
         only through shared vertex IDENTITY, and close_gap's first cut
         broke exactly that: it folded WALL ends onto one anchor
         (share_coincident_ends) but left the OUTLINES holding coincident-
         but-distinct twins, so the next drag moved the walls' corner and
         stranded the rooms'. FIX: after the fold, every room on the floor
         re-adopts its walls' corner vertices (share_outline_vertices, the
         load path's own discipline, late-imported per the cycle rule).
         RECEIPTS, fail-first: the invariant pin (every outline corner IS
         one of its room's wall-end vertices, by identity) red against the
         first cut in a worktree, green on the fix; end-to-end headless on
         symmetricP1: both 6.003" gaps close (1 weld each at (379.4, 456)
         and (379.4, 654)), stranded corners 0, and the M Bath/Lounge 24"
         down-drag adds ZERO diagonals (the four flagged are the file's
         own pre-existing 0.3" skew at (582.3, 483.6), below the weld
         band, identical at load and untouched throughout).

P4.2+ mini-gate finding 3: THE MIXED CORNER (partial-side run coverage)
ruff:    clean
pytest:  529 passed, 7 deselected, 4 xfailed (sum 540 local; CI 538 -- the
         two extra remain Patrick's untracked example files)
files:   walls.py (_plan_vertex_moves step 4: mixed-corner step surgery;
         collapse_degenerate_outline_edges + release/close_gap call sites),
         tests/test_wall_move.py (step pin), docs/CODE_REVIEW_v2.md (row
         30, third finding), this file.
notes:   Patrick: clean gaps, drag the Master Suite / M Bath wall down --
         diagonal across Hall (Screenshot 2026-08-01 172305.png). NOT the
         stranding class (the invariant held, 0 stranded); a genuinely
         deeper case: the dragged run is Master Suite's WHOLE south side
         (x 30..330) but Hall's top side extends past the run's end
         (330..396, backed by the Clst|Hall wall -- a continuation, which
         correctly stays). Hall's corner at x=330 is run-backed on one
         adjacent edge and continuation-backed on the other; one corner
         cannot serve two stretches that now sit on different lines --
         follow tears the continuation stretch (the diagonal seen), stay
         tears the run stretch. FIX, outline surgery at drag start (the
         same moment the anti-shear split runs): the mixed corner becomes
         TWO corners joined by an OPEN step edge (wall: null, drawn dashed
         -- at insert time there genuinely is no wall on the jog; the
         stretched perpendicular wall covers it after the drag, so the
         dash-over-wall is a known presentational wrinkle, noted not
         hidden). Hygiene: collapse_degenerate_outline_edges drops
         zero-length edges -- the welded corner pair a closed gap leaves
         in a room that held both corners (the Hall doubled-corner residue)
         and a step whose drag ended where it began -- unbinding a wall
         whose only naming edge was the zero one.
         RECEIPTS, fail-first: the step pin (4-room replica: run-bordered
         rooms follow, Clst byte-still, Hall gains the OPEN step at the
         run's end, everything axis-aligned) red against the pre-fix tree
         in a worktree, green on the fix. End-to-end on symmetricP1: clean
         gaps -> drag Master Suite/M Bath 24" down -> 0 diagonals, 0
         stranded, Hall = (248.4,678)(330,678)(330,654)(379.4,654)
         (396,654)(396,714)(248.4,714) exactly, Clst untouched, doubled
         corner gone.

P4.2+ mini-gate: DEFECT 35 FILED (residual drag report, shelved), and the
         version label added so the next report carries its code identity
notes:   Patrick reported residual drag diagonals after the mixed-corner
         fix and shelved them; filed as register row 35 rather than lost.
         The replay of the exact sequence on the fixed tree is clean twice
         over (outline edges AND painted cue segments), the reporting
         session's code identity is unverifiable (it predates the label),
         so the row records the report, the clean replay, both candidate
         explanations (stale process vs uncovered gesture), and the
         re-open protocol: reproduce with the status-bar version label
         visible (launch >= a1e6083) plus the gesture sequence. The P4.2
         mini-gate re-run decides: confirmed -> fixed before the PR
         merges; unreproduced with the label -> closed as stale-process.
         (a1e6083: status bar + About now show "v1.2 - <branch> @ <sha7>",
         captured at LAUNCH, with two pins -- names the checkout, and
         launch-stable.)

P4.2+ mini-gate finding 5 (via fiveRoomDragSplit.fpm): a three-bug cascade
ruff:    clean
pytest:  534 passed, 7 deselected, 4 xfailed (sum 545)
files:   extract.py (join merges at SHARE_TOL), rooms.py
         (split_partially_covered_edges, junction-degree guarded),
         walls.py (run-wide tee gather; release repair pass),
         tests/test_extract_join.py (macro pin),
         examples/fiveRoomDragSplit.fpm (Patrick's reproduction), this file.
notes:   Patrick's macro (drag R2 out/back 6" offset, slide the R3|R4 wall,
         slide the R1|R3 wall) tore R1 and R4 diagonal. THREE distinct
         bugs, each measured before being touched:
         (a) JOIN MERGED AT THE WRONG TOLERANCE: merge_wall's default
         perp_tol is the 6" auto-coalesce snap, so a room dropped a
         gesture-width off SNAPPED ITS NEIGHBOURS' WALLS onto its own line
         -- R4's north wall physically moved 6" to meet the offset R2,
         stranding R4's outline. The join now merges at SHARE_TOL (0.6",
         vertex_weld_in): at or below it two lines ARE one; beyond it
         nothing moves -- the join's own stated rule, now obeyed by its
         merge step.
         (b) PARTIAL COVER IS A LATENT TEAR: an outline edge NAMED by a
         live wall that covers only part of it follows at only one corner
         on the next drag -- the diagonal. split_partially_covered_edges
         (release + join): the coverage boundary becomes a real corner
         HOLDING THE WALL'S OWN END VERTEX, so later drags carry it by
         construction; the remainder re-binds or stays honestly open.
         GUARDED BY JUNCTION DEGREE: only a vertex held by 2+ wall ends
         splits -- a DANGLING end mid-edge is the deliberately-opened side,
         whose openness stays DERIVED so dragging the end back re-closes
         it (test_closing_gap_refuses_and_relocks caught the unguarded
         version freezing the gap open; it passes unchanged now).
         (c) THE TEE GATHER TESTED ONLY SELF'S BODY: an end resting
         mid-span of another RUN member was invisible, so the run slid out
         from under a mid-run corner, leaving it floating. Body landings
         now test against every run wall -- the run slides as one line.
         RECEIPT, fail-first: the macro pinned VERBATIM
         (test_drag_split_macro_keeps_every_room_rectilinear -- after
         EVERY line, nothing diagonal and no edge names a wall that does
         not span it), red against the pre-fix tree in a worktree, green
         on the fixes; the full replay is clean at every step, R1 ending
         as the correct stepped shape, R4 with the correct tee corner.
         Census 544 -> 545, sums reconciling.

P4.2+ mini-gate finding 6 (via fiveRoomDragSplit2.fpm): three more, fixed
ruff:    clean
pytest:  535 passed, 7 deselected, 4 xfailed (sum 546)
files:   rooms.py (repair_edge_bindings, grown from rebind_dead_edges:
         upgrade-only rebind of live-but-outspanned edges; the deliberate-
         open guard moved from junction degree to _corners_unlocked),
         walls.py (_split_outline_landings; spike collapse in
         collapse_degenerate_outline_edges; release repair re-adopts
         wall corner vertices), tests/test_extract_join.py (macro pin),
         examples/fiveRoomDragSplit2.fpm, this file.
notes:   Patrick's 13-gesture macro seeded and tore through THREE more
         mechanisms, each introspected to its exact site before touching:
         (a) MISBOUND EDGE: an edge named a collinear NEIGHBOUR wall that
         covered none of it while the exactly-matching wall sat right
         there (_edge_wall's partial-cover acceptance grabbed the wrong
         candidate during an earlier repair). repair_edge_bindings now
         also fixes live-but-outspanned names, UPGRADE ONLY (rebind solely
         when the candidate fully spans -- a legitimately short detached
         wall is never swapped). The junction-DEGREE guard from finding 5
         was WRONG and is replaced by the explicit workflow flag
         (_corners_unlocked): a slid wall can leave a genuinely dangling
         structural end mid-edge.
         (b) OUTLINE-CORNER TEE: a pure room corner resting mid-span on
         the run wall's BODY -- no wall end there at all, so the tee
         gather cannot see it -- and the run slid out from under it.
         _split_outline_landings (drag start, beside the wall-end tee
         pass): cut the run wall at the corner, point every coincident
         outline corner at the split vertex; identity is what rides.
         (c) COLLINEAR SPIKE: a zero-area overshoot (A->B then straight
         back) left where a stationary corner was passed by its sliding
         side; collapsed as a degenerate, iteratively, walls unbound when
         their last naming edge goes.
         Release repair also re-adopts wall corner vertices
         (share_outline_vertices) so coincident-but-distinct outline
         corners cannot accumulate.
         RECEIPT, fail-first: the macro pinned VERBATIM (after EVERY line:
         nothing diagonal, no edge names a wall that does not span it) --
         red against 6f3e2b9 in a worktree, green here. Both earlier
         macros replay with zero violations (no regression). Census
         545 -> 546, sums reconciling.

P4.2+ tooling & floors run, 2026-08-02 (sub-commits 16-23; consolidated
         here, details in the commit messages, each at a full green gate)
pytest:  543 passed, 7 deselected, 4 xfailed (sum 554 local; CI 552 --
         the two extra remain Patrick's untracked symmetricP2/P3 examples)
THE RECORDER, made whole (16-19) -- keyboard capture was broken THREE
         separate ways, each found by Patrick's restart-and-retest and
         each now pinned by a test replicating the REAL Qt delivery order:
         (16) shortcut-consumed chords never arrive as KeyPress ->
              capture ShortcutOverride too;
         (17) the `obj is viewport` mouse branch ran FIRST and ate every
              canvas keystroke (keyboard recording had never worked in
              the app); keys are dispatched by event TYPE now. ^O "path"
              records File>Open with its chosen file (hook pattern);
         (18) the QWindow-level delivery (which precedes widget delivery
              and never passes _belongs_to_main) SET the de-dupe guards
              before the eligibility check, poisoning the recordable
              delivery -- eligibility first, state second;
         (19) CARET_SHORTCUTS: ONE module-level table drives recorder AND
              runner -- adding a menu shortcut is one row, a design-guard
              test fails on a row naming a missing MainWindow method.
              ^+S "path" (Save As, hook), ^S soft-skips with no current
              file, unnamed chords record nothing.
FLOORS, per Patrick's spec (20-23; 20's cycle design was superseded by
         his fuller spec ONE SESSION LATER, stated not blended):
         (21) Floors menu = Select... (^F) / New... (^+F) / floors
              (default FIRST, "name (Default)" = the roster's first
              whatever its alias) / ghost toggle. ONE popup surface
              (^F, status-bar label, right-click on blank canvas except
              the Room tool) with the default PRE-HIGHLIGHTED so bare
              ENTER selects it. Macro: ^F "name" switches, BARE ^F ->
              default, ^+F "name" creates (IDEMPOTENT on replay); the
              popup route records PUP ... # ^F "name" (comment form).
         (22) floors paint in Z-BANDS: active floor = band 0 (always on
              top; new items land on top with no re-sync), ghosts on
              negative bands in a user-arranged display stack (per-floor
              Move to front/back (display); view state, not serialized).
              Applied as a DELTA so within-floor z is untouched -- NOT a
              fifth z scheme; defect 11's P4.5 collapse should absorb the
              band as the one between-floor term. Reference backdrop to
              the true bottom. Fail-first receipt: "assert 5.0 > 5.0" --
              all floors had shared one z.
         (23) ATMOSPHERIC DEPTH: active floor full contrast, each visible
              floor beneath fades by stack depth (0.60/0.39/0.25...,
              floor 0.18) via per-item opacity -- no paint() touched.
              Quick flip: Ctrl+PgDown/PgUp cycle; recording stays
              deterministic (the hook emits the resulting ^F token).
STANDING:  PR #4 remains on HOLD for the Patrick mini-gate (items 1-8, on
         a fresh launch; findings 1-6 all fixed and pinned). Defect 35
         stays OPEN until Patrick confirms the macro reproductions
         covered everything on his shelf. _perimeter_span's re-argument
         to P4.4 stands in the register. Noted follow-up, not built:
         per-floor visibility (show a chosen subset while editing).

P4.2  MINI-GATE PASSED 2026-08-02 -- defect 35 closed, census hygiene,
         P4.2 TICKED; PR #4 merges as a merge commit on this record
ruff:    clean
pytest:  541 passed, 7 deselected, 4 xfailed (sum 552 -- and LOCAL == CI
         for the first time since the mini-gate findings began: Patrick
         removed his two untracked symmetricP2/P3.json, so the 554/552
         delta the record has carried line-by-line is GONE)
files:   examples/multifloor.fpm (committed at P4.2(25)),
         docs/CODE_REVIEW_v2.md (row 35 closed), this file (the tick +
         this block).
notes:   Patrick ran the mini-gate on a FRESH LAUNCH with the status-bar
         version label verified at the launch sha -- ALL 8 ITEMS PASS.
         (The label discipline the stale-process round bought, doing its
         job on the very run it was built for.)
         DEFECT 35 CLOSED on the reporter's confirmation, per the row's
         own re-open protocol: the shelf is EMPTY -- nothing remains on
         the "still some problems with the drag" report beyond the
         harvested findings 4-6. The residuals were neither stale-process
         nor unreproducible: the macro loop converted them into findings
         5 and 6 (six mechanisms, fixed against measured reproductions,
         pinned verbatim); the reporter's confirmation retires the
         report, which the clean replay alone never could.
         MULTIFLOOR.FPM RULING, asked and recorded: CONVENIENCE FILE,
         not pinned as a regression test -- the floors/token machinery
         keeps its existing unit pins as its guard.
         P4.2 ticked in the Status table citing PR #4 and the sub-commit
         range dfd30af..ed9286c + this record commit (26 in all). The
         snapshot is re-cut AT THE MERGE, on main, as the next action.

P4.3(1) the pre-work census + both rulings recorded (branch p4.3-shuffle
         from main@778b4b9; read-back answered 2026-08-02, work begins)
ruff:    clean
pytest:  (census commit -- code untouched; trailer below is the branch-point
         gate)
files:   this file only.
notes:   RULING 1 (the P2.3 row) -- STAY, with the amendment: the settled
         anti-shear rule keeps the topology; the row closes as
         superseded-by-ruling, and the xfail pin is REPLACED BY TWO HARD
         PASSES, not deleted: (i) the stay contract promoted (a room-less
         body drag moves the grabbed segment only, continuation untouched
         -- the topology's one owner, asserted rather than implied);
         (ii) the HEAL (with auto_coalesce on, the room-less degree-2
         collinear seam an undo leaves dissolves at the next pass, and
         the merged wall body-drags as one) -- the restoration the row
         wanted, arriving through the document instead of the gesture.
         The workaround line survives only for the shuffle/
         auto_coalesce-off world, where staying split is honest.
         Executed at P4.3(5).
         RULING 2 (defect 25's deferred policy, all three questions) --
         TIERED: jamb within the gesture's join tolerance -> snap the end
         to the jamb and weld there (a legitimate gesture-tolerance move;
         gestures are where the 9" tolerance is allowed to act); no jamb
         in tolerance -> land-unwelded-and-report (P4.1b's message, the
         standing fallback). NEVER split (manufactures a homeless-door
         reported-fault document from a live gesture; R2c reserved that
         totality for loads, where no user is present), NEVER refuse (a
         gesture that undoes itself is defect 17's disease). It is
         AUTO_WELD'S decision -- no fifth flag (the doorway case is a
         sub-case of the weld pass's target-finding; the editing_modes
         family is complete at four). Under shuffle the landing never
         welds and the message is SUPPRESSED (an unwelded end is the
         mode's intended state, not a tear); the deferred information is
         delivered at the EXPLICIT JOIN, which reports anything it could
         not place or weld through the defect-6 vocabulary.
         THE CENSUS, measured against main@778b4b9 (the task line's four
         flags, one live and three dead):
         * auto_coalesce (LIVE): internal gates walls.py:537 (merge_wall)
           / :557 (merge_all); callers view.py:504 (draw release),
           walls.py:1952 (drag release), mainwindow.py:915 (ungroup),
           planio.py:200 (legacy load), extract.py:211 (EXPLICIT join).
           FINDING: the explicit join routes through the gated merge_wall,
           so auto_coalesce off (or shuffle) would leave a Join with
           doubled walls -- the join must merge regardless (the schema's
           own "rooms are joined explicitly"); fix = a force param for
           explicit callers. normalize_walls stays ungated by design.
         * auto_weld (dead): ONE gesture site -- view.py:506, the
           draw-release weld_wall_ends. Stated non-sites: the end-drag
           release never welds by design (walls.py:1940 "left exactly
           where the drag put it"); imageio.py:180 weld_scene is defect
           19's import repair; close_gap is defect 34's explicit review
           op; join/normalize are explicit. Ruling 2's jamb-snap tier
           lands on BOTH release paths (draw + end-drag), gated by
           effective auto_weld; the end-drag jamb-snap is a deliberate,
           narrow exception to "never snapped on release" and carries
           the fail-first receipt.
         * auto_bind (dead): NO gateable automatic site exists today --
           measured over all 9 bind_room_walls/repair callers: Room tool
           view.py:280, paste mainwindow.py:1348, room_boolean :849,
           undo restore :658 (constitutive of explicit gestures); load
           paths planio.py:235, csvio.py:148, macro.py:413; the explicit
           join extract.py:218; and the release repair family
           walls.py:1968-1975, which is tear-repair of derived state and
           is exempted DELIBERATELY (gating it would reintroduce the
           mini-gate's stranding class). auto_bind lands plumbed
           (SETTINGS, document, UI) with an empty enforcement surface,
           honored implicitly under shuffle because a floating room
           reaches no bind at all. Stated, not invented.
         * shuffle (dead): four touchpoints -- (a) implies the other
           three off (one effective-flag accessor, config.py, so every
           gate asks the same question); (b) the label-drag drop-join
           rooms.py:884-891: under shuffle a MOVED room stays floating
           (the task line's "joins nothing automatically"); a click that
           never moved still ends placed (P4.2's "a click must not leave
           a room afloat" -- needs a genuine moved flag, today's
           _moving_room is mode, not displacement); (c) suppresses the
           P4.1b doorway message per ruling 2; (d) the toolbar toggle
           (mainwindow.py:143 is the toolbar).
         * emit/apply: bridge.py:709 emit hardcodes the editing block ->
           reads live SETTINGS; bridge.py:891-901 apply already iterates
           DEFAULT_SETTINGS over editing.* -- adding the three keys makes
           load correct BY CONSTRUCTION; importer.py:333's conversion
           defaults are RIGHT for legacy docs (no shuffle concept to
           preserve) and stay; planio.py:144's legacy apply iterates
           DEFAULT_SETTINGS, so the new bool keys default correctly on
           v1-v4 loads.
         Order of work (per the go): plumbing -> gesture gating with the
         tiered weld -> acceptance -> ruling 1's tests + row closure.
         Merge on green CI + Patrick's acceptance; no mini-gate.

P4.3  implemented (branch p4.3-shuffle, sub-commits: a6ded30 census +
         rulings, e9abeb3 plumbing, 2e11a05 gesture gating + tiered
         weld, 0f5642f acceptance, + this record commit. PR opens on
         this commit; MERGE AWAITS PATRICK'S ACCEPTANCE -- the reviewer
         ticks the box, not the implementer.)
ruff:    clean
pytest:  558 passed, 7 deselected, 3 xfailed (sum 568, all three modes,
         every sum reconciling; trailer in this commit's message)
files:   config.py (three flags join DEFAULT_SETTINGS; editing_enabled,
         the ONE effective-flag accessor -- shuffle implies the auto_*
         passes off without rewriting them), walls.py (merge gates
         through editing_enabled; merge_wall force=True for explicit
         callers; snap_end_to_doorway_jamb; end-drag release wires
         snap + gated report), view.py (draw release: gated weld,
         tier-1 snap, gated report), rooms.py (label-drag drop under
         shuffle: moved -> stays floating, click -> still placed, via
         a real displacement flag), extract.py (join merges force=True;
         join-time doorway reporting, unconditional), bridge.py
         (editing block emitted from live SETTINGS; v5 apply re-syncs
         the editing UI), dialogs.py (auto_weld/auto_bind checkboxes),
         mainwindow.py (Shuffle toolbar toggle, text-only QToolButton;
         _sync_editing_ui on every load path; dirty on flip),
         tests: test_shuffle.py (NEW, 11), test_walls.py (4 doorway-
         policy gui tests), test_wall_move.py (xfail replaced by the
         two ruling-1 hard passes), register row (P2.3 closure), this
         file.
notes:   ACCEPTANCE MET, as the task line states it: with shuffle on, a
         floating room dragged ACROSS the plan -- one gesture through
         the real handlers, stepped straight through the anchor room's
         footprint -- leaves both unchanged, check() deep-clean at
         EVERY step (I11 exempts the floating room; I12/I14 exemptions
         hold), the door survives, the plan-side furnishing stays put.
         RULING 1 EXECUTED: the xfail deleted, the two hard passes in
         (stay contract asserted; the heal -- auto_coalesce dissolves
         the room-less degree-2 seam at the next merge pass and the
         merged wall drags as one); the P2.3 Known-regressions row
         CLOSED as superseded-by-ruling, its workaround column alive
         only for the shuffle/auto_coalesce-off world. Census: xfails
         4 -> 3 (the pin retired by ruling, stated).
         RULING 2 EXECUTED: the tiered doorway weld at both release
         paths (snap-to-jamb within JOIN_TOL, else the P4.1b message,
         never split, never refuse), auto_weld's decision with no fifth
         flag; shuffle suppresses the message (an unwelded end is the
         mode's intended state); the explicit join delivers deferred
         information through the defect-6 channel unconditionally. The
         P4.1b pins run UNCHANGED (their landing is 16" from either
         jamb, outside the tolerance -- tier 2 IS the old behaviour).
         RECEIPT, fail-first (worktree at e9abeb3, new tests copied in
         unchanged): all five behaviour flips RED on their verdict
         asserts with preconditions held (the drawn jamb case lands
         measurably at (108, 0) inside the door and fails on
         "108.0 == 104.0 +/- 0.1"; the shuffle label-drag fails on
         'placed' == 'floating'); the click-stays-placed pin passes
         BOTH eras (preservation, not a flip). All green here.
         TESTS CHANGED, declared: the xfail
         test_a_roomless_split_wall_body_drags_as_one_run DELETED by
         the ruling it existed to force (replaced, not relaxed).
         auto_bind lands PLUMBED with an empty enforcement surface
         (the census's measured conclusion, recorded not invented).
         NOTED follow-ups, not built: no macro token for the shuffle
         toggle (the recorder records nothing for it -- same class as
         the pre-P4.2 unnamed chords); a shuffle keyboard shortcut.
         Patrick wants ten minutes with the toggle after the merge.

P4.3(6) Patrick's finding: THE FUSE STRAGGLER (dragWallFuseStraggler.fpm)
ruff:    clean
pytest:  559 passed, 7 deselected, 3 xfailed (sum 569, every sum
         reconciling; trailer in the commit)
files:   extract.py (extract_room step 1b), examples/
         dragWallFuseStraggler.fpm (Patrick's reproduction, committed),
         tests/test_extract_join.py (the verbatim macro pin),
         docs/CODE_REVIEW_v2.md (row 36), this file.
notes:   Patrick: moving the fiveRoomTest design with his macro "leaves
         a wall behind that should not have been copied out."
         REPRODUCED HEADLESS VERBATIM, introspected to three measured
         links (register row 36 has the full chain): an offset join
         round-trip (6" off, by design) + a plain CLICK's release merge
         (6" perp_tol, across a seam that IS degree-2 by identity --
         the horizontals pass mid-body, so no planner rule broke) left
         R2 BOUND to a fused five-room column that no R2 outline edge
         names. extract_room then partitioned by the OUTLINE (step 1)
         but floated the BINDING list (_translate moves room.walls) --
         two definitions of "the room's walls" -- so the column rode
         out bodily with floating R2 and the return join stranded it.
         FIX at the operation whose contract broke: step 1b releases
         every bound wall no outline edge names (the outline is the one
         definition, P3.5); the wall stays with the plan.
         RECEIPT, fail-first: the macro pinned verbatim, red against
         b23d685 in a worktree on "wall count 15 != baseline 16: a wall
         was minted or stranded", green on the fix; fixed end state ==
         the fresh load (16 walls, areas identical, zero open edges,
         check() clean). The pin replays at the DEFAULT window geometry
         (the macro was recorded there; the two fiveRoomDragSplit pins
         replay at 1400x1000+fit for the same reason, stated in each).
         PRODUCER NOTED, not fixed: the release-merge's unconditional
         rebind of absorbed walls' rooms can still mint binding-without-
         naming; extract is immune now, rebind semantics are P4.5's.
         Census 568 -> 569.

P4.3+ the three ruled dispositions, one commit (post-merge, on main;
         ruled by Patrick 2026-08-03 with the acceptance)
ruff:    clean
pytest:  (trailer in the commit; census 569 -> 570, the watch test)
files:   dialogs.py (auto_bind checkbox removed),
         tests/test_extract_join.py (the row-36 watch),
         docs/CODE_REVIEW_v2.md (standing disposition + row 36 carry
         note + row 37), this file.
notes:   (a) AUTO_BIND LEAVES THE UI: modelled, emitted and plumbed
         with no gateable site as of P4.3; the control returns when one
         exists. Standing disposition in the register QUOTES the
         census reasoning verbatim. Nothing changes in SETTINGS, the
         document block, or editing_enabled -- a checkbox promising
         behaviour nothing enforces is what goes.
         (b) ROW 36's PRODUCER: carried to P4.5 CONDITIONALLY on the CI
         watch (test_the_merge_rebind_producer_is_watched): its
         preconditions pin that the producer still mints binding-
         without-naming (red -> re-argue the row before touching the
         test); its verdict pins that extract's step 1b releases the
         state (red -> the guard regressed, caught by CI not a field
         macro). If the watch goes, the carry ruling goes with it.
         (c) THE SHUFFLE TOGGLE'S MISSING TOKEN/SHORTCUT: filed as
         register row 37 -- a user-facing mode the recorder cannot see
         is a gap in the one-table CARET_SHORTCUTS design; a replayed
         session that toggled shuffle replays with the wrong mode,
         silently. ARGUED TO P4.4 (my call, invited): earliest next
         task, one table row + a chord choice, and P4.4's duplicate-as-
         template work is exactly where floating rooms and shuffle get
         exercised together in recorded macros.

P4.3+ Patrick's field report: THE PARKED-FLOAT FURNISHING STEAL (row 38)
ruff:    clean
pytest:  566 passed, 7 deselected, 3 xfailed (sum 576, every sum
         reconciling; trailer in the commit)
files:   rooms.py (sentinel + press guard), extract.py (prev-aware
         capture with claimed-exclusion; join resets to None),
         mainwindow.py (_set_shuffle re-baseline),
         tests/test_shuffle.py (6 pins + the acceptance's declared
         change), docs/CODE_REVIEW_v2.md (row 38), this file.
notes:   REPRODUCED before his clarification arrived, mechanism
         measured: init [] == captured-empty, falsy lazy-capture guard
         -> a parked float re-captured at EVERY press by whatever it
         hovered over. THE CONTRACT, ruled: (a) floating captures the
         furnishings inside, any mode; (b) under shuffle EVERY dragged
         room keeps its furnishings (plain non-shuffle drag still
         leaves them -- P4.2's trait, scoped); (c) no mid-shuffle
         pickup ever; the ONE re-baseline is the shuffle-ON toggle --
         carried stays its own, inside-and-unclaimed becomes assigned,
         claimed-by-a-placed-room is never taken.
         TESTS CHANGED, declared: the P4.3 acceptance's furnishing
         assert flips from stays-put to rides (ruling (b) reached the
         path it pinned); red pre-fix with the three new flips, three
         preservation pins pass both eras.
         Census 570 -> 576.

P4.4(1) the four rulings recorded + the pre-work census (branch
         p4.4-concept-duplicate from main@e4b2028; read-back answered
         2026-08-03, work begins)
ruff:    clean
pytest:  (census commit -- code untouched; branch-point gate trailer in
         the commit)
files:   this file only.
notes:   THE FOUR RULINGS, verbatim in substance:
         (1) CONTINGENCY CONFIRMED -- duplicate is built on the extract
         machinery per section 4. Consequence executed at P4.4(3):
         _copy_spec and _perimeter_span DIE (the carried census note's
         contingency resolves YES); Copy/Paste room rewire to the new
         op; the clipboard path's third definition of "the room's
         walls" (bounding_walls proximity + _perimeter_span trim) dies
         with them, so P4.5 inherits the binding/outline duality with
         the clipboard consumer RESOLVED.
         (2) CREATE-BY-TYPED-DIMENSION mints a FLOATING, WALL-LESS room
         carrying nominal_size -- a dialog off the Room tool AND from
         the menu. category: concept; I13 (concept must be floating)
         is the guard.
         (3) FILE MENU: "Load template room..." and "Save template
         room..."; Save enabled ONLY when a floating room is selected
         (highlighted).
         (4) THE SHUFFLE CHORD IS ^H (register row 37's fix, this
         task's first code piece).
         CENSUS (measured at the read-back + this commit):
         _perimeter_span rooms.py:314-337 (24 lines), sole caller
         _copy_spec rooms.py:339-373, sole caller the context-menu
         Copy (rooms.py:947 -> win.room_clipboard), sole consumer
         paste_room mainwindow.py:1348-1388 (rebuild + detect_room +
         bind_room_walls), surfaced at view.py:530. bounding_walls
         SURVIVES (report/inventory callers rooms.py:517,:575,
         mainwindow.py:918). Schema ground already present:
         room.nominal_size ("Never authoritative -- the outline is"),
         category concept, I13 in validate.py; model/bridge ride
         nominal_size verbatim (bridge.py:95 names P4.4). The macro
         table: CARET_SHORTCUTS one-row design, hook pattern on_floor/
         on_open; H unclaimed.
P4.4  implemented (branch p4.4-concept-duplicate, sub-commits 868e315
         census + rulings, ef74e11 the ^H chord + token, 8f3382b
         duplicate-as-template, d02d5ea concept rooms, + this record
         commit. PR opens on this commit; MERGE AWAITS PATRICK'S
         ACCEPTANCE -- the reviewer ticks the box.)
ruff:    clean over floorplanner/ + tests/ (the full-tree run is red only
         on viewer/fp3d.py, Patrick's parallel WIP, staged in the index
         and deliberately untouched by this branch -- stated, not
         counted green; its packaging is its own branch)
pytest:  588 passed, 7 deselected, 3 xfailed (sum 598, all three modes,
         every sum reconciling; trailer in the commit)
files:   design/template.py (NEW), rooms.py (make_concept_room;
         category/nominal_size modelled; the wall-less label drag;
         _copy_spec + _perimeter_span DELETED, 59 lines), planio.py
         (room_template / insert_room_template / duplicate_room /
         save+load_template_path / the interactive pair /
         selected_floating_room), mainwindow.py (File menu pair with
         the ruled enable rule, Rooms > New concept room...,
         new_concept_room, paste_room rewritten, _sync_template_action,
         toggle_shuffle / set_shuffle_mode), dialogs.py
         (ConceptRoomDialog), view.py (the Room-tool blank-canvas menu),
         macro.py (^H row + on_shuffle hook), design/bridge.py
         (category + nominal_size modelled in emit AND apply),
         tests: test_template.py (NEW, 11), test_concept_rooms.py
         (NEW, 8), test_shuffle.py (+3), test_outline.py (rewritten
         guard), register (row 37 + the carried census note), this file.
notes:   ACCEPTANCE MET, as the task line states it: a one-room file
         validates against the SCHEMA and all fifteen invariants and
         loads into an existing design as a FLOATING room, the host
         design untouched (test_save_and_load_template_room builds a
         SECOND MainWindow, so "an existing design" is genuinely
         another document rather than the same scene).
         THE INHERITED QUESTION ANSWERED YES, and the family is gone:
         _copy_spec + _perimeter_span deleted (59 lines), and with them
         the clipboard's THIRD definition of a room's walls. P4.5
         inherits the binding/outline duality with its clipboard
         consumer RESOLVED, which is what its rulings assumed.
         ONE MECHANISM, THREE WORKFLOWS: room -> one-room document ->
         floating room. A clipboard between the halves = Copy/Paste; a
         FILE between them = Save/Load template; back to back =
         Duplicate. The merged document goes through the ONE apply
         path, so an inserted room arrives by exactly the route a
         loaded file does.
         WHY FLOATING IS STRUCTURAL, not menu polish: the level walk
         gives a floating room its own vertex namespace and its own
         walls (I12), so the subset {room, the walls its OUTLINE names,
         their vertices, its furnishings} is CLOSED. A PLACED room is
         cut out through the REAL ops -- extract, template, join back
         -- whose zero-offset round trip IS the P4.2 label-click path;
         pinned by snapshot byte-equality across the operation.
         CONCEPT ROOMS: category + nominal_size MODELLED on the item
         (the P4.2 placement pattern, next field family) so a room the
         app itself creates can carry them; the name heuristic stays as
         the FALLBACK, pinned. I13 holds BY CONSTRUCTION (the factory
         cannot mint a placed concept room) and I11 exempts the class,
         so a sketch unit parks over the plan legally.
         FIXED IN PASSING, same class as the P4.3+ steal: the label
         drag required self.walls, so a WALL-LESS room's region stayed
         behind while its label wandered off.
         TESTS CHANGED, declared: test_copying_a_room_does_not_carry_
         its_geometry now asks its guard of the template DOCUMENT (the
         payload that also goes to disk -- the stronger place); paste
         lands a FLOATING room centred on the click rather than a
         placed one snapped to the grid.
         ROW 37 CLOSED with the ruled ^H chord (sub-commit 2).
         Census 576 -> 598.

OUT-OF-SEQUENCE, 2026-08-04: THE 3D VIEW POPUP (branch viewer-popup)
         NOT migration work, and recorded here precisely BECAUSE it is not:
         it landed between P4.4 and P4.5 rather than as a phase task, and
         it TOUCHES THE APP STARTUP PATH -- floorplanner/app.py, which no
         Phase-4 task has needed to open. A change to the first ten lines
         the process runs deserves a row in the sequence it stepped
         outside of, or the next person reading this log will find app.py
         changed by nobody.
ruff:    clean
pytest:  594 passed, 7 deselected, 3 xfailed (sum 604; trailer in the
         commits) -- census 598 -> 604, +6: five for the popup's own
         discipline and one more when the surface-format guard grew a
         BEHAVIOURAL test (simulate the missing import) beside the
         source assertion for the ordering.
files:   viewer/fp3dq.py (Plan3DQuickWidget extracted from main(), which
         becomes a caller), viewer/scene.qml (NEW -- the QML leaves the
         inline temp file), viewer/fp3d.py + viewer/system-checker.py
         (lint at source), viewer/VIEWER_NOTES.md (section 5), app.py
         (set_3d_surface_format), mainwindow.py (show_3d_view),
         view.py + levels.py (the two blank-canvas menus),
         pyproject.toml (scene.qml as package-data),
         tests/test_viewer_popup.py (NEW, 6).
notes:   THE STARTUP CHANGE, stated plainly because it is the part with
         blast radius: QSurfaceFormat.setDefaultFormat(QQuick3D.ideal
         SurfaceFormat(4)) MUST run before the QApplication exists (Qt
         reads the default format at GUI init), so it cannot live in the
         viewer with the rest of the Qt Quick 3D code -- main() is the
         one place guaranteed to be earlier. It is extracted as
         set_3d_surface_format() and GUARDED: the 3D stack is an optional
         extra, and an unguarded import at the entry point would make
         `pip install -r requirements-viewer.txt` mandatory just to
         launch the editor. Pinned by SIMULATING the missing import (the
         call returns False rather than raising) plus a source assertion
         for the ordering, which no runtime test can observe without
         building a second QApplication.
         READ-ONLY IS THE ACCEPTANCE: the popup reads design_document() --
         the SAME producer _write_plan writes, so no second definition of
         the plan was introduced -- and the walk's warning channel is
         suppressed for that one call, because an unwelded-end report
         belongs to the edit that tore the network and the 180 ms
         debounce walk owns it. Pinned against a genuinely SAVED plan:
         dirty flag, snapshot, and wall/room counts all unchanged, with
         any warning promoted to an error.
         ONE WIDGET, ONE QML: the CLI tool and the popup render through
         Plan3DQuickWidget and scene.qml, so neither can drift from the
         other. w._keep survives the extraction and is why -- QML holds
         no Python reference to the geometry.
         MENU PLACEMENT: appended to the blank-canvas right-click only on
         the RIGHT-CLICK route; ^F and the status-bar label stay a pure
         floor selector (P4.2's one-popup-surface spec is about floor
         SELECTION, and a chord named "select a floor" should not offer a
         renderer).
         CI's py3.10 leg earned its keep on the first change that gave it
         something to find: a tomllib import (3.11+) in the new test.
         MERGE HELD FOR PATRICK'S 8-ITEM SMOKE TEST and the reviewer's
         ruling; merge commit, not squash.

```
