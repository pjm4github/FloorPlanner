# Progress log - Phase 2 - IO cutover

> **Moved verbatim** from `V5_MIGRATION_PLAN.md` (its lines 1247-1657 as of
> commit 2f232bd) on 2026-08-06. Nothing was reworded, reordered, tidied or
> reformatted; the entries appear in the order they were appended. The code
> fence below is the one the log has always been written inside - it is
> reopened here and closed at the end, because a fence cannot be split.
>
> Index: [`README.md`](README.md) - Plan: [`../V5_MIGRATION_PLAN.md`](../V5_MIGRATION_PLAN.md)

```
P2.1  done   (commit ad62e66)
ruff:    clean
pytest:  OFF  377 passed, 4 xfailed, 1 xpassed in 12.51s
         ON   377 passed, 4 xfailed, 1 xpassed in 13.61s
         DEEP 373 passed, 3 xfailed, 6 deselected in 12.51s  (-m "not perf")
files:   floorplanner/design/importer.py (new), design/legacy.py
         (+weld_endpoints_counted), floorplanner/mainwindow.py (open_document,
         load_data split, _finish_open, defect 19), tools/migrate_to_design_v5.py
         (now a thin CLI), tests/test_load_path.py (new, 13),
         examples/symmetricP1.json + planc1.v5.json (surgical, see below)
notes:   NO EXISTING TEST TOUCHED.
         ACCEPTANCE HIT EXACTLY: planc1 opens at M Bath 182.0 sf / Hall 61.5 sf,
         provenance.endpoints_welded = 4, dirty; symmetricP1 opens clean and NOT
         dirty; the legacy file on disk is byte-identical afterwards (asserted).
         check(deep=True) on the converted document = 0 errors.
         FINDING 1 -- `load_data` was OVERLOADED, and migrating in it would have
         broken undo. It is the undo-restore path (mainwindow.py:896) AND a
         plain "apply this dict" helper used by a dozen round-trip tests. Had
         P2.1's migration gone there, EVERY UNDO would weld the geometry and
         re-trace every room -- a repair, not a restore, and silent. Split:
         `load_data` applies faithfully and never migrates (it now also accepts
         a v5 dict, routing to apply_design_to_scene); `open_document` is the
         file-open path that migrates, dirties and reports. load_path/open_plan
         call the latter. A test pins it with a divider stopping 1.5" short --
         geometry a weld WOULD move -- and asserts the gap survives an undo.
         The plan's task text says "Load path" as if it were one thing; it is
         two, and only one of them may repair.
         FINDING 2 -- a regression I introduced and caught: `active_floor` is
         VIEW state that the v4 FILE carries but the v5 Design deliberately does
         not (keeping it out is what stops a floor switch dirtying the
         document). Routing v4 opens through the importer silently forgot which
         floor the user was editing; test_floors::test_serialize_round_trip_two_
         floors caught it. Carried across by hand in open_document.
         FIXTURES: SURGICAL EDIT, NOT REGENERATION -- and the measurement is the
         reason. Regenerating symmetricP1.json produces TWENTY deltas: the two
         named (provenance.endpoints_welded 31->4, settings.area_basis
         inside_face->centerline) plus EIGHTEEN in rooms[5] -- the Garage
         outline's start vertex rotating, which is exactly the change P1.3b
         examined and deliberately declined to bake in ("the fixture STANDS,
         not regenerated"). A full regeneration would have silently reversed
         that decision. So the two fields were edited in place and the diff
         verified line-by-line: 3 changed lines across both fixtures, nothing
         else.
         THIRD FIXTURE DELTA, DECLARED: examples/planc1.v5.json also moves
         area_basis inside_face -> centerline. Not named in the brief, but it is
         the direct consequence of the approved importer decision, and leaving
         the corrupt fixture on inside_face would make the corpus disagree with
         the tool for no reason. Its corruption (I6 + I11) is untouched.
         FAITHFUL MODE PRESERVED. The importer keeps `clean=False`: it is what
         generates planc1.v5.json, the "does not launder its input" fixture from
         P0.7. Dropping it to serve only the load path would have orphaned that
         fixture. The CLI keeps naming ITSELF in provenance.tool, so
         symmetricP1's tool field did not move either.
         PROVENANCE IS RETAINED on the window (`_provenance`) rather than
         discarded after apply -- P2.2 needs it to write the audit trail into
         the saved file, and a v5 file that arrives with one keeps it.
         DEFECT 19 in-app arm closed: extract_from_reference now welds the walls
         it injects. Test asserts unwelded_ends == 0 after an extraction; it was
         2 before.
         CONCEPT-ROOM FIXTURE built as asked, because planc1 no longer exercises
         that path -- the weld closes its 1.5" gap, so M Bath and Hall now get a
         face each. The fixture is a single 20'x8' enclosure with TWO room
         labels and a chair in each half (the shape v4 produces because it never
         serialised open/archway edges). Pins: both rooms survive, the contest
         loser is category=concept + floating + extracted_from set, its outline
         edges are all wall:null, it is sized AROUND the furnishing it carried
         (asserted, not just counted), and check(deep=True) == [].
         FLAG for routing -- TWO THRESHOLDS FOR ONE IDEA. P1.6's bridge counts
         `unwelded_ends` at >1e-9 (reports 5 on planc1); this task's importer
         counts `ends_moved` at >0.6" (reports 4). Same underlying question,
         two numbers, which is the exact trap the 31-vs-4 episode was about. The
         0.6" floor is the principled one (it is the schema's own definition of
         "one vertex"). Aligning the bridge would change two P1.4/P1.6 test
         assertions, so I have NOT done it unasked -- flagging instead.

weld-floor  done   (commit e2a97b3; authorized follow-up to the P2.1 flag)
ruff:    clean
pytest:  377 passed, 4 xfailed, 1 xpassed (both flag OFF and ON)
files:   design/bridge.py (_weld_delta -> WELD_TOL), tests/test_design_bridge.py
notes:   One question, one floor. The bridge's telemetry counted movement above
         1e-9; the importer's ends_moved counts above 0.6". Now both use 0.6",
         the schema's own definition of "one vertex". The two NAMES stay
         distinct -- unwelded_ends is telemetry, ends_moved is a user report.
         ASSERTION CHANGED (authorized): test_weld_is_a_check_not_an_edit,
         planc1 unwelded_ends 5 -> 4. The dropped fifth is a 0.001" float nudge;
         the four real 1.5" divider gaps are unaffected, which is the point of a
         floor this small. The extract fixture stays at 0 (defect 19's weld at
         P2.1 already closed its 2 gaps, and they were far above 0.6" -- a floor
         this small does not launder a real gap). test_apply_design_rebases
         unaffected.
         ALSO CONFIRMED, in answer to the P2.1 report's omission: defect 19's
         in-app arm DID land at P2.1 (commit ad62e66) -- weld_all in
         extract_from_reference at mainwindow.py:1730 plus
         test_extracted_walls_are_welded. Only my summary dropped it; the
         register ticks correctly.

P2.2  done   (commit 6a7e5d4)
ruff:    clean
pytest:  OFF  386 passed, 4 xfailed, 1 xpassed in 13.35s
         ON   386 passed, 4 xfailed, 1 xpassed in 14.99s
         DEEP 382 passed, 3 xfailed, 6 deselected in 14.02s  (-m "not perf")
files:   floorplanner/design/canonical.py (new), design/bridge.py, design/
         importer.py, floorplanner/mainwindow.py (design_document, v5 save,
         legacy export), fp_extract.py, tests/test_load_path.py (+9),
         tests/test_floors.py (the authorized assertion), examples/
         symmetricP1.json + planc1.v5.json (regenerated)
notes:   ACCEPTANCE: save -> reopen -> check(deep=True) == [] and NOT dirty;
         legacy export round-trips through the old loader (asserted by loading
         it into a second window via load_data, the v4 path, and comparing room
         areas). Also pinned: save -> reopen -> save is a FIXED POINT, and
         opening a file the project wrote reproduces it exactly.
         THE ROTATION QUESTION, ANSWERED WITH A TEST rather than an assumption.
         It does NOT bite on save-reopen: apply builds RoomItem.corners in
         document order and the walk reads them back in that order, so rotation
         is carried, not regenerated (measured: Garage starts at (900.0, 12.0)
         both ways). The rotation delta was an artefact of REGENERATING the
         fixture, not of the save cycle. Per the ruling it is now moot anyway --
         canonical form DEFINES rotation.
         CANONICAL FORM MADE TOTAL. canonicalize() moved to design/canonical.py
         (Qt-free, so the importer can call it; it lived in bridge.py, which
         imports Qt) and now normalises outline rotation as well as ids: each
         loop restarts at its lexicographically-least (x, y) corner, orientation
         UNTOUCHED -- winding carries meaning, so reversing a loop would swap
         every wall's sides. Two tests pin it: outlines start at their least
         corner and canonicalize is a fixed point; and rotating every outline in
         the input produces byte-identical canonical output.
         FIXTURES REGENERATED, every delta class measured and named:
           symmetricP1.json  52/62 vertex ids renumbered; 0/20 room ids and
                             0/50 furnishing ids moved; 7/20 loops rotated
           planc1.v5.json    56/65 vertex ids; 0/20 and 0/50; 20/20 rotated
           BOTH: walls-as-coordinate-pairs IDENTICAL, vertex coordinate set
           IDENTICAL, room polygons identical as sets -- NO GEOMETRY MOVED.
           provenance identical, settings identical (area_basis and name carry
           over). planc1.v5.json still fails 23 invariants (I6 + I11), so the
           "does not launder its input" guard holds.
         THREE DATA LOSSES FOUND BY MEASUREMENT, not by a test failing. The
         P2.2 probe compared open(symmetricP1) -> design_from_scene against the
         file: vertices/walls/furnishings identical, but
           * rooms differed on exactly ONE field -- the Garage's
             area_accounting: "unconditioned" -- because the scene has no home
             for it. Fixed generally: v5 room/wall fields the scene cannot model
             are stashed on the item at apply and re-emitted by the walk, so
             category/placement/holes/nominal_size/thickness_in/finish_* survive
             a load-save too, not just the one field that showed up.
           * settings.name ("Symmetric P1") evaporated -- only DEFAULT_SETTINGS
             keys reach the global SETTINGS. Retained on the window.
           * provenance was dropped entirely. Now re-attached on EVERY save.
         ASSERTION CHANGED (authorized in advance; the third of the migration,
         and all three were declared before the fact): test_floors::
         test_serialize_round_trip_two_floors -- the file's remembered active
         floor moved from the top level to settings.active_floor, because the
         v5 root is a closed schema and settings is the designated open bag.
         Still absent from serialize(), so a floor switch still cannot dirty.
         fp_extract.py now calls export_legacy_v4_path, not save_path.
         Converting that writer is P2.4's, with the gallery/examples/macro
         tokens; save_path going v5 would have converted it early and out of
         step. Its output is not stranded -- opening a v4 file converts and
         welds it, which is defect 19's file arm.
         THE STASH'S LIFETIME, accepted rather than engineered around (recorded
         at review, and now a comment in bridge.py): the stash lives ON THE ITEM,
         so it survives ordinary edits but DIES WITH THE ITEM. A wall carrying
         thickness_in that is coalesced away, or a room deleted and re-detected,
         silently loses its stash. Acceptable only because these fields have no
         editor yet; P4/P5 model them properly (placement/nominal_size at
         P4.2-P4.4, area_accounting and finishes at P5.1-P5.3) and the stash
         retires then. Written down so it is a known limit, not a mystery.
         Not pushed -- Phase 2 pushes at its end.

P2.3  done   (commit bbe592c)
ruff:    clean
pytest:  OFF  393 passed, 4 xfailed, 1 xpassed in 15.33s
         ON   393 passed, 4 xfailed, 1 xpassed in 17.30s
         DEEP 388 passed, 3 xfailed, 7 deselected in 15.19s  (-m "not perf")
files:   floorplanner/mainwindow.py (snapshot, restore, dirty, serialize
         demoted), design/bridge.py (keep_backdrop, OpenWall rebuild, door_type),
         design/verify.py (reuse a caller's walk), tests/test_undo.py (+6),
         tests/test_scaling.py (snapshot + undo timings), tests/
         test_characterization.py + tests/test_io.py (the two assertions below)
notes:   snapshot() = canonicalize(design_from_scene().to_dict()), and undo,
         redo and the dirty flag are all defined on it. _restore_state applies
         through apply_design_to_scene with keep_backdrop (the retention
         deferred from P1.5). _is_dirty canonicalizes BOTH sides.
         ONE WALK per settled edit: _commit_if_changed builds the snapshot and
         passes it to verify(doc=..., walk_report=...) rather than walking the
         scene twice at the same quiescent point -- which also makes the latency
         number below honest instead of inflated by my own duplication.
         serialize() DEMOTED to the legacy exporter, with a comment naming its
         sole remaining caller and the release it dies with.
         GROUPS DO NOT CLOSE HERE, per the corrected task text. The bridge emits
         groups: [] until P4.5, so undo keeps dissolving groups exactly as
         today; I did NOT write the group-survives test. What is asserted is the
         narrower promise: undo after grouping restores the plan.
         WHY EDGE-GRANULAR RESTORE IS SAFE -- the canonical Design is
         GRANULARITY-INVARIANT. Whether the scene holds one long wall or three
         segments split at junctions, design_from_scene planarises to the same
         canonical document, so scene wall-count is PRESENTATION state, not
         document state. Pinned directly by
         test_undo::test_snapshot_is_granularity_invariant, which builds the
         same plan two ways and asserts one document. Consequences: (a) a test
         asserting scene wall counts across an undo is asserting presentation;
         (b) if coalesce re-merges collinear segments after a later edit, the
         document, dirty flag and undo comparison correctly do not notice.
         TWO REAL BUGS, found only because the restore now goes through the v5
         bridge:
           * OPEN WALLS were dropped. The v4 loader regenerated them via
             bind_room_walls -- which is DETECTION, and apply must not run it --
             so nothing rebuilt them. Undo silently ate every archway edge. apply
             now builds an OpenWall per `wall: null` outline edge; P3.7 retires
             the branch when null edges render dashed directly.
           * a WINDOW's door_type was clobbered to "". v5 carries door_type for
             DOORS only ("meaningful only when kind == door"), so absent means
             "not applicable", not "empty"; applying now leaves the scene's
             default alone. Caught by test_group_move_undo_restores, which was
             comparing v4 dicts.
         ASSERTIONS CHANGED (2, both presentation-vs-document, authorized in
         advance): test_group_move_undo_restores now compares snapshot() rather
         than serialize() -- v4 reported perimeter_corners ROTATED after an undo
         (same polygon, different first element) because canonical form
         normalises rotation; the polygon itself is now asserted separately so a
         REAL geometry change still fails. And test_unchanged_scene_is_not_
         falsely_dirty sets its baseline with snapshot(), as a save does.
         LATENCY BASELINE for P6.1, P0.3 grid, 16 -> 64 rooms:
           snapshot  2.1 ms -> 10.8 ms   ratio 5.10
           undo     22.0 ms -> 155.8 ms  ratio 7.09
         Guarded with ABSOLUTE bounds (undo < 500 ms, snapshot < 100 ms), not
         ratios: undo sits close enough to the threshold of 8 that a ratio
         assertion would flap -- the same call P0.6 made for select_burst. P6.1
         must make this independent of plan size; today it is not.
         KNOWN REGRESSION recorded in the table: after the first undo, a wall
         crossing a junction comes back split (measured by hand: one 480" wall
         with a mid-span T returns as two 240" walls), so body-dragging it moves
         half and leaves the neighbour. Checked deliberately rather than left
         for a user to find. Restored at P3.3/P3.4.
         Not pushed -- Phase 2 pushes at its end.

P2.4  done   (commit c085b8a)
ruff:    clean
pytest:  OFF  400 passed, 4 xfailed, 1 xpassed in 16.20s
         ON   400 passed, 4 xfailed, 1 xpassed in 17.78s
         DEEP 395 passed, 3 xfailed, 7 deselected in 18.35s  (-m "not perf")
files:   fp_extract.py (save_path), examples/make_examples.py, examples/
         README.md, examples/sample_plan.v5.json (new), tests/
         test_corpus_freeze.py (new, 6), tests/test_extract.py + tests/
         test_schema.py (the two assertions), gallery + example PNGs
ACCEPTANCE: `python docs/make_gallery.py` and `python examples/make_examples.py`
         both run; gallery images regenerated. `python tests/bench_rooms.py`
         also re-run (6x6: rebuild 59.1 ms, memoized no-op 1.9 ms).
notes:   THE FREEZE IS THE TASK. examples/planc1.json (v3) and
         examples/sample_plan.json (v1) are NOT converted and never will be:
         planc1 is the corruption fixture AND the importer's acceptance input;
         sample_plan is the clean legacy input the bridge tests run against, and
         the ONLY v1 file in the repo, so it exercises a migration path nothing
         else does. Converting either leaves the importer with no real v1-v4
         document to prove itself against.
         Made MECHANICAL rather than remembered: tests/test_corpus_freeze.py
         pins both files' format AND version and asserts the legacy corpus never
         drops below two files. Its failure message says what to do instead --
         write the v5 rendering ALONGSIDE, the planc1.json / planc1.v5.json
         pairing that already existed here, which is now what make_examples does
         for sample_plan. examples/README.md documents the freeze in a table.
         Chose that pairing over moving the legacy corpus to tests/fixtures/:
         planc1.json is referenced by path throughout CODE_REVIEW_v2.md,
         DESIGN_MODEL_v5.md, this plan and the migrator's CLI docs, and it has
         to stay in examples/ regardless -- splitting the pair across two
         directories would be worse than keeping both.
         VERIFIED, NOT ASSUMED: make_gallery.py and bench_rooms.py needed no
         format work (both build their scenes programmatically, neither reads
         the corpus), and the macro open/save tokens were already v5 via
         load_path/save_path.
         MACRO MODAL PATH TESTED, not claimed. `open` on a legacy plan through
         the macro runner converts, COLLECTS the report on win._conversion,
         writes it to the status line and leaves the document dirty -- with no
         QMessageBox. A modal there hangs a macro or a test forever, so the
         coverage matters more than the assertion (the test HANGS rather than
         fails if one returns, which is itself the signal). The v5 half is
         pinned too: not converted, not reported, not dirty.
         ASSERTIONS CHANGED (2, both declared in advance):
           * test_fp_extract_cli_end_to_end -- output is floorplanner-design
             now. The wall COUNT is deliberately relaxed to >= 5: v5 walls are
             edge-granular, so 5 detected runs planarise to however many graph
             edges they span. result["counts"]["walls"] == 5 still pins what was
             DETECTED, which is what that test is actually about.
           * test_corpus_discovered -- the pinned set grew by sample_plan.v5.json.
             It joined the validated sweep automatically the moment it existed
             (discovery works), and validates clean: schema 0, invariants 0 deep.
         Not pushed -- Phase 2 pushes after P2.5.

P2.4-followup  done   (commit 33e457d)
ruff:    clean · pytest: 400 passed, 4 xfailed, 1 xpassed
notes:   The `>= 5` wall bound was the WRONG SHAPE of guard -- a lower bound
         passes if planarisation ever explodes, so a bug splitting 5 detected
         runs into 500 spurious segments would sail through. Measured and
         hard-coded: 5 detected runs -> 9 graph edges over 8 vertices for that
         fixture, both exact (the fixture is deterministic and edge-granular
         walls are document state in v5). EIGHTH declared assertion change.
         Took the optional hardening too: the macro-modal test's failure mode
         was a HANG (a modal exec() blocks forever headless), which in CI means
         the job runs to its timeout. _modal_failsafe schedules a single-shot
         timer that dismisses any modal and records it, so the test goes RED
         instead. Timers fire inside nested exec loops -- the same mechanism
         macro._modal_step uses to drive dialogs, opposite purpose.

P2.5  done   (commit d274d21)
ruff:    clean
pytest:  OFF  400 passed, 4 xfailed, 1 xpassed in 14.89s
         ON   400 passed, 4 xfailed, 1 xpassed in 16.98s
         DEEP 395 passed, 3 xfailed, 7 deselected in 14.79s
files:   floorplanner/planio.py, csvio.py, imageio.py, levels.py (all new),
         floorplanner/mainwindow.py, CLAUDE.md
ACCEPTANCE: suite green with ZERO TEST CHANGES -- `git status tests/` empty --
         all three ways. MainWindow 100 methods / 2179 lines -> 49 / 1173,
         under the review's ~55 target.
INVENTORY (methods / lines):
         mainwindow.py  MainWindow    49  1173   UI wiring + edit orchestration
         planio.py      PlanIOMixin   26   544   open/save/export + bridges
         levels.py      LevelsMixin   13   198   the floor roster
         csvio.py       CsvIOMixin     6   260   room CSV import/export
         imageio.py     ImageIOMixin   6   186   reference image + extraction
notes:   MIXINS, NOT DELEGATING WRAPPERS. The suite calls these directly --
         win.serialize(), win.snapshot(), win.load_data(), win._import_rooms(),
         win._is_dirty(), win.switch_floor() -- and a mixin resolves every one
         unchanged with zero delegation boilerplate. A delegate-per-method split
         would ALSO have left MainWindow at 100 methods, missing the point of
         the target. The split is internal structure, invisible at the API.
         MOVER'S DISCIPLINE VERIFIED MECHANICALLY, not asserted: a script
         ast.unparse()s every method before and after the split and diffs them.
         100 before, 100 after, 0 missing, 0 CHANGED. Nothing improved in
         flight.
         BOTH KNOWN HAZARDS CHECKED rather than assumed: SETTINGS is ONE shared
         object (id() compared across config/planio/csvio/imageio/levels/
         mainwindow -- all identical; no module re-binds it), and serialize()
         travelled with its guard comment intact.
         The 84 unused imports left by copying mainwindow's header into each
         module were removed by `ruff --fix`; star imports keep their noqa.
         CLAUDE.md's module layout updated -- it described a layout that no
         longer existed and would have misdirected the next reader.
         NOTED FOR LATER, NOT DONE (the itches, per mover's discipline):
           * `import_from_image` (55 lines) and `_import_rooms` (137 lines) are
             both long enough to want splitting; neither is in P2.5's scope.
           * `apply_project_to_scene` (109 lines) is the v4 loader and is on a
             deletion path once the legacy export retires -- do not invest.
           * `room_boolean` (97 lines) stayed in mainwindow.py deliberately: it
             is rewritten as a polygon op at P3.5, so moving it now would churn
             a file that task rewrites.
         PHASE 2 COMPLETE. Ready to push.

PHASE 2 PUSHED  (52bd72e..3c2fbcf, 13 commits) -- CI GREEN on py3.10 + py3.13.
         Doubled suite: 16s/18s on py3.13, 17s/20s on py3.10; job total 1m13s.
         Still a clean doubling, still no cross-Python divergence.

GATE 2  manual sanity check -- FINDING, fixed on main before branching
         (commit d665e06)
ruff:    clean
pytest:  OFF  403 passed, 4 xfailed, 1 xpassed in 15.78s
         ON   403 passed, 4 xfailed, 1 xpassed in 18.43s
         DEEP 398 passed, 3 xfailed, 7 deselected in 15.84s
files:   floorplanner/design/importer.py (weld_room_corners),
         tests/test_load_path.py (+3), examples/symmetricP1.json (regenerated)
THE FINDING: reopening the app's OWN legacy-v4 export of a converted plan
         reported "5 wall ends moved (5 junctions checked)". Expected 0 -- the
         app's own output must never need repair. NO EXISTING TEST TOUCHED.
DIAGNOSIS -- (a), but UPSTREAM of the export. The export was faithful and the
         report honest (weld_ops == ends_moved == 5, nothing conflated). The
         IMPORTER baked a pre-repair artefact into the repaired document:
           1. the weld pulls the four divider ends 655.529 -> 654.0 (the fix);
           2. split_params then cuts those same walls at the STORED room
              corners, which are PRE-WELD data and still say 655.529;
           3. that injects a degree-2 vertex 1.53" from the freshly welded end
              and a 1.53" SLIVER wall -- the exact ghost of the gap just closed.
         The tell was the DIRECTION: displacements ran from 654.0 OUT to 655.53,
         away from the repair, not toward it.
         WHY NOTHING CAUGHT IT: 1.53 clears MIN_SPAN (1.0) so the sliver
         survives, and clears vertex_weld_in (0.6) so I14 stays silent; all 20
         room areas were correct. It is invisible until the document is exported
         and reopened, where the 2" end-to-end gesture weld fuses the pair.
FIX:     weld_room_corners() snaps stored perimeter_corners onto the welded wall
         ends using the same END_TOL the wall weld uses -- they describe the
         same corners. 66 corners welded on planc1; reopen now reports 0/0.
         It also removes a SECOND, quieter error: stored corners are rounded to
         2dp by _sync_corner_props, so using them verbatim seeded the vertex
         table with up to 0.005" of drift. Six symmetricP1 vertices gain
         precision (104.42 -> 104.4228, 280.24 -> 280.2416, ...).
WHY IT ESCAPED, and the missing test: P2.2 round-tripped only via load_data --
         the FAITHFUL apply, which never welds -- so the export was never taken
         back through the CONVERTER. The two paths were each covered and their
         composition was not. test_legacy_export_reopens_without_repair now
         drives the full journey (open -> save v5 -> export v4 -> reopen
         converting) and asserts ends_moved == 0 with areas identical, plus a
         unit test for the corner weld and a guard that no sub-2" sliver
         survives a conversion.
FIXTURE: symmetricP1.json regenerated, every delta class measured:
           2 sliver vertices REMOVED (the bug) -> 82 walls to 80; Hall 9->7,
             Great Room 11->10, M Bath 11->10 outline edges
           6 vertices gain precision (2dp stored corner -> exact wall endpoint)
           47/62 vertex ids renumbered, 11/20 loops rotated (consequences)
           0 OF 20 ROOM AREAS CHANGED -- the geometry is preserved
           provenance and settings identical
         planc1.v5.json BYTE-IDENTICAL: faithful mode never welds, so it never
         had the artefact -- which is itself a check on the diagnosis.
         Acceptance unchanged: M Bath 182.0, Hall 61.5, 4 ends moved, check
         clean. Side effect worth noting: suite warnings dropped 17 -> 2,
         because converted scenes no longer carry unwelded ends.
LESSON, recorded in one line because it generalises: both paths were covered;
         their composition was not -- COVERED-PATHS != COVERED-COMPOSITIONS.
         Every future gate should ask which pairs of covered paths have never
         been run back-to-back.
result:  GATE 2 -- PASSED, one finding found and fixed (d665e06). Patrick's two
         trailing checks (original file untouched on disk, undo feel) ride as
         optional confirmations, not blockers.
meaning: Phase 2's acceptance is complete. P3.1 may proceed.

```
