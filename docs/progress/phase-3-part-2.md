# Progress log - Phase 3 - vertices own the geometry (part 2)

> **Moved verbatim** from `V5_MIGRATION_PLAN.md` (its lines 2650-3518 as of
> commit 2f232bd) on 2026-08-06. Nothing was reworded, reordered, tidied or
> reformatted; the entries appear in the order they were appended. The code
> fence below is the one the log has always been written inside - it is
> reopened here and closed at the end, because a fence cannot be split.
>
> Index: [`README.md`](README.md) - Plan: [`../V5_MIGRATION_PLAN.md`](../V5_MIGRATION_PLAN.md)

```
P3.7  done -- TICKED 2026-07-30 by the reviewer. Three sub-commits, each at a
         full-mode green gate.
ruff:    clean
pytest:  Gate-Census: collected=520 ruff=clean
         Gate-OFF: 514 passed, 6 xfailed in 15.36s  -> sum 520  OK
         Gate-ON: 514 passed, 5 xfailed, 1 xpassed in 18.49s  -> sum 520  OK
         Gate-DEEP: 509 passed, 7 deselected, 4 xfailed in 17.82s -> sum 520 OK
         Gate-Verdict: GREEN (every sum reconciles against --collect-only)
         519 -> 520 collected, +1 (test_an_open_side_is_drawn_dashed); nothing
         removed.
commits: 2c5fd8d (1 amended acceptance) . b8fec07 (2 the cue) . 1260721 (3 the
         deletion sweep)

THE SPEC WAS AMENDED BEFORE THE CODE, and the census is why that mattered. Two
         divergences from the estimate, both found by grepping disk rather than
         reading the task line:
         * NO LIVE PRODUCER since P3.5 -- zero `OpenWall(` calls tree-wide. The
           "P2.3 producer branch in apply" the estimate named is already a
           COMMENT. The P2.3 log line promising P3.7 would retire it is stale
           history, ANNOTATED not rewritten (the log is history; wrong history
           gets an annotation).
         * `is_open` was the real sweep at ~7x the estimate: 44 readers across
           17 files, every one permanently False.

(a) VERIFIED, NOT RE-DONE: `test_open_walls.py` went to null edges at P3.5.
(b) THE PIXEL ASSERTION, polarity measured FIRST (P3.4's template): wall body
         150, vacated stretch with no cue 255 (pure background -- the
         regression), dash ~124 with gaps at ~255. So the cue is a DARK, GAPPED
         line and CLAUDE.md's `< 190` sits between dash and background. Both
         halves in one test. RECEIPT: fails in a worktree without the paint
         addition, in the regression row's own words -- `[255, ... 255]`.
(c) THE CLASS IS GONE: `git grep is_open -- '*.py'` and `git grep OpenWall --
         '*.py'` both return NOTHING. Prose keeps the history.
(d) THE KNOWN-REGRESSION ROW CLOSES on the pixel test, and it HAD to be pixels:
         every structural assertion in that file stayed green for the whole life
         of the regression, because they ask the outline what is open and the
         outline was always right.

SAME CUE, PROVEN NOT ASSERTED: drawing the new cue and a real `OpenWall` at once
         puts them on the same pixels (124 each alone, 97 stacked), so the row
         closes as "the same cue from one representation" rather than "a
         different cue". `docs/gallery/08-open-walls.png` regenerates with the
         dash visible and the README sentence P3.5 had to amend is reverted.

MY OWN SWEEP FAILED TWICE BEFORE IT WORKED, recorded because the mechanism is
         reusable and so are the traps: the tree is CRLF, so every MULTI-LINE
         pattern matched zero times while single-line ones applied (a half-swept
         tree), and two `if not w.is_open\n and abs(...)` sites left a dangling
         `and` -- syntax errors written into the tree. Recovered with `git
         checkout`, safe ONLY because every piece of real work was already
         committed and the sole uncommitted content WAS the broken sweep. That
         is the P3.5 rule read the right way round: the danger is uncommitted
         WORK, and there was none.

DEFECT 28 -- THE CORPSE TABLE, AND IT IS COMPLETE (2026-07-29). Ruling 3's
         standard met: no blank rows, every corpse attributed to the test whose
         scene it actually holds. Full table and method in
         `docs/evidence/defect28-ownership.json`; the register row carries the
         summary. Swept DIRECTLY, per the amendment, rather than waiting for a
         2-in-10 race.

  'Kitchen'/'Pan' IS OWNED, and the owner is `test_groups.py::test_a_group_move_
  leaves_the_outlines_still_holding_their_corners` -- defect 22's own receipt.
  So is 'M Bath'/'Toi', and so are two pairs the re-harvest added
  ('Garage'/'PWDR', 'Garage'/'Mud'). `'A'`/`'B'` stays owned-innocent, and its
  provenance stack shows the running test IS the owner -- it was never a
  misreport at all.

  ATTRIBUTION BY DOCUMENT SIGNATURE, which is what finally cracked it. Every
  20-room corpse's own document is symmetricP1 translated +48" in x with ONE
  corner displaced a further (+12,+12) -- that test's literal script (:545 and
  :557), run by no other test in the suite. The reduced evidence file had kept
  only a summary, so the ownership question was unanswerable until a 10-run
  re-harvest on the unfixed tree (4 red, 14 dumps) produced corpses carrying
  their FULL documents. Confirmed twice more: solo, with no other window in the
  session, the test errors at its own teardown 1 run in 12; and on a red DEEP
  run PYTEST ALREADY NAMES IT ("ERROR ... test_a_group_move_leaves_the_outlines_
  still_holding_their_corners", at "win fixture teardown").

  THAT LAST POINT IS A CORRECTION TO THIS DEFECT'S OWN FRAMING. The leak
  misattributes the corpse FILE (the stack shows `macro.py:98 processEvents()`
  above `_commit_if_changed`, a stale timer inside a later test) -- it does NOT
  misattribute the pytest error. The red DEEP runs were correctly blamed all
  along; only the evidence artifacts pointed at the wrong test.

  ROOT CAUSE, and "the race picks the victim" is WITHDRAWN -- there is no race
  in the choice. The test picks its party wall with `next(w for w in
  win.scene.items() if ...)`, and scene item order is not stable across
  processes, so the PICK varies per run. It then re-points the moved vertex for
  the party wall's TWO rooms only (`for r in (a, b)`), leaving any THIRD room
  whose outline holds that corner behind; where the geometry allows, that room
  overlaps a neighbour. MEASURED EXHAUSTIVELY over all 59 candidate picks:
  18 produce an I11 (31%, against the measured 4-in-10 red runs), and
  re-pointing EVERY holder of the corner produces 0. Which is what both app
  corner-movers already do -- `_DragVertex.ends`/`.edges` on the drag,
  `GroupItem._corner_records` on bake and rotation.

  TWO OF MY OWN CLAIMS WITHDRAWN BY THE SWEEP:
    * `window.visible=false` is NOT a staleness tell. No fixture window is ever
      shown, so a LIVE fixture window reads exactly the same. The original
      "recorded by a window that is NOT VISIBLE, while an unrelated test was
      running" over-read it.
    * A stale window's walk is SILENT on this tree. Forcing `_commit_if_changed`
      -- the identical call the leaked timer makes -- on every live window after
      every test, 518 times, produced ZERO reports, because every I11 a stale
      scene holds sits in that scene's own accepted baseline. The leak is real
      and still worth fixing; it is not what turns a run red.

  NOT ESTABLISHED, AND NOT ASSERTED: that an equivalent APP gesture can strand a
  holder. 38 synthetic endpoint drags over multi-room corners moved the corner
  in NONE of them -- the branch does not drive headlessly that way -- so that
  run's "0 stranded, 0 I11" is VACUOUS and is discarded rather than quoted as an
  acquittal. Checked because a "clean" result that was never in a position to be
  dirty is exactly defect 21's near-miss. The app is neither cleared nor accused
  here; if the question is wanted answered it needs a harness that drives the
  drag for real.

P3.6-followup  done -- DEFECTS 28 AND 29, AND P3.6 TICKS (branch v5-topology)
ruff:    clean
pytest:  the re-certification, ruling 4's condition, met in FULL mode:
         TEN consecutive `python tools/gate.py` runs, 10/10 GREEN, each
         trailer machine-written and each sum reconciled against
         --collect-only. The last of them:
           Gate-Census: collected=519 ruff=clean
           Gate-OFF: 513 passed, 6 xfailed, 3 warnings in 15.52s  -> sum 519  OK
           Gate-ON: 513 passed, 6 xfailed, 4 warnings in 17.44s  -> sum 519  OK
           Gate-DEEP: 508 passed, 7 deselected, 4 xfailed, 3 warnings in 16.77s
                      -> sum 519  OK
           Gate-Verdict: GREEN (every sum reconciles against --collect-only)
         These are the FIRST `Gate-DEEP` trailers on the branch -- every
         previous commit carried `--quick` (Census + OFF only), which is why
         the trailer requirement was made explicit: a 10/10 claimed against
         quick trailers would be the transcription class returning through the
         mode flag.
commits: b1679a4 (the corpse table) . c1496fe (28A, the owning test) .
         ee7e4e5 (28B, the fixture leak) . e8a7348 (29) . plus this doc commit.
census:  518 -> 519 collected, +1: test_undo::test_closing_a_window_stops_its_
         dirty_timer. Nothing removed.

WHAT THE DEEP FLAP ACTUALLY WAS, and it was not the leak. The corpse table's
         owner -- `test_a_group_move_leaves_the_outlines_still_holding_their_
         corners` -- picked its party wall with `next(w for w in
         win.scene.items() ...)`, and scene item order is not stable across
         processes. 18 of its 59 candidate picks leave two rooms overlapping
         (31%, against the measured 4-in-10 red DEEP runs), because the test
         re-pointed the moved corner for the party wall's TWO rooms and left
         any THIRD holder behind. Deterministic pick + every holder re-pointed:
         0 of 59, and 15 consecutive solo DEEP runs green where the same test
         on the same tree was 1-red-in-12 before.

THE LEAK IS REAL AND IS FIXED, AND IT IS NOT WHAT TURNED RUNS RED -- the two
         are separate and were being read as one. Measured across the suite:
         peak live MainWindows 16 -> 0, peak holding a LIVE dirty timer 9 -> 0,
         alive at session end 12 -> 0. What the leak did was misattribute the
         corpse FILES (a stale timer firing inside a macro test, the stack
         showing `macro.py:98 processEvents()` above `_commit_if_changed`); the
         pytest ERROR was correctly blamed on the owner all along.

THE GUARD IS AN INVARIANT, NOT A BUDGET: no window outlives its test holding a
         live dirty timer. A cap on the count would pass a suite that leaks
         quietly as long as it leaked few enough. FAIL-FIRST RECEIPT, in a
         detached worktree per the standing rule: the guard alone against
         pre-fix code produces 333 teardown errors.

TWO MISTAKES IN THE DISPOSAL, both found by running it rather than reading it,
         and both worth carrying forward:
         * stopping the timer BEFORE the close silences a timer the close then
           RESTARTS -- closing emits scene changes, they reach `_mark_dirty`.
           Close, let them settle, then stop.
         * `processEvents()` does not deliver `DeferredDelete`, so `deleteLater`
           left the window standing and still counting. `sendPostedEvents(None,
           DeferredDelete)` is what destroys it.

AND THE GUARD IMMEDIATELY EARNED ITS KEEP: `test_scaling._measure` leaks the
         same way, and its two windows come from a MODULE-scoped fixture, so
         they predate every per-test disposal and outlived the whole file.
         Fixed at source rather than by loosening the guard -- 67 errors in the
         OFF/ON runs (the perf tests DEEP deselects), which is the whole blast
         radius of (B).

DEFECT 29, SEPARATELY per ruling 1: `closeEvent` stops the timer, and only once
         the close is ACCEPTED -- a close the user cancels must leave the
         window as it was, debounce included, or the edit in flight when they
         hit the X never becomes an undo step. Its test asserts the
         PRECONDITION (that the edit started the debounce) before asserting the
         fix, so it cannot pass vacuously, and it fails pre-fix on exactly the
         line it names.

THREE CLAIMS OF MY OWN WITHDRAWN BY MEASUREMENT, recorded because the register
         carried them as fact:
         * "the race picks the victim" -- there is no race in the choice; the
           PICK varies because scene order does.
         * `window.visible=false` is a staleness tell -- it is not; no fixture
           window is ever shown, so a live one reads identically.
         * a stale window's walk reports -- forcing `_commit_if_changed` on
           every live window after every test, 518 times, gave ZERO reports:
           every I11 a stale scene holds sits in its own accepted baseline.

NOT ESTABLISHED, AND NOT ASSERTED: that an equivalent APP gesture can strand a
         room holding a dragged corner. 38 synthetic endpoint drags moved the
         corner in NONE of them, so that run's "0 stranded" is vacuous and is
         discarded rather than quoted as an acquittal -- the app is neither
         cleared nor accused. Answering it needs a harness that drives the drag
         for real, and that is not this task's.

P3.6  CODE COMPLETE, NOT TICKED -- blocked by defect 28 (branch v5-topology)
      [SUPERSEDED: ticked at the P3.6-followup above, 2026-07-30.]
         DEFECT 26 IS FIXED and the diagnosis is worth carrying forward as the
         standard for what "root cause" means here: a stack, then an
         explanation for every property the bug had, then a narrow fix. It was
         never memory corruption -- `verify()` raised inside a QTimer callback,
         and PyQt turns an exception escaping a C++ -> Python callback into
         `qFatal()` -> `abort()`. The guard is narrow (that exception type only,
         at the 7 callback paths reaching the 3 call sites) and the acceptance
         was 0/10 crashes against ~4/20 before.
         WHAT REMAINS IS DEFECT 28, which the crash was hiding: a group rotation
         genuinely produces overlapping placed rooms (I11), ~2/10 deep runs. The
         tick waits on it, because DEEP green-and-reliable is the condition.
         Every acceptance property is green and every ruling is implemented,
         and the tick is still withheld, because the gate ruled at this task
         is what found the reason. `tools/gate.py` runs the three gates with
         their output CAPTURED, and under `FP_VERIFY_DESIGN=deep` the suite
         then ABORTS about 40% of the time -- rc 0xC0000409, a hard process
         crash, not a failing test. Bisected to P3.6: 0 of 4 at `e3fabb6`,
         the commit immediately before this task's first. A phase whose gate
         cannot be relied on to run is not a phase that has passed its gate,
         whatever the counts say when it does complete.
ruff:    clean
pytest:  OFF  512 passed, 6 xfailed in 15.9s
         ON   512 passed, 6 xfailed in 19.8s
         DEEP 507 passed, 4 xfailed, 7 deselected in 20.0s
         516 collected; OFF 512+6 and DEEP 507+4+7 both reconcile against
         `--collect-only`.
commits: 94a4de6 (0 spec) . 2fb3c77 (1 the anchor) . f964394 (1a the phantom E)
         . 80435c1 (1b R4b/R2b rulings) . 7fe1aa2 (2 defect 24) . 3cdf046 (3
         R4b) . e4907c7 (3a the gate that was not gating) . 52111c3 (4 R2c) .
         41cc975 (5 R2b) . ea50dce (6 R5)

THE AMENDED ACCEPTANCE (R1), and each of its four properties green:
  (a) an opening anchored `from: "v2"` keeps its `offset_in` exactly when the
      wall is stretched AT v2 -- `test_an_opening_holds_its_offset_when_the_
      far_end_is_stretched`. RECEIPT: failed against s-based code before the
      anchor landed.
  (b) reversing a wall leaves the opening's physical position unchanged --
      `test_reversing_a_wall_leaves_its_openings_where_they_are`. RECEIPT:
      failed measurably, the door mirroring 200.0 -> 40.0.
  (c) the split of R2 -- `test_a_split_clear_of_a_door_leaves_it_exactly_where_
      it_was`. WRITTEN AT R2b, and it did not exist before: R1 listed it, but
      the split coverage was the two refusal pins, and refusal is not a
      property of the anchor -- it is the absence of one.
  (d) loading a plan whose door no longer fits REPORTS it --
      `test_an_opening_that_cannot_be_placed_is_reported_not_dropped`, on the
      v4 load path specifically.

THE THREE NUMBERS IN THE TASK LINE WERE ALL WRONG, and the read-back is what
         caught them: "13 `except ValueError` sites" was every such site in the
         package, not the opening drops (7 at baseline, 8 today); `walls.py:568`
         had moved to `:1004`; and "P0.4 test 1 passes without xfail" pinned
         nothing, having never been xfail. Corrected in place at 94a4de6.

TWO DEFECTS FOUND WHILE DOING IT, both measured before being claimed:
         * DEFECT 24 -- `offset_in` read and written as a CENTRE distance in
           `topology.py`, near-edge everywhere else. 18.00" on a 36" door.
           THREE sites, not the two first registered: the third was a fourth
           hand-written copy of the arithmetic inline in `apply_merge_plan`,
           found only when fixing the other two turned its test red. All now
           route through one conversion.
         * DEFECT 25 -- a gesture can create a door-straddles-junction scene
           state the document can only represent as a reported fault. Registered
           P4.1 per ruling, with my argument for P4.3 and a move trigger in the
           entry rather than swallowed.

THE GATE AUDIT, ruled at the process failure, and it is a measurement in three
         layers because the first two were not trustworthy:
         1. GREP of every commit message (44 branch + 172 main): ONE hit, and
            it is e4907c7 -- my own disclosure, not a gate committed over.
         2. WHY THAT IS NOT THE ANSWER: 3cdf046's gate line was transcribed
            WITHOUT its ", 2 errors". The message looked green. Grepping
            messages audits what I wrote, not what ran.
         3. EMPIRICAL REPLAY of OFF and ON at all 27 code-touching branch
            commits: 8 red. Re-replayed with the P0.3b ratio class excluded:
            SEVEN GO GREEN, ONE STAYS RED.
         VERDICT: exactly ONE commit was made over a genuinely red gate --
         3cdf046 (P3.6(3), R4b), red on ON and DEEP with 2 errors, green at
         e4907c7 the next commit. Everything else was the timing-ratio class.

AND THE SEVEN ARE THE FLAP ROW'S EVIDENCE. `test_bake_scales_subquadratically`
         was caught red at 8.05 against a threshold of 8, and all seven show
         the tell: exactly "1 failed", ALTERNATING between the OFF and ON runs
         of the same commit. Broken code fails both; a straddling ratio fails
         whichever run the machine was busier during. ~7 of 27 replays, so the
         P3.8 row is widened from one test to the CLASS, with three members
         named.

TESTS: +9 (tests/test_openings.py, new). CHANGED, each with its one line:
         * the two R2b PINS flipped -- `split_edge` raising, `split_wall_at`
           declining. Both were placeholders pending representability;
           `match="P3.6"` was one test naming its own executioner.
         * the drag-side twin of the decline in test_wall_move.
         * two in test_topology_ops / test_topology that had encoded defect
           24's arithmetic (offset 50.0 where the near edge is 18.0) or were
           passing only because of it (a midpoint split that always fell
           inside the door).
         * test_a_clipped_band_leaves_every_room_coherent gained `rebase(win)`
           -- see the phantom-E resolution above.

P3.5-followup  done   commit d0ab89d -- DEFECT 22: a group move is a vertex move.
ruff:    clean
pytest:  OFF  503 passed, 5 xfailed in 16.5s
         ON   503 passed, 5 xfailed in 19.4s
         DEEP 498 passed, 3 xfailed, 7 deselected in 19.1s
FOUND BY A SMOKE TEST, not by the suite, and the gap is the finding as much as
         the bug. Symptoms on a v5 plan: some rooms did not track a whole-design
         group move; later individual room moves worked; and `unwelded_ends`
         warnings fired repeatedly with a moving count on a file that opened at
         zero.
REPRODUCED HEADLESSLY BEFORE ANY FIX, per the standard:
         * 140 of 140 room outline corners held one of their own walls'
           vertices before the bake -- 0 of 140 after. A party-wall drag then
           resized NOTHING: M Bath -18.20 sf / WIC +9.50 sf before, +0.00 /
           +0.00 after.
         * `unwelded_ends` 0 -> 133 grouping every ROOM; 0 -> 1 on a rubber
           band; 0 -> 0 grouping every WALL.
         * split telemetry during the bake: 160, all at items.py:703/704 --
           the exact residue P3.4 (iv) attributed to `bake()` and assigned to
           P4.5.
THE HYPOTHESIS WAS CONFIRMED FOR THE LOAD-BEARING HALF AND REFUTED FOR THE
         VISIBLE ONE, which is worth separating. CONFIRMED: `bake` assigned new
         COORDINATES to every member wall end (split-on-write) and rebuilt each
         carried room's corner list beside it, so the two agreed numerically and
         shared nothing -- orphaning the outlines P3.5 made authoritative.
         `refresh_rooms` re-bound and re-shared after every bake, so deferring
         bake's conversion to P4.5 was safe exactly as long as detection
         existed; P3.5 changed the deferral's premise, which is why this is a
         P3.5-followup and not P4.5's. REFUTED as the cause of "some rooms don't
         track": that is duplicate-on-group (defect 3, P4.5). A rubber band
         needs an item FULLY inside, so a wall poking out is left behind, its
         room's walls are DUPLICATED into the group, and `room_owns_walls` is
         then correctly false -- 17 of 20 tracked, and the 3 that did not were
         right not to. P3.5 only removed the re-detection that used to hide it.
THE FIX IS THE PLAN'S OWN `move_vertices`, and it is smaller than what it
         replaces. `_corner_records` resolves every corner the group's geometry
         holds together with the wall ends and outline edges on it;
         `_apply_corner_records` relocates each once. Walls and outlines follow
         because they hold those corners -- a bake is now the same operation as
         a wall drag.
THE CARVE-OUT IS RESPECTED BY SPLITTING, not by an exclusion list. A corner a
         NON-member wall also holds is split off before anything moves, so the
         group goes and the outsider stays -- today's behaviour exactly.
         Relocating it wholesale would wire a member to an outside wall, which
         is what the `group() is None` guards exist to prevent. Own test.
ROTATION HAD THE IDENTICAL DEFECT (140/140 -> 0/140) and now moves through the
         same records, resolved once at `_begin_rotation` and re-applied from
         the START point each event -- drift-free AND identity-preserving, where
         before it was split-on-write per mouse move. THE FIRST ATTEMPT WAS
         WRONG AND SAID SO: re-welding at `_finish_rotation` CONVERGED rather
         than closed (0/140 -> 138/140, then 139/140 on a second pass), which is
         how a positional instrument fails where an identity one is needed.
THE WARNING'S ERGONOMICS, because a correct warning that misattributes teaches
         people to ignore the channel that will one day be right. It said
         "expected on a plan loaded from a legacy file" for EVERY case -- true
         of what a file arrives with, false of what an edit tears -- and fired
         on every debounced snapshot, so a plan that opened clean produced a
         stream of them with a moving count. Now the first walk after a load
         sets the BASELINE, only a walk finding MORE warns, the message names
         the split (opened-with vs NEW), and a repeat of the same state is
         silent. `strict=True` is untouched: two tests pin it.
PERF HELD, and the harness earned its keep twice. bake 6.5 -> 28.6 ms
         (n=4 -> n=8), ratio 4.39, against P3.5's 6.9 -> 28.0 / 4.03. The FIRST
         cut rebuilt each member wall inside the loop -- redundant with the
         `rebuild_all_walls` that follows, and cascading -- and cost 9x
         (25.9 -> 251.3 ms, ratio 9.70). Caught by `test_bake_scales_
         subquadratically` on the first full run.
TESTS ADDED (5), and one of them is NOT the receipt -- verified by running all
         five against pre-fix code in a worktree:
         * whole-plan group + move carries every room, unwelded_ends still 0.
           PASSES ON BOTH SIDES: the old bake translated each carried room's
           corner list explicitly, so the rooms tracked POSITIONALLY. It guards
           the property at a scale the rest of test_groups.py never reaches (20
           rooms / 80 walls vs ~5 members) and is the first group test to look
           at the debris counter at all. Annotated as such in its own docstring
           so it is not mistaken for the receipt later.
         * the outlines still hold their corners after a bake, and a corner move
           still resizes the rooms -- THE RECEIPT, fails pre-fix.
         * the rotation half -- fails pre-fix.
         * a group move never drags a wall outside it -- the carve-out guard;
           passes on both sides by design, since it pins what must NOT change.
         * the warning names its cause and says it once (plus its mirror, that a
           legacy plan is still blamed on the file) -- both fail pre-fix.
WHY 503 GREEN TESTS MISSED IT: every group test in the suite tops out at ~5
         members, and not one had ever asserted on `unwelded_ends`. The bug
         needed a plan big enough to have party walls and a check nobody was
         making. Both gaps are closed here.

P3.5-followup, PER-ROOM DIAGNOSIS -- asked for after the fix landed, to explain
         the TWO presentations in the reported screenshot (one room fully
         detached with its dashed outline at the original position, another
         offset but coherent). Measured per room on a rubber-band selection over
         92% of symmetricP1, reporting (a) outline vertices matching no endpoint
         of any wall the room names, (b) whether walls moved, outline moved,
         both or neither, and the identity count underneath both.
         THE TWO PRESENTATIONS ARE TWO DIFFERENT DEFECTS, and the prediction
         that they collapse to one cause is REFUTED. Recording that is the
         point of having predicted:
         * OFFSET BUT COHERENT -- 17 of 20 rooms. walls 13/13 moved, outline
           13/13 moved, (a) = 0. Nothing visible is wrong. IDENTITY 0/13: every
           corner is a different object from its wall's vertex, because the old
           bake computed the room's new corner list SEPARATELY from the walls'
           new coordinates and the two agreed only numerically. This is DEFECT
           22, it is invisible in any screenshot, and it is fixed -- the same
           run post-fix reads 13/13 identity with every other column unchanged.
         * FULLY DETACHED -- 3 of 20 (Garage, PKT Off, Util). walls 6/9 moved,
           outline 0/9, (a) = 5 stranded corners, identity 4/9 -- the four
           corners it shares with the walls that did NOT move. The room was not
           carried at all (`room_owns_walls` false), because the band clipped
           one of its walls and `group_selected` duplicated the rest.
           BYTE-IDENTICAL BEFORE AND AFTER THE DEFECT-22 FIX: 46.65" / 39.98" /
           23.32" of region-to-walls drift either way. The vertex translation
           cannot touch it, because the room is not in the set being moved.
         AND THE "P3.5 UNMASKED IT" CLAIM IS WITHDRAWN, having been asserted
         before it was measured. The same drift measurement on the pre-P3.5
         tree strands Garage by 148.3" against 46.65" now -- re-detection was
         not hiding the detachment, it was landing the room somewhere worse.
         The detached presentation predates P3.5 and is REGISTERED AS DEFECT 23
         against P4.5, because what to do about it is a semantics decision (does
         a room whose walls partly moved DEFORM to follow the corners that
         moved, as a party-wall drag already makes both its rooms do -- or stay
         put?) and that question is what a group IS.
         METHOD NOTE: metric (a) is NOT comparable across the P3.5 boundary.
         Before P3.5 an outline edge could be spanned by a LONGER wall, so a
         corner legitimately sat mid-wall; "corner matches no wall endpoint"
         only became a defect once one edge meant one wall end to end. The
         cross-boundary comparison is the drift number, which is basis-free.

P3.5-followup, ACCEPTANCE ITEMS -- four, answered in order.

COMMIT NAMING, and the rule was NOT honoured on the first pass. The fix, its
         telemetry and its tests went in as ONE commit, d0ab89d, not three. The
         full gate (ruff + OFF/ON/DEEP) was run immediately before it, so the
         green is real; what is missing is the ROLLBACK POINTS the sub-commit
         rule exists to create. Recorded rather than rewritten -- history
         surgery to make a log entry look tidier is the wrong trade. The
         remainder was split properly: 06c2145 (a) the warning wording,
         408adf7 (b) the tests, plus this doc commit, each at a full gate.

THE +6, named from a collect-only diff of f738437 against HEAD (502 -> 508
         collected; nothing removed):
           test_groups::test_whole_plan_group_move_carries_every_room
           test_groups::test_a_group_move_leaves_the_outlines_still_holding_
             their_corners
           test_groups::test_a_group_rotation_also_keeps_the_corners
           test_groups::test_a_group_move_never_drags_a_wall_outside_it
           test_design_bridge::test_the_warning_names_the_cause_and_says_it_once
           test_design_bridge::test_a_legacy_plan_is_blamed_on_the_file_not_on_
             an_edit
         Plus, at (b), a SEVENTH that is an xfail rather than a pass:
         test_groups::test_a_clipped_band_leaves_every_room_coherent -> P4.5.
         So the census is now 503 passed / 6 xfailed, and the sixth marker is
         that one -- named here so the next delta starts from a known set.

STEP 4 WAS HALF-DONE AND IS NOW WHOLE. The whole-plan test asserted only that
         each room's outline LANDED in the right place, which is why it passed
         against the pre-fix code. It now asserts all four per-room columns --
         walls-moved, outline-moved, identity, unwelded_ends -- on a 100%
         selection with no clipped rooms, and FAILS pre-fix (identity 0 where 4
         is required, verified in a worktree). The diagnosis's columns and the
         guard's columns are now the same columns.

STEP 5 WAS DONE AT d0ab89d, and the specific question is answered by
         measurement on the defect-23 repro POST-FIX: the duplicated walls left
         behind by a clipped band DO register as unwelded ends under a live
         gesture, so the rewording belongs to this task exactly as reasoned.
         Same 10-walk sequence (open, idle, group, bake, four debounced
         snapshots, a second move, one more snapshot):
           BEFORE  8 warnings, one per snapshot, every one of them saying
                   "expected on a plan loaded from a legacy file"
           AFTER   2 warnings, one per DISTINCT state (1 end, then 8), both
                   reading "... are NEW ... this is not the legacy-load case"
         The idle and post-open walks are silent in both, and the legacy case
         still says legacy (`test_a_legacy_plan_is_blamed_on_the_file_not_on_an_
         edit`). Reading the message the repro actually printed also caught the
         copy saying it backwards -- "0 of them since the plan was opened and 1
         NEW" -- fixed at 06c2145.

ONE UNEXPLAINED OBSERVATION, recorded rather than dismissed: a single `E`
         appeared in one DEEP run's truncated progress output. Not reproduced in
         five subsequent full DEEP runs (NOT "under different random seeds" --
         that phrase is withdrawn at defect 26 round 2: pytest-randomly is not
         installed, so every run in this project has always been in the same
         order), and an
         explicit ERROR grep over a full `-ra` run finds nothing. Most likely a
         cut-off pipe rather than a real error, but it is written down here so
         that if it recurs at P3.6 it is the second sighting, not the first.
         STANDING INSTRUCTION, carried into P3.6 by ruling: a recurrence during
         P3.6 is a SECOND SIGHTING and is investigated on the spot -- not
         re-filed as a first.
         >> RESOLVED AT P3.6, and the guess above was wrong in both halves: not
         a cut-off pipe, and not a timing flap. It is
         `test_a_clipped_band_leaves_every_room_coherent`, added at 408adf7 --
         the defect-23 characterization. It deliberately leaves the scene
         corrupt (stranded rooms are its subject) and never declared that state
         as a baseline, so under FP_VERIFY_DESIGN=deep the `win` fixture's
         teardown verify fires and pytest reports the test TWICE: an `E` in the
         progress line, a second XFAIL in the summary. Fixed with `rebase(win)`,
         the move `_overlapping_rooms` has always made for its deliberate
         overlap. THE SAME DOUBLE-REPORT WAS THE OFF-vs-DEEP CENSUS DISCREPANCY
         -- one cause, two symptoms. Recorded as a closed sighting; a THIRD
         would be a new bug, not this one.

P3.4  done   (branch v5-topology; four sub-commits + two riders)
ruff:    clean
pytest:  OFF  491 passed, 4 xfailed, 1 xpassed in 19.2s
         ON   491 passed, 4 xfailed, 1 xpassed in 24.6s
         DEEP 486 passed, 3 xfailed, 7 deselected in 22.2s
         (baseline in: P3.3's 447/4/1. +44 tests, one deleted -- see (iv).)
commits: ea54413 (i) · 340816c (ii) · a4a3336 457105e e49c07f (iii, three
         families) · 670fded (rider: the two divergence rulings) · 89f3d8b (iv)
         · cf7f850 (defect 20) · plus the per-sub-commit doc entries below.
         Logged sub-commit by sub-commit per the handoff-spec rule, so a
         successor session reads the state from here plus the seven settled
         points at lines 375-408 rather than from a chat summary.
(i) done   commit ea54413 -- planner/applier factoring + the scene applier for
         merge_collinear.
ruff:    clean
pytest:  OFF  468 passed, 4 xfailed, 1 xpassed in 18.4s
         ON   468 passed, 4 xfailed, 1 xpassed in 21.9s
         DEEP 463 passed, 3 xfailed, 7 deselected in 18.5s
files:   floorplanner/design/topology.py (GraphView/WallView/OpeningView,
         Merge/PlannedOpening, plan_merge_collinear, apply_merge_plan,
         graph_from_design; merge_collinear becomes their composition),
         floorplanner/walls.py (graph_from_scene, apply_merge_plan_to_scene,
         merge_collinear_scene), tests/test_topology_ops.py (new, 21)
NO EXISTING TEST CHANGED -- `git status tests/` shows only the new file, all
         three ways. The changed-test budget point 4 governs is still untouched
         going into (iii).
THE SHAPE, since it is the crux and the thing (ii)-(iv) all lean on: the
         decision runs ONCE, pure, over a neutral `GraphView` whose keys and
         anchors are the CALLER's own handles -- wall ids and vertex ids for a
         Design, `WallItem`s and `Vertex` objects for a scene. It returns a
         `Merge` delta (survivor, absorbed, the corner anchors the ends adopt,
         the planned opening offsets, the corners consumed). Two thin appliers
         execute it, touching only what it names. The delta deliberately does
         NOT name room binding: a Design records that as wall.left/right, the
         scene as WallItem.rooms, and each applier derives its own from
         `Merge.absorbed`. That is the one thing the two targets genuinely
         represent differently, and saying so is cheaper than pretending
         otherwise.
TWO BEHAVIOUR CHANGES IN THE PURE OP, both found BY single-sourcing rather
         than in spite of it, and both fixes:
         * merge no longer REFUSES a wall carrying openings. They are
           redistributed onto the merged span and deduped -- DEFECT 9, closed
           on the live-editing path the task text names. Guarded both ways: the
           new op yields one door, and `_coalesce_all_impl` on the identical
           input still yields two, so the closure is legible rather than
           asserted.
         * the survivor keeps its OWN DIRECTION. The old code wrote
           `w1.v1, w1.v2 = far1, far2`, which REVERSES the survivor whenever the
           run extends behind its v1 -- and did not swap left/right to match, so
           every side on that wall silently flipped. Latent, unpinned, and
           invisible until the same code had to serve a scene that renders
           sides. Own test.
TELEMETRY, ahead of point 5's ledger: an exact end-to-end merge causes ZERO
         split-on-writes -- the merged end is re-pointed AT the corner's vertex
         (`set_end_vertex`), not assigned a coordinate as coalesce did. A merge
         absorbing a wall from up to perp_tol off the line still splits, and
         that is correct: that end lands where no corner was, so it is a new
         corner and should say so.
A NARROWER CLAIM THAN IT LOOKS, stated so (iii) does not inherit a
         misconception: the merge shares the SURVIVOR's end with the corner
         anchor. It does not rebind OTHER walls sitting at that corner -- that
         is weld's job, and weld is still on this task's deletion list. What is
         true today is that both ops resolve the same corner to the same
         representative `Vertex`, so they converge rather than fight.
(ii) done  commit 340816c -- split_edge scene-side, the split rule's second
         half, the guard retarget.
ruff:    clean
pytest:  OFF  482 passed, 4 xfailed, 1 xpassed in 18.4s
         ON   482 passed, 4 xfailed, 1 xpassed in 21.8s
         DEEP 477 passed, 3 xfailed, 7 deselected in 20.7s
files:   design/topology.py (Split, plan_split_edge, apply_split_plan;
         split_edge becomes their composition), walls.py
         (apply_split_plan_to_scene, split_wall_at, WallItem.
         _split_body_landings + _run_wall_under), tests/test_wall_move.py
         (+7, ADDITIONS ONLY -- 0 deletions), tests/test_topology_ops.py (+7),
         tests/test_topology.py (the one rewrite, below)
THE SPLIT RULE IS NOW WHOLE. P3.3 built the first half and left the second
         declared-but-not-done, tee branch on the coordinate path with a
         comment naming this task. A body-landing now SPLITS the wall it lands
         on -- which MAKES the vertex it never had -- and is then promoted onto
         it exactly as a corner attachment is. The new segment joins the run,
         so the user still slides the whole wall they grabbed (own test; that
         is the way this could have silently gone wrong).
TEST CHANGED (1), the pre-authorized one, named per the working agreement:
         tests/test_topology.py::test_split_edge_raises_on_a_wall_with_openings
         asserted `pytest.raises(NotImplementedError, match="P3.3")`. OLD OP:
         split_edge refused any wall carrying an opening. NEW OP: it
         redistributes them. WHY THE ASSERTION MOVED: that message was a
         placeholder for unbuilt work and said so; the work is built here, so
         the assertion pinning its absence has nothing left to pin. Rewritten
         as TWO tests -- redistribution works, and the guard SURVIVES narrowed
         to the case redistribution genuinely cannot answer. Hence the
         pre-authorized string change, `match="P3.3"` -> `match="P3.6"`.
THE GUARD IS RETARGETED, NOT RETIRED, and the distinction is the content of the
         ruling. Redistribution answers "which segment owns the door". It
         cannot answer "which segment owns a door the cut runs THROUGH",
         because neither does -- that is an opening which no longer fits where
         it lands, and reporting one instead of silently sliding it is P3.6's
         line in this plan. So the guard keeps its P1.3-followup discipline
         (fail loud AT the call site) on a strictly smaller domain.
TWO POLICIES, ONE DECISION -- declared, because it is the closest this task
         comes to the applier drift point 1 forbids, and it is not that.
         `topology.split_edge` RAISES on a straddling split; the scene op
         DECLINES it. Same planner, same delta, same `straddled` flag. What
         differs is what each CALLER does with a flagged delta, because one is
         a document repair and the other is a mouse gesture that must not
         crash mid-drag. The decision is single-sourced; only the policy is
         local, and a declined split leaves P3.3's exact behaviour behind.
TELEMETRY -- point 5's prediction, measured BOTH ways rather than asserted:
         * dedicated tee scenario, 12 drags: 12 split-on-writes BEFORE
           (measured by disabling the new pass), 0 AFTER. The branch is silent,
           which is the claim point 5 makes.
         * composite (coalesce + weld + group + bake + ungroup + 12 drags):
           mouseMoveEvent splits 4 -> 1.
         * AND THE RESIDUE IS NOT THE TEE BRANCH FAILING. Two landings were
           DECLINED because the split point falls inside an opening -- and
           those openings turn out to be 15 IDENTICAL 96" windows stacked at
           one `s`, produced by the old `_coalesce_wall_impl` on the
           bake/ungroup path. That is DEFECT 9 in the wild, inside the code
           (iii)/(iv) delete. PREDICTION FOR (iii), recorded now so it is a
           prediction and not a rationalisation: retiring coalesce removes the
           stacks and those two landings then split.
         * a call site P3.3's scenario never triggered: 8 splits at
           walls.py:233 in `_coalesce_wall_impl`. Also (iii)/(iv)'s.
THE CORPUS GUARD HAS GONE VACUOUS, and saying so is the point. P3.3's
         press-every-wall test still passes -- but neither corpus plan has an
         unwelded body-landing, so pressing every wall of sample_plan and
         planc1 now makes exactly 0 splits (measured). It no longer exercises
         the risk it was written for. Added the case that DOES split, asserting
         the document is unchanged across it: the scene walk already cuts walls
         at junctions (`split_params`), so a press-time split only makes the
         scene agree with what the document always said. Verified rather than
         assumed -- 2 scene walls -> 3, document byte-identical, 3 document
         walls before and after.
(iii) done  commits a4a3336 (family 1), 457105e (family 2), e49c07f (family 3).
ruff:    clean
pytest:  OFF  491 passed, 4 xfailed, 1 xpassed in 16.7s
         ON   491 passed, 4 xfailed, 1 xpassed in 19.3s
         DEEP 486 passed, 3 xfailed, 7 deselected in 17.4s
NO EXISTING TEST CHANGED across all three families. The changed-test budget
         point 4 governs is still spent only on (ii)'s one pre-authorized
         rewrite, going into (iv).
FAMILY 1 -- COALESCE (5 sites): view.py:487 and walls.py:1385 (draw / drag
         release) -> `merge_wall`; planio.py:181 (load), rooms.py:1020 (room
         label drop), mainwindow.py:820 (ungroup) -> `merge_all`.
         `merge_wall` forces the passed wall to be the run's SURVIVOR -- the
         caller has just drawn or dragged that item, holds a reference to it,
         and it carries the selection; the planner takes the run's first wall
         in the caller's order, so the whole of "this one survives" is a sort
         key. UNGROUP IS WIRED, NOT MIGRATED, per the ruling, with the comment
         at the site: under P4.5 nothing is duplicated so nothing needs merging
         on ungroup, making that call P4.5's to DELETE rather than this task's
         to port.
         Behaviour change, small and a fix: the merged wall lands on the union
         span exactly, where `_coalesce_wall_impl` re-snapped both ends to the
         6" grid. bridge.py:550 already flags that snap in its own words
         ("Coalesce MOVES geometry"). No test depended on it.
         PERF: the planner gained `_candidate_groups`, `_WallIndex`'s line
         bucketing moved to where the merge decision now lives -- without it a
         per-wall merge scans every wall on every draw-release, trading
         coalesce's O(local) for O(plan), the direction P3.8 must not go.
FAMILY 2 -- WELD (3 sites): view.py:489 `join_endpoints` -> `weld_wall_ends`;
         imageio.py:180 `weld_all` -> `weld_scene`; mainwindow.py:827 ->
         `normalize_walls`. After this the whole coalesce+weld set is a
         CALLERLESS ISLAND.
         THE COMMAND OUTLIVES ITS IMPLEMENTATION, per the ruling. Edit ▸
         Coalesce all walls now is the explicit plan-wide normalization: merge
         every collinear run, then weld -- close the gaps, fold coincident ends
         onto one vertex, split a wall where another's end lands on its body.
         Same menu item, same intent, new machinery, still ungated.
         Welding now has a TOPOLOGY half. `weld_all` left a welded corner as
         two coordinates that happened to agree, which is exactly what P3.3's
         drag then had to rediscover by scanning at every press. The geometry
         snap is kept verbatim: closing a 9" gap is a repair, not topology, and
         it is the only way a drawn or extracted plan closes junctions at all.
         ONE RULE, FOUND BY A FAILING TEST. The first cut had `weld_scene`
         split body landings too, and test_extract_from_reference_adds_walls
         went 5 walls -> 7. The split is CORRECT topology -- but shipping it
         inside a call-site migration is a behaviour change smuggled under a
         rename, and it edits a wall the user never touched. So splitting
         belongs to the EXPLICIT pass and nowhere else: `weld_wall_ends`
         doesn't, `weld_scene` doesn't, `normalize_walls` does. Applying the
         rule uniformly made the test change unnecessary, which is the tell
         that the rule was right and not a dodge. P3.5 will want plan-wide
         planarity for `enclosing_face`; that is P3.5's to ask for, through the
         pass built for it.
FAMILY 3 -- THE QUERY HELPERS: one migrated, one policed, two divergences.
         `_joined_at` MIGRATED: a 0.6" coordinate search becomes a DEGREE
         lookup on a `_CornerIndex`, and `_WallIndex`'s endpoint hash is gone.
         Zero behaviour change, and the replacement carries its own oracle --
         `_joined_at`'s un-indexed fallback still runs the old search, so the
         test compares the two directly on every end rather than trusting the
         reasoning. `_CornerIndex` is now the SINGLE definition of "these ends
         are one corner"; both halves earn their place, since identity is the
         real question but load deliberately does not weld, so in a loaded plan
         only position can see the corner.
         `coincident_walls` POLICED, NOT MERGED, and that is a decision. It is
         on the hottest path in the app (`WallItem.rebuild`, once per wall per
         pass) and routing it through the planner would allocate a view per
         candidate to prove a predicate that is already a transcription. A
         drift gate pins the two equal across overlapping / off-grid /
         abutting / perpendicular / diagonal pairs instead -- the same move
         `--verify-design` makes for the two appliers.
TWO CENSUS DIVERGENCES, reported rather than forced (Touches lists are hints):
         * `_WallBBoxIndex` CANNOT die at P3.4. The task line lists it, but its
           last caller is rooms.py:340, the memoized room dirty-check -- and
           "refresh_rooms memoization" is on P3.5's list BY NAME. A line dies
           when its last caller dies, and this one's last caller is P3.5's.
         * `wall_endpoint_open` NOT migrated to degree, deliberately. Its
           tolerance is JOIN_TOL (9"), not SHARE_TOL: the 9" scan was a PROXY
           for a question the pre-vertex code could not ask. Degree is the
           truer question, but swapping them changes which ends the draw-snap
           offers to align with on unwelded geometry -- a behaviour change
           needing this task's own three-part earning, and it buys no deletion
           since the helper survives Phase 3 either way. Recommended as its own
           change or as P3.5's.
         Consequence: `_WallIndex` SHRINKS rather than dies. Its line buckets
         are a spatial index, not detection machinery, and the planner needed
         the identical bucketing badly enough that `_candidate_groups` is a
         copy of them. The honest end-state is one index, not zero.
RIDER (commit 670fded) -- the two (iii) divergences, ruled:
         * `wall_endpoint_open` REFRAMED PERMANENTLY, in its own docstring, so
           no future task "migrates" it out of a misplaced sense of
           completeness. It is not a survivor of the old world; it is a correct
           citizen of the new one. Its tolerance is JOIN_TOL, the GESTURE
           tolerance, and gesture questions are inherently spatial. Degree
           answers the MODELLING question ("are these ends one corner?"); this
           answers the AIMING question ("is there something near enough to snap
           to?"). Degree cannot serve here even in principle -- the ends worth
           offering the user are precisely the ones NOT yet welded, so a degree
           query calls every one of them free and the snap has nothing to aim
           at. The docstring names `_joined_at` as the one that DID migrate.
         * THE BUCKETING DUPLICATION UNIFIED, not pinned. `topology.line_bucket`
           + `bucket_reach` are the one definition; `_candidate_groups` and
           `_WallIndex` both call them and `_WallIndex.OFF` is gone.
           Unification beat a second drift gate because the policy is pure
           coordinates, so it belongs on the Qt-free side with the scene
           importing it -- the dependency flows the right way, which is not
           true of most things one might want to share across that fence.

(iv) done   commit 89f3d8b -- the deletion, the junction contract, the checks.
DELETED, 149 lines across 7 functions, all callerless after (iii):
         `_coalesce_wall_impl` (59), `coalesce_wall` (8), `_wall_count` (5),
         `_coalesce_all_impl` (26), `coalesce_all` (7), `weld_all` (23),
         `WallItem.join_endpoints` (21) -- plus `_WallIndex`'s endpoint hash,
         folded into `_CornerIndex` at (iii): 50 lines -> 40.
EXIT CHECK 1 -- MEASURED DELETION vs THE ESTIMATE. Estimated 375 across 13
         functions; MEASURED 149 across 7. The gap is three survivors with
         named reasons, not shortfall, and 169 lines of the census live on:
         * `fracture_delete_wall` (55) + `_merge_intervals` (9) -> P4.1. Two
           live callers, not migrated at (iii), and retiring them IS P4.1's
           deliverable -- its acceptance is literally "P0.4 test 2 flips to
           pass". AND THE MEASUREMENT IS THE FINDING: a plain delete now KEEPS
           the room (1 room, 100.0 sf, 3 built walls + 1 open edge -- exactly
           test 2b's assertion), because P3.2 gave RoomItem a stored outline.
           P4.1's blocker is already gone and P4.1 is now a small change;
           doing it here would be landing another task's deliverable under this
           one's name.
         * `_WallBBoxIndex` (34) -> P3.5, as reported at (iii).
         * `_compute_wall_junctions` (31) STAYS -- next paragraph.
         * `_WallIndex` (40) shrank rather than died.
EXIT CHECK 4 -- THE JUNCTION CONTRACT, AND THE SWAP IT REFUSED. Point 3 said
         "if the junction test needs touching, the replacement is wrong."
         IT NEEDS TOUCHING, so the replacement is not made. Measured on the
         structural guard's own scene -- a horizontal and a vertical wall
         crossing mid-span -- the two share ZERO corners (all four ends degree
         1) while their `_solid`s genuinely intersect and the bbox pass
         correctly clips both. Adjacency-only neighbours find nothing, set both
         clips to None, and fail the guard. An unwelded crossing is a legal
         scene state (crossing-point insertion is not built), so bbox search is
         not legacy machinery here -- it is the only thing that answers the
         question. The contract worked exactly as designed: it was written to
         catch a wrong replacement, and it caught one.
         THE PIXEL ASSERTION LANDED ANYWAY, an ADDITION, because it is what
         makes any future attempt safe. POLARITY MEASURED, NOT ASSUMED, and it
         is the INVERSE of the spec's wording: the wall body is grey (150) and
         a seam is a DARK line across the junction (56), so "no LIGHT seam
         pixel" names the wrong failure. Seam-free asserts the interior stays
         body-grey; the `< 190` threshold is used where it genuinely belongs --
         the negative half, clip cleared, where an antialiased 1-px dark line
         must read under 190 and nowhere near 100. Both halves in one test, so
         the positive assertion cannot go vacuous. The structural pin is green
         and UNCHANGED.
EXIT CHECK 2 -- THE P2.3 KNOWN-REGRESSIONS ROW DOES NOT CLOSE, and the row's
         predicted fix was wrong on its own terms. Checked by hand: the 480"
         wall still returns as two 240" segments after the undo restore,
         `merge_all` does NOT re-merge them, and the body-drag still moves one
         segment (p1.y 12 and 0). It MUST not -- the mid-span T is a degree-3
         vertex, load-bearing for the planar subdivision, and merging through
         it would destroy planarity. So this was never merge's row to close.
         NOT FLIPPED; retargeted in place with the real fix named: the drag's
         run-gathering, where `_collinear_run()` short-circuits to `[self]` for
         a room-less wall. Left unassigned rather than invented, with P4.2 as
         the nearest task that touches the drag.
EXIT CHECK 3 -- THE DEFECT-9 PREDICTION, GRADED HALF-RIGHT AND PRECISELY.
         FIRST HALF CONFIRMED: retiring coalesce removed the stacks -- 16
         openings on one wall became 1. SECOND HALF FALSIFIED: the two tee
         landings still decline. But the residual cause is now legitimate
         rather than debris -- the harness puts a 96" window at the centre of a
         240" wall and the neighbouring grid line lands at s=120, dead inside
         it (measured: openings [(120.0, 96.0)], straddled 1). A genuine
         straddle, correctly declined, P3.6's case. The count coinciding at 2
         is coincidence; the mechanism the prediction named was real and is
         gone. Recording the falsified half is the point of having predicted.
EXIT CHECK 5 -- TELEMETRY RESIDUE, 137 splits on the composite scenario:
         64 + 64  items.py:703/704 in bake()   -- P4.5's, correct that they stay
          8       walls.py in _adopt_end()     -- MOVED, not new
          1       walls.py in mouseMoveEvent() -- the grouped/rigid branch, P4.5
         The 8 were `_coalesce_wall_impl`'s at (ii); they are the merge
         applier splitting on write when an absorbed end lands where no corner
         was -- declared at (i) as correct for that case. Same count, honest
         new home.
TESTS REWRITTEN -- the plan's biggest changed-test risk, one line each:
         * test_coalesce.py (whole file): `_coalesce_*_impl` -> `merge_all` /
           `merge_wall`. THE ASSERTIONS DID NOT MOVE -- they are the behaviour
           contract, not the implementation, and every line still says exactly
           what it said. Only the call changed.
         * test_walls.py: `join_endpoints` -> `weld_wall_ends`, `weld_all` ->
           `weld_scene`, `_coalesce_wall_impl` -> `merge_wall`. Assertions
           unchanged: the geometry snap they pin was lifted verbatim into
           `_snap_wall_ends`. Plus the pixel test, an addition.
         * test_characterization.py 5 and test_floors.py: `coalesce_all` ->
           `merge_all`; the group-exemption and cross-floor assertions
           unchanged.
         * test_topology_ops.py: the defect-9 OLD-op comparison DELETED with
           the op it exercised. Once the defect's implementation is gone there
           is no old behaviour left to exhibit and the test would be asserting
           against a museum piece. It did its job at (i) and (ii); a claim
           about code that no longer exists belongs in this log, and a comment
           at the site says so.
         * test_scaling.py, test_design_bridge.py: stale `coalesce_all` wording
           only, no assertion touched.
(iv) EXIT CHECKS as fixed before the work (all five answered above):
         1. the measured deletion count against the estimated 375 across 13
            functions, with `_WallIndex`/`_WallBBoxIndex` surviving named;
         2. the P2.3 Known-regressions row re-checked BY HAND (the 480"
            body-drag moving as one run) and flipped ONLY if it genuinely
            closes;
         3. (ii)'s recorded prediction, promoted to an exit check by ruling:
            retiring coalesce removes the defect-9 stacks, so the two tee
            landings that DECLINED in the composite telemetry should then
            split. Falsifiable, cheap, and if it holds it is the cleanest
            demonstration yet that the old machinery was manufacturing the
            conditions that defeated the new one;
         4. the junction contract's two halves: `test_junction_outline_is_
            clipped_so_walls_read_solid` green UNCHANGED, plus the new pixel
            assertion at the `< 190` threshold;
         5. tests/test_scaling.py's ungroup xfail reason still says "calls
            O(walls^2) coalesce_all" -- stale from family 1, true again only as
            history. Fix it with the deletion, where the claim actually changes.
Census re-verified on disk before starting:
         `coincident_walls` at walls.py:656 and :695 and view.py:597,
         `wall_endpoint_open` at view.py:248, and the dying caller at
         walls.py:201 inside `_coalesce_wall_impl`. ONE CORRECTION to the
         census's wording, not its content: BOTH walls.py hits are inside
         `WallItem.rebuild` (:656 is the party-wall opening cascade, :695 the
         neighbour-rebuild tail), not "rebuild and paint" -- `paint` reads the
         already-built `_path`. The adjudication is unaffected; both survive
         Phase 3 and both migrate.

```
