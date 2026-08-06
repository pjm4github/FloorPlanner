# Progress log - Phase 4 - rooms as durable movable units (part 2)

> **Moved verbatim** from `V5_MIGRATION_PLAN.md` (its lines 4361-4935 as of
> commit 2f232bd) on 2026-08-06. Nothing was reworded, reordered, tidied or
> reformatted; the entries appear in the order they were appended. The code
> fence below is the one the log has always been written inside - it is
> reopened here and closed at the end, because a fence cannot be split.
>
> Index: [`README.md`](README.md) - Plan: [`../V5_MIGRATION_PLAN.md`](../V5_MIGRATION_PLAN.md)

```
P4.5(0) THE RULINGS, recorded BEFORE any code (branch p4.5-groups-zorder
         from main@adaa519). Patrick ruled all of sections 2-4 of the
         read-back plus three amendments; the census that preceded them
         is in the read-back and its measured numbers are used below.

RULED (2a) DEFORM -- RATIFIED AS A CONSEQUENCE, NOT CHOSEN AS A POLICY.
         Under vertex identity a room holding a moved corner follows
         BECAUSE THE CORNER MOVED; stay-put is the option that would need
         machinery built to hold a room back from corners it holds. So:
         build no hold-back. And when test_a_clipped_band_leaves_every_
         room_coherent passes, the log says it passed AS A CONSEQUENCE OF
         THE MECHANISM rather than claiming a fix -- that distinction is
         the record's to keep, not the code's.
         ASKED WITH IT: which invariant catches a room whose OWN outline
         crosses itself after a large deforming move?
         ANSWERED, and it is NOT a gap: I5b -- "room-outline
         self-intersection", validate.py:155-168, O(edges^2) per room.
         It exists and it is exact.
         THE FINDING IS ITS REACH, not its absence, and it is sharper
         than "reports": I5b is one of the THREE DEEP-ONLY checks
         (validate.py:77), so shadow mode's always-on twelve never sees
         it while editing -- but save_path runs _verify_or_report("save",
         deep=True) and REFUSES TO WRITE when it fails. So a deform that
         self-intersects is SILENT AT THE GESTURE and then BLOCKS THE
         SAVE: the user learns at the moment they try to keep their work,
         which is the worst possible ordering. (The refusal itself is
         deliberate and correct -- P4.1's "do not write a corrupt plan"
         -- so the fix is NOT to relax it.)
         PROPOSED, for Patrick's ruling and NOT built here: run I5b
         SCOPED TO THE ROOMS A GROUP MOVE ACTUALLY CARRIED, at bake, and
         report through the status channel. Scoped, it is cheap (edges^2
         over a handful of rooms, not the plan), it fires at the gesture
         that caused it, and the deep sweep stays exactly where it is.
         The operation stays allowed either way -- this is about WHEN the
         document speaks, not whether the gesture is permitted.

         AMENDED 2026-08-05, AND THE AMENDMENT IS TO THIS RULING'S OWN
         PREMISE. The ordering stated above -- "SILENT AT THE GESTURE and
         then BLOCKS THE SAVE" -- is FALSE AS SHIPPED, and the error is in
         the second half. save_path does call _verify_or_report("save",
         deep=True), but verify() returns None immediately unless shadow
         mode is on (design/verify.py:210), and app.py:47 sets the env var
         ONLY for --verify-design. So the refusal is a diagnostic-mode
         behaviour, never the default launch.
         MEASURED on one corrupt scene, the fragment case, three ways:
           FP_VERIFY_DESIGN unset  -> the save WROTE the file, carrying
                                      I5b x1 and I11 x3
           FP_VERIFY_DESIGN=1      -> refused
           FP_VERIFY_DESIGN=deep   -> refused
         WHAT ACTUALLY SHIPS is therefore neither the ordering feared here
         nor the one proposed: report_self_intersections DOES fire by
         default (confirmed with the var unset), so the I5b half speaks at
         the gesture as ruled -- and the I11 half, room-vs-room overlap,
         speaks NOWHERE AT ALL. Not while editing (deep-only), not at the
         save (no refusal without the flag).
         The proposal above was therefore right for the wrong reason: it
         treated the save refusal as the backstop that made a gesture-time
         report merely better-timed. There is no backstop. Row 49 carries
         the repair; this ruling's own conclusion -- report at the gesture,
         do not block -- is UNCHANGED, and is now the only thing standing
         between the user and an unreported overlap.
         Evidence: docs/evidence/defect23-fragment.json, reproducible with
         docs/evidence/defect23_fragment_probe.py.

RULED (2b) DO NOT PROMOTE. The band takes exactly what it encloses.
         Option (c), a size threshold, is out for defect 13's reason: a
         tolerance may pick a TARGET, it may not set a semantic RESULT.
         THE DECIDING ARGUMENT IS PATRICK'S, recorded because the
         read-back did not make it: PROMOTION HAS NO NATURAL STOPPING
         POINT. If clipping a room's wall pulls in that whole room, does
         it also pull in the walls that room shares with rooms outside
         the band? And theirs? In a connected plan that cascades toward
         "select everything", and any rule that stops it is an arbitrary
         depth limit. Selection stays what it LOOKS like. Deformation is
         the honest, visible result, and extract is the tool for
         detaching a room first -- which is precisely why P4.2 built it.
         REQUIRED ALONGSIDE: the group action REPORTS WHAT IT DID at the
         moment it does it -- e.g. "Grouped 5 rooms; 3 partly enclosed --
         their shapes will follow." Not a warning, and not the edit-tear
         channel: the plain status line, said once, to the 06c2145
         wording standard (that commit fixed a message that read as
         nonsense at its boundary value -- "0 of them since the plan was
         opened" -- so the standard is: read the sentence the code will
         actually print, at its edge cases, before shipping it). The
         difference between a surprising result and an explained one is
         one sentence, and this is the gesture most likely to surprise.

RULED (3) RETIRE kind == "rigid", and record the expired justification
         VERBATIM beside its removal, so the record shows a carve-out
         that died when its stated reason expired rather than one that
         quietly vanished. The reason, from walls.py:1529-1537 as it
         stands today: "a GROUPED neighbour still follows, but on the
         old coordinate path -- grouping duplicates a room's walls onto
         the originals, so promoting one would wire a group member to an
         outside wall permanently, and what a group even IS
         topologically is P4.5's question. Same instinct as the
         `group() is None` gate that keeps grouped walls out of
         coalesce." BOTH clauses expire in this task.

AMENDED (3b) DO NOT RETIRE THE 12 group() is None GUARDS AS A CLASS.
         Patrick's split, and the census confirms it: they are not one
         guard. Enumerated, with what each protects and its disposition.
         KEEP -- 7, not one of them about duplication:
           1. extract.py:91 (capture_floating_furnishings) -- a GROUPED
              furnishing is not swept into a floating room's cargo.
              Ownership arbitration between a group and a float.
           2. items.py:94 (_handle_visible) -- the individual selection
              box/rotator hide inside a group; the group's outline
              governs. Pure presentation.
           3. macro.py:315 (^A select-all) -- top-level items only.
              Selecting a child AND its group double-moves it.
           4. mainwindow.py:728 (arrow nudge) -- the same double-move
              class: groups move as groups.
           5. walls.py:1448 (WallItem.mousePressEvent) -- a grouped
              wall's drag belongs to the GROUP, not to the wall.
              Interaction ownership.
           6. walls.py:2389 (OpeningItem.mousePressEvent) -- ditto.
           7. walls.py:2409 (OpeningItem.mouseMoveEvent) -- ditto.
         RETIRE -- 1:
           8. walls.py:1537 -- the rigid carve-out itself (ruling 3).
         CONSEQUENTIAL, RULING NEEDED BEFORE ANY IS TOUCHED -- 4. These
         are the "grouped walls are exempt from the topology passes"
         family, and letting grouped walls in is a far larger change
         than retiring a drag branch:
           9.  walls.py:544  (merge_wall) -- THE coalesce exemption
               Patrick named by hand.
           10. walls.py:503  (weld_scene) -- grouped ends never weld.
           11. walls.py:267  (graph_from_scene) -- grouped walls are
               invisible to the planner's graph view entirely, so
               merge / split / weld cannot see them at all.
           12. rooms.py:1030 -- a room outline edge will not bind to a
               grouped wall.
         WHY THESE CANNOT BE WAVED THROUGH: today they are load-bearing
         because a grouped wall is a COPY -- letting copies into the
         graph would double every edge. Under no-copy a grouped wall IS
         a plan wall, so the same guards become the opposite thing: a
         wall the planner is blind to. That is a change of KIND, not of
         degree. And 9-11 are exactly ROW 36's producer path (the
         release-merge rebind), so relaxing them is precisely what would
         trip the watch. Each returns to Patrick individually.

RULED (4) ASSENT to z = floor_term + stack_term + type_term, with both
         consequences accepted: the backdrop's -1e9 becomes a TYPE TERM
         rather than a magic number, and z ENTERS THE SNAPSHOT so "Bring
         to front" survives save/load and becomes undoable (F4's
         complaint closes). bring_to_front's full-scene max scan dies
         with it.
         ADDITION 1 -- STATE THE BAND ARITHMETIC AS CONSTANTS AND ASSERT
         IT. This is one scheme rather than three that happen not to
         collide only because max(type_term) < STACK_BAND and
         max(stack_term) < FLOOR_BAND. Those become NAMED CONSTANTS with
         the inequality written beside them, PINNED BY A TEST --
         otherwise it is three schemes again the first time someone
         raises a type constant.
         ADDITION 2 -- CHECK THE SCHEMA BEFORE ASSUMING. Done, and the
         answer SPLITS THIS TASK: design-schema.v5.json has NO field for
         a stacking index anywhere -- not on room, wall, furnishing or
         group -- and all four set additionalProperties: false, so there
         is nowhere to put one and no way to smuggle one in. The
         measured property lists are in the read-back.
         THEREFORE, and NOT folded in: the RUNTIME collapse (one scheme,
         one number, the constants and their test, the full-scene scan
         retired) proceeds in P4.5. The SERIALIZATION half is BLOCKED on
         a schema ruling with version implications, and returns to
         Patrick as its own decision. Until it is ruled, z stays OUT of
         the document and defect 11 closes only its runtime half --
         stated plainly rather than half-claimed.

RULED (5) Test dispositions agreed as read back, including the rewrite
         of test_grouping_rooms_without_their_walls_still_copies_them
         into its opposite, and the widening of the twenty-room test
         from "creates no walls" to "creates no objects at all".

RULED (6) ROW 36's WATCH IS A LIVE TRIPWIRE FOR THIS TASK. If
         test_the_merge_rebind_producer_is_watched goes red mid-task:
         STOP. The row is re-argued and Patrick rules BEFORE the test is
         touched. Confirmed green against the merged tree at adaa519.

RULED (7) MINI-GATE APPROVED, with a NEW ITEM 1 -- the headline number
         of the whole migration: group the WHOLE PLAN (20 rooms), move
         it, ungroup. Expect ZERO new objects. The original review
         measured >= 106 duplicate walls and >= 149 duplicate openings
         on exactly this gesture; closing that to zero is what Phases 3
         and 4 were for. Time it too -- it should feel instant. The
         eight items from the read-back follow as 2-9.
         CROSS-CUTTING, ADDED 2026-08-04 -- not a tenth item but a thing to
         watch at EVERY step: NO ROOM MAY SHOW A DASHED OPEN EDGE WHERE A
         WALL ACTUALLY EXISTS. That is the user-visible signature of the
         whole group-guard family (a room reading OPEN over a wall that is
         right there), it costs nothing extra to watch for while doing the
         nine items, and it catches the class ANYWHERE in the gate rather
         than only where we thought to look -- which is exactly how the
         P4.2 mini-gate's six findings were caught.
         DELIBERATELY STILL BROKEN -- DO NOT REPORT THESE (added 2026-08-05
         with the fragment ruling). A gate spends its credibility on the
         first known defect it is asked to rediscover, so what is knowingly
         unfixed is named up front:
           * ROOM BOOLEAN "FRAGMENT" (register row 47). Fragmenting two
             overlapping rooms and then dragging one piece clear leaves
             that piece's REGION behind and opens a dashed edge on each
             neighbour, over walls that are really there. Measured, filed,
             and argued as the FIRST task after P4.5 merges. The
             cross-cutting dashed-edge watch above therefore EXEMPTS the
             fragment gesture and nothing else.
           * The runtime z-order collapse (row 11's remaining half) is
             still open; it is not reachable from any gate item, but if
             the app hangs on a drag, that is it and not a new fault.

P4.5(1a) the three amendments to (1), before the mechanism work
ruff:    clean
pytest:  601 passed, 7 deselected, 4 xfailed (sum 612; trailer in the commit)
files:   docs/CODE_REVIEW_v2.md (rows 41 + 42 amended), this file.
notes:   ROW 41 NOW CARRIES MEASURED FIXTURES, verified here rather than
         inherited. A loop can be non-simple by TOUCHING as well as by
         crossing, and the shipped corpus has the touching kind:
           python -m floorplanner.viewer.fp3d examples/symmetricP1.json --dump
           python -m floorplanner.viewer.fp3d examples/planc1.v5.json --dump
         Measured: symmetricP1.json -- WIC, 1 zero-width spur;
         planc1.v5.json -- Hall 4, M Bath 6, WIC 1 (the last not named in
         the ruling, found by running it). Both files return ZERO I5b
         errors under check(deep=True) -- planc1.v5 reports 23 errors of
         other kinds, none of them I5b -- so they pass the invariant while
         being non-simple. Both halves of the claim verified before
         recording, per the standing rule.
         AND THE FIXTURES CARRY A CONSTRAINT WITH THEM: symmetricP1.json
         is the REFERENCE CLEAN FILE and is corpus-frozen, so "is a
         spurred loop an I5b violation?" cannot be answered without also
         deciding whether the frozen reference gets re-cut. That is a
         corpus decision as much as an invariant one, and it now has
         something concrete to be decided against.
         ROW 42 sharpened as ruled, plus the adjacent finding recorded and
         NOT acted on: the three structurally identical appliers
         (_DragVertex.apply, GroupItem._apply_corner_records,
         RoomItem._translate) are a consolidation candidate -- one concept,
         three implementations, F2's shape, and the reason row 42 exists
         at all is that there was no single seam to hang a check on.
         ARGUED PHASE 6, where the command layer's MoveVertices IS that
         seam. Not P4.5's.
         THE XFAIL IN test_self_intersection.py IS A MECHANISM RECEIPT,
         and is named as such here so a future reader does not tidy it
         away as a stale marker. It is a DISTINCT USE from the P0.4
         characterization xfails: those mark behaviour that is wrong today
         and will be fixed; this one marks a test that CANNOT pass under
         copy-based grouping for a structural reason (_corner_records
         deliberately splits any corner an outsider holds, so a clipped
         bake cannot deform a room and there is nothing to report). Its
         flip in the no-copy sub-commit is therefore not a bug fix but the
         PROOF THE MECHANISM ACTUALLY CHANGED -- if it still xfails after
         duplicate_wall dies, the death was cosmetic.

P4.5(2a) the ungroup-merge question, measured on the PRE-P4.5 tree, and a
         claim of my own withdrawn
ruff:    clean
pytest:  602 passed, 7 deselected, 3 xfailed (sum 612; trailer in the commit)
files:   mainwindow.py (the comment corrected), this file (the rule + this
         block).
notes:   THE QUESTION, asked before filing: was ungroup's plan-wide
         merge_all destroying geometry BEFORE P4.5, or only after the
         copies stopped hiding it? Two filings hung on it -- "a pass that
         was about to become harmful" (one line) versus "the shipped app
         has been silently deleting walls from real plans" (an F5-family
         defect, with a note that saved plans may have lost geometry).
         MEASURED in a worktree at main@adaa519. The isolation that makes
         it decisive: merge_all is PLAN-WIDE, so it does not care whether
         a wall was in the group -- running it alone on a freshly loaded
         file answers the question without any grouping at all.
           symmetricP1.json    scene walls 80 -> 78
           planc1TestV5.json   scene walls 82 -> 78
           planc1.v5.json      scene walls 83 -> 80
           fiveRoomTest.json   scene walls 16 -> 16
         End-to-end (group everything, bake a move, ungroup) gives the
         IDENTICAL numbers, confirming the loss came from the plan-wide
         pass and not from the group.
         AND THEN THE DECIDING MEASUREMENT, which is the one that changes
         the filing -- RE-TAKEN ON THE SAVED-FILE PRODUCER after the
         reviewer asked which instrument it used, because the claim is
         'nothing reached a saved plan differently' and snapshot() is
         NOT that producer (it is canonicalize(design_from_scene(...))
         minus provenance, unmodelled settings and active_floor):
           snapshot()          identical on all three
           design_document()   identical on all three  <- _write_plan's
           json.dump bytes     identical on all three  <- the user's file
         They agree because design_from_scene CANONICALISES internally
         (Design.from_dict(canonicalize(...))), so both producers rest
         on a canonical walk, and the three things design_document adds
         are window state merge_all cannot touch. Reasoning that out
         would have been enough to be right and not enough to be
         MEASURED, which is the difference the census doctrine exists
         for. The original wording said only win.snapshot() and is
         superseded by this. The absorbed walls are collinear same-type
         segments the walk planarises to the same document, and wall count
         is PRESENTATION state (P2.3's Known-regressions row says so in as
         many words). So NO GEOMETRY WAS EVER LOST, by ungroup or
         otherwise, and this files as (1): a pass removed before it became
         harmful. One line, no defect number, nothing for SANITY_CHECK.md.
         A CLAIM OF MINE IS WITHDRAWN. P4.5(2)'s message said the ungroup
         "absorbed 2 REAL walls that no gesture asked it to touch" and
         called it "purely destructive". The first half is true of wall
         ITEMS and the second half is false: nothing was destroyed. The
         code comment is corrected to the measured truth, and the
         correction is recorded here rather than amended away -- the same
         discipline as defect 32's withdrawal and defect 23's.
         WHAT WAS ACTUALLY WRONG, stated accurately: a LOCAL gesture
         silently reshaped the WHOLE plan's item structure, which breaks
         "the group moves and nothing else changes" and makes an undo step
         look bigger than the edit that caused it. That is reason enough
         to remove it, and it is the reason the task line already gave.
         THE RULE IS RECORDED IN THE WORKING AGREEMENT, not beside the
         function, because it is general: "a tidy-up pass that outlives
         the mess it tidied only touches things nobody asked it to."
         Phase 6 meets it again when snapshot() retires -- the debounced
         full-document walk exists to serve snapshot-undo, and once the
         command stack owns undo every remaining caller needs
         re-justifying rather than inheriting.

P4.5(17a) THE OVERCLAIM ANNOTATION -- history stays, the correction sits
         beside it (the gate-failure disclosure's treatment, and the CRLF
         normalisation's)
notes:   TWO COMMIT MESSAGES ON THIS BRANCH CONTAIN CLAIMS THAT WERE FALSE
         WHEN WRITTEN. Neither is rewritten; both are named here so the
         record shows the correction rather than concealing the error.
         * 7b99030 "P4.5(8) - row 36 re-argued by MEASUREMENT" -- its third
           bullet claims the census doctrine was extended to cover
           BEHAVIOURAL claims. That edit never applied: the script used
           `if anchor in s:` and skipped silently when the anchor did not
           match -- a MISSING CHECK. The commit's other claims (the
           grouped-merge measurement, the sibling watch, the
           visibility/permission procedure, the boundary-marker
           precondition rule) did land and stand.
         * 39a4ada "P4.5(16) - the divergence named as latent; justifications
           join the census" -- its second item claims the doctrine was
           extended to cover SURVIVAL JUSTIFICATIONS. That edit never
           applied either: the script RAISED and was committed through
           because the gate was green in the same output -- a CORRECT CHECK
           IGNORED, the worse of the two shapes. The commit's first item
           (row 45's latent-divergence amendment) did land and stands.
         Both entries were added for real at a6bbd80, in the census section,
         and grepped for afterwards. The instrument that should have caught
         them is tools/record.py, added at P4.5(18) -- which then refused
         its own second edit on an ambiguous anchor, which is the behaviour
         being bought.

P4.5(24) THE ENDPOINT DRAG JOINS THE VERTEX OPS -- three method notes kept
         because each is a rule being obeyed rather than a result
notes:   * A COUNT WAS NOT ACCEPTED AS A FINDING. The receipt showed "2
           distinct uids" across a drag, which reads as churn REDUCED. Traced
           event by event it is V1, V2, V2, V2, V2, V2, V2 -- the original
           shared corner sampled before the snapped target had left it, then
           ONE detached vertex for the whole gesture. Churn ELIMINATED, not
           reduced, and the two readings are different claims.
         * DEFECT 13's RULING WAS MEASURED, NOT ARGUED. The conversion does
           not touch `_endpoint_target`/`_corner_target`, so "where the end
           lands is unchanged" was deducible -- and was taken at 0.25x, 1.0x
           and 4.0x anyway, identical before and after. An identity change
           that also moved geometry would be two changes wearing one commit,
           and the difference between a correct inference and a taken reading
           is the whole of "being right from the source is not the same as
           having measured".
         * A RECEIPT WAS DOWNGRADED RATHER THAN QUOTED AT FACE VALUE. Of the
           two fail-first reds, one was a behavioural verdict ("the end
           changed identity 6 times in one drag") and one was an
           AttributeError -- the API not existing yet. The second shows the
           test is new, not that the behaviour was wrong, and it is reported
           as the weaker shape it is. A red is not evidence merely because it
           is red.

P4.5(27) THE FRAGMENT CASE MEASURED -- evidence committed before any reading
notes:   docs/evidence/defect23_fragment_probe.py + defect23-fragment.json.
         Replayed on both trees. The product is the same on each and is
         already broken: 20 distinct Vertex objects on 10 geometric points,
         room_owns_walls FALSE for all nine (group, room) pairs. The walk
         WELDS on the way out (20 -> 10 vertices, 16 -> 12 walls, merged=4),
         so check(deep) is CLEAN on it. Base: the gesture moves 4 of 4 walls
         and 0 of 16 outline corners, opens four dashed edges that each have a
         real wall on them, and the SAVE SUCCEEDS on a file recording that
         nothing moved. Deform: I11 1 -> 3, I5b 0 -> 1, all pairs between
         rooms fragment itself created.

P4.5(28) THE SEVEN RULINGS RECORDED, before any code. Masking accepted as a
         Working-agreement entry at its second instance; rows 47 (fragment ->
         extract, first task after P4.5, and mainwindow.py:982-996 named as a
         SECOND duplication site duplicate_wall never reached), 48 (the
         invariants have never checked the scene the user edits), 49 (I11
         speaks nowhere in the shipped app); 2a amended in place; the
         mini-gate gains a "deliberately still broken" list.

P4.5(29) THE FRAGMENT TEST OFF ITS VACUOUS BASIS. all(enclosed(r)) after the
         move read the NEIGHBOURS duplicate walls, never the piece that moved
         -- it passed on a tree that stranded the room completely. New
         verdict: no wall belongs to two fragments, via room_walls. Three
         preconditions, including that the pieces ABUT (4 coincident edges
         measured). --runxfail lands on the VERDICT, not a precondition.

P4.5(30) DEFORM-TO-FOLLOW LANDS. Clipped band: Garage 0 of 9 -> 7 of 9
         corners, PKT Off 0 -> 5, Util 0 -> 3, the other 17 unchanged.
         THE OLD ASSERTION COULD NOT HAVE FLIPPED: it compared walls-moved to
         corners-moved and A RUN OF k WALLS HAS k+1 CORNERS, so "neither xfail
         flipped" was never evidence against the mechanism. A second
         formulation was tried and REJECTED FOR VACUITY -- "corners moved ==
         corners held by a moved wall" passes on the pre-fix tree too, both
         sides empty -- caught by running it against d57a76f before keeping
         it.

P4.5(31) THE SECOND XFAIL FLIPS, and it was the TEST's geometry. Its body said
         "move ONE corner"; a group of the two walls meeting at a corner holds
         THREE. Its delta (-400,300) yields a NON-crossing quad, so the silence
         it failed on was correct. Swept: crossing at (0,150) (0,200) (0,300)
         (60,240) (-60,300). The deform is now a PRECONDITION before the
         message is demanded.

P4.5(32) ALIGN AND DISTRIBUTE ON THE FINISHED GATHER. rooms_holding moves to
         rooms.py as the single definition; GroupItem._rooms_holding aliases
         it. THE RECEIPT IS THE NEIGHBOUR: three rooms on party walls, A and B
         selected, C never selected -- sharing before -> after (old) -> new is
         A 4/4 -> 1/4 -> 4/4, B 4/4 -> 0/4 -> 4/4, C 4/4 -> 2/4 -> 4/4, open
         edges 2/3/2 -> 0/0/0. Distribute destroyed sharing on every room
         WHILE MOVING THEM BY ZERO. THE GATHER HAD TO WIDEN TO WALLS TOO,
         found by walking into it: with only the room half widened, C drew a
         dashed edge with 0 walls spanning it. Same hole in _corner_records
         (unwelded_ends 0 -> 1 after the clipped bake), fixed by INVERTING the
         scan that used to split the outsider off.

P4.5(33) view.py:402 -- THE LAST p1/p2 WRITER IN floorplanner/. 40 mouse-move
         events: 40 split-on-writes -> 0, the drawn wall byte-identical.
         grep now returns ZERO writers in floorplanner/.

P4.5(34) THE SETTER DELETION IS STOPPED ON A SCOPE-CHANGING MEASUREMENT, and
         this entry is the finding rather than the work.
notes:   The completeness proof itself is DELIVERED: `grep -rn "\.p1 = \|\.p2
         = " floorplanner/` returns nothing. What deleting the setters would
         additionally buy is that they cannot be re-used; what it COSTS was
         not visible until censused.
         MEASURED: `Vertex.moved_to` is the ONLY thing that increments the
         split counter (`_SPLITS[0] += 1`, vertex.py:145), and its ONLY
         callers are the two setters (walls.py:1224, 1234). Delete them and
         `split_count()` is frozen at 0 for the life of the process.
         CONSEQUENCE: SIX ASSERTIONS BECOME UNFALSIFIABLE -- test_topology_ops
         :269 and :320, test_wall_move:223, :331 and :620, test_view:90 --
         each of the form `assert split_count() == before`. They are watches
         that an operation caused no splits; with nothing able to split they
         become tautologies that still read as coverage. That is VACUOUS BY
         TAUTOLOGY, the one shape the gate greps for, in a form its four
         literal patterns will not match -- and it would be introduced BY a
         cleanup, which is how the instrument-boundary rule says these
         arrive.
         SO THE PIECE IS BIGGER THAN "delete two properties": it is retire the
         shim AND its telemetry AND convert six watches from "no splits" to
         "identity preserved" (comparing Vertex objects, which is strictly
         stronger), plus 22 writers across seven test files and
         docs/make_gallery.py, plus tests/test_vertices.py, which is the
         shim's OWN spec and pins split-on-write as a behaviour.
         NOT DONE, and not fudged: a deletion that silently vacates six
         assertions is exactly the trade this project stops for. Ruling
         wanted on whether the counter retires with the setters (converting
         the watches) or the setters stay until Phase 6's command layer owns
         the move.

P4.5(35) THE RULING ON (34): retire the setters AND split_count() together.
notes:   Recorded before the code. VACUITY GAINS A FIFTH SHAPE -- THE
         UNSATISFIABLE ASSERTION, the mirror of the first: shapes 1-3 cannot
         be FALSE, this one cannot be TRUE. A test that cannot fail gives
         false CONFIDENCE; one that cannot pass gives false DOUBT, and false
         doubt is worse in one respect because it sends you hunting bugs that
         are not there. Not machine-detectable. The tell: a red that survives
         every plausible fix -- at which point try to satisfy the assertion BY
         HAND, and if you cannot, the test is the bug.
         AND: MIGRATION TELEMETRY RETIRES WITH THE THING IT MEASURED. Keeping
         split_count() meaningful means keeping split-on-write reachable,
         which is KEEPING THE DEFECT TO PRESERVE ITS ALARM -- ungroup's
         merge_all again. The replacement goes in AT A DIFFERENT LAYER: the
         counter measured runtime churn, what is wanted is that the MECHANISM
         CANNOT RETURN, and that is a question about the source text.

P4.5(36) THE CENSUS MADE PERMANENT. Gate-Census gains `end_assign=N`; any
         `.p1 = ` / `.p2 = ` in floorplanner/ fails the gate. Added BEFORE the
         deletion, so it passes in both states and protects the deletion
         rather than following it. Receipt: 0 clean, 1 with a no-op writer
         reintroduced (named with file and line), 0 after reverting.

P4.5(37) NINE WRITERS SAY WHAT THEY MEAN. Every one turned out to mean DETACH
         THIS END, not MOVE THIS CORNER; the `if p2 else p1` branches collapse
         to one line because the choice was always about which end. TWO
         FIXTURES ARE ONLY CONSTRUCTIBLE VIA THE SPLIT (test_outline's south
         shorten, test_walls' overhang) -- relocating carries the outline
         corner and the edge never opens, which is the state they exist to
         build. Informative, not an obstacle: the split survives as an
         explicit operation, only the coordinate-assignment spelling dies.

P4.5(38) THE SIX WATCHES CONVERTED to identity assertions. The view one is
         genuinely RED against 431a761 ("the drawn end took 36 identities
         across 40 move events"); the other five were green before and after,
         so they were PROBED instead -- make set_end_vertex fabricate rather
         than adopt, and four fail, one on its precondition (reported as the
         weaker shape it is). THREE DRAFTS were wrong before the corpus one
         was right: "same object" forbids PROMOTION, "already existed" forbids
         the ANTI-SHEAR SPLIT (measured: 4 ends re-minted at (216,288) and
         (432,144), all AT THE SAME COORDINATES, 8 sharing classes before and
         after). THE OLD COUNTER NEVER SAW THOSE MINTS -- they go through
         Vertex.at, not moved_to -- so a watch cannot be converted
         mechanically: what it measured and what it appeared to measure are
         different sets.

P4.5(39) test_vertices.py REWRITTEN as the spec for the operations that
         replaced the shim, pinning `Vertex.at` against `relocated_to` on the
         SAME scene and the SAME movement, so the only difference is which was
         asked for.

P4.5(40) THE SHIM RETIRES. Setters, _carry_anchors, moved_to, _SPLITS,
         _SITES, _blame, split_count, split_sites, note_vertex_splits and its
         two logs. 178 lines out, 73 in.
notes:   THE CENSUS THAT OPENED THIS PIECE WAS WRONG, and that is the finding.
         It counted 22 writers by grepping `.p1 = `. It MISSED FIVE, all
         `setattr(wall, attr, <point>)` with attr a variable -- four in
         walls.py, one in a test -- which surfaced as AttributeErrors the
         moment the setters went. EXACTLY the boundary P4.5(36) had written
         into the new check's own comment, crossed within the hour by the
         person who wrote it. A CENSUS BY SPELLING FINDS ONLY THAT SPELLING;
         the deletion is what made the true count visible, and it is now its
         own enforcement for that shape (setattr raises, and no grep can be
         fooled by that).
         THE OPERATION SURVIVES AS `WallItem.detach_end`, because those five
         sites genuinely mean it -- and it could NOT be
         `set_end_vertex(attr, Vertex.at(p))`: that routes through
         _fuse_anchors, which deliberately does not move an opening's anchor
         to a vertex somewhere ELSE (R1(b)). Here the end really moved, so the
         anchor must follow, which is what _carry_anchors did. 12 of 41
         openings on planc1 mirrored down their wall before that carry
         existed, so it is folded into the operation rather than deleted.

P4.5    MERGED 2026-08-06 at PR #10 -- merge commit 4b379fc, two parents
        (b2a7809 main, 1c6ff61 branch). NOT squashed.
ruff:   clean
pytest: 633 collected; OFF/ON/DEEP each 625 passed, 7 deselected, 1 xfailed,
        every sum reconciling; vacuous=0, end_assign=0. CI green on main
        (py3.10, py3.13, deep invariants, ruff -- run 31067224148).
notes:  PATRICK'S MINI-GATE: ALL TEN ITEMS RUN AND PASSED, including item 10
        (Align to grid and Distribute on a plan with shared party walls) and
        the cross-cutting dashed-edge watch. Ticked on that plus the
        reviewer's acceptance.
        PHASE 4 IS COMPLETE at this merge -- P4.1, P4.1b, P4.2, P4.3, P4.4,
        P4.5 -- and the status table carries the mark with the date.
        THE TICK CARRIES AN EXPLICIT CARVE-OUT, and that is the point of it:
        defect 11's RUNTIME z-order collapse was in P4.5's charter and DID
        NOT LAND. Only 11a did (the ghost-band escape). Ruling 4's z rule is
        carried forward INTACT in both the status row and register row 11 --
        floor_term + stack_term + type_term, the backdrop's -1e9 as a TYPE
        TERM, bring_to_front's full-scene scan retired, and the band
        arithmetic as NAMED CONSTANTS with max(type_term) < STACK_BAND and
        max(stack_term) < FLOOR_BAND written beside them and PINNED BY A
        TEST. The serialization half stays blocked on the schema ruling. A
        PHASE THAT TICKS OVER AN UNLANDED CHARTER ITEM IS THE RECORD LYING
        BY OMISSION, so the row says which half landed and where the rest
        goes.
        THE TWO WIP BRANCHES ARE DELETED, local and remote, and their heads
        are recorded HERE because deleting them is what makes this line the
        only handle left:
          p4.5-align-wip     5f679e9  DISCARDED. Its own commit message
                                      predicted it ("this diff will be
                                      REWRITTEN"); P4.5(32) rewrote it
                                      against the finished gather. The code
                                      did not survive, the measurements did.
          p4.5-defect23-wip  4e967c0  ABSORBED. Cherry-picked at P4.5(30)
                                      with its F401 fixed and its one open
                                      ruling taken (fragment: masking, not
                                      regression).
        Neither is an ancestor of main -- align-wip because it was rewritten,
        defect23-wip because a cherry-pick copies content and not the commit
        object -- so both needed a force delete, and that is why the SHAs are
        written down rather than left to reflog.
        THE OPEN QUEUE, in order, all of it carried deliberately: row 47
        (fragment builds duplicate wall loops instead of extracting -- the
        first task, ahead of grid snap), defect 11's runtime collapse, rows
        48 and 49, then grid snap, then Phase 5.


```
