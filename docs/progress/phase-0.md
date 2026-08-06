# Progress log - Phase 0 - baseline, safety net, free wins

> **Moved verbatim** from `V5_MIGRATION_PLAN.md` (its lines 585-828 as of
> commit 2f232bd) on 2026-08-06. Nothing was reworded, reordered, tidied or
> reformatted; the entries appear in the order they were appended. The code
> fence below is the one the log has always been written inside - it is
> reopened here and closed at the end, because a fence cannot be split.
>
> Index: [`README.md`](README.md) - Plan: [`../V5_MIGRATION_PLAN.md`](../V5_MIGRATION_PLAN.md)

```
P0.0  done
ruff:    n/a (doc only)
pytest:  n/a
files:   CLAUDE.md
notes:   "## v5 migration (in progress)" block added verbatim after Architecture,
         before "## Generated assets". No code change.

P0.1  blocked -> resolved
ruff:    23 findings at first run — ALL in tools/ and docs/_superseded/,
         0 in floorplanner/ or tests/. Correctly reported rather than papered over.
         RESOLUTION: fixed at source (17 after dedup across the two copies),
         docs/_superseded moved to _to_delete/. ruff check . now clean.
pytest:  287 passed, 0 failed, 0 xfailed, 0 skipped in 7.59s
quick:   276 passed, 11 skipped in 6.18s
files:   tools/{validate_design,migrate_to_design_v5,make_site_demo}.py (lint only)
notes:   No test changed. Tools re-verified after the lint fixes: welds=31,
         rooms_traced=19, openings_deduped=2; symmetricP1 + site_demo PASS/PASS;
         planc1.v5 still 23 invariant errors (intended fixture).

BASELINE OF RECORD
  full   287 passed / 0 failed  in 7.59s
  quick  276 passed / 11 skipped in 6.18s
  ruff   clean over the whole tree
  15 slowest: test_extract::test_detect_walls_on_clean_plan 0.75s;
              test_extract::test_fp_extract_cli_end_to_end 0.30s;
              test_macro::test_fp_macro_cli_pup_resize 0.29s; rest <= 0.12s.
  Note: the suite is fast because nothing in it is large. No test exceeds ~5
  group members and none exceeds 36 rooms — which is precisely why P0.3 exists.

P0.2  done
ruff:    clean
pytest:  287 passed, 0 failed, 0 xfailed, 0 skipped in 6.67s
files:   FloorPlanner.py (4 private re-exports removed);
         test_inventory.py, test_coalesce.py, test_walls.py, test_rooms.py
         (direct submodule imports);
         test_rooms/test_view/test_groups/test_selection (phase comments only)
notes:   NO assertion changed — import source + comments only.
         Touches list was wrong in three ways and the code was followed instead:
         test_io.py listed but references none of the names (left alone);
         test_inventory.py (_money) and test_walls.py (_coalesce_wall_impl)
         not listed but did need the switch. Correct call.
         Phase annotations corrected after review:
           room._detect_sig  -> P3.5   (refresh_rooms memoization)   confirmed
           win._sel_order    -> P3.5   (room_boolean rewrite)        confirmed
           dup._path         -> P0.5   (NOT Phase 3 — see below)     corrected
           g._angle          -> P4.5   (group semantics)             confirmed
           view._zoom_accum  -> none   (NOT scheduled for removal)   corrected
         dup._path: test_selection's duplicate comes from select_in_rect ->
         synthesize_room_edge, which P0.5 fix 4 removes. Retired at P0.5, not
         Phase 3.
         view._zoom_accum: wheel coalescing is a deliberate, documented perf
         feature (CLAUDE.md, view.py:159-179) that the migration KEEPS and
         copies to drags. Nothing deletes it. The assertion is brittle (an exact
         accumulator value of 400) but that is a test-quality nit, not a
         migration hazard.

P0.3  done   (commit 12024f1; b00af84..12024f1 = four rollback points, unpushed)
ruff:    clean
pytest:  289 passed, 2 xfailed, 0 failed in 8.72s
         --quick: 276 passed, 15 skipped in 5.46s (harness behind `slow`, as intended)
files:   tests/test_scaling.py (new)
notes:   No existing test touched. Ratios recorded WITHOUT weakening the
         threshold, per acceptance — group and ungroup are xfail(strict=False)
         -> P3.8; rebuild and bake assert hard.
         Numbers surfaced via warnings.warn (visible under plain -ra) rather
         than print (captured and hidden unless -s). Adopted as the convention.
         FINDING: room detection is clipped to canvas_rect() (rooms.py:29), so
         the n=8 grid (960") overflowed the default 840" canvas and edge rooms
         went undetected until the canvas was enlarged. Logged as defect 16.

P0.3b  done   (commit 43e838b; step 3 landed separately, see below)
ruff:    clean
pytest:  289 passed, 3 xfailed in 9.19s
         --quick: 276 passed, 16 skipped (all 5 scaling tests skipped)
files:   tests/test_scaling.py (fifth timed op; no other test touched)
notes:   Selection-building is the worst-scaling op measured, and the one
         nothing was timing before Ctrl+G.
           select   2.7 ms (16 rooms) -> 71.8 ms (64 rooms)   ratio 27.07  XFAIL
         27 is ABOVE the quadratic reference of 16 -> confirmed O(R^2 * W): each
         setSelected fires _update_edit_actions -> _selected_room_shapes(), which
         reruns bounding_walls() (QPainterPath booleans) for every already-
         selected room. ACCEPTANCE FIGURE: selecting all 64 rooms one at a time =
         71.8 ms HEADLESS -- excludes ALL repaint cost (FullViewportUpdate, no
         setCacheMode), so the felt stall is this PLUS a full-scene repaint per
         click, i.e. strictly worse. xfail(strict=False) -> P3.8. Nuance: P3.5's
         stored outlines cut the per-room W constant, but the O(R^2) recompute
         STRUCTURE lives in _selected_room_shapes and may not clear until P4.5.

P0.3b-step3  done
ruff:    clean
files:   pytest.ini (register `perf` marker); tests/test_scaling.py (tag every
         test perf + slow); .github/workflows/ci.yml (test step -> -m "not perf")
notes:   Precondition for the first push. `perf` and NOT `slow`, deliberately:
         excluding `slow` from CI would also drop the deterministic slow tests
         (fp_extract CLI, macro CLI subprocess) worth running there. Only the
         timing-ratio assertions are unsafe on shared runners. --quick behaviour
         unchanged (scaling tests keep `slow`).

P0.4  done
ruff:    clean
pytest:  294 passed, 6 xfailed in 10.42s
files:   tests/test_characterization.py (new)
notes:   6 behaviours pinned; no existing test modified. Passes: opening-s under
         group move AND rotate; delete-wall keeps the room (2a); grouped walls
         exempt from coalesce_all; group/ungroup 4x fixed point. xfail: 2b
         delete-actually-removes-the-wall (P4.1), group survives roundtrip
         (P4.5), group+move+undo restores (P4.5).
         FINDING that reshaped the task: test 2 was predicted xfail->P4.1 but
         PASSED. Diagnosed: the room survives because the wall is never deleted
         -- fracture_delete_wall keeps the perimeter stretch and rebinds it
         (measured 4 walls in, 4 out, 0 open edges). A single "room survived"
         test passes in both today's and P4.1's world, so it proves nothing about
         the change. Split per the amended plan into 2a (invariant, asserts hard,
         must never regress) and 2b (wall actually gone: 3 built + 1 open edge,
         xfail->P4.1). Refused deletion with no message = defect 17.

P0.5  done   (5 fix commits 947ae4f..76c32ee + 1 gate-resolution commit)
ruff:    clean
pytest:  298 passed, 6 xfailed, 0 failed, 0 xpassed in 9.14s
files (source): rooms.py (fix1 RoomItem.itemChange + sip import),
         mainwindow.py (fix2 dict(it.properties); fix3 refresh_rooms_cmd active-
         floor scope), view.py (fix4 select_in_rect read-only),
         catalog.py (fix5 price overrides -> config_dir, merged on load).
TESTS ADDED (one per fix): test_rooms::test_removing_room_unbinds_its_walls;
         test_io::test_project_from_scene_copies_room_properties;
         test_floors::test_refresh_rooms_cmd_spares_inactive_floor_rooms (two
         floors, inactive-floor room survives -- per acceptance);
         test_ai_pricing::test_apply_prices_writes_config_not_manifest +
         test_price_override_reloads_from_config.
TESTS CHANGED (each a red flag, named per the working agreement):
       * fix 4 (authorised): test_selection.py's two defect-asserting tests
         rewritten to assert selection creates nothing --
         test_room_edge_on_party_wall_is_not_duplicated,
         test_party_wall_edge_selection_leaves_the_door_intact; module docstring
         updated; the P0.2 dup._path assertion retired here as scheduled.
       * fix 5 (necessary consequence): test_apply_prices_updates_manifest_and_
         catalog asserted the defect (a manifest write) -> replaced with
         test_apply_prices_writes_config_not_manifest; manifest_guard fixture
         (existed only to restore the mutated asset) -> price_sandbox (redirects
         override path to tmp); test_placed_item_picks_up_price and
         test_dialog_fetch_applies_without_network switched to it.
       * gate fallout from fix 4 (NOT anticipated in the 3 named tests):
         test_groups::test_extracted_room_region_follows_move failed -- its
         "extract via rubber-band" workflow stood on the synthesis fix 4 removed.
         Root cause: old select_in_rect synthesised the party edge AND the
         following rebuild rebound the room to that private copy, so bake's strict
         room_owns_walls could carry it. Decision (a): xfail -> P4.2, logged in
         Known regressions; label-drag (_privatize_shared_walls) is the workaround.
       * XPASS resolved: test_characterization::test_group_move_undo_restores
         (was xfail->P4.5) PROMOTED to a hard pass -- fix 2 closed it (snapshot no
         longer aliases live properties). Verified first that test 3
         (group_survives_roundtrip) is STILL xfail, so P4.5's remaining half is
         still held; comment points at test 3 as the holder.
notes:   PROCESS: after this, run the FULL gate before each commit in a multi-part
         task, not just at the end -- fix 4 committed green on test_selection.py
         alone but red on the full suite (the extracted-room test). A targeted run
         proves the fix; only the full suite shows what else it touched.

P0.6  done   (item 1 commit c9451a5 + items 2-6/harness-split commit)
ruff:    clean
pytest:  300 passed, 4 xfailed, 1 xpassed in 8.44s
files:   mainwindow.py (item 1 debounce+cheap-count selection actions; item 3
         _update_totals off scene.changed onto the 180ms dirty timer),
         items.py (item 2 GroupItem._oriented_box cache; item 5 FurnishingItem
         DeviceCoordinateCache), rooms.py (item 4 cache QFontMetricsF x2 +
         boundary stroker), tests/test_scaling.py (split select op).
BEFORE -> AFTER ratios (t(2n)/t(n), n=4->8; before = P0.6 start):
                       before        after
           rebuild     2.48          2.84         (paint items don't touch it)
           select      25.90/75.5ms  -> SPLIT:
             select_burst              5.56 / 1.1ms   HARD PASS (debounce)
             select_interactive        3.63 / 6.6ms   HARD PASS (cheap-count)
           group       12.37         10.92        (still xfail -> P3.8)
           bake         4.53          4.69
           ungroup      8.56          5.62         (item 2's _oriented_box cache
                                                    cut its boundingRect cost.
                                                    Kept xfail(strict=False)->P3.8
                                                    -- see below: the sub-8 is
                                                    incidental, not a real fix.)
ITEM 1 (the headline): selecting all 64 rooms 75.5ms -> select_interactive 6.6ms
         (~11x on the honest per-click model; ~44x on the coalesced single pass).
         Split per the amendment: select_burst (no pump; debounce does the work)
         and select_interactive (processEvents per click; cheap-count does it).
         Both clear the threshold, so both are HARD PASSES (was one xfail).
ITEM 6: measured NoIndex vs BspTreeIndex on the 64-room grid -- NoIndex wins
         every op (rebuild 3.4 vs 3.6, group 138.6 vs 148.1, bake 136.9 vs 162.6,
         ungroup 197.5 vs 229.6 ms). Default UNCHANGED, per "only if BSP wins".
notes:   Items 2-5 are paint-time wins the headless harness barely reflects
         (no repaint), so rebuild/bake/group ratios move within noise; they are
         behaviour-preserving (full suite green, no test changed except the
         harness split).
       * select_burst: CONVERTED to an absolute assertion (large < 5 ms), ratio
         assertion dropped for that op only. 0.2 ms -> 1.1 ms is timer-floor
         noise; a ratio on it is noise wearing a threshold's clothing. Fixed now
         rather than waiting for it to flap.
       * ungroup: kept xfail(strict=False) -> P3.8 deliberately, NOT promoted.
         ungroup_selected calls coalesce_all on release, which is O(walls^2) by
         construction, so ungroup is genuinely super-linear. The sub-8 at n=8 is
         incidental (item 2 cut the boundingRect constant) and reasserts at
         larger n. Promoting would encode "ungroup is fine" -- false; only "less
         bad at n=8". P3.8's topology ops replace coalesce_all.

P0.7  done
ruff:    clean
pytest:  304 passed, 4 xfailed, 1 xpassed; pytest -m io = 38 passed (corpus)
files:   floorplanner/design/ (new pkg: __init__.py, validate.py, and the
         schema moved in via git mv from docs/); tools/validate_design.py (now a
         thin CLI over the package); tests/test_schema.py (new); requirements-
         dev.txt (+jsonschema); .github/workflows/ci.yml (+corpus-validate step);
         pyproject.toml (packages += floorplanner.design; package-data += the
         schema); docs/design-schema.v5.md (pointer); path refs updated in
         CLAUDE.md, DESIGN_MODEL_v5.md, SANITY_CHECK.md, and this plan's header
         + P0.0 block.
notes:   check(doc)->list[str] ported VERBATIM (pure Python, no third-party
         import) so it is safe to call from the app; JSON-Schema validation is a
         separate schema_errors() that LAZY-imports jsonschema -- a dev/test dep
         (requirements-dev.txt), never shipped, so importing floorplanner.design
         never requires it. Corpus results: symmetricP1 + site_demo schema PASS /
         invariants PASS; planc1.v5 schema PASS but 23 invariant errors incl I6
         -- test_corrupt_fixture_passes_schema_but_fails_I6 pins that (the "does
         not launder its input" guard). test_corpus_discovered guards against a
         rename silently emptying the parametrized corpus.
         The schema MOVED (git mv, not copied) into the package as packaged data;
         docs/ keeps design-schema.v5.md as the pointer. The CLI now defaults its
         schema to the packaged one and inserts the repo root on sys.path so it
         runs from any cwd (the package is not pip-installed; tests reach it via
         conftest). Ran only P0.7 as specified -- the actions/checkout@v5 +
         setup-python@v6 bump is deliberately held for a standalone commit at the
         top of Phase 1 (changing the CI environment is a different risk class
         from adding a step, and CI runs once per push).

GATE 1  manual sanity check — PASSED (user-run, 2026-07-26)
scope:   Phase 0 complete, format unchanged, CI green py3.10 + py3.13
result:  regression sweep clean; five P0.5 fixes verified; known regression
         (party-wall room via rubber-band) confirmed as expected; selection
         responsiveness confirmed improved.
meaning: the Phase 0 safety net is validated three ways — 304-test suite, CI on
         two Python versions, and a human using the application. Phase 1 may
         proceed. Next manual gate is Gate 2, after P2.2.

CI-bump  done   (commit 58590a2, pushed alone)
         actions/checkout@v5 + setup-python@v6. Shipped alone at the top of
         Phase 1; CI green on py3.10 + py3.13, Node-20 deprecation warning gone.

```
