# Progress log - Phase 1 - the v5 document, shadow mode

> **Moved verbatim** from `V5_MIGRATION_PLAN.md` (its lines 829-1246 as of
> commit 2f232bd) on 2026-08-06. Nothing was reworded, reordered, tidied or
> reformatted; the entries appear in the order they were appended. The code
> fence below is the one the log has always been written inside - it is
> reopened here and closed at the end, because a fence cannot be split.
>
> Index: [`README.md`](README.md) - Plan: [`../V5_MIGRATION_PLAN.md`](../V5_MIGRATION_PLAN.md)

```
P1.1  done
ruff:    clean
pytest:  308 passed, 4 xfailed, 1 xpassed (+4 from test_design_model.py)
files:   floorplanner/design/model.py (new); floorplanner/design/__init__.py
         (+model exports); tests/test_design_model.py (new).
notes:   Qt-free dataclasses (Level, Vertex, Wall, Opening, Room, OutlineEdge,
         Furnishing, Group, Provenance, Design) over the v5 schema. from_dict/
         to_dict driven by a per-class FIELDS table; sub-structures the schema
         gives no object type (settings, anchor, placement, label, properties,
         pos, provenance fields) ride as RAW values.
         BYTE-IDENTICAL round-trip verified for symmetricP1.json AND site_demo.json
         -- both dict== and json.dumps== (not just the required symmetricP1). The
         crux is a _MISSING sentinel via d.get(k, _MISSING): a present-with-null
         field (free wall left: null) is kept null; an absent field (a room with
         no area_accounting) stays absent, never emitted as null. A dedicated test
         pins that distinction.
         WHY _MISSING IS LOAD-BEARING BEYOND P1.1: P2.1's "a v5 file never opens
         dirty" promise rests ENTIRELY on Design.from_dict(x).to_dict() == x. Had
         the model normalised absent -> null, every v5 file would round-trip
         structurally different from what was written and open dirty on every
         load -- and that bug would surface in Phase 2, months after the real
         cause. So this fidelity is a P2.1 dependency, not a P1.1 nicety.
         ZERO Qt: model.py imports only the stdlib. test_model_imports_zero_qt
         execs the file in ISOLATION (bypassing floorplanner/__init__, which star-
         imports the Qt scene layer) and asserts no PyQt6 module was pulled in --
         so it catches a stray Qt or floorplanner import, not just a direct one.
         No behaviour, no callers yet (the scene<->design bridge is P1.4/P1.5).
         Not pushed -- Phase 1 pushes at its end (or on the v5-topology branch for
         Phase 3), per the push policy.

P1.2  done
ruff:    clean
pytest:  312 passed, 4 xfailed, 1 xpassed
files:   floorplanner/design/validate.py (deep split + docstring); tests/
         test_schema.py (deep-gating + two negative tests); tests/
         test_design_model.py (planc1.v5.json added to the round-trip set).
notes:   COUNT CORRECTED (my error, was propagating): 15 named checks, not 14 --
         I1-I14 plus I5b. Split: deep-only 3 = I5b, I11, I14 (the O(n^2) ones);
         always-on 12 = I1 I2 I3 I4 I5 I6 I7 I8 I9 I10 I12 I13. Verified on the
         corpus: planc1.v5 trips I11 (deep) + I6 (always-on); deep=False drops
         I11 but still reports I6.
         DEFAULT = deep=True, and this FLIPS the "cheap by default" wording in my
         earlier P1.2 amendment (a894221) -- called out here because a changed
         decision is a red flag too. Rationale: forgetting deep=False on the hot
         path is a loud slowdown; forgetting deep=True on load/import is SILENT
         corruption (exactly where I11/I14 matter most). Loud failure wins. The
         per-command path (P1.6 --verify-design) opts out with deep=False; the
         CLI and corpus tests keep the default and validate fully -- no caller
         change needed.
         Negative tests each FAIL the check (not just not-crash): I14 fires on a
         welded corner split into two vertices 0.3" apart AND does not fire under
         deep=False (proves the gate); I6 fires on a wall side that disagrees with
         the room outlines.
         Also (riding with P1.2): planc1.v5.json added to the P1.1 round-trip --
         byte-identical, exercising wall: null open edges + a provenance block
         (three fixtures now). And recorded that _MISSING is a P2.1 dependency
         (see the P1.1 entry above) with a matching line added to P2.1's
         acceptance -- "opening a v5 file must not dirty it".

P1.3  done
ruff:    clean
pytest:  323 passed, 4 xfailed, 1 xpassed (+11 from test_topology.py)
files:   floorplanner/design/topology.py (new), floorplanner/design/legacy.py
         (new), floorplanner/design/__init__.py (+exports), tests/
         test_topology.py (new).
notes:   BOTH concrete acceptances hit exactly: trace_faces on symmetricP1
         recovers 19 room areas; weld_endpoints on legacy planc1.json welds 31.
         Per the three structural notes:
         (1) Ported to Design, not dicts: topology functions take and return
         P1.1 dataclasses; adjacency/pos are built from design.walls/vertices.
         (2) The one-shot legacy path is SEPARATE: weld_endpoints lives in
         design/legacy.py, on raw p1/p2 wall dicts (it runs at v1-v4 import,
         before a Design exists). Its lifetime ends when files are converted;
         split_edge/merge_collinear/trace_faces are forever. Not peers, so not
         in the same module.
         (3) Winding pinned by its own test: left = the (dy,-dx) side, verified
         79/79 walls-with-left on symmetricP1 (you said 61/61 -- the convention
         holds 100%, the count is 79). A second test ties trace_faces' winding
         to the stored `left`: the (dy,-dx) probe of a shared wall lands in a
         face whose area is the left room's. Without this, a flipped winding
         swaps every left/right and I6 still passes.
         The 19-vs-20: trace_faces returns 20 inner faces; exactly 19 match a
         stored room area. The sole unmatched room is the Garage (largest,
         boundary-touching) -- its face IS the outer boundary that _inner_faces
         drops. A test asserts unmatched == {Garage}, not just the count.
         Forward-looking ops (split_edge, merge_collinear, planarize) are pure
         Design->Design and tested for the invariant that matters -- they
         preserve trace_faces (rooms unchanged); planarize is idempotent on the
         already-planar corpus. DEFERRED with a note in the code: opening
         redistribution across a split, and crossing-point insertion, land at
         P3.3/P3.4 where the wall-move split rule is built -- split_edge leaves
         openings on the first segment for now.
         Zero Qt: model.py proven by isolated exec (P1.1); topology.py and
         legacy.py asserted Qt-free at the source level (no PyQt import; their
         only floorplanner imports are floorplanner.design.*), since importing
         them via the package would pull Qt through floorplanner/__init__.
         Not pushed -- Phase 1 pushes at its end.

P1.3-followup  done   (responding to the two P1.3 flags)
ruff:    clean
pytest:  324 passed, 4 xfailed, 1 xpassed (+1: split_edge raises-on-openings)
files:   design/topology.py (split_edge guard), design/legacy.py (docstring),
         tests/test_topology.py (raises test), docs/CODE_REVIEW_v2.md (defect 18),
         docs/V5_MIGRATION_PLAN.md (P1.4 acceptance amended).
notes:   FLAG 1 (landmine) fixed: split_edge no longer leaves openings on the
         first segment -- it RAISES NotImplementedError naming P3.3 on any wall
         carrying openings. P3.3 removes the guard as it builds redistribution.
         pytest.raises(match="P3.3") pins it. Same principle as deep=True: the
         failure mode is loud, at the call site, not a rendering oddity three
         tasks later.
         FLAG 2 (probe the unmatched face): I checked, and it is TWO findings,
         not the benign "no" branch.
         - The unmatched 60.6 sf face's centroid is inside NO room (Garage
           included) -- a genuinely unclaimed wall-bounded region in symmetricP1.
           Not an M-Bath-class outline/wall disagreement; a corpus observation.
         - Digging further: the Garage (868.5 sf) IS a valid raw traced face
           (9 edges) -- it is not unenclosed. _inner_faces DROPS it because its
           "drop the largest inner face as the outer boundary" heuristic is
           unsound: the true outer boundary (4535 sf) is opposite-wound and
           already excluded by the majority-sign filter, so inner[1:] discards
           the biggest ROOM. The migrator masks this (per-room enclosing_face
           recovers the room); standalone trace_faces loses it. Logged as
           DEFECT 18 -> P3.5 (identify the boundary by winding, not area).
         So the P1.3 "19 not 20" is really: Garage wrongly dropped by the
         heuristic + a separate 60.6 unclaimed region. The unmatched=={Garage}
         test still holds and still cannot pass for the wrong reason.
         Also corrected legacy.py's docstring: it is PRE-VERTEX geometry (raw
         p1/p2), used by BOTH the v4 importer (P2.1) AND design_from_scene (P1.4,
         scene still p1/p2 until P3.1) -- not purely import-only. Retired at P3.1.

P1.3b  done   (defect 18 fix + corpus diff, before P1.4)
ruff:    clean
pytest:  324 passed, 4 xfailed, 1 xpassed
files:   design/topology.py + tools/migrate_to_design_v5.py (_inner_faces /
         inner_faces fix), tests/test_topology.py (test updated to the fixed
         behaviour), docs/CODE_REVIEW_v2.md (defect 18 -> fixed), this plan
         (P1.3 acceptance 19->20).
notes:   FIX: _inner_faces now keeps the majority winding and drops ALL
         opposite-wound faces (one outer boundary per connected component --
         a detached garage or a Phase-4 floating room each has its own), never
         by size. Retargeted defect 18 P3.5 -> P1.3b and fixed NOW: P2.1's
         import traces outlines, so the old heuristic would have silently fallen
         back to stored corners for the largest room of every imported plan --
         user-facing, four tasks out. Fixed in BOTH topology.py and the migrator.
         Result: trace_faces on symmetricP1 now recovers all 20 rooms (Garage
         included), plus one extra face for the 60.6 sf unclaimed region.
         CORPUS DIFF (the required check): regenerated symmetricP1 with the fixed
         migrator (migrate(planc1.json, --clean --name "Symmetric P1"), the
         command that produced the committed file) and diffed. Result: GEOMETRY
         IDENTICAL -- Garage 868.5 sf both ways, same 9 edges, same cycle; the
         only file change is the Garage outline's start vertex rotating (the
         migrator now TRACES the Garage, rooms_traced 19->20, instead of the
         stored-corners fallback). So the Garage's stored outline AGREES with
         its traced face -- NOT an M-Bath-class disagreement. Per the decision
         tree that is the "identical" branch: the fixture STANDS, not
         regenerated (a cosmetic loop-rotation is not worth churning a fixture
         that P1.1/P1.4/P1.5/P1.6 pin). Had they disagreed, that would have been
         a corruption baked in by luck (the buggy fallback) -- they don't.

F5-correction  done   (doc-only commit e613b5d, taken BEFORE the P1.4 code)
ruff:    n/a (doc only)
pytest:  n/a
files:   docs/CODE_REVIEW_v2.md (F5 rewritten + a correction note),
         docs/DESIGN_MODEL_v5.md (section 6 sentence; a note at the head of 7a)
notes:   F5 and section 6 both said the editor welds "on every draw release and
         on load". The "on load" half is FALSE: apply_project_to_scene
         (mainwindow.py:1298) runs coalesce_all + rebuild_all_walls and no
         weld_all. Welds happen only at draw release (view.py:489) and via
         Edit > Coalesce all walls now (mainwindow.py:821).
         Corrected mechanism, verified in the source: coalesce is itself a gap
         SOURCE -- _coalesce_wall_impl (walls.py:200-201) re-snaps the survivor's
         p1/p2 onto the 6" on-centre grid independently of whatever neighbour an
         end was welded to, so it can pull a previously-welded end off its
         partner. Gaps are created and accumulated by the app's own pipeline and
         survive every round-trip, rather than merely failing to persist a weld
         the app already performed.
         CONSEQUENCE FOR P2.1, recorded in 7a: weld-on-load is NEW, deliberate
         repair behaviour the app has never applied to a user's file -- not
         persistence of something it already did. That strengthens the
         conversion report and the dirty flag rather than weakening them.

P1.4  done   (commit c78cb5e)
ruff:    clean
pytest:  337 passed, 4 xfailed, 1 xpassed in 10.16s (+13 from
         test_design_bridge.py; 324 -> 337, no other count moved)
files:   floorplanner/design/bridge.py (new), floorplanner/design/legacy.py
         (+VertexTable, +split_params -- PURELY ADDITIVE, weld_endpoints is
         byte-identical), floorplanner/design/__init__.py (docstring only),
         tests/test_design_bridge.py (new, 13 tests)
notes:   NO EXISTING TEST TOUCHED -- `git status` showed two modified source
         files and two new files, nothing else.
         The three notes, as built:
         (a) LEVEL-SCOPED BY CONSTRUCTION, not by filter. _by_floor() buckets the
         scene once; each level's walk receives ONLY its bucket, and the vertex
         table, wall graph and room polygons are per level. There is no global
         query left to forget to filter -- defect 12 closes structurally.
         test_walk_is_level_scoped builds two GEOMETRICALLY IDENTICAL rooms on
         two floors (coincident coordinates are precisely what a leaking walk
         would fuse) and asserts the levels share no vertex.
         (b) Outlines from RoomItem.corners, never trace_faces.
         (c) legacy.py grew the two pre-vertex helpers the walk needs:
         VertexTable (weld-on-insert at WELD_TOL 0.6") and split_params (cut at
         junctions + every room corner, so one wall spans one outline edge).
         THE WELD DECISION, resolved explicitly before any code: weld_endpoints
         is a CHECK, never an edit. It runs on a deepcopy to count what it WOULD
         move; the emitted geometry is always the scene's own. Non-zero ->
         report["unwelded_ends"] + a warning, and strict=True raises (the P1.6
         --verify-design hook). Rationale: silently welding would have made
         P2.2's Save move a user's walls up to 9", and would have made P1.6's
         shadow comparison diverge from the scene it shadows. Only the 0.6"
         weld-on-insert runs for real, and at that tolerance two points ARE one
         vertex -- representation, not repair.
         ACCEPTANCE: room areas match project_from_scene() EXACTLY (not merely
         within 0.1 sf) on planc1.json, sample_plan.json and fixture scenes.
         sample_plan walks fully clean: check(deep=True) == [], 0 unwelded ends,
         0 open edges, and schema_errors() == [] too. planc1 reports 17x I6 +
         1x I11 -- asserted as measured, per the acceptance, not forced to [].
         Same fault classes as its v5 fixture (I6 + I11), as predicted.
         FINDING 1 -- the 31 is a count of ATTEMPTS, not of damage. My checker
         reports 5 unwelded ends on planc1, not 31. Cross-checked: weld_endpoints
         returns 31 on the FILE geometry and 31 on the SCENE geometry -- identical,
         so the scene->raw-walls extraction is faithful and load's coalesce
         changed nothing here (46 walls in, 46 out). The 31/5 gap is the counting
         method: 31 counts weld OPERATIONS, and 26 of them are no-ops on
         junctions that are already exact. Measured displacements: 4 ends move
         1.529" (the documented divider gaps, y 655.529 -> 654.0) and 1 moves
         0.001" (float noise). So "31 wall ends were welded" in section 6 and in
         7a's user-facing conversion message overstates the geometry actually
         changed by ~6x. The P1.3 acceptance pinning 31 is still correct (it
         pins the function's return) and its test is untouched -- but 7a's
         message to the user should probably say "4 wall ends moved", not "31
         welded". FLAGGING, not editing: that is user-facing copy.
         FINDING 2 -- the SCENE's planc1 corruption is worse than the FILE's.
         On disk Hall and M Bath differ (243.5 sf / 18 corners vs 591.6 sf /
         24 corners). Load re-detects rooms, the 1.5" gap leaks the flood-fill,
         and BOTH label anchors resolve to the same merged region: they come out
         as the SAME 21-vertex loop at 243.5 sf each. I11 is firing on an exact
         coincidence, not a partial overlap. The test asserts the shared vertex
         set, so it cannot pass for the wrong reason. P2.1's repair has to fix
         a worse input than the file suggests.
         THREE CALLS the task text did not specify (all endorsed before coding):
         bridge.py is the home, and is deliberately NOT re-exported from
         design/__init__.py so model/topology/legacy/validate stay importable
         without the Qt scene layer; groups emit [] (defect 3 -- a grouped wall
         has no single id here, it splits into segments; emitting a guess would
         make characterization test 3 pass for the wrong reason, and both close
         at P4.5); settings.area_basis is "centerline", NOT the migrator's
         "inside_face", because the scene's areas ARE centreline areas and
         declaring the better basis would itself be a repair.
         Not pushed -- Phase 1 pushes at its end, per the push policy.

P1.4-followup  done   (doc-only; responding to the two P1.4 findings)
ruff:    n/a (doc only)
pytest:  n/a
files:   docs/DESIGN_MODEL_v5.md (7a message + the two-counter rule),
         docs/V5_MIGRATION_PLAN.md (P2.1 task text; this entry)
notes:   FINDING 1 SETTLED -- two counters, with the threshold taken from the
         document's own semantics rather than picked: the schema defines
         vertex_weld_in = 0.6" as the distance at which two coordinates ARE one
         vertex, so a displacement at or below it is not a geometry change BY
         DEFINITION. weld_ops = operations performed (31); ends_moved =
         displacement > 0.6" (4). Only ends_moved is ever shown to a user or
         written to provenance.endpoints_welded -- whose schema description
         already reads "Wall ends MOVED onto a neighbour", so the corrected
         reading is what the schema always meant and the fixture's stored 31
         contradicts its own field. 7a's example message now reads "4 wall ends
         moved to close gaps (31 junctions checked)".
         symmetricP1.json's provenance is NOT regenerated now -- deliberately.
         P1.1/P1.4/P1.5/P1.6 all pin that fixture; regenerating mid-phase is
         churn for a semantics fix P2.1 implements properly. Folded into P2.1's
         task text instead.
         FINDING 2 MADE BINDING -- P2.1's task text now REQUIRES the importer to
         derive outlines from the welded FILE geometry, never from the scene's
         re-detection, and cites the measurement: loading planc1 collapses Hall
         and M Bath into one identical 21-vertex region (both 243.5 sf, same
         vertex set), where the file keeps them distinct (243.5/18 corners vs
         591.6/24 corners). The scene's belief about a corrupt file is STRICTLY
         WORSE than the file. test_planc1_reports_its_real_faults pins the shared
         vertex set and is named in the plan as the guard.

P1.5  done   (commit 2678ff5)
ruff:    clean
pytest:  347 passed, 4 xfailed, 1 xpassed in 12.27s (+10; 337 -> 347)
files:   floorplanner/design/bridge.py (+apply_design_to_scene, +_canonicalize,
         +geometric ordering in the walk), tests/test_design_bridge.py (+10)
notes:   NO EXISTING TEST TOUCHED -- git status showed exactly two modified
         files, both mine. Existing IO and undo tests green unchanged.
         ACCEPTANCE MET on sample_plan.json AND planc1.json: scene -> Design ->
         scene -> Design is dict-identical at the second Design. planc1 is in
         the round-trip set deliberately -- a corrupt plan must round-trip as
         faithfully as a clean one; had apply quietly repaired the Hall/M Bath
         collision the second Design would be "better" and the bridge would be
         lying about what it holds.
         THE FINDING THAT SHAPED THE TASK -- ids were not canonical. The first
         round trip came back ISOMORPHIC BUT UNEQUAL: identical counts
         (8/8 vertices, 10/10 walls, 3/3 rooms on sample_plan; 61/80/20 on
         planc1) with different ids. Cause: P1.4 minted ids in EMISSION order,
         which is source-wall order, but apply turns each split segment into its
         own WallItem, so the second walk visits the same geometry in a
         different order. Fixed with _canonicalize: vertices sorted by
         (level, x, y), walls by (level, v1 pos, v2 pos, type), rooms by
         (level, name, centroid), furnishings by (level, pos, kind, rotation),
         openings renumbered along the wall -- then ids assigned and every
         reference rewritten. The walk's per-level item lists are sorted
         geometrically too, so the vertex-table weld order is deterministic.
         This is the same z-independence Project.to_dict already gives the v4
         snapshot (model.py:211-224) and for the same stated reason; P2.3's undo
         comparison needs it as well. A test pins it directly: bring a wall to
         the front, re-walk, document unchanged.
         The four mirror notes, as built:
         (1) NO coalesce/weld/detection in apply. Pinned by an OFF-GRID plan
         (205x101 at (7,3), no corner on the 6" wall-snap grid): a coalesce pass
         would re-snap the endpoints and the test asserts the exact
         coordinates survive.
         (2) Rooms READ, never re-detected. Ordering does the work --
         rebuild_all_walls runs BEFORE any RoomItem exists, so refresh_rooms
         returns at `if not rooms: return` and no flood-fill can overwrite a
         stored outline. Each room's _detect_sig is then primed via the public
         room_signature(scene, room) so a LATER rebuild also leaves it alone;
         the test asserts d1 == d2 across an explicit rebuild_all_walls.
         (3) Openings invert exactly. _opening_s is the algebraic inverse of the
         s -> anchor conversion, and the test compares openings wall-by-wall
         across planc1's 20+ openings (with a guard that the corpus has not
         silently got weaker), not just a count.
         (4) floor assigned from the level explicitly on every wall, room and
         furnishing. The test sets active_floor to the WRONG floor before
         applying, so anything trusting the active_floor() global lands
         visibly wrong.
         TWO SMALL CALLS: apply collapses the scene's anchor + label_offset into
         the anchor (v5 stores ONE label offset, relative to the centroid --
         the schema's stated intent), which round-trips exactly; and
         keep_backdrop / reference-image retention is deliberately NOT handled
         here, it belongs with the undo-restore path at P2.3.
         Opening failures are COLLECTED and surfaced (report["openings_failed"]
         + warning, strict=True raises), not dropped by the v4 path's silent
         `except ValueError: continue` -- pre-figures P3.6.
         Not pushed -- Phase 1 pushes at its end, after P1.6.

P1.6  done
ruff:    clean
pytest:  OFF  364 passed, 4 xfailed, 1 xpassed in 11.84s
         ON   364 passed, 4 xfailed, 1 xpassed in 12.50s   <- THE ACCEPTANCE
         DEEP 360 passed, 3 xfailed, 6 deselected in 11.23s  (-m "not perf")
files:   floorplanner/design/verify.py (new), floorplanner/mainwindow.py (3
         hooks + import), floorplanner/app.py (--verify-design -> env var),
         floorplanner/design/bridge.py (rebase at the end of apply),
         tests/conftest.py (fixture rebase + teardown verify),
         tests/test_verify_design.py (new, 17), .github/workflows/ci.yml
         (second suite run with the flag on), docs/CODE_REVIEW_v2.md (defect 19)
TEST CHANGED (declaring it, per the working agreement): tests/test_rooms.py
         `_overlapping_rooms` gained a `rebase(win)` call. NO assertion changed
         -- it declares that the helper's overlapping rooms are the deliberate
         INPUT to room_boolean, the same "this state is accepted" mechanism a
         corrupt legacy file uses at load. See finding 2.
notes:   Hooks at quiescent points only, never scene.changed (mid-operation the
         scene is legitimately inconsistent): _commit_if_changed before the
         snapshot (cheap twelve), save (deep), load (deep + REBASE), and the
         conftest fixture teardown -- that last one because the 180 ms dirty
         timer NEVER FIRES HEADLESS, so without it the suite would verify
         almost nothing.
         FINDING 1 -- unwelded_ends must NOT raise, and this contradicts the
         spec I was given ("same treatment as an invariant class"). Two
         independent reasons, both measured:
         (a) THE SCHEMA FORBIDS IT. join_tol_in is documented as "GESTURE
         TOLERANCE ... Never an invariant: a wall deliberately stopping 6"
         short of another is a legitimate design (a reveal, a pilaster gap),
         and nothing may silently close it." Raising would fail a user for
         drawing a reveal.
         (b) IT IS NOT A DOCUMENT PROPERTY. apply_design_to_scene rebuilds
         planc1 from a BYTE-IDENTICAL Design and the count goes 5 -> 15,
         because Design walls are edge-granular and a wall split at its
         junctions has more ends to be near things with. A metric that moves
         while the document is provably unchanged cannot be a document
         invariant. Resolution: REPORT_ONLY -- carried in the profile, warned
         once when it rises, never raised on. The real weld invariant is I14 at
         the 0.6" modelling tolerance, and that stays in the raising set.
         A test pins REPORT_ONLY's contents so adding to it can't silently
         disarm an invariant.
         FINDING 2 -- one I11 fired, and it is NOT a defect. Under the deep
         sweep, test_rooms::test_room_op_needs_two_rooms tripped "I11 two placed
         rooms overlap". Diagnosed rather than suppressed: the overlap is built
         by the `_overlapping_rooms` helper as the deliberate input to
         room_boolean, and the operation under test is a no-op by design, so
         nothing INTRODUCED it. Declared with a rebase in the helper.
         FINDING 3 -- defect 19, a real one. extract_from_reference writes
         detected walls into the scene and commits with no weld pass; per the
         corrected F5 nothing welds them later either. Every extracted plan is
         born with open junctions -- the exact condition that leaks room
         detection between spaces. Measured: 2 unwelded ends on the test_extract
         fixture. Logged -> P2.1. Note it is NOT caught by the gate (it is an
         unwelded_ends rise, which is report-only per finding 1), so it needs
         fixing on purpose.
         ON THE INVARIANT SCORE, honestly: ZERO invariant classes fired from
         app operations. Given this migration's hit rate I did not expect that,
         so I checked rather than celebrated -- which is what FP_VERIFY_DESIGN=
         deep is for. It promotes every quiescent point to all fifteen, so the
         sweep covers I5b/I11/I14 (the two that caught the real planc1
         corruption) across the whole suite, not just at save/load. Result after
         findings 2 and 3: still zero. Two honest caveats on that number -- the
         suite's scenes are small and mostly clean, and deep mode cannot run
         over the 64-room perf grid (O(rooms^2) + O(walls^2) per quiescent point
         is exactly what P1.2 split the invariants to avoid), so `-m "not perf"`.
         The acceptance run is the cheap twelve, as specced; deep is a
         diagnostic.
         CI now runs the suite TWICE per Python version, the second with
         FP_VERIFY_DESIGN=1. --verify-design on the CLI just sets the env var,
         so there is one switch however it is thrown.
         PHASE 1 COMPLETE. Ready to push (P1.1..P1.6 + the doc commits).

PHASE 1 PUSHED  (58590a2..52bd72e, 14 commits) -- CI GREEN on py3.10 + py3.13.
         Doubled suite: "Run tests" 14s / 15s, "Run tests with --verify-design"
         14s / 15s -- a clean doubling of the pytest step and nothing else
         (job total ~45s -> ~60s; the ~30s apt/pip setup is now amortised over
         two runs). NO cross-Python divergence with the flag on, which was a
         real risk worth measuring: P1.5's canonical sort keys are raw floats
         off QPointF, so a tie-break difference would have renumbered the
         document and broken the round-trip on one Python only. It did not.

```
