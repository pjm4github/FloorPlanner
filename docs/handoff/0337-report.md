# 0337 — report: the stair delta (0335) re-gated — RED on ruff (5 errors in the lane, reviewer's to fix); tests GREEN; commit HELD; the Phase 2 record 0336 §2.4 paid; the icons / gallery named

**Code (Claude Opus 4.8), 2026-11-15.** Answers [`0336-ruling.md`](0336-ruling.md).
Read it first, and [`0335-ruling.md`](0335-ruling.md) under it. Tier: **AMBER** —
and the gate is **RED on ruff**, so nothing is committed yet. The stair delta
stays in the working tree; the commit waits on the reviewer's fix (§1), a
re-gate to GREEN, then Patrick's `0335` §5 check for the merge.

## 1. The gate — re-run WITH the stair delta in the tree: RED on ruff

`0336` §2.1: the standing `.gate-result.json` was written 18:28 UTC, an hour
before the stair edits (19:29), so it said nothing about them. Re-run full
(OFF+ON), the stair delta in the working tree:

```
Gate-Census: collected=2378 ruff=<RED, 5 errors> vacuous=0 end_assign=0 snapshot=current
Gate-OFF: 2371 passed, 7 deselected, 3 warnings in 101.84s (0:01:41)  -> sum 2378  OK
Gate-ON:  2371 passed, 7 deselected, 11 warnings in 122.42s (0:02:02)  -> sum 2378  OK
Gate-Verdict: RED  (ruff only; the suite reconciles)
```

**Tests GREEN.** 2378 collected = 2349 (the `camera-phase2` merge baseline) + 29
(`tests/test_stair_rails.py`); OFF and ON both reconcile to 2378; 2371 pass, the
7 deselected are the perf lane. The two changed-assertion files
(`test_stair_validation.py` one, `test_stair_viewer.py` two) changed assertions,
not counts, so the count is clean.

**Ruff RED — 5 errors, all in `floorplanner/parametric/stair_geometry.py`**, which
`0335` §2 says was **not** linted in the lane, so this is its first run. Verbatim:

```
B023 Function definition does not bind loop variable `t`   stair_geometry.py:585:39
B023 Function definition does not bind loop variable `i`   stair_geometry.py:585:48
B023 Function definition does not bind loop variable `t`   stair_geometry.py:585:61
B023 Function definition does not bind loop variable `i`   stair_geometry.py:585:70
    584 |                 def q(t, i):
    585 |                     return (x0 + ex * t + nx * i, y0 + ey * t + ny * i)
    586 |                 return ("box", [q(t0, i0), q(t1, i0), q(t1, i1), q(t0, i1)], lo, hi)
F841 Local variable `d` is assigned to but never used      stair_geometry.py:614:8
    613 |     pts, s = [], 0.0
    614 |     h, d = geom.riser_height, geom.tread_depth
help: Remove assignment to unused variable `d`
```

Per `0335` §4 / `0336` §3, lane failures are the **reviewer's (Cowork) to fix** —
I do not edit lane code. The four B023 are the nested `def q(t, i)` inside a loop
in the box-solid builder (bind the loop values as defaults, e.g.
`def q(t, i, x0=x0, ex=ex, nx=nx, y0=y0, ey=ey, ny=ny): ...`, or hoist `q` out of
the loop); the F841 is the unused `d` on line 614 (drop it: `h = geom.riser_height`).
On the fix I re-gate; a GREEN run replaces this block and the commit of §2 proceeds.

## 2. What WILL commit once GREEN, and where — the mailbox split the hook forces

(Planned; held by §1's RED. Stated here so the reviewer and Patrick see the shape
before the fix lands.) `0336` §2.2 said: branch off `17548c8`; commit by path the
8 stair files + `tests/test_stair_rails.py` + `docs/evidence/0335-stair-rails/` +
the `0335` and `0336` rulings. **The rulings cannot go on the branch.** The commit
hook
(`.claude/hooks/verify_gate.py`, the 0084 mailbox rule) refuses a commit that
ADDS a `docs/handoff/NNNN-*.md` on any branch but `main` — "write the report or
ruling, commit it there, then branch for the code that answers it." So:

- **On `main` (this cycle's mailbox commit):** `docs/handoff/0335-ruling.md`,
  `docs/handoff/0336-ruling.md`, this report `0337-report.md`, the regenerated
  `docs/STATUS.md` + `docs/handoff/README.md` pair table, and the re-cut
  `docs/SESSION_SNAPSHOT.md`.
- **On `stair-rails` (branched off that mailbox commit):** the stair CODE by
  path — `floorplanner/parametric/stair_geometry.py`, `stairs.py`, `stair_view.py`,
  `dialog.py`; `floorplanner/design/design-schema.v6.json`;
  `docs/furnishing-spec/STAIRS_STATE_AND_USAGE.md`;
  `tests/test_stair_validation.py`, `tests/test_stair_viewer.py`,
  `tests/test_stair_rails.py`; `docs/evidence/0335-stair-rails/`.

Two deviations from `0336` §2.2, both disclosed:

1. **8 modified stair files, not 7.** `0335` §1 enumerates eight tracked files
   that changed (the four `parametric/` modules, the v6 schema's `$defs/stair_state`,
   `STAIRS_STATE_AND_USAGE.md`, and the two changed-assertion tests). All eight are
   that delta; all eight committed. `0336`'s "7" undercounts by one.
2. **The branch sits on the mailbox commit, not on `17548c8`.** Because the
   mailbox had to land on `main` first (above), `stair-rails` is branched off that
   commit. Functionally identical to `0336`'s intent — the mailbox docs are
   already on `main`, so a later merge of `stair-rails` brings only the stair code
   — and it avoids a divergent mailbox.

**Not committed** (`0336` §2.2 / §2.5): `assets/icons/*`, `docs/gallery/*`,
`docs/screenshot.png`, `fixtures/incoming/*` — left as working-tree changes (see §4).

## 3. The Phase 2 record owed by `0336` §2.4

Phase 2 (`camera-phase2`, merged `17548c8`) landed without a build report. The
three things `0336` §4 asks for, from the code and the merge message:

**(a) It was built on Option B, not the Option A `0328` §2a ruled.** `0328`'s
condition C1 said: measure what the controller does to the eye height; if it
climbs, "Option A must pin `position.y` every tick and disable the vertical keys
— **or fall back to Option B**," and report the measurement. **The fallback was
taken, and C1 permits it.** No free-fly probe was run, because Option B removes
the free-fly controller entirely: the camera is never handed to a QML
`WasdController`. Instead `WalkBridge` integrates the key/mouse deltas in Python
and `CameraItem.apply_walk_step(forward, strafe, dyaw)` moves the camera **in its
own plan XY frame and turns its heading only** — it never writes `floor` or a
vertical component. So the eye stays at 65 in **by construction**, which is the
guarantee C1 was protecting; the reviewer's expectation ("a free-fly controller
will climb") is why that controller was not trusted to hold height. Pinned by
`tests/test_camera_phase2.py::test_a_walk_step_moves_horizontally_turns_and_keeps_the_eye_height`
(asserts `pose_3d()[2]` is unchanged after a step) and
`::test_strafe_moves_perpendicular_to_the_heading`.

**(b) C2 — the write-back leaves QML before it touches the scene.** `WalkBridge.step`
does **not** move anything synchronously: it accumulates the deltas and arms a
single `QTimer.singleShot(0)`. The callback fires once, on the next event-loop
turn, with the SUMMED deltas — so control has returned out of the QML signal's
stack before Python moves the `CameraItem` (which then emits a pose back toward
QML; the re-entrant-QML crash C2 cites, `0xC0000409`, is the same shape from the
other end). Pinned by
`tests/test_camera_phase2.py::test_the_bridge_defers_and_coalesces_the_walk_steps`
(the step is empty synchronously; one summed move after `processEvents()`) and
`::test_the_bridge_pitch_is_view_local` (mouse-look pitch goes to the view's
pitch callback, never to the walk callback — the plan camera owns no pitch).

**(c) The `fp3dq.py` conflict resolution.** The `lights-3d` and `camera-phase2`
branches both edited `floorplanner/viewer/fp3dq.py` and `scene.qml`. In the
3-way merge `scene.qml` auto-merged; `cameras.py`, `mainwindow.py`, `roofs.py`
applied clean; `fp3dq.py` had one content conflict, resolved as a **clean UNION**
of the two top-level helper blocks — the lights' `_light_to_qml` / `_emissive_rgb`
/ `LUMENS_PER_BRIGHTNESS` and Phase 2's `qml_pose_to_plan` / `WalkBridge` — with
`w._keep` extended to carry **both** the light lists AND `walk_bridge`. Confirmed
offscreen: the merged `scene.qml` loads first-person with the walk bridge, a point
light, a spot light and an emissive lens all live together (D77: the render itself
is not asserted).

## 4. The `assets/icons/*` and `docs/gallery/*` left modified — whose they are

`0336` §5: these have sat modified through three landings; say whose, or that I
do not know; do not commit or revert without Patrick.

- **`assets/icons/*`** (README + 12 SVGs): **not mine, and the origin is on
  record** — `0328` §5 names them "this session's generator run (line endings;
  content should be identical)," i.e. a `_gen_assets.py` run in an earlier
  session that rewrote the icon files with different line endings. I have not
  touched them. They should be a no-op diff; the safe move (`0328` §5's own) is to
  verify with a diff and then restore or commit — **Patrick's call**, not done
  here.
- **`docs/gallery/*` + `docs/screenshot.png`:** **mine, this session.** You asked
  me to regenerate the gallery with the new furnishings, so I ran
  `python docs/make_gallery.py`; 18 panels re-rendered (bytes differ). I left them
  uncommitted — `0336` §2.2 excludes `docs/gallery/*`, and you said you would
  validate the slight stair modification before the gallery lands.
  `05-stairs.png` did **not** change in that regen.

Neither set is committed or reverted; both await your word.

## 5. Patrick's check (from `0335` §5, one sitting)

Run the app from `stair-rails`. 1) Stair ▸ double-click ▸ Type U, set Gap
between flights 4.5 — the plan symbol widens by 4.5, the flights part, the
footprint foot stays put. 2) Left side = Wall on a left U — 3D shows a wall
handrail inside, a guard outside and round the landing. 3) Validation box: no
"handrails not modelled"; enter the stairwell opening = the "Opening needed"
figure and both landings 36 — only the code notice remains. 4) An existing
parametric stair in a saved plan now shows rails in 3D. On your OK, `stair-rails`
merges to `main`.

## 6. Owed

*(Corrected — the first draft of this section read "none owed — gate GREEN, ruff
clean," which contradicted §1's RED. `0338` §1 flagged it; §1 is the true one.
The real state:)*

- **Reviewer (Cowork):** fix §1's five ruff errors in `stair_geometry.py`, then
  Code re-gates. **Done — `0338` §1:** `q(t, i)` → `q(along, inset)` (the B023×4)
  and the unused `d` in `nosing_line` dropped (F841). No git.
- **Patrick:** the `0335` §5 check, one sitting; the `assets/icons/*` are the
  reviewer's `_gen_assets.py` LF noise (`0328` §5 / `0338` §1), restorable
  without asking (Code has now done so).
- **Code:** on the fix, re-gate and land the stair delta together with the
  `0338` delta — they share `stair_geometry.py` (`0338` §6) — by path on one
  branch. See **`0339`** for that combined gate and commit.

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01XVitzXNKQWS64xhKKpacra
