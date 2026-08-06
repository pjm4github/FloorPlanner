# Progress log - Phase 3 - vertices own the geometry (part 1)

> **Moved verbatim** from `V5_MIGRATION_PLAN.md` (its lines 1658-2649 as of
> commit 2f232bd) on 2026-08-06. Nothing was reworded, reordered, tidied or
> reformatted; the entries appear in the order they were appended. The code
> fence below is the one the log has always been written inside - it is
> reopened here and closed at the end, because a fence cannot be split.
>
> Index: [`README.md`](README.md) - Plan: [`../V5_MIGRATION_PLAN.md`](../V5_MIGRATION_PLAN.md)

```
P3.1  done   (commit f0990d4, on branch v5-topology)
ruff:    clean
pytest:  OFF  415 passed, 4 xfailed, 1 xpassed in 16.69s
         ON   415 passed, 4 xfailed, 1 xpassed in 20.20s
         DEEP 410 passed, 3 xfailed, 7 deselected in 18.22s
files:   floorplanner/vertex.py (new), floorplanner/walls.py (read-through
         p1/p2 + v1/v2), floorplanner/design/verify.py (split logging),
         tests/test_vertices.py (new, 12)
ACCEPTANCE: suite green with NO TEST CHANGES -- `git status tests/` shows only
         the new file -- and the --verify-design run stays green.
notes:   A Vertex is a shared, identity-bearing point; two wall ends holding the
         SAME Vertex object are the same corner. No registry: the "table" is the
         set of vertices reachable from the walls, exactly as Design.vertices is.
         SPLIT-ON-WRITE, per the ruling. Assigning a moved position mints a
         fresh vertex and leaves any sharer put; a NO-OP assignment returns the
         same vertex, so identity and sharing survive the many places that
         re-set the same coordinates. Pinned by a test that shares a corner
         explicitly, moves one end, and asserts the other did not follow.
         SPLIT LOGGING: verify() records the per-operation delta in
         win._vertex_split_log. It LOGS rather than warns -- a drag legitimately
         splits, so a warning per drag would be noise, not signal.
         A PERFORMANCE REGRESSION I INTRODUCED AND FIXED, recorded because the
         HARNESS caught it and review would not have: the first version
         allocated a QPointF on every p1/p2 READ and a uid string on every
         write. p1/p2 are read on every rebuild, paint and hit-test, so rebuild
         slowed ~50% and bake nearly doubled -- test_bake flapped at 8.54
         against a threshold of 8. Fixed by storing the QPointF once and
         returning it SHARED, and minting uids lazily. Both are safe only
         because a vertex is never mutated in place: a move produces a NEW
         vertex, so a caller holding an old p1 still sees the old position --
         identical to the previous behaviour, where assignment rebound the
         attribute to a fresh QPointF. Verified before relying on it (nothing in
         the codebase mutates a p1/p2 in place; every access is .x()/.y()) and
         pinned by test_vertex_is_never_mutated_in_place. bake now 43.7 -> 297
         ms ratio 6.83 vs P2.3's recorded 40.8 -> 278.7 ratio 6.83 -- restored,
         not merely under the threshold. This is the second time P0.3's harness
         has paid for itself on a change that looked free.
         FINDING -- WHY P3.1 STOPS AT THE REPRESENTATION. design_from_scene
         still builds its own vertex table by welding COORDINATES at 0.6"; it
         does not yet consume the live uids. It cannot: nothing creates sharing
         yet, so today every coincident wall end is a DISTINCT vertex, and
         emitting live uids would put two vertices 0" apart in the document and
         trip I14 across the whole corpus. Consuming the live table therefore
         has to wait until weld/join create shared vertices explicitly, at
         P3.3/P3.4. That ordering is not a shortcut -- it is the same
         representation-then-behaviour discipline the split-on-write ruling
         encodes.
         COMPOSITION GATE (the Gate 2 lesson): round trips asserted through BOTH
         apply paths -- load_data (faithful) and open_document (converting,
         composed all the way out to a legacy export and back).

CI-ON-BRANCH  done   (draft PR #1)
notes:   Pushing v5-topology ran NO CI -- ci.yml triggers on push-to-main and
         pull_request only, so the whole geometry rewrite would have gone
         unvalidated until the merge: exactly the situation P0.3 called out.
         Fixed with a DRAFT PR (v5-topology -> main) rather than editing
         ci.yml's push list: the pull_request trigger then covers every push,
         and it costs no config change on main that we would later revert. The
         PR also gives a running diff of the phase and is the merge vehicle at
         P3.8. First run green: ruff, py3.10 and py3.13, both suite runs.

P3.2  done   (commit 77bc91a, branch v5-topology)
ruff:    clean
pytest:  OFF  428 passed, 4 xfailed, 1 xpassed in 16.69s
         ON   428 passed, 4 xfailed, 1 xpassed in 18.64s
         DEEP 423 passed, 3 xfailed, 7 deselected in 16.80s
files:   floorplanner/rooms.py (OutlineEdge, derived corners, mirror deleted,
         edge->wall in bind_room_walls, clipboard fix), floorplanner/planio.py
         (export re-derives, load strips), floorplanner/items.py +
         mainwindow.py (mirror call sites), tests/test_outline.py (new, 13),
         tests/test_groups.py (one deleted-method call)
ACCEPTANCE: room areas unchanged across the corpus (asserted on sample_plan and
         planc1 through the faithful apply, with the document identical after);
         _sync_corner_props and its six call sites deleted.
notes:   INTERIM REPRESENTATION, stated not implied: an outline edge holds a
         COORDINATE, not a vertex identity. P3.1's split-on-write world has no
         shared corner vertex to name -- at every corner each wall owns a
         distinct Vertex. Borrowing one wall's end picks arbitrarily between
         two (and two rooms meeting there could pick differently); minting a
         room-owned vertex adds a third object no wall references. Both encode
         an authority that does not exist yet; a coordinate states exactly what
         is known. THE TEST FOR CHOOSING AN INTERIM REPRESENTATION IS WHICH ONE
         DOES NOT LIE.
         Two guards pin the gap: outline corner and wall end have equal
         coordinates but are distinct objects, and a corner is still two
         distinct wall vertices. Both say in their docstrings that FAILING is
         the signal P3.4 closed the gap, not that something broke.
         The edge->wall mapping is the real content of the task -- before it a
         room had corners and an unordered walls list with no correspondence.
         SHIPPED POPULATED (bind_room_walls already computed it to place
         OpenWall placeholders), so the fallback rider does not apply and P3.4
         inherits nothing.
         THREE FATES, all three exercised by tests: the live mirror DELETED;
         the legacy v4 export KEPT byte-compatibly via
         RoomItem.export_properties() re-deriving at serialization time at the
         same 2dp rounding (the v4 loader needs it for OPEN rooms, whose
         detection fails); the importer reading legacy FILES untouched forever.
         Plus "ignored on load" -- read for the fallback, then stripped.
         AUDIT FINDING -- THE MIRROR WAS MASKING A LATENT BUG, and only the
         grep-everything instruction found it. _copy_spec carried
         dict(self.properties) -- including the SOURCE room's perimeter_corners
         -- into the clipboard; paste_room passed it to the new RoomItem, where
         _sync_corner_props overwrote it. Deleting the mirror naively would have
         shipped the source room's geometry into every pasted room, in a corner
         the suite does not reach. Fixed by keeping geometry out of the
         clipboard, with a test. All 20 tree-wide hits reconcile: 6 importer
         (4 live + 2 docstrings), 2 mirror body, 1 legacy-load fallback, 1
         bridge pop, 1 tool docstring, 8 tests, 1 schema (which FORBIDS the key,
         confirming the plan's parenthetical).
         The room-properties dialog and the inventory paths were checked too:
         the dialog updates an explicit key list, inventory reads include_sqft
         only. Neither touches geometry.
         TEST CHANGED (1): tests/test_groups.py called room._sync_corner_props()
         directly -- a SEVENTH call site, in tests rather than production.
         Removed; a call to a deleted private method, not an assertion (the P0.2
         class). The change I PREDICTED to test_design_bridge's _project_areas
         did NOT materialise: because the export re-derives the key rather than
         dropping it, that helper reads it unchanged.

P3.3  done   (branch v5-topology)
ruff:    clean
pytest:  OFF  447 passed, 4 xfailed, 1 xpassed in 18.04s
         ON   447 passed, 4 xfailed, 1 xpassed in 19.61s
         DEEP 442 passed, 3 xfailed, 7 deselected in 17.69s
files:   floorplanner/vertex.py (relocated_to + call-site attribution),
         floorplanner/walls.py (_DragVertex, end_vertex/set_end_vertex,
         _is_continuation, _plan_vertex_moves, the drag rewritten),
         floorplanner/design/verify.py (SITE_LOG_ATTR),
         tests/test_wall_move.py (new, 19)
ACCEPTANCE: suite green with NO TEST CHANGES -- `git status tests/` shows only
         the new file, all three ways.
THE LOG ENTRY FOR THIS TASK WAS NOT ON DISK. The brief said the five settled
         points were in this Progress log; they were not, and 3d6d32e touched
         only two lines (defect 12a, and the P2.3 regression row). Reported
         rather than reconstructed, per the P0.6 rule. Two of the five WERE on
         disk and are quoted here: the same-level constraint (defect 12a,
         `_attached`) and `_collinear_run` at walls.py:888 gathering 2 of 2. The
         "72 splits" figure appears nowhere in the repo (a grep for it over
         docs/*.md is empty), so it is not quoted; the measured figure for this
         task's scenario is below. The 0.6" tolerance was verified in the CODE
         (walls.py, `QLineF(q, rp).length() < 0.6`), which matches
         vertex_weld_in / WELD_TOL -- the schema's own definition of one vertex,
         and now named SHARE_TOL rather than repeated as a literal.
THE HEADLINE NUMBER, measured both ways on the same 4x4 grid: 12 wall drags
         caused 148 SPLIT-ON-WRITES before this task and 2 after. The two that
         remain are the branches deliberately NOT promoted (see below), so the
         drag path is converted, not merely quieter.
(1) PROMOTION. The 0.6" scan used to discover coincident ends and then push each
         one by hand on every mouse event, which is split-on-write: the corner
         came apart and was rebuilt from coordinates 60 times a second. Now the
         scan runs ONCE at press and REBINDS those ends to one Vertex object
         (`set_end_vertex`), and the drag moves the vertex (`relocated_to`) --
         so a neighbour follows because it IS the corner. Asserted with `is`,
         never `==`: equal coordinates are exactly what the old code already
         produced and would not distinguish the two worlds.
         `relocated_to` CARRIES THE UID. A moved corner is the same corner, so
         renaming it would be wrong on its own terms and would also break P4.5,
         which serializes groups by member id. It is not counted as a split,
         because it is not one -- otherwise P3.3's own conversion would show up
         in the very telemetry that exists to find the call sites still needing
         it. A test pins that the count does not move across a drag.
         SAME LEVEL ONLY (defect 12a, now closed). Filtered at the LOOP HEAD, so
         cross-level sharing is impossible by construction. Note the filter
         covers the whole scan, not just the promotion: leaving the tee branch
         unfiltered would have left half of defect 12a alive for no benefit, and
         the transient cross-floor mis-drag is a real bug too. Declared because
         it is one line wider than "promotion is same-level".
(2) THE SPLIT RULE, and what it is really a rule about: what must NOT be shared.
         A wall collinear with the slide that continues past an endpoint cannot
         ride the corner -- the slide is perpendicular, so moving the shared end
         would swing its far end and SHEAR it. So the continuation is split off
         FIRST (its own vertex, and it stays put), before any sharing is made.
         Verified in both directions rather than asserted: with P3.3 reverted,
         test_a_collinear_continuation_is_never_sheared FAILS with the
         continuation's end at y=12 instead of y=0 -- it really was being
         dragged and sheared, so this is a behaviour FIX, not just a
         representation change.
         THE FIRST EARNED BEHAVIOUR CHANGE OF PHASE 3, and the label is the
         standard rather than a flourish. Phase 3's contract is that P3.1 and
         P3.2 are compat shims -- representation moves, behaviour does not, and
         "suite green with no test changes" is the receipt. A behaviour change
         inside that contract has to earn its place, which means all three of:
         DECLARED in advance (the split rule was in the task text), TESTED IN
         BOTH DIRECTIONS (it fails on reverted code, at a named coordinate, so
         the bug is exhibited and not merely described), and BRACKETED BY A
         MEASUREMENT (148 -> 2 splits over the same 12 drags, so the size of
         the change is known and not guessed). A behaviour change with fewer
         than three is a regression that has not been noticed yet.
         The rule also has to BREAK sharing that already exists, not merely
         decline to create it (a corner welded by an earlier operation is
         exactly what P3.4's weld produces). Own test.
(3) DETECTION STAYS AUTHORITATIVE. Nothing here reads outlines off vertices;
         room areas after a drag are what refresh_rooms arrives at, and the
         scene test asserts that. P3.5 flips it.
(4) CALL-SITE ATTRIBUTION, and the data it immediately produced. P3.1's counter
         said an operation splits; it could not say WHERE, and "which call sites
         should become real vertex moves" is a question about lines. `_blame()`
         walks past this module and past the p1/p2 setters -- blaming the
         setters would put every split on two lines and answer nothing.
         MEASURED, over coalesce + weld + group + bake + ungroup + 12 drags = 82
         splits:
             40  items.py:703 in bake()
             40  items.py:704 in bake()
              2  walls.py     in mouseMoveEvent()
         So 80 of 82 are GroupItem.bake, on two adjacent lines, and that is
         P4.5's ("groups move the real items -- no duplicate_wall"). The 2 are
         the tee and grouped branches this task deliberately left on the
         coordinate path. The drag's own corner moves contribute ZERO.
         TWO LOGS, not a wider tuple: SPLIT_LOG_ATTR keeps its (operation,
         splits) shape and SITE_LOG_ATTR carries the blame, so the P3.1 reader
         (and its test) is not broken to add data it did not ask for.
         COST measured, per the P3.1 lesson: 622 ns per split for the
         sys._getframe walk. Never on a READ -- reads are the hot path P3.1 had
         to fix -- and at 82 splits per heavy session it is under noise. The
         harness confirms: bake ratio 6.57 / 6.90 / 7.78 over three runs
         (absolute 303-332 ms) against P3.1's recorded 6.83 / 297 ms. The 7.78
         sample is variance, not a regression -- checked by re-running rather
         than by assuming, because the first run alone looked like one.
A HAZARD FOUND WHILE REVIEWING MY OWN DIFF, and it is not a corner case:
         GROUPING DUPLICATES A ROOM'S WALLS ONTO THE ORIGINALS, so a grouped end
         coincident with a dragged wall is the COMMON case. Promoting it would
         wire a group member to an outside wall permanently, and what a group is
         topologically is P4.5's open question. Grouped neighbours therefore
         keep the OLD coordinate path (`kind == "rigid"`) -- they still follow
         the drag exactly as today, they just do not become topology. Same
         instinct as the `group() is None` gate that keeps grouped walls out of
         coalesce, applied one task before the semantics that need it.
COMPOSITION GATE (the standing additions): both apply paths after a real drag --
         load_data (faithful) and open_document (converting, composed out to a
         legacy v4 export and back, ends_moved == 0) -- plus a corpus test that
         presses EVERY wall of sample_plan and planc1 without dragging and
         asserts the whole document is unchanged and zero splits occurred. That
         last one is the new risk this task introduces and nothing else would
         catch: the press rewrites which vertex a neighbour points at, on every
         wall the user so much as clicks. Areas would survive a promotion that
         re-pointed an end at the WRONG corner; the document would not, so the
         document is what is asserted. Measured on planc1: 80 walls pressed,
         document byte-identical, 0 splits.
DEFERRED, DECLARED, NOT DONE -- and it needs a ruling. The plan's P3.3 task text
         has a second half of the split rule: "a vertex landing on another
         wall's body splits that wall." It is NOT among the five settled points
         (which specify the promotion, detection authority, attribution, the
         four tests, and the gate), and it is P3.4's shape of work: splitting a
         WallItem at a landing point is `split_edge` scene-side, in the same
         task that replaces coalesce/weld/fracture. Doing it here would
         duplicate that and would add an automatic wall-splitting side effect to
         every drag release -- a wide blast radius for something no acceptance
         test asks for. The tee branch is left on the coordinate path with a
         comment naming P3.4. Flagging rather than quietly widening or
         narrowing the task: say the word and it lands here instead.
DEMO PORT: `w24` no longer exists as that wall. The demo named it, but ids are
         canonical and the Gate 2 regeneration (82 walls -> 80, 47/62 vertex ids
         renumbered) moved every id in symmetricP1.json -- w24 is now a Master
         Suite / Rear Porch wall, and pre-Gate-2 it was Hall / Lounge. The
         BEHAVIOURAL pin holds exactly on today's fixture: the Lounge / Front
         Porch party wall (currently w18, 210" at y=864), +12 y, Lounge +17.5 sf
         and Front Porch -17.5 sf, TOTAL UNCHANGED to 0.0, check(deep=True) ==
         []. The test picks the wall by rooms and axis, never by id, so it fails
         for a regression rather than for a renumbering. A second test pins that
         the chosen wall really has no collinear continuation -- the demo's own
         precondition -- so the first cannot pass by luck.

P3.5  done   (branch v5-topology; five sub-commits)
ruff:    clean
pytest:  OFF  497 passed, 5 xfailed in 13.7s
         ON   497 passed, 5 xfailed in 16.0s
         DEEP 492 passed, 3 xfailed, 7 deselected in 15.4s
         (baseline in: P3.4's 491/4/1.)
THE XFAIL/XPASS DELTA -- ASKED TWICE, ANSWERED FROM DISK. Both ends were run
         in worktrees and the marker lists diffed, rather than reasoned about:

           c133205 (P3.5 in)   493 passed, 4 xfailed, 1 xpassed
           f738437 (P3.5 out)  497 passed, 5 xfailed

         THERE IS NO "+1 XFAIL". The marked set is BYTE-IDENTICAL at both ends
         -- the same five tests, same order, same reason strings:
           test_characterization::test_delete_wall_actually_removes_the_wall  P4.1
           test_characterization::test_group_survives_roundtrip               P4.5
           test_groups::test_extracted_room_region_follows_move               P4.2
           test_scaling::test_group_scales_subquadratically                   P3.8
           test_scaling::test_ungroup_scales_subquadratically                 P3.8
         P3.5 added no marker and retired none.

         THE VANISHED XPASS IS THE LAST OF THEM, `test_ungroup_scales_
         subquadratically` -- same test, same `xfail(strict=False)` marker,
         reporting XPASS at c133205 and XFAIL at f738437 because its ratio
         crossed the threshold of 8. MEASURED 7.85 / 8.29 / 8.54 / 8.82 on
         successive runs of one build: it straddles. Its ABSOLUTE improved
         sharply (300.7 ms -> ~106 ms at n=8, from the deleted re-detection),
         which is exactly why it now sits ON the threshold instead of well
         above it.
         >> WIDENED AT P3.6 FROM ONE TEST TO THE CLASS, by measurement. The
         P3.6 gate audit replayed OFF and ON at all 27 code-touching branch
         commits and found 8 red -- of which SEVEN are this, and not one of
         them is `test_ungroup` alone: `test_bake_scales_subquadratically` was
         caught red at 8.05 against a threshold of 8, and every one of the
         seven shows the tell -- exactly "1 failed", ALTERNATING between the
         OFF and ON runs of the same commit. Code that is broken fails both
         gates; a ratio that straddles fails whichever run the machine was
         busier during. So the row is not one flaky test, it is the P0.3b
         TIMING-RATIO CLASS, flapping at roughly 7 of 27 replays (~26%), and
         whatever P3.8 decides -- a wider threshold, best-of-N, or moving them
         out of the suite entirely -- applies to the class and not to one
         member. Members seen flapping so far: `test_ungroup_scales_
         subquadratically`, `test_bake_scales_subquadratically`,
         `test_rebuild_scales_subquadratically`.
         >> SIGHTING, P3.7 (2026-07-30): `test_ungroup_scales_subquadratically`
         XPASSED once in 8 ON runs -- that is what the P3.7 (2) gate trailer's
         "5 xfailed, 1 xpassed" was. Named by re-running with `-ra` rather than
         inferred, because the trailer reports counts and not names.
         >> FOURTH MEMBER, AND IT CHANGES THE STAKES (2026-07-30):
         `test_select_interactive_scales_subquadratically` FAILED **1 of 8 and
         2 of 8** across two ON sweeps. The first three members are
         `xfail(strict=False)` -- they flap in a column nobody reads. THIS ONE
         IS A HARD PASS, so it turns the GATE RED on a busy machine.
         CONSEQUENCE, and it is why the P3.8 decision stops being housekeeping:
         **as of today a red gate has two indistinguishable causes -- a
         regression or machine load -- separable only by READING WHICH TEST
         FAILED, which is precisely the manual step the gate exists to
         replace.** The decision is therefore a PRECONDITION for trusting any
         future gate, and the merge does not happen before it is made and
         applied class-wide.
         EXONERATION OF P3.7's PAINT ADDITION, measured not assumed: the same
         failure reproduces on the PRE-P3.7 tree in a worktree at `2c5fd8d`
         (ratio **9.71** against the threshold of 8), while the three runs after
         the paint addition read **4.10 / 2.22 / 4.00**. The flap is the class,
         not the change.
         >> RESOLVED AT P3.8 (2): the ratios are RECORDED, never asserted;
         every timing assertion is an ABSOLUTE bound at n=8; and the lane is
         out of the gate in all three modes (`tools/gate.py --perf` runs it
         explicitly). The wider-threshold option is RULED OUT by measurement,
         not preference -- the ratio's noise band reaches ~27 while the whole
         diagnostic range it exists to read is 4 (linear) to 16 (quadratic).
         Full reasoning in the P3.8 (2) entry.
         CONSTRAINT ON THE P3.8 DECISION, ruled 2026-07-30 and NOT negotiable:
         **no wall-clock ratio may remain a gate-reddening hard pass on a shared
         machine.** Wider thresholds, best-of-N, or a non-gating
         recorded-benchmark lane with one very loose catastrophic guard -- P3.8
         chooses from its own fresh numbers, but it chooses for the CLASS (all
         four members), not for one test.
commits: ac9ad45 (0) . 600fdef (1) . 02eff1e (2) . 733d7d6 (3) . f07dbdb (4)
         Logged sub-commit by sub-commit per the handoff-spec rule, so a
         successor reads the state from here plus the four riders at lines
         416-424 rather than from a chat summary.
(0) done   commit ac9ad45 -- doc-only, committed BEFORE any code per rider 2.
         THE RETARGET WAS ITSELF A FINDING: both P3.2 guards' docstrings named
         P3.4 as the task that would close the coordinates-vs-identity gap.
         P3.4 replaced the coalesce/weld/fracture ops and never touched
         outlines, so both stayed green straight through it -- they were
         addressed to the wrong task. Retargeted in tests/test_outline.py
         (module + both docstrings + both failure messages) and rooms.py's
         OutlineEdge note, and the second guard's message now names BOTH ways
         it can fire so a red says which.
(1) done   commit 600fdef -- the flip.
ruff:    clean
pytest:  OFF  493 passed, 4 xfailed, 1 xpassed in 18.4s
         ON   493 passed, 4 xfailed, 1 xpassed in 20.3s
         DEEP 488 passed, 3 xfailed, 7 deselected in 18.5s
files:   rooms.py (OutlineEdge holds a Vertex, `p` read-through;
         share_outline_vertices; the bind_room_walls hook), walls.py
         (_CornerIndex.vertex_at), vertex.py (defect 21),
         tests/test_outline.py (the two guards replaced + rider 1's test),
         tests/test_wall_move.py (+1, the defect-21 case)
THE GUARDS FLIPPED, AND ONLY THE GUARDS -- both P3.2 tests went red at this
         change and the whole rest of the suite stayed green through it. That
         is exactly what rider 2's sequencing was for: the red is the flip,
         not a weld that wandered in. Their two causes turned out to BE one
         cause: the weld is the flip's first step, because an outline can only
         NAME a vertex once the corner IS one vertex.
DEFECT 21 -- FOUND BY RIDER 1's OWN TEST, and it is the best kind of find.
         `relocated_to` copied `self._uid`, and uids mint LAZILY on first
         read, so a corner nobody had named carried None across a move and got
         a FRESH identity the moment anything asked. Invisible while only the
         document walk read uids -- which is how it survived P3.1, P3.3 and
         P3.4 -- and a live bug at P4.5, which serializes groups by member id.
         THE NEAR-MISS IS THE LESSON: P3.3's
         test_relocation_carries_the_vertex_identity has pinned this exact
         rule since P3.3 and PASSES FOR A REASON IT DOES NOT STATE -- it reads
         `v.uid` before relocating, which forces the mint. A test that
         establishes the precondition it means to test cannot see the bug.
         Fixed, and pinned by a test that constructs the unnamed case.
PERF, checked not assumed (the P3.1 lesson): test_bake flagged 8.83 against a
         threshold of 8 on the first full run. Re-ran three times -- 6.31 /
         6.89 / 7.17, absolutes 307-310 ms against P3.3's recorded 297-332 --
         so variance, not the new property read. Same call as P3.3's 7.78.
(2) done   commit 02eff1e -- the region derives from the outline.
ruff:    clean
pytest:  OFF  495 passed, 4 xfailed, 1 xpassed / ON same / DEEP 490, 3 xfailed
files:   rooms.py (path + area_sqft become properties; _translate relocates),
         walls.py (_DragVertex carries outline edges), items.py + mainwindow.py
         (three rigid-move sites go through set_region),
         tests/test_outline.py (+2)
THE STEP P3.2 AND (1) DID NOT TAKE, and without it the deletion is impossible
         rather than merely risky. `corners` derived from the outline at P3.2
         and the corners became real vertex identities at (1) -- but `path` and
         `area_sqft` were still a stored QPainterPath and a stored float that
         ONLY `refresh_rooms` refreshed. So an outline that moved by
         construction still reported a stale area until a detection pass caught
         up, and deleting that pass would have frozen every number a user reads.
         Both derive now, memoized on the corner COORDINATES -- not identity,
         because `relocated_to` returns a NEW vertex for a moved corner and an
         id-keyed memo would be stale in exactly the case that matters.
NO EXISTING TEST CHANGED.

(3) done   commit 733d7d6 -- the deletion, and the lift.
ruff:    clean
pytest:  OFF  495 passed, 5 xfailed / ON 495/4/1xpassed / DEEP 490, 3 xfailed
DELETED, 418 lines across 11 top-level definitions, all callerless:
         `_RoomGrid` (90) + `_WallGraph` (131) -- the two engines, a raster
         flood-fill and a hand-rolled planar face walk; `_detect_room` (12),
         `detect_room_region` (6), `trace_room_perimeter` (6); the memo,
         `room_signature` (23) + `refresh_rooms` (53) + `_room_probe_points`
         (19); `reloop_open_room` (48); `synthesize_room_edge` (15) and
         `_wall_along_segment` (15). Plus `bind_room_walls` 70 -> 38.
         rooms.py 1425 -> 1162 lines.
`detect_room` SURVIVES AS A NAME, and this is the census's one real divergence
         on the rooms.py side. The task line lists it among the dead; it has
         ~40 call sites across the app, the tooling, the fixtures and eleven
         test modules, and this task's authorized rewrite zone is two test
         files. Deleting the NAME would have been a rewrite of the suite
         wearing a deletion's clothes. What the line MEANS is delivered in
         full: the editor no longer has its own answer to "what is a face". It
         asks the document's, through `bridge.face_at` -> `enclosing_face`.
THE LIFT, and why it is allowed where P3.4 point 1 forbade it. That ruling
         rejected lift-to-Design for EDIT ops, on measurement: an edit runs per
         mouse event and a full-plan rebuild destroys item identity. "Detect
         room here" is a ONE-SHOT gesture -- the six call sites (csvio, macro,
         mainwindow x2, planio, view) each fire once per user action -- so the
         walk costs no more than the `_RoomGrid` + `_WallGraph` pair it
         replaces, both of which were also rebuilt per call and one of which
         was O(walls^2). Single-sourced instead of duplicated.
THREE THINGS CAME FREE, and they are why the swap is worth making rather than
         merely equivalent:
         * DEFECT 16 closes STRUCTURALLY. The grid was sized by `canvas_rect()`
           and any flood reaching its edge counted as unenclosed, so a plan
           larger than the canvas silently lost its edge rooms. A graph walk has
           no canvas in it. Closed by deletion, which is the only kind of fix
           that cannot regress. Pinned.
         * every returned edge NAMES the wall covering it, so `bind_room_walls`
           stopped SEARCHING for a room's own walls and now only attaches them.
           A room binds its outline as a fact the detection reports.
         * a wall split at a T yields one edge per SEGMENT -- invariant I5
           ("every outline edge maps to exactly one wall") holding by
           construction, where the old tracer dropped pass-through corners and
           could leave an edge no single wall covered.
DEFECT 13 -- REPRODUCED BEFORE THE SUBSTRATE WENT, which rider 3 asked for and
         which is the reason the verdict is worth anything. At zooms 0.25x-4x
         on the `detach_wall_from_room` path, measured on the code as it stood:
         * DETECTION was already IDENTICAL at every zoom -- same area, same
           corners, 5/5. It never read the view.
         * THE DRAG was not. The same scene-space gesture gave 0 open sides at
           0.25x and 1 at 0.5x-4x, leaving the wall's far end at y=120 vs y=60.
         So the defect is real and its mechanism is the drag's zoom terms
         (`20.0 / _view_scale()` catch radius, `16.0 / view_scale` stick),
         exactly as rider 3 predicted. Detection half CLOSED and now structural;
         drag half RETARGETED and left UNASSIGNED, the same disposition the P2.3
         row got, with P4.2 as the nearest task that touches the drag. NOT
         "repro substrate removed" -- the substrate was still there and the
         measurement was taken.
TWO CORRECTIONS THE LIFT NEEDED, both found by a failing test rather than by
         reasoning, and both are findings about `trace_faces` as much as about
         this task:
         * SPUR PRUNING. A dangling wall stub is IN the wall graph, so the face
           walk enters it and comes straight back out. Free for a FACE (the
           excursion encloses no area) and wrong for an OUTLINE: the room grows
           a corner at the stub's free end, and every consumer that asks "is
           this room inside the rubber band" answers from it. Caught by
           test_selection, which is not in the authorized zone and was right not
           to be changed. `bridge._prune_spurs`.
         * CANONICAL WINDING. `_inner_faces` picks the inner sign by MAJORITY,
           decisive from two rooms on but a TIE at exactly one -- a lone wall
           loop traces two faces of equal area and opposite winding. So a
           one-room plan came back wound whichever way the rest of the plan
           happened to vote, and the outline ORDER is serialized. Caught by
           test_room_walls' idempotent round-trip. Fixed at the one-shot entry
           to the sign the document already uses (positive shoelace, verified
           against every face of symmetricP1).
THE APPLY PATH NOW CARRIES THE DOCUMENT'S VERTEX IDENTITY, one live `Vertex`
         per document vertex, shared by every wall end and outline edge naming
         it. The first attempt reconstructed it by WELDING
         (`share_outline_vertices`) and `test_malformed_v5_is_reported_not_
         rewelded` caught it within the minute: apply must not repair, and a
         corner that has drifted 0.3" is a malformed file to be REPORTED, not
         quietly closed up. The document already knows the identities; reading
         them is exact where welding is a guess.

(4) done   commit f07dbdb -- defect 8, the predicates, the privatize ruling.
ruff:    clean
pytest:  OFF  497 passed, 5 xfailed / ON 497/5 / DEEP 492, 3 xfailed
DEFECT 8, and it was TWO faults with ONE cause -- `room_boolean` worked from a
         re-traced boundary rather than from what the rooms said they were made
         of. (a) It DELETED WALLS THAT WERE NOT ITS OWN: inputs came from
         `bounding_walls()`, a proximity query with no floor filter, and the op
         removes everything handed to it -- so a combine took the wall a third
         room shared with an input, breaking that room open, and any wall of any
         other FLOOR whose body touched the band. (b) It FORCED every result
         wall to "interior", downgrading 6" exterior walls to 4 1/2" ones.
         Both fixed at the source: inputs come from the room's OUTLINE
         (`room_walls`), a wall still bordering a non-input room is kept, and
         each result edge inherits type and floor from whichever input wall runs
         along it. TWO REGRESSION TESTS, both CONFIRMED FAILING against the old
         code before being kept -- and the first fixture was rebuilt on the
         shared-wall model, because two `make_room` calls leave a coincident
         PAIR at the boundary and a duplicate wall is a different problem.
THE TWO PREDICATES, rewritten and not deleted, exactly as rider 4 tabled.
         `room_owns_walls` and `walls_cover_room` keep their criteria and read
         the outline through a new `room_walls(room)` -- one answer to "which
         walls are this room's?" -- instead of the parallel bound-wall list the
         deleted binder maintained.
`_privatize_shared_walls` ASSESSED IN-TASK: KEEP. Its reason is untouched -- a
         party wall is one wall, so a room moving off it must stop owning it.
         It needed one repair to stay honest: it swapped the room's BOUND wall
         for a private copy and left the OUTLINE naming the shared one, and the
         outline is now the authority, so `room_walls` went on handing bake and
         room_boolean a wall the room had just given up.
         AND IT WORKS FOR A REASON WORTH WRITING DOWN: `_translate` RELOCATES
         corners, and a relocation mints a new `Vertex` that only the ends
         REBOUND to it follow -- so a wall the room no longer owns simply stays
         on the old corner, with nothing holding it back. P4.2's real `extract`
         still replaces the shape of it; `_perimeter_span` still falls with
         `fracture_delete_wall` at P4.1.
         [ANNOTATED at the P4.1 read-back, 2026-07-31 -- the last clause failed
         checking, the third task-line census figure to do so. `_perimeter_span`
         does NOT fall at P4.1: `_copy_spec` (rooms.py:335, unowned by any
         phase) and `_privatize_shared_walls` (rooms.py:785, P4.2's) both call
         it and both outlive `fracture_delete_wall`. Earliest death is P4.2,
         contingent on `_copy_spec` being reshaped there; the authoritative
         statement is the register's carried census note. The line above stands
         as written -- this corrects it in place without rewriting history.]

EXIT 1 -- MEASURED DELETION vs THE CENSUS. Rider 4 tabled ~470 from rooms.py
         + 34 from walls.py. MEASURED: 418 in whole definitions plus 32 from
         `bind_room_walls`' shrink = 450 of the ~470, and 0 from walls.py.
         Two divergences, both reported rather than forced:
         * `_wall_along_segment` (15) is REPLACED, not deleted, by `_edge_wall`
           (48) -- LARGER, because it absorbed the job the deleted three-priority
           search was doing: find the wall behind an outline edge that came from
           a FILE and names none. It also had to accept PARTIAL cover, or a v4
           reload stops agreeing with the live scene about a side whose corner
           was dragged away, and the round-trip stops being idempotent.
         * `_WallBBoxIndex` (34) CANNOT DIE, and P3.4 (iv) is why. That
           sub-commit reported it as P3.5's on the grounds that `refresh_rooms`
           was its last caller -- but the SAME sub-commit refused the adjacency
           swap in `_compute_wall_junctions` and said so at length: an unwelded
           crossing shares no corner, so bbox search is the only thing that can
           answer there. `_compute_wall_junctions` stays, so its index stays. A
           line dies when its LAST caller dies, and P3.4 (iv)'s own ruling
           created the caller that outlives this task.
EXIT 2 -- RIDER 1'S HEADLINE CHECK, PASSING, AND THE ASSERTIONS DID NOT MOVE.
         `test_a_dragged_wall_resizes_the_rooms_it_borders` -- the editor half
         of the Lounge / Front Porch demo -- still asserts equal and opposite
         resizing with the total unchanged, now with `refresh_rooms` DELETED.
         Written at P3.3 the numbers came from detection; they now arrive
         because the rooms' outlines hold the very vertices the divider holds.
         A `not hasattr(fp, "refresh_rooms")` guard makes the claim explicit
         rather than implied, so the test cannot quietly stop proving it.
EXIT 3 -- PERF, MEASURED NOT ASSUMED: the same harness on the same machine at
         c133205 (pre-P3.5) vs HEAD. P0.3 warned that `rebuild` at 2.7 was
         ALREADY sub-linear and that a regression there would be a real
         finding. It improved.
                        before (n=4 -> n=8)      after
           rebuild      1.2 -> 3.7   r 3.05     1.0 -> 2.4    r 2.31
           bake        44.8 -> 299.1 r 6.68     6.9 -> 28.0   r 4.03  <- 10.7x
           ungroup     45.9 -> 300.7 r 6.55    13.5 -> 106.1  r 7.85  <- 2.8x
           undo        21.3 -> 157.7 r 7.40    20.9 -> 123.5  r 5.92
           group       27.7 -> 360.1 r 12.99   33.3 -> 370.1  r 11.10 (P3.8's)
         `bake` is the headline and the mechanism is exactly the deletion: a
         group move ended in `rebuild_all_walls` -> `refresh_rooms`, which
         re-detected every room the move touched. Nothing re-detects now. The
         ungroup RATIO worsened while its absolute fell 2.8x -- it is
         xfail(strict=False) -> P3.8 either way, and P3.8 owns the reading.
EXIT 4 -- TOOLING. `python docs/make_gallery.py` and
         `python examples/make_examples.py` both run; images regenerated.
         `08-open-walls.png` legitimately changed and README's open-wall
         paragraph was corrected to match -- see the new Known-regressions row.

CHANGED-TEST LEDGER, one line each, since this is the second-biggest such risk
         in the plan after P3.4:
         * test_rooms.py [AUTHORIZED]: test_region_follows_wall_move rewritten
           -- coordinate assignment -> corner relocation, because a bare
           `w.p1 = ...` is SPLIT-ON-WRITE by P3.1's ruling, so the old test
           replaced wall ends and asked detection to notice. Three
           room_signature / refresh-memo tests DELETED with the memo they
           measured. +4: defect 13 (view-independence), defect 16 (no canvas
           clip), and the two defect-8 regressions.
         * test_room_walls.py [AUTHORIZED]: test_wall_stretch_keeps_binding
           rewritten, same one-line reason. +2 assertions in the privatize test.
         * test_open_walls.py [DIVERGENCE -- the whole file]: this is P3.7's
           rewrite arriving early, because P3.5 deletes the PRODUCER. An open
           side was an ITEM (a dashed `OpenWall`, regenerated by
           `reloop_open_room` + `bind_room_walls`); it is now a fact about the
           outline, reported by the new `RoomItem.open_edges()` -- which is
           where `bridge._rooms_of` has emitted it since P1.4. The scene was
           carrying a second, item-shaped representation of something the
           document already said. `test_open_wall_is_editable` DELETED: it
           asserted drag controls on a placeholder nothing constructs. The
           CLASS still dies at P3.7, as planned.
         * test_design_bridge.py + test_verify_design.py [OUTSIDE THE ZONE, and
           named as such]: planc1's I6 characterization 17 -> 13. planc1's four
           divider walls stop 1.5" short, so each is a dangling STUB; the old
           tracer carried those out-and-back excursions into the outline (which
           is how Hall and M Bath each held 21 corners, several at the free end
           of a wall nowhere near the room). Spur pruning drops them, so four
           walls only a spur ever touched stop being claimed. Same fault
           classes, same Hall/M Bath collapse, same areas -- all three verified.
         * test_wall_move.py: docstrings + the `refresh_rooms`-is-gone guard.
           The ASSERTIONS DID NOT MOVE; that is exit check 2.
         * test_outline.py: +3 (the region derives; the memo is keyed on
           coordinates; plus (1)'s pair).
PROCESS NOTE, since the working agreement is explicit about the mechanism: a
         `git checkout floorplanner/mainwindow.py`, used to undo a deliberate
         break-it-to-prove-the-test experiment, discarded that file's
         uncommitted work along with it. Reapplied and re-verified. The rule is
         written for handed-back DOC edits; it applies to uncommitted code just
         as literally, and the safe move is to make the experiment in a copy.
         RULED at the P3.5 close and now a working-agreement entry of its own
         ("Destructive experiments run in a worktree, or after a WIP commit"):
         the solution was already in use in this same task, since the perf
         comparison ran the old code in a `git worktree`. The followup below
         used exactly that to verify its new tests against pre-fix code.

DEFECT 28 -- RULINGS AT THE SESSION BOUNDARY (2026-07-29). Committed here
         before stopping, per the handoff-spec rule: a fresh session reads the
         state from this block and needs nothing from chat.

  1. TWO DEFECTS, NOT ONE. The leak has a test half and an app half and they
     are fixed separately.
       * THE FIXTURE LEAK -- `tests/conftest.py`'s `win` fixture ends with
         `w.close()`, which hides a window and neither destroys it nor stops
         its 180 ms dirty timer. Registered under DEFECT 28.
       * DEFECT 29 -- the APP half: `MainWindow.close()` leaves a timer running
         that walks the whole document. A user closing one plan window while
         another is open pays that cost invisibly, so this is a real behaviour
         defect and NOT to be slipped in under a test-isolation fix.

  2. LEAK GUARD AS ACCEPTANCE, WITH A FAIL-FIRST RECEIPT. The fix is accepted
     by a guard that asserts no stale `MainWindow` keeps an active dirty timer
     (equivalently: `live_mainwindows` stays bounded across the suite). The
     guard MUST be shown FAILING against the current tree before the fix
     lands -- the receipt standard, unchanged.

  3. THE CORPSE-TABLE STANDARD: NO BLANK ROWS. Every corpse is attributed to
     the test whose scene it actually holds, not the test that was running.
     A corpse with no owner is listed AS unowned rather than dropped.
     Currently unowned: **'Kitchen' / 'Pan' on symmetricP1** -- no test has yet
     been shown to leave that overlap, and until one is, defect 28 is NOT
     dissolved into "leaked windows misreport". `'A'`/`'B'` IS owned:
     `test_save_verifies_deep`'s own deliberate fixture, working as designed.

  4. RE-CERTIFICATION: DEEP GREEN 10/10 under the machine-written trailer
     (`tools/gate.py`). Not 1 clean run, not "it looks fixed" -- ten.

  5. THE HISTORICAL CLAIM IS BOUNDED. What is established: a leaked window CAN
     misreport an earlier test's state, and did, five times on two harvests.
     What is NOT established, and must not be asserted: that DEEP's green/red
     has been meaningless for its whole existence. The mechanism has existed as
     long as the timer has; the OBSERVED instances are all from P3.6, when the
     first tests loading a twenty-room plan into `win` arrived. Anything wider
     needs its own measurement.

  6. DEFECT 26's `E` SIGHTINGS, one line: they are the same mechanism -- a
     stale window's timer firing inside a later test -- so the four sightings
     and the "suppressing" interventions are all explained by it, and no
     separate cause is outstanding.

P3.8  done -- PERF VERIFICATION AND THE EXIT SURVEY. The last task of Phase 3.
ruff:    clean
pytest:  Gate-Census: collected=523 ruff=clean
         Gate-OFF: 510 passed, 7 deselected, 6 xfailed in 12.89s  -> sum 523  OK
         Gate-ON: 510 passed, 7 deselected, 6 xfailed in 15.55s   -> sum 523  OK
         Gate-DEEP: 510 passed, 7 deselected, 6 xfailed in 16.35s -> sum 523  OK
         Gate-Verdict: GREEN (every sum reconciles against --collect-only)
commits: 4997da2 (1 the numbers) . 7b6c342 (2 the flap decision) . 65c4c02 +
         90bad2d (defect 27's DEEP half) . 28e6a59 (3 the stranding row) .
         9bd52c3 (4-5 the survey completed) . plus this entry.

=== 1. THE NUMBERS, against BOTH baselines, same machine, medians of seven ===

                    PRE-PHASE-3 (b82256c)      HEAD              what it says
                    n=4 -> n=8    ratio        n=4 -> n=8  ratio
  rebuild           1.2 ->   3.3   2.82        1.0 ->  2.6  2.61   improved
  snapshot          2.1 ->  10.8   5.06        2.2 -> 10.8  4.80   flat
  undo             22.0 -> 154.0   6.99       19.1 ->126.2  6.64   -18%
  select_burst      0.2 ->   1.0   5.26        0.2 ->  1.0  5.48   flat
  select_interact   2.5 ->   7.6   3.19        2.4 ->  9.5  4.13   +25%, unattributed
  group            27.8 -> 349.7  12.77       29.3 ->356.4 12.43   untouched
  bake             41.0 -> 279.0   6.81        6.4 -> 26.4  4.09   **10.6x**
  ungroup          41.5 -> 292.5   6.89       11.5 -> 99.8  8.64   2.9x abs, ratio worse

  P0.3's reading rule: 4 is linear in rooms, 16 quadratic, 8 = rooms^1.5.
  `bake` is the headline and the mechanism is exactly P3.5's deletion: a group
  move used to end in `refresh_rooms` re-detecting every room it touched.
  `ungroup` is the honest half -- 2.9x faster absolutely while its ratio crosses
  the threshold; both true, and the row says both. `rebuild` answers P0.3's
  standing warning that a regression there would be a real finding: it improved.
  `group` is the one op Phase 3 never touched.

  0 NEW WALLS, ASSERTED (not observed): grouping the 20 rooms of symmetricP1
  together with their walls -- what Ctrl+A or a band actually selects -- leaves
  80 walls at 80 across group and bake. The rooms-ALONE reading of the same
  sentence is +868 walls and is P4.5's; it is pinned xfail, not reworded.

=== 2. THE FOUR SURVEY ROWS, and the theme they share ===

  * SPLIT-ON-WRITE: 9 -> 11 sites, because the P3.6 census grepped a shape that
    cannot see `setattr(wall, attr, ...)`. Five are correct as they are, two are
    lower-stakes identity churn (P4.5), FOUR are one defect with four faces.
  * STRANDING: ANSWERED BY A REAL DRAG -- it strands. Defect 30, filed not
    fixed. The endpoint drag is a separate and correct answer.
  * THE P2.3 COLLINEAR ROW: re-checked by hand, does not close, cause intact,
    unassigned -> P4.2.
  * DEFECT 13's DRAG HALF: dispositioned, not re-measured; it needs a ruling,
    not another number. Register row 13 stays authoritative.

  **THE THESIS P4.2 INHERITS, and it is one thesis rather than four errands:
  every one of these is an operation that knows about ROOMS where it should
  know about CORNERS.** Defect 30's gather, the four coordinate-assignment
  faces, and `_collinear_run()`'s short-circuit are the same mistake wearing
  four hats -- Phase 3 moved the geometry onto vertices, and these are the call
  sites that still ask a room what they should be asking a corner.

=== 3. THE FLAP DECISION, applied class-wide ===

  Ratios are RECORDED, never asserted; every timing assertion is an ABSOLUTE
  bound at n=8; the lane is out of the gate in all three modes and runs under
  `tools/gate.py --perf`. The wider-threshold option is ruled out BY
  MEASUREMENT: the ratio's noise band reaches ~27 while the whole diagnostic
  range it exists to read is 4 to 16. Receipt: 8 consecutive full-mode gate
  runs, 24 mode-runs, every one byte-identical, zero xpassed and zero failed --
  against 1-in-8 and 2-in-8 red before. It is this file's own precedent
  (`select_burst` P0.6, `undo` P2.3) finished rather than a new mechanism.

=== 4. CI NOW RUNS THE DEEP INVARIANTS ===

  https://github.com/pjm4github/FloorPlanner/actions/runs/30592873265
  Gate-DEEP: 510 passed, 7 deselected, 5 xfailed in 21.26s -> sum 522 OK
  The job calls `tools/gate.py --deep`, so CI and the local gate are ONE
  instrument. Its census was byte-identical to the local Windows run -- the
  branch's first cross-platform confirmation, and it landed on the two things
  most likely to differ: the deep invariant walk and the pixel assertions.

=== 5. THE MERGE CHECKLIST, hashes verified on disk ===

  | # | condition | state |
  |---|---|---|
  | 1 | P3.8's numbers recorded; 0 new walls asserted | DONE `4997da2` |
  | 2 | four survey rows answered or dispositioned | DONE `28e6a59`, `9bd52c3` |
  | 3 | flap decision made and applied class-wide | DONE `7b6c342` |
  | 4 | defect 27 DEEP CI job added and green | DONE `65c4c02`, `90bad2d` |
  | 5 | Gate 3 passed by Patrick, findings dispositioned | PENDING -- his |
  | 6 | CI green on branch head; MERGE COMMIT, not squash | CI green; merge waits on 5 |

P3.8 (5)  THE REMAINING TWO SURVEY ROWS, and the survey is complete.

THE P2.3 COLLINEAR-RUN ROW: RE-CHECKED BY HAND, DOES NOT CLOSE, cause intact.
         Built the row's own scenario -- a 480" wall with a mid-span T,
         bordering NO room -- and ran it:
           before undo   2 walls, spans [120, 480]
           after undo    3 walls, spans [120, 240, 240]
           the grabbed segment borders 0 rooms
           `_collinear_run()` gathers 1 of 2 collinear segments -- SHORT-CIRCUITED
           a 12" body drag moves 1 of 2 segments
         Every clause of the row is still literally true, and the fix it names
         still fits: gather the run over VERTEX ADJACENCY rather than
         short-circuiting to `[self]` when `self.rooms` is empty. Left
         UNASSIGNED with P4.2 as the nearest task that touches the drag --
         unchanged from P3.4 (iv), and now re-verified rather than assumed at
         the phase exit.
         NOTE THE COMPANY IT KEEPS: this is the same family as defect 30 and
         the four coordinate-assignment faces above -- an operation that knows
         about ROOMS where it should know about CORNERS. P4.2 inherits one
         theme, not four errands.

DEFECT 13's DRAG HALF: DISPOSITIONED, NOT RE-MEASURED, and that is deliberate.
         The merge condition is "answered by measurement OR explicitly
         dispositioned to a named task". This row was measured at P3.5 (0 open
         sides at 0.25x, 1 at 0.5x-4x; the wall's far end at y=120 vs y=60) and
         its cause named (the drag's `20.0 / _view_scale()` catch radius and
         `16.0 / view_scale` stick). Nothing since has touched those terms.
         Re-running it would re-derive a number the register already holds;
         what it needs is a RULING on whether a gesture tolerance may set a
         geometric RESULT, and that is P4.2's to make. Status stays
         authoritative in register row 13, per the pointer filed at P3.7.

P3.8 (4)  THE SPLIT-ON-WRITE EXIT SURVEY -- re-grepped, and the count went UP
         because the census method was wrong, not because the code got worse.

P3.6 RECORDED 9 SITES. THE TRUE FIGURE IS 11, and the two extra were never
         missing from the code -- they were invisible to the GREP. The census
         searched for `.p1 = ` / `.p2 = `, which cannot see an assignment made
         through `setattr(wall, attr, ...)`. P3.6's list did contain two setattr
         sites (the `rigid` and `tee` branches, found by reading rather than by
         the pattern), so the pattern had already failed once without being
         corrected. The survey now greps BOTH FORMS, and that is the finding to
         carry: a census is only as good as the shape it looks for.

THE ELEVEN, EACH WITH WHAT CARRIES THE THINGS ATTACHED TO THAT END:

  1-2  `mainwindow.py:571,572`  align-to-grid (`w.p1/p2 = grid_snap(...)`).
       CARRIES NOTHING -- it snaps each end independently, so a shared corner
       comes apart and any room outline on it is left behind. It is a
       user-invoked plan-wide normalisation, and the honest fix is the same one
       defect 30 names: move CORNERS, not coordinates. UNASSIGNED, argue P4.2.
  3-4  `mainwindow.py:581,582`  `_translate_shape`. Same shape, same answer,
       but lower stakes: it translates a whole selection by the same delta, so
       the geometry stays self-consistent even though identity is minted fresh.
       UNASSIGNED, argue P4.5 (it is the group/selection family).
  5    `view.py:402`  the rubber-band wall being DRAWN. Nothing is attached to
       an end that does not exist yet -- this is the one site where
       split-on-write is not merely safe but correct. KEEP, permanently.
  6-7  `walls.py:1563,1565`  the ENDPOINT drag. Split-on-write is the DESIGNED
       behaviour here (P3.1's ruling), and P3.7 made it visible: pulling a
       corner away opens that side and the room keeps its shape. KEEP.
  8    `walls.py:290`  `_adopt_end`, the merge applier's fallback. NEW TO THE
       CENSUS. Documented at P3.4 (i) and correct: it splits only when the plan
       named no corner, i.e. the end is landing where no corner was. KEEP.
  9    `walls.py:455`  `weld_scene`'s geometric snap. NEW TO THE CENSUS, and
       the interesting one: it closes a gap by MOVING a coordinate, then the
       topology half shares the ends. Assigning here is what the weld is for --
       but it means a room outline holding the old position is not carried.
       Not observed to bite (load does not weld, and the explicit command
       re-shares afterwards); RECORDED, argue P4.2 with defect 30, since it is
       the same "coordinate moved, holders not told" shape.
  10-11 `walls.py:1601,1603`  the `rigid` and `tee` branches of the body drag.
       Unchanged disposition: `rigid` is a grouped wall held back by the group
       guard -> P4.5; `tee` is a body-landing, which P3.4 (ii) gave a real
       vertex, so this branch is now reached only for landings the split
       declined (a straddling opening) -> P3.6's report path covers it.

SO THE SURVEY'S OWN QUESTION -- "what carries the things attached to that end"
         -- has three answers: FIVE sites are correct as they are (5, 6, 7, 8,
         and the tee half of 11), TWO are lower-stakes identity churn (3, 4),
         and FOUR are the same defect-30 shape at different call sites (1, 2, 9,
         and the rigid half of 11). That is the number worth carrying forward:
         **the coordinate-assignment family is no longer a list of survivors to
         chase, it is ONE defect with four faces.**

P3.8 (2)  THE FLAP-CLASS DECISION, made from the numbers and applied to the
         class. It is the merge checklist's item 3 and the precondition for
         trusting any later gate run.

THE DECISION IN ONE LINE: **the ratios are RECORDED, never asserted; every
         timing assertion is an ABSOLUTE bound at the large grid; and the
         timing lane is out of the gate in every mode.**

AND IT IS NOT A NEW MECHANISM -- IT IS THIS FILE'S OWN PRECEDENT, APPLIED TO
         THE CLASS. `tests/test_scaling.py` already converted two ops for
         exactly this reason and wrote the reason down at the time:
           * `select_burst`, P0.6 -- "the numbers here (0.2 ms -> 1.1 ms) sit
             at the perf_counter floor, so a ratio built on them is timer noise
             wearing a threshold's clothing. The absolute is the meaningful
             guard."
           * `undo`, P2.3 -- "An ABSOLUTE bound, not a ratio: a ratio assertion
             this close to the threshold would flap (the P0.6 precedent)."
         The flap class is precisely the ops that were never converted. So the
         ruling's "applied class-wide" is satisfied by finishing a job this file
         started twice and stopped halfway through.

WHY NOT A WIDER THRESHOLD -- the option the evidence RULES OUT rather than
         merely disfavours. Measured over 7 identical runs per tree:
           ratio spread, four big ops        1.06 .. 1.70x
           ratio spread, `select_interactive` at 2c5fd8d   **21.98x**
                                             (1.22 .. 26.82)
           ABSOLUTE spread at n=8, big ops   **1.03 .. 1.15x**
         The diagnosis: the n=4 leg is 0.2-4 ms, so a ratio divides one
         noise-dominated number by another and doubles its exposure. THE NOISE
         BAND (up to ~27) SWALLOWS THE ENTIRE DIAGNOSTIC RANGE THE RATIO EXISTS
         TO READ -- 4 is linear, 8 the threshold, 16 quadratic. A threshold
         cannot separate signal from noise when the noise is wider than the
         signal. Only a different measurement can, and the absolute is it.

WHY NOT BEST-OF-N: it would work -- a minimum is the right estimator when
         interference is one-sided -- but it costs N x the lane's runtime to
         buy back a number the absolute gives for free at 1.05x spread. It is
         recorded here as the option not taken, and it remains available if a
         later task needs the RATIO to be trustworthy rather than merely
         recorded.

WHAT CHANGED, five assertions and one tool:
         * `rebuild` / `select_interactive` / `group` / `bake` / `ungroup`:
           ratio assertion -> absolute bound at n=8, each with its measured
           median in the comment. `bake`'s bound (200 ms, median 26.4) is set
           so A RETURN TO THE PRE-PHASE-3 COST (279.0) TRIPS IT -- the one
           regression here that would matter most, and one the ratio would have
           called "still under 8".
         * THE TWO xfail MARKERS GO WITH THEM (`group`, `ungroup`). There is no
           ratio assertion left to expect-a-failure from, and a known-quadratic
           op's fact now lives in prose and the printed report instead of in a
           marker that flapped between xfail and xpass on machine load.
         * `tools/gate.py`: `-m "not perf"` in ALL THREE modes, not just DEEP.
           The lane could redden OFF and ON, and did. A side effect worth
           having: all three runs now reconcile against the SAME collected
           total, where DEEP alone used to report "7 deselected".
         * `tools/gate.py --perf` runs the lane explicitly and prints its
           numbers -- P0.3b's "invoked explicitly at the moments its numbers
           decide something", given a command instead of a memory.

WHAT THIS COSTS, said plainly: an absolute bound catches a BLOW-UP, not a
         DRIFT. A 20% regression will pass every bound here. That is the trade
         the evidence forces -- a ratio that cannot tell 4 from 27 was not
         catching drift either, it was reporting the machine's mood -- and
         drift is now caught where P0.3b always said it would be: by the
         numbers being read at the tasks whose decisions depend on them.

RECEIPT: 8 consecutive full-mode gate runs, all three modes each, after the
         change. See the sub-commit's trailer and the tally below.

P3.8 (1)  the numbers, measured SAME-MACHINE and as MEDIANS OF SEVEN.
ruff:    clean
pytest:  (trailer with the sub-commit)
THE METHOD IS THE FIRST FINDING. Every previous perf entry in this log is a
         SINGLE RUN, and the flap class says a single run of a ratio is not a
         measurement. So: 7 runs per tree, medians reported, spread reported
         beside them -- and the comparison tree is re-measured TODAY in a
         worktree rather than quoted from a table recorded weeks ago, because
         comparing today's HEAD against an old table conflates the code change
         with the machine.
         Anchor: `1a4d125^` = `b82256c`, the commit immediately before Phase 3
         opened.

                    PRE-PHASE-3 (b82256c)        HEAD (dedfc57)
                    n=4  -> n=8    ratio         n=4  -> n=8    ratio
  rebuild           1.2  ->   3.3   2.82         1.0  ->   2.6   2.61
  snapshot          2.1  ->  10.8   5.06         2.2  ->  10.8   4.80
  undo             22.0  -> 154.0   6.99        19.1  -> 126.2   6.64
  select_burst      0.2  ->   1.0   5.26         0.2  ->   1.0   5.48
  select_interact   2.5  ->   7.6   3.19         2.4  ->   9.5   4.13
  group            27.8  -> 349.7  12.77        29.3  -> 356.4  12.43
  bake             41.0  -> 279.0   6.81         6.4  ->  26.4   4.09
  ungroup          41.5  -> 292.5   6.89        11.5  ->  99.8   8.64

THE HEADLINE IS `bake`: 279.0 -> 26.4 ms at 64 rooms, **10.6x faster**, ratio
         6.81 -> 4.09. That is P3.5's deletion of the detection engine, paid
         out: a group move used to end in `refresh_rooms` re-detecting every
         room it touched, and nothing re-detects now.
`ungroup` IS THE HONEST HALF: 292.5 -> 99.8 ms, **2.9x faster absolutely**,
         while its RATIO WORSENS 6.89 -> 8.64 and crosses the threshold of 8.
         Both are true and the row must say both. It is `xfail(strict=False)`,
         so it xfails today where it used to pass -- exactly the reading P3.5
         predicted and left for this task.
`rebuild` ANSWERS P0.3's WARNING. P0.3 recorded 2.7 and warned that the
         memoized machinery was already sub-linear, so a regression here would
         be a real finding rather than noise. It improved: 2.82 -> 2.61, and
         3.3 -> 2.6 ms absolute.
`group` IS UNCHANGED (12.77 -> 12.43) and remains the one op Phase 3 did not
         touch. It is not wall duplication -- the harness groups walls AND
         rooms, which copies nothing (measured below).
`select_interactive` READS 25% SLOWER THAN PRE-PHASE-3 (7.6 -> 9.5 ms), AND
         THAT IS NOT P3.7's PAINT ADDITION -- measured against `2c5fd8d`, the
         commit immediately before it, with the same 7-run method: pre-paint
         10.3 ms / spread 21.98x, HEAD 9.5 ms / spread 1.49x. HEAD is faster
         and far steadier. The Phase-3-wide difference is real and unattributed;
         it is small, and the op is one of the flap class's four members.

AND THE SPREAD COLUMN IS THE FLAP CLASS'S EVIDENCE, gathered here because this
         is the task that has to decide about it. Same code, same machine,
         seven runs:
           rebuild            ratio spread 2.12x  (2.32 .. 4.91)
           select_interactive ratio spread 1.49x on HEAD -- but **21.98x** at
                              2c5fd8d (1.22 .. 26.82), where a `< 8` assertion
                              passes six times and fails once
           ungroup            1.12x on HEAD, 1.70x pre-paint
         THE DIAGNOSIS, and it points at the fix: the n=4 leg is 0.2-4 ms, so
         the RATIO is a quotient of two noise-dominated numbers. It is not that
         the code is unstable; it is that the instrument divides by a
         millisecond. Any decision that keeps ratio-of-small-durations as a
         gating assertion will keep flapping whatever threshold it picks.

THE 0-NEW-WALLS ACCEPTANCE IS AMBIGUOUS, AND MEASUREMENT SPLIT IT IN TWO --
         the P0.4 test-2 precedent, applied without being asked:
           * rooms AND their walls (Ctrl+A, or a band -- what a user's
             selection actually contains): 80 walls -> 80 after group -> 80
             after bake. **0 new walls, asserted** in
             `test_grouping_twenty_rooms_with_their_walls_creates_no_walls`.
           * the 20 ROOM items alone, which is what the sentence literally
             says: **+868 walls**. `duplicate_wall` copies a room's walls when
             the room is grouped without them, and P3.5's census assigned that
             to **P4.5**. Pinned as `xfail(strict=False)` naming P4.5 rather
             than asserted-and-failed or quietly reworded.
         AND THE DUPLICATION COMPOUNDS, which is new: grouping the 20 rooms one
         at a time sums to **258** new walls, all together **868** -- 3.4x more,
         because each room's copy sees the copies the earlier rooms just made.
         Per room it is roughly 2x that room's own wall count (Foyer: 4 own ->
         10 new). Recorded for P4.5, whose deliverable this is.
         COST, DECLARED: these two tests TRIPLED the suite -- 16s -> 46s --
         because one loads a 20-room plan and the other builds 868 walls.
         Both are marked `slow` (not `perf`: they are deterministic and
         belong in CI), so `--quick` is 13s again while the full gate pays
         ~50s. A 10-run re-certification now costs ~10 minutes, which is a
         real change to the gate's ergonomics and is said out loud rather
         than discovered by whoever runs it next.

```
