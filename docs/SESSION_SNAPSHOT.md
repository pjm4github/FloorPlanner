<!-- SNAPSHOT-HEAD: 366c78e -->

# Session snapshot — read this first

**Re-cut 2026‑08‑12 for the gate condition below, and kept current by the gate
ever since.** **Trimmed to its stated job 2026‑08‑16, Patrick's ruling —
[`handoff/0028-ruling.md`](handoff/0028-ruling.md).** The file had grown to 621
lines by accumulating narrative that already lives in `handoff/`, `defects/`
and `WORKING_AGREEMENT.md` — the ruling's own measure: *"an index that
summarises the thing it indexes has stopped being an index."* Only §1 (state)
and §5 (traps) stay dense by design; everything else is now a pointer.

This file exists so a fresh session can start from disk instead of from a chat
summary. It is an **index and a state marker, not a second copy of the record** —
where it points at another document, that document is authoritative and this one
must not be trusted over it.

> ### THIS FILE'S STALENESS IS NOW A GATE CONDITION — 2026‑08‑12, Patrick's ruling
>
> **`tools/gate.py` fails if the `SNAPSHOT-HEAD` marker above is not the current
> tip**, in **full mode** as well as `--docs` — full mode, because that is the
> only one that writes `.gate-result.json`, which is the only thing the commit
> hook reads. A check living only in the docs lane would be one more thing
> nobody runs, which is the exact failure it exists to close.
>
> **Why it took a gate.** The previous cut carried, in bold at its line 9, a
> note saying a stale §1 had once sent a reader down the wrong queue and that
> *"the cost is paid at every reset."* **It then went stale itself, in the same
> section, in the same way, and the warning did nothing** — eight commits, and
> an archaeology pass to establish what was true. **A warning is a note to a
> reader; staleness is a property of the file.** The only two things that have
> ever fixed this class here are **generation** (`defects/INDEX.md`, `--check`)
> and **a gate that fails**. This is now the second.
>
> **The semantics, which are not the obvious ones.** The marker records the
> commit this file was cut **against** — the tip at gate time, which is what the
> pending work is built on, not the commit about to be made (which has no hash
> yet). **The marker may name HEAD or its parent**, and that one commit of slack
> is not leniency: the gate runs *before* a commit, so the instant that commit
> lands the marker is one behind. **An exact-match rule would leave the
> repository RED AT REST** — red after every correct commit, red for CI on every
> push (CI calls this tool with `--deep`, which runs the check), red for the next
> session before it had done anything wrong. **A gate that is red in its resting
> state trains people to ignore it**, which would rebuild this very problem in a
> louder form. Worst-case drift is **two** commits, against the **eight** it
> reached.
>
> **What it does not do:** it cannot check that anyone re-read the content. It
> makes this file impossible to ignore, not impossible to update carelessly —
> which is why the gate asserts the marker and the `main` row in §1 carry the
> **same** hash, so the marker cannot be bumped while the prose beside it goes
> on lying.
>
> **On a PR's merge-ref checkout** (`refs/pull/N/merge`), `HEAD` has two
> parents and the check reads `HEAD^2` instead — [D78](defects/0078-the-snapshot-staleness-gate-cannot-pass-on.md),
> gated on `GITHUB_EVENT_NAME == "pull_request"` so a genuine merge commit on
> `main` is never misread the same way. `tools/gate.py`'s own docstring on
> `_snapshot_checkout_base` carries the full reasoning.

> **[`README.md`](README.md) is the map** — what each document is, which decide
> things, which are history. **[`ROADMAP.md`](ROADMAP.md) is the autonomy
> charter** — which items may proceed without Patrick and which may not, and
> **§3 is the full tiered work queue** this file no longer restates.

---

## 0. WHERE THE WORK IS

> **Trimmed again 2026‑10‑03, on Patrick's word — [`handoff/0203-report.md`](handoff/0203-report.md).**
> This section had regrown to 18,600 characters of closed-tranche narrative
> and §1's `main` row to 13,000. Both now say **where the work is and where
> to read the rest**. Nothing was moved anywhere new: every sentence removed
> restated a numbered report. The text as it stood is at
> `git show 52a2870:docs/SESSION_SNAPSHOT.md`. **Keep it this size:** when a
> tranche closes, REPLACE its entry with one line and a link; do not append.

**NOTHING IS OPEN ON A BRANCH. THE ROOF-WRAP TRANCHE IS MERGED — [PR #81](https://github.com/pjm4github/FloorPlanner/pull/81) at `37b58d6`, AMBER, on his word after his own check ("the dormers look right"), recorded at [`0246`](handoff/0246-report.md): the lower roof runs under the overhang ([`0241`](handoff/0241-report.md)), nothing of roof hangs from a roof's edge ([`0242`](handoff/0242-report.md), [`0243`](handoff/0243-report.md)), the dormer's sides and face are projected up from the roof ([`0244`](handoff/0244-report.md), [`0245`](handoff/0245-report.md)); his three short-angle designs are fixtures. 0241 §2's reach on the three-ridge and two-level fixtures is RULED — the rule stays as it is, his word at [`0247`](handoff/0247-report.md). HIS HOUSE PICTURE BUILT AS A DESIGN — `fixtures/incoming/house_cutout.json` (clean), four iterations with renders in `incoming/house_cutout_work/`, nine tool shortfalls measured and A–E PROPOSED for the roof and dormer tools — [`0248`](handoff/0248-report.md). HE ORDERED A AND C: MERGED — [PR #82](https://github.com/pjm4github/FloorPlanner/pull/82) at `c93c392`, AMBER, on his word after his own check ("The dormers and roofs look right"), recorded at [`0251`](handoff/0251-report.md): the `shed` roof form, a shed's ends never joined, a dormer's generated side or face yielding to a house wall ([`0249`](handoff/0249-report.md), [`0250`](handoff/0250-report.md)). The house model is iteration 9 in `incoming/` (his plan, three roof blocks at 45°, the shed dormer's top on the gables' ridge line), uncommitted, his to keep. HE ORDERED B AND D: MERGED — [PR #83](https://github.com/pjm4github/FloorPlanner/pull/83) at `32fd37d`, AMBER, on his word after his own look at the shots ("The dormers and roofs look right"), recorded at [`0253`](handoff/0253-report.md): openings on a dormer record cut into its generated face (B), the equal-height ridge meeting in the clip (D), and the app's own Quick3D view taking a shot with a settable camera and lens (`fp3dq.py --shot --yaw --pitch --zoom --fov`) ([`0252`](handoff/0252-report.md)). ITERATION 10 OF THE HOUSE DONE — [`0254`](handoff/0254-report.md): the gable faces were solid because a first-floor gable wall's header climbed through the second storey and its window (the gable climb had no level check; the dormer's did); FIXED on branch `roof-gable-climb-level`, ONE commit, AMBER, WAITING ON HIS CHECK — the climb stays on the wall's own level; the dormer windows then sized to the picture ("4860", "2460", sills on the 48″ knee wall), `house_cutout.json` was iteration 10. HIS FOUR FIXES BUILT — [`0255`](handoff/0255-report.md): the End-On dialog on the porch's shed roof no longer takes the app down (a division by the shed's zero right span in the canvas's paint; the canvas draws a shed now), the window's sill is a property on its sheet with a plan default (`DEFAULT_SILL_IN`, 36″; carried by the item, the bridge, every copy path), the schema audited against everything the app writes (a gate's swing was dropped on save — fixed; `sill_in`/`head_in` described), and iteration 11 of the house with the windows at the picture's elevations and heights (`house_cutout.json`); on `window-sill-endon`, ONE commit, STACKED on `roof-gable-climb-level`, pushed, NO PR — his word: land in turn, or fold into PR #84. HIS REPORT ON THE SHED DORMER'S DIALOG — [`0256`](handoff/0256-report.md): the End-On dialog refused every correctly placed shed dormer ("never meets the host roof", OK dead) because R5b's meeting rule is a gable dormer's and a shed dormer's high edge lies ON the host; a shed dormer now stands while the host is at or above its edge at both ends, nothing derived, both ends faces; and its RIDGE GRIP no longer creeps an inch toward the eave on every move (the gable rebalance's clamp with no right span to give) -- a shed's ridge is its high edge, the eave stays, the span follows; folded into this one commit. HIS WORD after his own check of the shed dormer ("the shed dormer looks right, fold and land #84"): `window-sill-endon` FOLDED into `roof-gable-climb-level` (fast-forward) and `main` (`caab2c0`, [`0255`](handoff/0255-report.md) and [`0256`](handoff/0256-report.md) landed) merged in; MERGED as [PR #84](https://github.com/pjm4github/FloorPlanner/pull/84) at `7a0a4bf`, AMBER, recorded at [`0257`](handoff/0257-report.md); both branches deleted. HIS WORD ON E AND THE HIP RUN ("Go ahead"): BUILT — [`0258`](handoff/0258-report.md): `hip_run_in` per ridge end on the record, the item, the clip twin, the 3D builder, the End-On dialog's two run fields and the bridge (null = the mean of the spans, as before); a `post` furnishing (form `column`) that the 3D builder runs from its level to the underside of the roof over it; the porch floor as an exterior room (no new kind); iteration 12 of the house (`house_cutout.json`: the porch floor, eight posts, 48" end hips); MERGED as [PR #85](https://github.com/pjm4github/FloorPlanner/pull/85) at `180c486`, AMBER, on his word after his own check ("the porch looks right"), recorded at [`0259`](handoff/0259-report.md); the branch deleted. Not built: 0248's items 8 and 9 (steps and base; a porch roof turning a corner), not ordered. THE COMPOSE COST BUILT on his word ("Go ahead with the cost tranche from the patch") — [`0260`](handoff/0260-report.md): the clipper's arrangement built from one set of disjoint cells (a roof's lines cut only the cells its domain can reach) and a neighbour graph once per piece list for the reach walk — 15 roofs 32 s → 8 s, 12 roofs 5 s → 1.7 s; the first cut's double-counted region measured and closed, every promoted fixture's ground pinned unchanged against a record taken before, the cells pinned disjoint; his second ask pinned as a test (the clip sees roofs alone); MERGED as [PR #86](https://github.com/pjm4github/FloorPlanner/pull/86) at `95ebc65`, AMBER, on his word after his own check ("the roofs look right"), recorded at [`0261`](handoff/0261-report.md); the branch and the parked patch deleted. HIS `wiscaway2026-10-11R2.json` GIVEN THE SHED DORMER AND THE PORCH ROOF as the house's iteration 11 has them — [`0262`](handoff/0262-report.md): a new file beside his in `incoming/`, nothing of the tools changed; CHECKED by him ("the dormer and porch roof look right"), changed by him in the app and RENAMED on his word to `wiscaway2026-10-11R3.json` (the script and shots in `incoming/wiscaway_r2_work/`); exit his to name. HIS FOUR FEATURES BUILT — [`0263`](handoff/0263-report.md): annotations (text, the T tool), measurements (the L tool: each end snapped to an item, one thin line with a slash at each callout point, feet-and-inches or inches, a datum per level), the items' callouts in a settable colour (default blue, the layer off until asked), and a Show menu switching each on its own; the schema's `annotations` block given its writer and reader, `SETTINGS_VERSION` 3; on `annotations-measure`, ONE commit; HIS REVIEW ANSWERED — [`0264`](handoff/0264-report.md): the item callouts are the items' DOCUMENT IDS (what the problem report names and the wall dialog shows), stamped by a load and by every settle's walk, on when a plan opens; the measure's four red knobs (move a callout point, Ctrl rotates about the other on the snap, Shift frees; the end slides along the line; the label slides), the selection tight; folded into the one commit; HIS WORD ON THE CALLOUTS — [`0265`](handoff/0265-report.md): the SESSION LABELS always (W7, V12, O3, R2, F4, RF1, one mint in `labels.py`), adopted from the file's own ids when a plan opens so the two match, the Malformed-design report translated to them, both shown only while that report is open and they differ; folded in; the knobs made small, black and fixed in pixels on his screen; MERGED as [PR #87](https://github.com/pjm4github/FloorPlanner/pull/87) at `aacccc2`, AMBER, on his word after his own check ("the measurements look correct ... the knobs look right"), recorded at [`0266`](handoff/0266-report.md); the branch deleted. HIS ANNOTATION-DISPLAY CLEAN-UP BUILT — [`0267`](handoff/0267-report.md): ONE font size (nine view pixels at any zoom) and ONE colour for every item annotation — wall, corner, opening, room, furnishing, roof — through `callout_font`/`draw_callout` in `annotations.py`; the opening's session label on the other side of the wall from its size code, the room's painted last so the fill does not tint it, the furnishing's unclipped; on `item-annotations-font`, ONE commit; HIS TWO PDF ASKS BUILT — [`0268`](handoff/0268-report.md): the plan set renders the plan's DRAWN dimensions (each as the screen draws it, in the plan's units) in place of the auto rows and lanes when a level has any and Show ▸ Measurements is on, the rows as before otherwise; its text annotations only while Show ▸ Annotations is on; on `pdf-drawn-dims`, ONE commit STACKED on it; BOTH MERGED as [PR #88](https://github.com/pjm4github/FloorPlanner/pull/88) at `d4083ba` after the fold, AMBER, on his word after his own check of both ("The export looks good. The Item Font side looks good"), recorded at [`0269`](handoff/0269-report.md); both branches deleted. THE LEADER ANNOTATION BUILT on his word ("add a leader annotation") — [`0270`](handoff/0270-report.md): a text with an arrow to the thing it names (the N tool: the point snapped as a measure's end, the text end on the grid, the text asked for; a filled arrowhead, a shoulder under the text, two knobs, double-click edits; the schema's reserved `leader` kind given its item; on the PDF sheet by the Show switch); on `leader-annotation`, ONE commit; his mid-build words folded into it: the annotation tools in BOTH macro recorders and the player — the letters T, L, N and the commands `@TEXT`, `@LEADER`, `@DATUM` carrying the dialogs' values. THE DOCUMENTS AND THE SCHEMA BROUGHT TO THIS `main` AS VERSION 6 on his words — [`0271`](handoff/0271-report.md): the schema file renamed `design-schema.v6.json` (title, id, a version description naming what 6 holds; 5 still accepted), every document the app writes version 6; `README.md` rewritten to this `main`, **`docs/COMMANDS.md`** new — every tool, key, menu, context menu, dialog, macro token, application command and command-line program with an example each — the docs map, the architecture roster, the model, the sanity check, `CLAUDE.md` and `tests/README.md` brought up; on `docs-v6`, ONE commit STACKED on it; BOTH MERGED as [PR #89](https://github.com/pjm4github/FloorPlanner/pull/89) at `9be6e0b` after the fold, AMBER, on his word after his own check of both ("the leader and docs look right, fold and land #89"), recorded at [`0272`](handoff/0272-report.md); both branches deleted. THE GALLERY REGENERATED on his words ("regenerate the gallery with roofs, annotations and 3D frames") — [`0273`](handoff/0273-report.md): the demo house given a gable with a dormer, a hip and a shed; four new frames — the roofs with their grips, the End-On dialog, the annotations (text, measures with the knobs, leader, datum, item callouts), the Qt Quick 3D view shot in its own process on the windows platform; the classic frames keep their look; on `gallery-frames`, ONE commit; MERGED as [PR #90](https://github.com/pjm4github/FloorPlanner/pull/90) at `bcad46c`, fast-forward, AMBER, on his word ("this code looks good at the moment"), recorded at [`0274`](handoff/0274-report.md); the branch deleted. NOTHING IS OPEN ON A BRANCH. THE UI'S SLOWNESS UNDER A DRAG MEASURED on his words — [`0275`](handoff/0275-report.md), an analysis and a recommendation, NO CODE CHANGED: 3 frames a second on his two-floor plan, the grip's handler 0.5 ms of a 330 ms frame, 214 of a repaint's 246 ms in `roof_clip_trace` recomputed from scratch in every roof's `paint()` (5.9 million point-to-edge distances a drag), and the 180 ms settle walk firing inside the drag because the frame outlasts it; RECOMMENDED: cache each roof's clip trace on its own geometry and a rooms epoch (measured 3 → 22 fps), the walls' roof-clip dashes likewise, the settle walk held while a grip is down, then `MinimalViewportUpdate` with his eye on it; the probes and their output in `docs/evidence/0275-drag-timing/`. HIS WORD ("Go ahead with steps 1 to 3"): BUILT — [`0276`](handoff/0276-report.md): the roof clip trace cached on exactly what it reads (`RoofItem.clip_trace`, `floor_rooms_key`), the walls' roof-clip dashes likewise, the settle walk held while a roof gesture holds the clips; AND A SECOND FAULT FOUND AND FIXED, from 0264: the settle walk's unconditional callout repaint re-armed its own timer — a walk and a full repaint every ~280 ms, idle; measured 3 → 15–26 fps on the drags, the idle loop gone; still slow and named, not built: a drag that moves walls or rooms under roofs (7 fps, every roof over it rightly recomputes; R6.b's hold is the way); on `drag-speed`, ONE commit; MERGED as [PR #91](https://github.com/pjm4github/FloorPlanner/pull/91) at `7319fe4`, fast-forward, AMBER, on his word ("the drag-speed seems fine on #91"), recorded at [`0277`](handoff/0277-report.md); the branch deleted. HIS GARAGE ROOF'S DEAD KNOB — [`0277`](handoff/0277-report.md): the garage gable in `wiscaway2026-10-13R1.json` is a dormer of the main roof whose face stands 48″ past the host's eaves, so the back-end knob measured its reach from outside the host (0.0) and refused every move silently; FIXED on `dormer-knob` (the reach measured from where the ridge enters the host, `roofclip.entry_along`; a refused drag says why in the status bar), ONE commit; MERGED as [PR #92](https://github.com/pjm4github/FloorPlanner/pull/92) at `c8de4ef`, fast-forward, AMBER, on his word ("the knob works now"), recorded at [`0278`](handoff/0278-report.md); the branch deleted. THE WALL-AND-ROOM DRAG HOLD AND REPAINT-ONLY-WHAT-CHANGED BUILT on his words — [`0279`](handoff/0279-report.md): a left button down on the plan holds the floor's rooms for the roof traces and wall dashes (`roofs.hold_rooms`), the release repaints once, the settle walk waits for the gesture; the view runs `MinimalViewportUpdate` after an audit of every item's box (furnishing callouts, a gate's swing, a roof's ridge callout, the ridge grip and the measure fixed) and a probe that emulates the screen on eleven kinds of drag (0 stale pixels); wall, furnishing and opening drags 5–12× faster; on `drag-hold-minimal`, ONE commit; MERGED as [PR #93](https://github.com/pjm4github/FloorPlanner/pull/93) at `9a51df6`, fast-forward, AMBER, on his word ("the drags look right ... land #93"), recorded at [`0280`](handoff/0280-report.md); the branch deleted. HIS SLOW CTRL+Z — [`0280`](handoff/0280-report.md): undo reloads the whole document as new objects, and the reload recomposed all 15 roofs and threw away their traces though the edit touched no roof (3.6 s on his R1 plan); FIXED on `undo-fast` by keeping the compose and the traces BY VALUE (0.34 s); undo by command (P6.b) named for the rest; on `undo-fast`, ONE commit; MERGED as [PR #94](https://github.com/pjm4github/FloorPlanner/pull/94) at `1a0d5cf`, fast-forward, AMBER, on his word ("undo works now"), recorded at [`0281`](handoff/0281-report.md); the branch deleted. HIS "UNDO BY COMMAND" — [`0282`](handoff/0282-report.md), A CORRECTION FIRST: P6.b as built is a memento stack, so wiring it would not make undo faster (the claim after 0280 was wrong); BUILT what did not depend on the choice: the walk after a restore removed (0.34 → 0.26–0.28 s; the walk before an undo kept, its skip refuted by the suite); on `undo-restore-walk`, ONE commit; MERGED as [PR #95](https://github.com/pjm4github/FloorPlanner/pull/95) at `6ed6049`, recorded at [`0283`](handoff/0283-report.md). HIS CHOICE, OPTION A — UNDO BY DIFFERENCE BUILT [`0283`](handoff/0283-report.md): the apply's building blocks moved verbatim into shared helpers; `bridge.apply_design_difference` compares the shown and restored documents by content with ids removed (references resolved, vertex sharing counted) and rebuilds per level only the web, furnishings and annotations that differ, the roofs as one roofscape, declining to the full reload whenever unsure (settings, levels, groups, cross-level vertices ...); undo 0.27 → 0.17 s on his R1 plan; on `undo-diff`, ONE commit; MERGED as [PR #96](https://github.com/pjm4github/FloorPlanner/pull/96) at `bc68e43`, AMBER, on his word ("land #96, the cntrl+Z looks good!"), recorded at [`0284`](handoff/0284-report.md); the branch deleted. THE PLAN'S ANNOTATIONS IN THE DXF AND THE CHIEF SECOND-FLOOR PROCEDURE: MERGED as [PR #97](https://github.com/pjm4github/FloorPlanner/pull/97) at `ea5a4bc`, AMBER, on his word ("The DXF import into Chief Architect works well"; "Land #97 now"), recorded at [`0285`](handoff/0285-report.md)–[`0287`](handoff/0287-report.md). DORMER PLAN CONTROLS (A–G), THE HOST-UNDER-OVERHANG 3D FIX, THE APEX MARKER MENU (edit/delete/outline), THE DORMER OUTSIDE WALLS DRAWN AT `EXTERIOR_T`, the `partition` AND `beam` WALL TYPES (both dashed in plan — beam timber-brown, partition grey; a partition divides rooms but builds no 3D volume, a beam is a 3D ceiling beam that does not divide a room), AND THE NON-MODAL WALL-GAP REVIEW TOOL (Zoom to problem draws a red box, Rescan re-detects): MERGED as [PR #98](https://github.com/pjm4github/FloorPlanner/pull/98) at `23237a0`, AMBER, on his order "accept the PR and merge this branch into main", recorded at [`0288`](handoff/0288-report.md); the branch deleted. THE REVIEW-WALL-GAPS FIX: a wall is no longer listed as a gap (its two ends are 6" apart because it is a 6" wall, not a near-miss -- `near_vertex_gaps` excludes a pair joined by a wall), and each gap now names its two VERTICES and the WALL(s) each holds in the plan's session labels; MERGED as [PR #99](https://github.com/pjm4github/FloorPlanner/pull/99) at `0438669`, AMBER, on his word ("The gaps look right, merge #99"), recorded at [`0289`](handoff/0289-report.md); the branch deleted. DORMER GABLE ENDS & SHED FRONTS CLOSE IN 3D (Phase A of a single-record dormer-window plan): a wall piece under a same-level dormer climbs to the dormer's surface (`_wall_under_roofs.dormer_over`), closing the gable, instead of capping at the lower host it stands on; a window in the wall stays a void (no dormer face generated, so the 0248 invariant holds); MERGED as [PR #100](https://github.com/pjm4github/FloorPlanner/pull/100) at `617182b`, AMBER, on his word ("Land #100 now"), recorded at [`0290`](handoff/0290-report.md); the branch deleted. PHASE B -- CROSS-LEVEL DORMERS BUILT: a dormer is drawn and edited on the storey its gable occupies while its host roof is a floor BELOW -- `roofs.host_roof_at` looks DOWN a level (`_floor_below`) when no host is on the drawn floor, `view.py` sets a new dormer's `floor` to the DRAWN floor (`active_floor()`), and `fp3d.build_model` lifts a dormer by its HOST's level base (`_lift_base`/`host_of`/`level_of`) so re-levelling the drawn floor doesn't move it, while the same-level climb still brings that floor's wall and window into the gable; the dormer record stays single-source. MERGED as [PR #101](https://github.com/pjm4github/FloorPlanner/pull/101) at `7857a7f`, fast-forward, AMBER, on his word after his own check ("that looks good lets merge"), recorded at [`0291`](handoff/0291-report.md); the local branch deleted, the remote head's ref cleanup held for an approved retry. NEXT (ruled with him, not built): Phase C -- a dormer's windows shown as a READ-ONLY SHADOW on the floor it is drawn on (that floor's own storey windows stay normal); then Phase D (floor-below in-place gable editing that syncs back) and Phase E (cheek walls projected into the floor). PHASE C MERGED as [PR #102](https://github.com/pjm4github/FloorPlanner/pull/102) at `e584c29`, fast-forward, AMBER, on his word ("Land #102 + fix load bug, then wall-gable windows"), recorded at [`0292`](handoff/0292-report.md); the branch deleted. The editor (a window list in the End-On dialog, dormers only) writes the dormer's single `openings` record; the plan shadow (`RoofItem.dormer_face_window_spans()`) draws them read-only. His check surfaced two things (0292 §2): the dormer-FACE window renders only for a SET-BACK dormer (his cross-gables form the gable from a climbing wall, so `fp3d` builds no face and a face window shows nothing in 3D — 0 mesh change measured), so a gable-end window belongs on the floor-above WALL; and a cross-level LOAD BUG (`bridge.py:1516` drops a dormer whose host is a floor below). THE LOAD BUG IS FIXED AND LANDED — PR #103 at `3761819` ([`0298`](handoff/0298-report.md)). THEN HIS SPEC REVIEW PRODUCED THE **1½‑STOREY ARC** — charter [`0297`](handoff/0297-ruling.md), sources [`0293`](handoff/0293-ruling.md)–[`0296`](handoff/0296-ruling.md): a roof governs by ABSOLUTE height, not level identity; a dormer has ONE datum (its host's), its `level` only its editing home (3D never reads it after P1); windows live in the dormer's `openings` record (0294); the dormer's face/cheeks become a `dormer` WALL type on the storey above (0296). Five AMBER phases, each its own branch on the previous: **P1** the stacked climb (3D, `_wall_under_roofs` by absolute height); **P2** the dash + the knee line (plan); **P3** the dormer's level/datum/dialog and the four views (0295); **P5** windows on the dormer face (editor + the plan `DormerWindowItem` + the 3D cut into the climbing wall); **P4** the `dormer` wall type. Check session A after P1–P3, B after P5–P4. CHECKPOINT 0 CLOSED ([`0298`](handoff/0298-report.md)): the load fix recorded, the three unmeasured items of 0293 §1 measured, `_to_delete/` emptied. P1 — THE STACKED CLIMB (3D) — BUILT on branch `p1-stacked-climb` ([`0299`](handoff/0299-report.md)): `_wall_under_roofs` grants the gable/dormer climb by ABSOLUTE height from any level (`dormer_over` any-level, the `same_level` gate gone), BOUNDED at the storey-above base where that storey stands over the piece (`_on_a_wall` reused, or an `_wall_loops` room). Receipts on his `wiscawayL2-fix.json` (he reset L2 height to 96; L2 base 120): doubled L1/L2 **7→0**, L2 climbs **0→14**, highest L1 top under an L2 piece **289.5″→120″** (= L2 base), the `8048` L2 gable window a **VOID**; `dormer-test.json` byte-identical; one changed assertion named (0299 §4). AMBER, not merged — the merge of P1–P3 waits on his check session A. P2 — THE DASH AND THE KNEE LINE (plan) — BUILT on `p2-dash-knee` (stacked on P1, [`0301`](handoff/0301-report.md)): the R3b wall dash (`roof_clip_spans`) reads every roof in ABSOLUTE height (an L2 wall under the L1 roof now dashes — L1 9→9, L2 5→19), and the KNEE LINE (`room_ceiling_break_lines` + `RoomItem.paint`) shows where a roof crosses a room's ceiling plane (his BR2/BR3 at y=756, from rf1's record). AMBER, not merged. P3 — THE DORMER'S LEVEL/DATUM/DIALOG AND THE FOUR VIEWS (0295) — BUILT on `p3-dormer-level` (stacked on P2, [`0302`](handoff/0302-report.md)): a dormer's `level` is its editing home only, promotable between its two legal levels (host's own and the one above) by the End-On dialog's "Edited on level" selector and the apex-marker "Move to level" menu (`legal_dormer_levels`, `move_dormer_to_level`, the `MOVEDORMER` macro word); its 3D datum stays the HOST's base regardless of level (the two level-reading sites in `fp3d.build_model` fixed — the roof section's `z0` and the cheek/face `near` walls both read the host, so a promotion is BYTE-IDENTICAL in the model, proven in `docs/evidence/p3-dormer-level/`); the dialog's heights read from the host's base (M1 closed); the dormer shows and is hittable in all four views (both legal levels' plans, the End-On dialog, 3D); the schema's `roof.host`/`roof.openings` text corrected. HIS CHECK SESSION A FOUND THREE BUGS, FIXED ON THE BRANCH: (1) a cross-level dormer lost its `host` on save (`_roofs_of` names a host by the id its own level minted, but a host a storey below is in another level's bucket — the link was dropped and 3D re-datumed the dormer to its own level, a storey-high POP-UP); `design_from_scene` now resolves every dormer's host ACROSS all levels; (2) the End-On dialog opened taller than the desktop — its fields are now two columns; (3) a promoted dormer drew an INCOMPLETE ghosted outline on its host level (`RoofItem.paint` gated the whole dormer branch on `not ghost`) — now it paints the full outline in the ghost ink. **P1–P3 MERGED into `main`** on his word ("the ghosted outline on L1 looks complete now, merge P1–P3"), a two-parent merge of `p3-dormer-level`, recorded at [`0303`](handoff/0303-report.md); `dialogs.py`/`levels.py` keep BOTH #104's derived-base and P3's work (auto-merged). NEXT in the arc: P5 (windows on the dormer face), then P4 (the `dormer` wall type); check session B after. 0248's items 8 and 9 BACKLOGGED on his word (below, named not ordered). D88 is FIXED and MERGED, PR #80 ([`0237`](handoff/0237-report.md), [`0238`](handoff/0238-report.md)). The roof-editor lock-up he reported measured as compose cost doubling per roof (15 roofs: 32 s a release), no hang (0237 §0); CLOSED by PR #86 (8 s at 15 roofs). D87 is MERGED, PR #79 ([`0236`](handoff/0236-report.md)). THE 3‑INCH REACH IS CLOSED AND MERGED** —
[PR #71](https://github.com/pjm4github/FloorPlanner/pull/71) landed on `main`
by this merge commit on Patrick's word (2026‑10‑04: "OK that fix is good. commit and push # 71."),
the branch deleted in the merge step; recorded at
[`0211-report.md`](handoff/0211-report.md). Grid snap by default is closed with it: a wall
gesture lands on the grid; within 3″ of another wall's end or line it goes
to that instead; Shift turns both off. **MACRO LANGUAGE v2 IS IN — his spec,
[`docs/macro-spec/MACRO_SPEC.md`](macro-spec/MACRO_SPEC.md); the read-back and his
three answers, [`0212`](handoff/0212-report.md).** A macro whose first line is
`; fpmacro 2` runs on `floorplanner/macro2/`; anything else runs on
`MacroRunner`, untouched. Merged: the language (PR #72,
[`0213`](handoff/0213-report.md)), and — folded into ONE PR on his word and
merged by this commit ("fold all three into #73 and merge"), [PR #73](https://github.com/pjm4github/FloorPlanner/pull/73) —
the player ([`0214`](handoff/0214-report.md)), application commands
`@NAME arg …` ([`0215`](handoff/0215-report.md)) and the v2 recorder
([`0216`](handoff/0216-report.md)). The merge is recorded at
[`0217-report.md`](handoff/0217-report.md). **The spec's six tasks are DONE:** the
legacy converter (`fp_macro.py --convert`), the v2 docs, whole-line top-down
Replay and the recorder window's line numbers merged as
[PR #74](https://github.com/pjm4github/FloorPlanner/pull/74) on his word
("line numbers look good, push the branch and merge") —
[`0218`](handoff/0218-report.md), [`0219`](handoff/0219-report.md). **The error indicator in that gutter, and his rule that a v2 error lets
the lines before it run and stops there (spec sec8.3 amended), are MERGED —
[PR #75](https://github.com/pjm4github/FloorPlanner/pull/75), on his word
("Go ahead and land # 75"); [`0220`](handoff/0220-report.md),
[`0221`](handoff/0221-report.md), the merge recorded at
[`0222`](handoff/0222-report.md).**
`MacroRunner` and the committed `.fpm` files are not
touched. **The four-way crossing fault ([`0208`](handoff/0208-report.md) §4) is
CLOSED AS NOT REPRODUCED, no defect, on his word ("close it as not
reproduced, no defect") — 96 runs, one state ([`0226`](handoff/0226-report.md),
[`0227`](handoff/0227-report.md)); the instrument stays in `docs/evidence/`.**
**MERGED as [PR #77](https://github.com/pjm4github/FloorPlanner/pull/77), three tranches folded
on his word ("wall properties look right, fold all three into #77 and land"):**
parallel walls 6″ apart merging — a gesture merges at A6's 3″
([`0228`](handoff/0228-report.md)); the "Malformed design file" report as a
list that zooms to each violation ([`0229`](handoff/0229-report.md)); the
wall-properties dialog on double-click, with walls and vertices gaining an
optional `name` document field ([`0230`](handoff/0230-report.md) §2); the merge
recorded at [`0231`](handoff/0231-report.md). Of [`0211`](handoff/0211-report.md)
§4's queue the status board remains (THE QUEUE below); plus the
`roofs-r3-planes-gables.png` re-shot, his display needed.

**`fixtures/single-floor-90-roof-gable-end-check.json` — his own, PROMOTED
2026‑10‑06 as THE GABLE-END CHECK PLAN** ([`0223`](handoff/0223-report.md) §2); `incoming/` is empty.
**The gable-end tranche is MERGED — folded into [PR #76](https://github.com/pjm4github/FloorPlanner/pull/76)
with the D67 pair on his word ("gable ends look right, fold into #76 and
land"); [`0223`](handoff/0223-report.md), [`0224`](handoff/0224-report.md), the
merge recorded at [`0225`](handoff/0225-report.md):** no roof-material triangle
at a gable end; the exterior wall perpendicular to the ridge beneath it climbs
to the roof.

**OPEN FOR HIS RULING, none built:**

* A dormer on a roof of another level, and the R3b wall dash / R5a trace
  across levels — one decision (0202 §6; [`0200`](handoff/0200-report.md) §6).
* The crossed-arm rule reads the plan, not the height; L2's storey height in
  his fixture is 196″ (0200 §5–6).
* The End-On dialog's level line was built from a finding, not a fault — his
  to reverse (0202 §2).

**THE ROOFLINE ARC, CLOSED TRANCHES — on the board.**

**One line each, and the line is now in [`STATUS.md`](STATUS.md)** — generated
from the mailbox's `**Landed:**` lines by `tools/status_index.py` (built 2026‑10‑10,
[`0232`](handoff/0232-report.md)); the roofline arc's PRs #48–#71 are rows there,
each with its report. This table left so the file cannot drift from the board.

Everything before the roofline arc — the vessel/enclosure split, the three
redraws, the wall orthogonality repair, the wall id fix, the snap-to-grid
features — is merged and closed; `handoff/README.md`'s pair table is its
trail.

**Named, not ordered:** valley/hip lines; a roof-plan export sheet; yard **His backlog (2026‑10‑11):** 0248's item 8, the porch's steps and stone base; item 9, a porch roof turning a house corner (two sheds meeting at a corner, or an L-shaped one-plane roof). Also named: DXF/PDF export of annotations; a leader annotation; the compose's next term.
items. **Carried, undated:** room-label rounding
([`0131`](handoff/0131-ruling.md) §2); delta-snap sites; the D61 family.
**Numbering collisions on the record:** `0036`, `0043`, `0050`, `0101`,
`0138`, `0139` — neither renamed after commit.

**Traps for whoever touches `roofclip.py` next:** the fixed point's
three classes (phantom / root limb / orphan) and the ORDER they prune in
are load-bearing — measured alternatives that fail are recorded in the
in-code comments and in 0182 §2–3 (judge-with-others-removed deadlocks;
poke-height ordering fails the saddle in isolation; whole-component
limbs re-open D85; root-only limbs strand rf3's rake). `_reach`'s
`no_step` veto is the strip rule; `_under_pieces(..., exclude=)` keeps
phantoms out of the network. `diag=` is the testing hook: cells,
original coverers, blank cells, limb cells, and every round. Seams are
read off the FINAL pieces (`_shared_segment`, 0183), never off the
in-round crossing bookkeeping. A swallowed end's `ext` is zero when the
end is open (0184: short of every host's ridge and above the host) --
the item and `fp3d` both key the end line and fascia on it. The mailbox
lands on `main` only (the commit hook enforces it); branch deletions
count as pushes to the hook -- delete a merged ref through `gh api`. R5a's
trace (`roof_clip_trace`) is computed at PAINT time like the wall dash
(rooms change without the roof hearing), and the join extension it
carries while clipped is R4d's raw reach -- hundreds of inches -- only
ever seen through `_drawn_trace`'s region clip; never draw the
unclipped locus of a clipped roof. **Since R6.b** composition is the
whole building's (`compose_building`, absolute height), and
`hold_roof_clips` holds it during a load and a drag; **since R6.c** a roof
of a level not being edited has an empty hit shape (`_roof_hittable`).

---

## THE QUEUE

> **Trimmed 2026‑10‑03, on Patrick's word — [`handoff/0204-report.md`](handoff/0204-report.md).**
> Six of this section's eight numbered items were DONE and still carried
> their whole build narrative. What is open is stated; what is closed is
> one line and its report. The text as it stood is at
> `git show 0f833f4:docs/SESSION_SNAPSHOT.md`. The roofline arc — the
> work actually in flight — is §0, not here.

**OPEN — nothing; the last item merged.** (Grid snap by default, A6, which stood
first here, is CLOSED AND MERGED — PR #70, [`0207`](handoff/0207-report.md),
[`0208`](handoff/0208-report.md). **Left open by his word, not dropped from
the spec: the angled-wall rule**, quantising length along the ray; and
snapping what an OPERATION produces, which A6 never covered.)

1. **The status board — MERGED, PR #78 on green CI (GREEN):** [`docs/STATUS.md`](STATUS.md),
   generated by `tools/status_index.py` from one `**Landed:**` line per merge
   report (33 backfilled; `handoff/0000-landings.md` holds the 44 no report
   records), the defect register and `ROADMAP.md` §3's RED table; `--check` in
   the gate's docs lane, RED on drift and on a landing commit with no line; the
   migration table frozen and its six rows moved (0019 ONE and TWO, done);
   `handoff/README.md`'s pair table generated; *the mailbox is the record now*,
   his word, written into `progress/README.md`. Read-back [`0232`](handoff/0232-report.md),
   build [`0233`](handoff/0233-report.md), the merge [`0234`](handoff/0234-report.md).

**Full tiered queue (A2–A5, the command-roster census, Phase 5's
remainder):** [`ROADMAP.md`](ROADMAP.md) §3.

**NAMED, NOT BUILT — each waits on its own ruling:**

* [D79](defects/0079-six-catalog-symbols-extrude-as-disconnected.md) — six
  catalog symbols with a fragmented body, exempted by name from the
  extrudability predicate; `boat_trailer` with them.
* `boat_trailer` and the vehicle loft — behind a read-back; design at
  [`floorplanner/viewer/VIEWER_NOTES.md`](../floorplanner/viewer/VIEWER_NOTES.md) §5.
* The four masked reachability sites, and `wall_endpoint_open`'s
  `floor=None` default, which should invert but changes two callers
  ([`0063-ruling.md`](handoff/0063-ruling.md)). Every mouse/macro hit path
  trusts Qt's visible/enabled state where `walls.py`'s geometry paths check
  `.floor` — the structural gap [`0037`](handoff/0037-ruling.md) §5 names.
  **D67's class: its two measured sites are in §0.**
* The orthogonality repair's clause (f): a wall the repair REFUSES can
  still move, through a vertex it shares with one the repair does move
  ([`0083-report.md`](handoff/0083-report.md) §§4–5). And its item 3 — a
  user-settable `T`, the graph solve — stays RED.

**CLOSED — on the board.**

**Each is a row of [`STATUS.md`](STATUS.md)** (PRs #33, #34, #37, and the GREEN
batches around #40–#48), with its report; the table left so the file cannot drift
from the generated board.

**Confirmed by Patrick, 2026‑10‑03:** *"PR #37 and PR #34 are complete. The cheif architect import is completed and it works."*

**Patrick's cross-floor report of 2026‑08‑17**
([`0035`](handoff/0035-ruling.md)–[`0037`](handoff/0037-ruling.md);
[`0038-report`](handoff/0038-report.md) refuted the load-path suspect):
its snapping half is the align fix above; its selection half is D67,
reproduced at [`0201`](handoff/0201-report.md) and CLOSED at `cdc54de`.

**Numbering collisions in this range, neither renamed:** `0036` and `0038`
each name a ruling and an unrelated report (§0 lists the later ones).

---

## 1. Where the work stands

| | |
|---|---|
| **`main`** | **`366c78e`** = the WELD commit on branch `p4-dormer-wall-type` (cut from `main` 08364cc, the P5 merge) that this CLICK-CYCLE commit stacks on. **P4 (the `dormer` wall type, 0296) IS FEATURE-COMPLETE on that branch — foundation + minting + the 3D fix + CHECKBOXES + UNDO SAFETY + the CEILING→ROOF CLAMP + the DORMER KNEE/DASH DATUM + the WELD (deform-to-follow) + CLICK-CYCLE SELECT; reported at [`0305`](handoff/0305-report.md), AMBER, awaiting his CHECK SESSION B.** CLICK-CYCLE (his report 2026-11-07: a hand-drawn L2 wall, and the dormer's own minted walls raised with their room, sit above the roof's grips — which appear only once the roof is SELECTED — so a buried dormer can never be selected and opened). **Alt+click** selects the topmost selectable item under the point; **Alt+click again at the same spot** cycles to the next down and LIFTS it (`PlanView._cycle_select`/`_stacked_targets`, ranked by `_hit_rank` so the order is stable under z churn; a child grip/opening resolves to its top-level parent). A roof also now opens on a plain **double-click of its ridge** (`RoofItem.mouseDoubleClickEvent`, SELECT + hittable only — the door a cycled-to dormer uses without finding its small apex grip). Tests `tests/test_click_cycle.py`. WELD (0296 §2, his ask #2 — deform-to-follow): a hand-drawn L2 wall whose end lands on a cheek's back end SHARES that cheek's `Vertex` (the existing draw-release weld already sees `dormer` walls); when the dormer moves, `sync_dormer_walls` re-derives the cheek's vertices and now RELOCATES a shared corner (`Vertex.relocated_to`, rebinding every holder) instead of `detach_end` (which stranded the knee wall on a fresh corner), so the knee wall follows — a free end still detaches, byte-identical. The weld survives save/reload (the shared vertex serializes to one doc vertex, re-shared then relocated on load). Tests `tests/test_p4_dormer_wall.py` (the weld follows a move, survives save/reload, a free end detaches). KNEE/DASH DATUM (his report, 2026-11-07: "the knee wall clip on L2 is not calculated ... you can see the knee wall on L2 only when the dormers are on L1"): `roof_clip_spans` (the R3b wall dash) and `room_ceiling_break_lines` (the P2 knee line) read a roof's height datum as `floor_elevation(rf.floor)` — but a dormer's `floor` is only its EDITING home (P3, 0295); its eaves/ridge are measured from its HOST's level. A dormer PROMOTED to the storey above shifted its clip a whole storey, so the ceiling crossing fell outside the room and the knee/dash vanished. New `_roof_datum_floor(rf)` returns the host's floor for a dormer, the roof's own floor otherwise; both functions now key and compute off it (a non-dormer, and a dormer on its host's own level, stay byte-identical). Test `tests/test_roof_clip.py::test_a_dormers_knee_line_ignores_its_editing_level`. CEILING CLAMP (his word, 2026-11-07: "the ceiling of a floor needs to be the lesser of the roof or the ceiling height ... the L2 ceiling pokes through the roof"): `fp3d.build_model` now builds each room ceiling AFTER the roof clips are known and clamps it to `min(ceiling line, roof underside)` — each room triangle (a room may be non-convex, so it is triangulated first) is split along every covering roof's cut lines and its knee (where the underside crosses the ceiling plane) and the piece height follows the lower of the two (`_ceiling_pieces`), so an attic ceiling follows the roof slope and nothing pokes through; flat at the ceiling line where no roof stands over it. Test `tests/test_viewer_ceiling.py::test_the_ceiling_does_not_poke_through_the_roof`. CHECKBOXES: the dormer dialog has three "Walls on <level>" checkboxes (face/left cheek/right cheek, on by default, enabled once a storey above exists) that opt a wall out; `RoofItem.dormer_wall_parts` + `sync_dormer_walls` honour it, serialized as the roof's `dormer_walls` (omitted = all on; in the schema + `Roof` model) and read on load. UNDO: a dormer edit now writes derived+serialized walls on another floor, so the diff path (`apply_design_difference`) would duplicate them (restored + re-minted = the "resurrected wall"); a plan with dormer walls now DECLINES the diff and reloads in full, which adopts them (one per part). `sync_dormer_walls` also dedups by grouping every scene dormer wall of this dormer (bound / loaded `bound_to` / geometry) and keeping one per part. 3D FIX (his report, "nothing renders ... extent too large"): a climb-band header wholly above the roof hit `_wall_under_roofs`'s `_box` fallback and extruded to the `_CLIMB_TOP_IN` sentinel; it now builds nothing (latent P5 §3 bug). Tests `tests/test_p4_dormer_wall.py` (9), `tests/test_p5_dormer_face_windows.py`. Foundation (a649754): the `dormer` wall `type` in the schema (with a `bound_to` object — required for `dormer`, forbidden otherwise), `STD_T["dormer"]=6.0`, a categorical dormer-blue dashed-centreline plan mark. MINTING: `RoofItem.sync_dormer_walls()` (called from `rebuild`) mints the three bound walls (face + two cheeks, from `_dormer_wall_lines()`) as real `dormer`-type `WallItem`s on the storey ABOVE the host (`_level_above`), vertices derived each rebuild, not selectable (read-only), removed with the dormer; **the L2 attic room now CLOSES against them** (`detect_room` finds it — the keystone for his #1 knee line and #2 wall-joining). `bound_to` serialized (resolved to the dormer's minted id in the cross-level pass, carried in the `Wall` model + `_WALL_MODELLED`) and re-adopted on load by geometry so a save/reload doesn't duplicate (tests `tests/test_p4_dormer_wall.py`). NEXT on the branch: the dialog checkboxes "Walls on level L2" (off to opt out), welding/deform-to-follow a hand-drawn knee wall, undo robustness; then his check, then #1 (the knee line) and #3 (the gable-end elevation). **P5 OF THE 1½-STOREY ARC IS MERGED into `main`** on his word after his CHECK SESSION B ("the ceilings look correct now merge"), recorded at [`0304`](handoff/0304-report.md): §3 (the 3D cut), §2 (the plan item), the sill-datum refinement, and CEILINGS. CEILINGS (his word, 2026-11-06: "there are no ceilings/floors over the 1st floor"): `fp3d.build_model` now builds a CEILING slab per interior room at the storey top (`top(level)` or the room's `ceiling_in`), raised `SLAB_T` above the ceiling line so it never z-fights an upper floor — the attic floor over a 1½-storey, a new `"ceilings"` mesh (`CEILING_C`). Tests `tests/test_viewer_ceiling.py`. **THE 1½-STOREY ARC IS COMPLETE THROUGH P5; ONLY P4 REMAINS (the `dormer` wall type, 0296).** SILL REFINEMENT (his word, 2026-11-06): a dormer window's sill is EDITED from the dormer's own floor — the top of the ceiling of the storey it sits over (the host floor's height, `RoofItem.dormer_sill_floor_in`) — not the ground, and clamped so the sill never drops below that floor and the head never rises above the dormer ridge (`_DormerWindowDialog`; the record still stores the host-datum number, a display conversion per 0294 §1c). §3: a dormer's own face window is cut into the CLIMBING WALL on its face (`_dormer_face` records the opening bands where it yields to a wall; the wall loop cuts them as climb-band voids — head unclamped, header climbs to the dormer surface with a high nominal top so a non-climbing cell yields empty, not an inverted box; receipts `tests/test_p5_dormer_face_windows.py`, set-back + normal windows byte-identical). §2: each face window is a hit-testable `DormerWindowItem` (a RoofItem child kept in step by `sync_windows`) — a dashed blue band with a gable-triangle glyph, offset up-slope just inside the face (the SECOND ROW, told apart from the storey wall's window below), drag-along-face snapped, double-click → the dialog with that window, right-click edit/dup/delete; the old read-only blue band in `RoofItem.paint` retired (tests `tests/test_p5_dormer_window_item.py`). **P1–P3 OF THE 1½-STOREY ARC ARE MERGED into `main`** on his word after his CHECK SESSION A ("the ghosted outline on L1 looks complete now, merge P1–P3"), recorded at [`0303`](handoff/0303-report.md): P1 (the stacked climb, 3D, [`0299`](handoff/0299-report.md)), P2 (the dash + knee line, plan, [`0301`](handoff/0301-report.md)), P3 (the dormer's level/datum/dialog, four views, [`0302`](handoff/0302-report.md)), plus three session-A fixes — (1) a cross-level dormer lost its `host` on save → it popped a storey in 3D, now `design_from_scene` resolves a host across levels; (2) the End-On dialog compacted into two columns; (3) a promoted dormer's ghosted outline on its host level is now complete. `dialogs.py`/`levels.py` keep BOTH PR #104's derived-base and P3's work (auto-merged, both kept). NEXT in the arc: P5 (windows on the dormer face), then P4 (the `dormer` wall type); check session B after. PR #104 (the floor dialog derives the base from the floor below, read-only, with an opt-out; a lower floor's height change re-derives the stack above — [`0300`](handoff/0300-report.md)) merged by fast-forward on his word "merge that", orthogonal to the arc. Earlier: the arc charter and sources (`0293`–`0297`) committed (doc-only, `0297` §0 item 1), and checkpoint 0 CLOSED ([`0298`](handoff/0298-report.md)): PR #103 (the cross-level dormer LOAD fix: `bridge.py` accepts a host on the dormer's floor OR the one directly below) recorded and landed at `3761819`; the three unmeasured items of 0293 §1 measured (M1 the dialog overstates a cross-level dormer's heights by 96″; M2 an L2 wall under the L1 roof gets 0 clip spans; M3 `dormer_defaults` reads the host floor's rooms — evidence `docs/evidence/1p5-storey-checkpoint0/`); `_to_delete/` emptied. The **1½‑STOREY ARC** charter [`0297`](handoff/0297-ruling.md) (sources [`0293`](handoff/0293-ruling.md)–[`0296`](handoff/0296-ruling.md)) governs the dormer work. Earlier: PR #102 (dormer-window editor in the End-On dialog + a read-only plan shadow, Phase C, [`0292`](handoff/0292-report.md)) merged by fast-forward at `e584c29` on his word "Land #102 + fix load bug, then wall-gable windows". Earlier: PR #101 (cross-level dormers: host a floor below, anchor the dormer to the host's level, [`0291`](handoff/0291-report.md)) merged by fast-forward at `7857a7f`, its record landed at `0053c54`. Earlier: PR #100 (dormer gable ends & shed fronts close in 3D: a wall under a dormer climbs into it, [`0290`](handoff/0290-report.md)) merged "Land #100 now", the foundation for the cross-level work; PR #99 (the Review-wall-gaps fix: a wall is no longer listed as a gap, and each gap names its walls and vertices, [`0289`](handoff/0289-report.md)); PR #98 (dormer plan controls A–G, the host-under-overhang 3D fix, the apex marker menu, the dormer outside walls at `EXTERIOR_T`, the `partition`/`beam` wall types, and the non-modal wall-gap review tool, [`0288`](handoff/0288-report.md), merged at `23237a0`); PR #97 (the plan's annotations in the DXF, [`0285`](handoff/0285-report.md); the Chief second-floor procedure, [`0286`](handoff/0286-report.md)), recorded at [`0287`](handoff/0287-report.md). Every PR through #100 is merged (#59 was closed, superseded by #60). **Never name an open PR number in a `main` commit subject** — the board check reads it as a landing (0287 §2). |
| **`p4` branch** | **`p4-dormer-wall-type` OPEN (P4, 0296) — FEATURE-COMPLETE, reported at [`0305`](handoff/0305-report.md), AMBER for CHECK SESSION B** — cut from `main` (08364cc, the P5 merge). The `dormer` wall type + minting: a dormer mints its face + two cheeks as real `dormer`-type `WallItem`s on the storey above, read-only, and **the L2 attic room closes** (`detect_room` finds it), `bound_to` round-trips (tests `tests/test_p4_dormer_wall.py`). The ceiling now clamps to the roof underside so the attic ceiling no longer pokes through (`tests/test_viewer_ceiling.py`). A PROMOTED dormer's knee line and wall dashes now compute from the HOST's datum, not the dormer's editing level, so they still draw on L2 (`_roof_datum_floor`, `tests/test_roof_clip.py`). A hand-drawn L2 knee wall welded to a cheek's back end FOLLOWS the cheek when the dormer moves and survives save/reload (deform-to-follow, `sync_dormer_walls` relocates a shared corner, `tests/test_p4_dormer_wall.py`). A dormer BURIED under overlapping L2 walls is now reachable by **Alt+click cycling** (`PlanView._cycle_select`) and opens on a **ridge double-click** (`tests/test_click_cycle.py`) — his report on checking the branch. P4 is now feature-complete. NEXT: his CHECK SESSION B (the 0296 §3 receipts on `little-dormer-test.json`); on his word, land P5 + P4; then his #1 (the L2 knee line, now unblocked) and #3 (the dimensioned gable-end window elevation). (His three asks, 2026-11-06: #1 L2 knee line — found it DEPENDS on P4 closing the attic room; #2 L2 walls join the dormer — P4 makes them joinable; #3 a dimensioned gable-end window elevation — a separate feature, after P4/#1.) The remote `p5-dormer-face-windows` ref awaits an approved delete. Named, not ordered: his backlog (0248's items 8 and 9). |
| **Gate** | full mode, re-run for this commit. GREEN — see this commit's own gate run. The **7 deselected are the PERF LANE** (standing P3.8 flap-class ruling). |
| **Records** | **88 records, 31 open** (D88 CLOSED 2026‑10‑11, `closed_by 6ee358b`; D87 CLOSED 2026‑10‑11, `closed_by d90f8b4`; D67 CLOSED 2026‑10‑07, `closed_by cdc54de`, [`0225`](handoff/0225-report.md); D50 CLOSED 2026‑09‑25, R6.0, `closed_by b8475b7`). D75 an accepted limit, D44's precedent; D76 the non-compositing renderer limit, cross-referenced to D69; D77 a tooling gap in `fp3d.py --shot`. D78 CLOSED (fixed 2026‑08‑16, `handoff/0027-ruling.md`). D80 CLOSED (fixed 2026‑08‑22, closed 2026‑08‑23 on Patrick's own check, `handoff/0088-ruling.md`, merged `main` at `ac6d763`). **D81/D82 CLOSED 2026‑08‑30** — `fp2pdf.py`'s door symbols and dimension-fraction formatting, fixed and merged, `handoff/0122-report.md`. **D83/D84 OPEN, filed 2026‑09‑02** — two macro-recorder gaps Patrick found, held for later, not scheduled. **D85 CLOSED 2026‑09‑05** — a very short roof ridge (or a thin-span one) was unselectable because its shape only covered the ridge, not the dashed eave/gable lines; fixed and confirmed on his own check, merged with R3b. `python tools/gate.py --docs` GREEN. |
| **Working tree** | see §5 — check `git status --untracked-files=all` before believing a census disagreement. |
| **THE MIGRATION** | **CLOSED 2026‑08‑11** — closing statement with its evidence in [`ROADMAP.md`](ROADMAP.md). Everything after it is features or cleanup. |
| **PHASE 6** | **PARKED 2026‑08‑12, Patrick's ruling** — see §2. |
| **PHASE 5** | **P5.2 (settable wall types + porch railings) COMPLETE**, PR #26 then PR #27, D73 and D74 closed. Progress entry at [`progress/phase-5.md`](progress/phase-5.md). **P5.1 and P5.3 not started**; the Yard catalog stays RED on artwork scope, and D46 closes with it. |

**A commit gate is enforced, not merely available.** `tools/gate.py` writes
`.gate-result.json`; a `PreToolUse` hook blocks any `git commit` unless that file
exists, reads GREEN, and is **newer than every tracked file** — every tracked
file, `.md` included, so a document edit made after the gate ran makes it stale.
See §5.

---

## 2. PHASE 6 IS PARKED — 2026‑08‑12

**P6.a and P6.b stay MERGED AND DORMANT; P6.c and P6.d are NOT WIRED.**
Refuted by measurement: Phase 6 does not retire `snapshot()`, and neither
D42's applier consolidation nor D45's `_edge_wall` folds in here. **Full
record, reasoning and the two named reopening conditions:**
[`ROADMAP.md`](ROADMAP.md) § "PHASE 6 IS PARKED".

---

## 3. How to read this repo's record

Which document answers which question:

| the question | the document |
|---|---|
| *What is the architecture? What are the house rules?* | **`CLAUDE.md`** |
| *What is every document, and which are authoritative?* | **[`README.md`](README.md)** — the map. Start here when unsure. |
| *What may proceed without Patrick, and what may not?* | **[`ROADMAP.md`](ROADMAP.md)** — the tier charter (GREEN / AMBER / RED), the autonomy policy, rulings **R‑A** and **R‑B**, the full work queue, and the **Phase 6 park**. |
| *What rules bind the work?* — census doctrine, gate discipline, what a receipt is, how vacuity is detected | **[`WORKING_AGREEMENT.md`](WORKING_AGREEMENT.md)**. Extracted from the plan because the rules outlive the migration. |
| *What is planned, and what is done?* | **[`V5_MIGRATION_PLAN.md`](V5_MIGRATION_PLAN.md)** — Status table, phase specs, risk register, sequencing rationale. |
| *What happened, and what proved it?* | **[`progress/`](progress/)** — the log, split by phase, verbatim and contemporaneous. Index at [`progress/README.md`](progress/README.md). |
| *What is broken, and what was decided about it?* | **[`defects/`](defects/)** — one record per file, `D23` is the permanent key. Index at [`defects/INDEX.md`](defects/INDEX.md); field rules at [`defects/README.md`](defects/README.md). |
| *What did an agent report, and what was ruled?* | **[`handoff/`](handoff/)** — the mailbox. Chat is not the record. |
| *What was measured, and how do I reproduce it?* | **[`evidence/`](evidence/)** — cited by records, never inlined. |
| *What was the plan before this one?* | **[`superseded/`](superseded/)** — kept because it holds material found nowhere else, **not** because it is safe to skip. |

**Reading order for a fresh session:** `CLAUDE.md` → this file →
[`handoff/`](handoff/) (highest number first) → [`README.md`](README.md) →
[`ROADMAP.md`](ROADMAP.md) → then whichever row above the task needs.

**`docs/CODE_REVIEW_v2.md` is still worth reading** for §1 (module verdicts) and
§2 (the five structural findings). Its §3 is now a pointer into `defects/`.

---

## 4. The rules that bind the work

**Full text and reasoning for every rule below is
[`WORKING_AGREEMENT.md`](WORKING_AGREEMENT.md).** This is names only — enough
to know a rule exists and where to read it, per
[`handoff/0028-ruling.md`](handoff/0028-ruling.md)'s own instruction that this
section stop carrying the reasoning WORKING_AGREEMENT.md already carries.

- a green signal is only evidence about what it measures
- retire visibility before permission; enumerate a view's consumers first
- a task that changes what an operation does owes a differential receipt
- vacuity has three shapes, plus UNSATISFIABLE, its mirror
- negative assertions are where vacuity concentrates — preconditions are mandatory there
- verify a probe — and a record edit — actually landed
- measure survival justifications like any other claim
- grep for identifiers, parse for shapes
- in a test, call the production predicate rather than restating it
- a tidy-up pass that outlives its mess only touches things nobody asked it to
- every census is shaped by its enumeration source — enumerate from the PROPERTY, not a container
- identity needs a categorical channel, not a scalar one
- a criterion that splits two structurally identical cases is measuring the wrong thing, and the aggregate never shows it
- an acceptance stated as a count is satisfied by replacement — measure identity, not a total
- a content correction discovered during a structural move is never folded into the move
- a lint that fails on correctly-recorded history is a lint that gets disabled
- a boundary belongs at the instrument — annotate, do not rewrite
- truncation invites fabrication
- the GREEN criterion: "no new semantics, and nothing the user must learn"
- an append-only shared file serialises parallel branches
- **every instrument is validated against a case known to be non-zero before its zero is believed** — the positive-control family, four members, all in `WORKING_AGREEMENT.md`: an instrument reporting nothing; one reporting a plausible something; one that can report only one of its two answers; and **a control proves the question it was built to answer, and no more** (added 2026‑08‑16)

---

## 5. Things that will waste your time if you don't know them

- **A task that changes `main`'s head, the queue, the record count or the gate
  line RE-CUTS §0/§1 IN ITS OWN COMMIT** — not "before the next session." This
  file went stale for eight commits, once, because each one left it for the
  next.
- **A `git commit` is BLOCKED unless a fresh green gate result exists on disk.**
  `tools/gate.py` writes `.gate-result.json` (gitignored) at the end of a
  full-mode run; `.claude/hooks/verify_gate.py` checks it exists, reads GREEN,
  and is **newer than every tracked file** — **including `.md` files**, so *edit
  the documents first, then gate, then commit*. The hook reads the RESULT FILE,
  never the commit message.
- **A NEW `docs/handoff/NNNN-*.md` ONLY COMMITS ON `main`** (0084-ruling.md
  §4) — `.claude/hooks/verify_gate.py` refuses a `git commit` that ADDS one on
  any other branch, merge commits exempt. Write the report or ruling, commit
  it on `main`, then branch for the code that answers it.
- **ONE CALL CANNOT BOTH RUN THE GATE AND COMMIT**, and the hook blocks that
  shape outright. **`--trailer` is exempt** — it runs nothing and writes nothing,
  and it is exactly the command that belongs beside a commit. **The hook's match
  is a plain substring on `tools/gate.py`**, so it also fires on a `git add`
  that merely names that path (or `tests/test_gate.py`) in the same command as
  a commit, and on a commit MESSAGE that quotes the string — stage in one call,
  commit (ideally via `-F <file>`, not an inline message) in the next.
- **A `NameError` inside a Qt virtual override PRESENTS AS A SEGFAULT.** PyQt6
  aborts the process on an unhandled Python exception in an override, so the run
  dies with **no traceback and no pytest summary**. **`config.py` has an
  `__all__`**, so a constant added there is invisible to the star-importing
  modules until it is *listed*. If a headless run dies silently, wrap the handler
  and re-raise before suspecting Qt.
- **Importing `floorplanner.design.validate` DRAGS IN THE QT BINDINGS** —
  measured at P5.2 — because `floorplanner/__init__.py` star-imports the editor.
  `viewer/fp3d.py` is deliberately Qt-free and loads that module **by path**. A
  **source-text grep** guards it, so prose that merely names the bindings trips
  it; reword the prose rather than weakening the guard.
- **`fp3d.py`'s GL rendering (`--shot`, `make_view`) needs a REAL display, not
  `QT_QPA_PLATFORM=offscreen`.** Measured 2026‑08‑16 (D77, D78's investigation):
  under `offscreen`, this project's Qt cannot create a GL context at all —
  `grabFramebuffer()` returns a null image, `.save()` returns `False` (its
  return value is unchecked), and `--shot` prints `wrote <path>` and writes
  nothing, reproducibly. The real platform, an actual window, works. Headless
  2D work (`QGraphicsScene`, `export_canvas`) is unaffected — this is GL-specific.
- **A SHALLOW git checkout (`fetch-depth: 1`, `actions/checkout`'s default)
  hides ALL parent-relative revisions at the boundary commit** — not just a
  merge commit's second parent; `HEAD^1` fails too. Measured on CI building
  D78. `git cat-file -p HEAD` still shows the true `parent` lines (raw object
  content, unaffected); `git rev-parse HEAD^N` / `HEAD~N` do not. Jobs that
  need real ancestry (this file's own staleness check, `closed_by` validation)
  need `fetch-depth: 0`.
- **`QRubberBand.show()` on an offscreen viewport kills the process** —
  pre-existing, reproducible on `main`, and why no headless test covers the
  Ctrl+drag band.
- **A running app keeps the code it imported** — the status-bar version label
  shows the launch identity; restart before re-testing.
- **`gh` is not on `PATH` in PowerShell**: `& "C:\Program Files\GitHub CLI\gh.exe"`.
  It *is* on PATH under the bash tool.
- **`.gitattributes` forces LF**, so the CRLF phantom-diff class is closed
  structurally — but the working tree still checks out CRLF, so multi-line `\n`
  patterns in ad-hoc scripts still match nothing. Use `tools/record.py`, which
  handles it once and verifies.
- **`git commit` after `git add` commits the WHOLE index** — use
  `git commit <paths>` when anything else is staged.
- **The census reads the WORKING TREE (D51).** A stray `.json` in `examples/`
  changes `collected=` and can turn the gate red, which — with the commit hook —
  **blocks every commit in the repository**. Check
  `git status --untracked-files=all` before believing a census disagreement is
  real.
- **A plan for a MANUAL CHECK goes in `fixtures/`, never `examples/`.**
  `examples/` is the corpus: schema-validated, frozen, and a change there needs a
  declared justification. See [`../fixtures/README.md`](../fixtures/README.md).
- **Macro replay geometry matters**: a `.fpm` replays correctly only at the
  window geometry it was recorded at; each pinned test states which.
- **The suite's console is cp1252** — no non-ASCII in test output.
- **Migrating the records to GitHub Issues has a precondition**: none of the 15
  labels or 20 milestones exist yet. `tools/defects_to_github.py --create-labels
  --yes` first; `--execute` refuses without them.
