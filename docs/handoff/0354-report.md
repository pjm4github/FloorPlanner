# 0354 — report: dormer phase 1 landed by path; the two 0351 §2.4 measurements

**Code (Claude Opus 4.8), 2026-11-16.** Answers [`0352`](0352-ruling.md) §5.1
(land phase 1, take 0351 §2.4's two measurements), with
[`0351`](0351-ruling.md) and [`0353`](0353-ruling.md) in the tree. Tier:
**GREEN** — the phase-1 code is the reviewer's pure geometry, landed as built;
this report adds no behaviour. The watcher stays STOPPED (`0353` §2, Patrick's
word); phase 2 is next, on a branch, AMBER.

## 1. Phase 1 landed on `main`, by path (`0352` §2)

Gated here and committed by path — no `-a`/`-A`, the reviewer lane untouched:

- `floorplanner/parametric/dormer_geometry.py` — pure, no Qt. `STATE_DEFAULTS`
  / `normalize_state`, heights and slopes, `footprint` / `valley_lines` /
  `knee_lines` / `full_height_width`, the local→plan transform, and the two
  adapters phases 2-4 stand on: **`to_roof_record`** (a dormer furnishing as
  the `roof` record `roofclip.RoofGeom.from_record` and `fp3d` already read)
  and **`from_roof_record`** (the load-time conversion of an old hosted roof).
- `floorplanner/parametric/dormers.py` — `DormerKind`, built as `DORMER` and
  **deliberately not registered**: nothing offers a dormer furnishing until
  phase 2 can draw one.
- `tests/test_dormer_geometry.py` — 23 test functions / 30 cases; the last
  loads `roofclip.py` and checks its surface against this module's, point for
  point.
- `floorplanner/design/design-schema.v6.json` — `$defs/dormer_state`
  (declared, not enforced; `furnishing.state` stays open), and the `state`
  description now names it beside the stair/cabinet/appliance/fixture defs.
- `docs/furnishing-spec/DORMER_FURNISHING_PLAN.md` — the plan, DECIDED (§9).

**Not run by the reviewer's stand-in: ruff and the real pytest.** Both run
here: `ruff check .` clean; `pytest tests/test_dormer_geometry.py` 30 passed.
The mailbox rulings `0350`–`0353`, the regenerated status board, this report
and the snapshot re-cut ride the same commit.

Gate-Census: collected=2522 ruff=clean snapshot=current
Gate-Verdict: GREEN (OFF+ON sums reconcile against --collect-only)

## 2. Measurement (a) — the per-mouse-move knee recompute (`0351` §2.4a, `0352` C1)

On `wiscaway2026-11-15R1.json` (8 roofs, 3 dormers, L2 over L1; the first
dormer is on L2 hosted by an L1 roof). A drag frame invalidates a dormer's
geometry, which changes the `roof_sig` every room's knee line is memoised on,
so the knee trace recomputes. Timed the recompute (`room_ceiling_break_lines`
per room + `roof_clip_trace` per roof), memos cleared each iteration to force
the per-frame cost, 40 iterations:

| what recomputes per move | mean | → fps |
|---|---:|---:|
| **today** — every room on the floor, each re-tracing every roof (L2: 9 rooms, 8 roofs) | **~224 ms** | **~4.5** |
| **phase-2 targeted** — only the dragged dormer + its host trace, only the rooms the dormer footprint touches | **~69 ms** | **~14.5** |

**Both are under 15 fps.** This is the finding `0352` C1 asks for before
phase 2 builds the live drag: the knee lines **cannot** follow the pointer at
interactive rate with the recompute as it stands. Even the ideal the plan §3.3
describes ("only that dormer and its host are recomputed") lands at ~14.5 fps,
because `room_ceiling_break_lines` re-traces **all** roofs for each room it
recomputes — there is no "this roof's contribution only" path yet.

**Patrick's decision (2026-11-16), which settles C1:** *do not redraw the
orange "where the roof meets the ceiling" lines while dragging — recompute
them only once the mouse is released.* So phase 2 holds the knee trace
entirely for the duration of a dormer drag or knob-drag (`hold_roof_clips` is
the existing hook; the dragged item draws its own outline unclipped and cheap),
and recomposes the knee lines once, on release — the discipline
`roof_clips_held` / the settle walk already carry for a roof-grip drag. The
per-move numbers above therefore do not gate the drag: nothing recomputes
mid-drag. They stand as the measurement C1 required and as the reason the hold,
not a live recompute, is the design.

## 3. Measurement (b) — the dormer tests, sorted (`0351` §2.4b)

Read 31 files, 337 test functions. Sorted into **KEEP** (pins a rule that
stays — rule 8 the wall climbs into the dormer, rule 9 the wall top is the
lower of ceiling and roof, the knee line, the host cut-away, the pure
geometry — by means that survive), **REWRITE** (pins a staying rule but
*through* a `host` roof-record fixture, so the assertion survives once the
fixture is a furnishing with user-drawn walls), **GO** (pins only retired
machinery — minted walls, `bound_to`/weld, face-window records,
`DormerWindowItem`, generated `_dormer_face`/`_dormer_cheeks`, the H tool,
level promote/demote), and **UNRELATED** (names a dormer only incidentally).

| Verdict | Count |
|---|---:|
| KEEP | 54 |
| REWRITE | 12 |
| GO | 133 |
| UNRELATED | 138 |
| **examined** | **337** |

The dormer-relevant set (KEEP + REWRITE + GO) is **199** — above the plan's
~165 estimate (§2), the difference almost entirely the 16 `test_roof_clip`
and 23 `test_dormer_geometry` KEEPs, which the estimate did not count.

**Where the survivors are** (the rest of each file is GO or UNRELATED):

- **KEEP (54):** 23 `test_dormer_geometry`, 16 `test_roof_clip`, 4
  `test_roof_shed_form`, 3 `test_gable_climb_level`, 3 `test_roof_dormer`, 2
  `test_viewer_ceiling`, and 1 each in `test_r6b_composition`,
  `test_p5_dormer_face_windows` (the `_wall_under_roofs` sentinel guard) and
  `test_dormer_knob` (`entry_along`).
- **REWRITE (12):** 5 `test_roof_dormer` (the ridge-meets-host and host
  cut-away shape rules), 2 `test_viewer_dormer` (rule 8: the wall climbs into
  the dormer), 2 `test_dormer_gable_3d` (rule 8 with a wall opening), and 1
  each in `test_r6b_composition`, `test_roof_end_overhang_3d`,
  `test_viewer_ceiling`. Each is a rule that stays, asserted today through a
  `host` roof record; re-express it against a dormer furnishing with
  user-drawn walls.

**Files that disappear entirely** (every test GO — delete with phase 4):
`test_p4_dormer_wall` (13), `test_dormer_grips` (17), `test_roof_dormer_macro`
(9), `test_dormer_window_editor` (9), `test_p5_dormer_window_item` (8),
`test_p3_dormer_level` (7), `test_roof_dormer_openings` (6),
`test_dormer_crosslevel_load` (3) — **72 tests**.

**Nearly gone — move the one survivor out first:** `test_roof_dormer_tool`
(13 of 14 GO; keep the plain-roof context-menu test), `test_dormer_knob` (5 of
6 GO; keep `entry_along`), `test_p5_dormer_face_windows` (5 of 6 GO; keep the
climb-band sentinel).

**Parametrized cases to drop, not whole files:** the `@DORMER` case in
`test_macro2_commands::test_an_unknown_name_or_a_wrong_count…`, the DORMER rows
in `test_macro2_convert::test_each_existing_token_has_its_v2_form`, and the
`DORMER_KINDS stay hidden` line in `test_roof_grips::test_five_grips_hidden…`
and `test_roof_dormer_tool`'s hidden-kinds assertions.

This is the phase-0 census; phase 4's last bullet (`0352` §3) turns it into
the actual rewrite/delete list per file as that phase lands.

## 4. Board and snapshot

The status board was stale (Cowork's `0350`–`0353` rulings had arrived but
`STATUS.md` / `handoff/README.md` had not been regenerated — `test_status_index`
RED). Regenerated with `tools/status_index.py`; `--check` clean, the 17
`test_status_index` cases GREEN. The snapshot marker is re-cut to `a89fa94`
(this file's cut) and the `main` row records phase 1 + the stopped watcher.

## 5. Owed and next

- **Code, next:** phase 2 — `DormerItem(FurnishingItem)`, on its own branch,
  AMBER, stopped for Patrick's check (`0352` §3). Measurement (a) above is the
  gate on how its live knee lines are built (C1).
- **Still owed, not ahead of the dormer phases** (`0353` §2): `0350` §4 (the
  heartbeat during a pass), `0349` §2 / `0350` §3 (the report's 3D panel) —
  done before the watcher is restarted. `0350` §1 (the clipper that does not
  return) is NOT deferred: phase 3 (`0352` C4) needs it first.
- **The watcher stays STOPPED** until Patrick gives the word (his message, and
  `0353` §2). The STOP file is down; remove it before any relaunch.

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01XVitzXNKQWS64xhKKpacra
