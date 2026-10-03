<!-- SNAPSHOT-HEAD: 52a2870 -->

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

**OPEN NOW — R6.c, the roof tool across levels: BUILT, AMBER, STOPPED FOR
PATRICK'S CHECK.** [PR #69](https://github.com/pjm4github/FloorPlanner/pull/69)
on `roofs-r6c-tool-levels`, report [`0202-report.md`](handoff/0202-report.md)
(on his word, "proceed with R6.c"; [`0197-ruling.md`](handoff/0197-ruling.md)
§5 names the tranche). His check is 0202 §5. **On his word: merge, delete the
branch in the merge step, record the merge in the report that follows
(0197 §7).**

**READ THIS BEFORE TOUCHING THE BRANCH.** On 2026‑10‑03 the branch's working
tree held uncommitted work that is **not this session's** and is not in any
report: `fixtures/r6c-two-level-tool-check.json` + `.md` (a tiny two-level
manual-check fixture, dated 2026‑09‑29), a test for it added to
`tests/test_r6c_roof_tool_levels.py`, and a row in `fixtures/README.md`
saying it was *"added after the six-step cumulative check on the real
Wiscaway plan ended in a native Qt crash."* **That crash is not recorded in
any report and has not been reproduced here** — establish it first.
`fixtures/incoming/single-floor-90-roof-gable-end-check.json` arrived
2026‑10‑03, untriaged. All of it was left in place, untouched.

**OPEN FOR HIS RULING, none built:**

* [D67](defects/0067-selection-is-not-scoped-to-the-active-floor.md) —
  reproduced, mechanism `RoomItem.interior_walls()` with no floor predicate,
  undo complete; the fix is one predicate ([`0201`](handoff/0201-report.md) §1).
* The Door/Window tool places an opening on another level's ghosted wall —
  D67's class, measured 56 → 57 ([`0202`](handoff/0202-report.md) §4).
* A dormer on a roof of another level, and the R3b wall dash / R5a trace
  across levels — one decision (0202 §6; [`0200`](handoff/0200-report.md) §6).
* The crossed-arm rule reads the plan, not the height; L2's storey height in
  his fixture is 196″ (0200 §5–6).
* The End-On dialog's level line was built from a finding, not a fault — his
  to reverse (0202 §2).

**THE ROOFLINE ARC, CLOSED TRANCHES — one line each; the report is the record.**

| tranche | what | PR | report |
|---|---|---|---|
| R1–R3b | model, ridge sketch, end-on marker, show/edit, planes and gables, the wall clip line | #48–#53 | [`0139`](handoff/0139-ruling.md)–[`0153`](handoff/0153-report.md) |
| R4a–R4c | schema, parameters dialog, five grips | #54–#56 | [`0155`](handoff/0155-report.md)–[`0163`](handoff/0163-report.md) |
| R4d–R4g | intersection clip, mesh clip, the three-ridge envelope, the full footprint | #57, #58, #60 (#59 closed, superseded by #60) | [`0164`](handoff/0164-ruling.md)–[`0185`](handoff/0185-report.md) |
| R5a | the clip trace on the roof | #61 | [`0187`](handoff/0187-report.md) |
| 3D wall clip | walls capped under roofs | #62 | [`0188`](handoff/0188-report.md), [`0189`](handoff/0189-report.md) |
| R5b | dormers; then undo, the `DORMER` macro token, the grip clamp | #63–#65 | [`0190`](handoff/0190-report.md)–[`0196`](handoff/0196-report.md) |
| R6.0 | D50 closed: a level's elevation and height survive | #66 | [`0198`](handoff/0198-report.md) |
| R6.a | plan-view roof rule; 3D builds the whole building | #67 | [`0199`](handoff/0199-report.md) |
| R6.b | one roofscape, composed in absolute height | #68 | [`0200`](handoff/0200-report.md) |
| (measurements) | D67 reproduced; roof paths and the level's elevation | — | [`0201`](handoff/0201-report.md) |

Everything before the roofline arc — the vessel/enclosure split, the three
redraws, the wall orthogonality repair, the wall id fix, the snap-to-grid
features — is merged and closed; `handoff/README.md`'s pair table is its
trail.

**Named, not ordered:** valley/hip lines; a roof-plan export sheet; yard
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

1. **THE EXTRUDABILITY PREDICATE — BUILT, GREEN, MERGED TO `main`.**
   `floorplanner/viewer/fp3d.py:extrudability()` plus `tests/test_extrudability.py`,
   three predicates from [`handoff/0029-ruling.md`](handoff/0029-ruling.md) §2.
   **Census result:** only `glass_shower` had zero closed filled shapes before
   the redraw; `boat_trailer` plus six more items (`motorcycle`, `bicycle`,
   `garden_tractor`, `riding_mower_snow`, `drill_press`, `water_softener`) have
   a fragmented body, exempted by name pending a ruling on filing — [D79](defects/0079-six-catalog-symbols-extrude-as-disconnected.md)
   filed for those six (`0034` §5); 73 of 95 have a body with no internal
   region; the 3% connectivity tolerance's raw values are printed and land in
   the test's own docstring (`0034` §4 — nothing sits between ~1% and 3%).
   **D76 reconciliation** ([`0030`](handoff/0030-ruling.md) §4, confirmed not
   withdrawn by [`0034`](handoff/0034-ruling.md) §1): `walk_in_shower`'s bench
   is fully contained in the body on all three axes — D76 stands, unamended.
   **Consequence: a region-shaped mark (nested) inherits D76's invisibility
   whenever the body is translucent; a `beside` mark (a second top-level ring,
   sharing the body's material, never enclosed) does not** — the redraw brief
   is `beside` shapes, not regions. Full detail: [`0032`](handoff/0032-report.md) ·
   [`0036-report.md`](handoff/0036-report.md).
2. **THE ARTWORK REDRAWS — BUILT, CHECK PASSED, MERGED
   ([`0050`](handoff/0050-ruling.md)).** `shower` and `glass_shower` gain a
   filled door leaf (`glass_shower` also gains its first-ever filled body);
   `walk_in_shower` gains a fixed glass panel at the opening, alongside its
   already-correct, already-invisible bench. All three: `build_prism`
   `beside` shapes, not regions. **Two cameras, both on record** (`0034` §2):
   room-scale (comparability) — [`before`](evidence/shower-glance-before.png) ·
   [`after`](evidence/shower-glance-after.png) — and working-distance (the
   actual glance test) —
   [`before`](evidence/shower-glance-working-distance-before.png) ·
   [`after`](evidence/shower-glance-working-distance-after.png), reproducible
   via `docs/evidence/shower_glance_working_distance.py`. **At working
   distance the marks are unambiguous. Patrick's check was in the running
   app** (his own working zoom), so `0034` §2's camera question is answered
   by construction — [`0050`](handoff/0050-ruling.md) §1. **The branch was 9
   behind `main` at check time**; brought current in this merge, re-gated on
   the combined tree (GREEN, `collected=754`), and the extrudability census
   re-run: `glass_shower` goes from zero filled shapes (predicate 1's only
   prior failure) to 2, `shower` 2/1 frag/no region, `walk_in_shower` 3/1
   frag/has region (the pre-existing D76-invisible bench) — all three
   predicates pass, no new exemptions. `floorplanner/viewer/fp3d.py` has no
   diff between the branch's fork point and `main`'s tip, so the render is
   unaffected by anything `main` gained — no after-shot retake needed, per
   [`0050`](handoff/0050-ruling.md) §3 step 4. Full build notes:
   [`0033`](handoff/0033-report.md) · [`0036-report.md`](handoff/0036-report.md).
   Brief: [`handoff/0016-ruling.md`](handoff/0016-ruling.md) §2–3.
3. **[`handoff/0019-ruling.md`](handoff/0019-ruling.md)'s status board — GREEN,
   read-back first, priority lowered by [`0029`](handoff/0029-ruling.md) §6**
   (Patrick has a Cowork skill rendering the same state on demand — a VIEW,
   not the artifact; `STATUS.md` is still owed, the skill removes the urgency
   not the requirement). Freeze the closed migration's Status table as
   history; move forward status to a generated `docs/STATUS.md`. Read-back
   owed: what identifies a completed unit when recent work has no phase
   number at all.
4. **Grid snap — the largest daily-use improvement left, fully specified, read-back
   owed before any code.** Snap-by-default; shift means unconstrained; the
   angled-wall rule quantises length along the ray; intersection joins with
   their two refusals; the live readout shows snapped values. The read-back:
   clause-by-clause EXISTS/PARTIAL/ABSENT, thresholds with reasons, the shift
   modifier audit, the angle convention already in the geometry code, and
   Ctrl's disposition. Spec: [`ROADMAP.md`](ROADMAP.md) A6.
5. **`Docs-Snapshot` moves out of the `pull_request` CI lane — DONE.**
   [`handoff/0042-ruling.md`](handoff/0042-ruling.md): the only check this
   project's CI has ever failed on when the code itself was fine; it read git
   topology (`HEAD~1`), which a merge-ref reshapes, while the local commit
   hook already prevents a stale marker from landing at all. `tools/gate.py`'s
   `_snapshot_check()` now skips it on `GITHUB_EVENT_NAME == "pull_request"`,
   at the `main()`/`_docs()` call sites only — `_snapshot_head()` and the
   `HEAD^2` merge-ref logic are untouched, so every existing D78 regression
   test still exercises the real thing. Two new controls (skip-when-stale,
   skip-scoped-to-PR). Full receipt: [`handoff/0048-report.md`](handoff/0048-report.md).
6. **The commit hook splits quick-for-commit / full-for-push — DONE.**
   [`handoff/0043-ruling.md`](handoff/0043-ruling.md) §4 /
   [`handoff/0047-ruling.md`](handoff/0047-ruling.md) §4: `.gate-result.json`
   carries a `mode` field now (`--quick` writes too); `git commit` accepts
   either mode, `git push` requires `mode == "full"`. All four controls, in
   the same commit, at both events: no result refused; `--quick` GREEN
   allowed at commit / refused at push; full GREEN allowed at both; any RED
   refused; "no result" / "RED" / "quick-at-push" each produce a
   **different** message. `tests/test_verify_gate_hook.py`, 18 tests against
   an isolated fixture repo, caught a real `"pushs"` pluralisation bug before
   it shipped. Full receipt: [`handoff/0049-report.md`](handoff/0049-report.md).
7. **An orthogonality REPORT — DONE (item B only; item C is a separate,
   unauthorised repair, still RED).** [`handoff/0055-ruling.md`](handoff/0055-ruling.md):
   grid snap will NOT fix the off-axis walls Patrick's own export showed
   Chief flagging — measured as two populations (`L1`'s large angles are
   likely real architecture, `L2`'s 75 sub-2° deviations are drift, not
   drawing) produced by operations (move/join/weld/coalesce) relocating a
   vertex, which snap (constrains cursor input only) cannot touch.
   `floorplanner/design/validate.py` gains `wall_orthogonality()` /
   `orthogonality_bands()`, wired into both `tools/validate_design.py` (the
   corpus census) and a new Edit ▸ "Wall orthogonality report…" dialog.
   Cross-checked against `0055`'s own corpus numbers (6/2 off-axis walls),
   not just written to pass — matched. 17 new tests, gate GREEN. Full
   receipt: [`handoff/0056-report.md`](handoff/0056-report.md). Grid snap
   itself (item 4 above) is unchanged but its read-back still owes one more
   clause: does snapping cover the *output* of an operation, or only cursor
   input? **Item C (a repair) is RED — no ruling exists, none owed here.**
   **The corpus census B's whole justification depended on — run
   ([`0057`](handoff/0057-ruling.md) §2 / [`0058-report.md`](handoff/0058-report.md)),
   then corrected ([`0059-ruling.md`](handoff/0059-ruling.md) /
   [`0060-report.md`](handoff/0060-report.md)):** 948 walls across 16 v5
   plans (`docs/evidence/orthogonality_census.py`, 8 files skipped and each
   named why). **`0058`'s printed table could not reproduce its own 63
   headline** — the bottom band merged "exactly on axis" with "off by up to
   0.01°", hiding 12 of the 63. `ORTHOGONALITY_BANDS` now splits that bucket
   into `0.01-0.1 deg` / `0 < dev < 0.01 deg` / `on axis` (its own row,
   matched on `deg == 0.0` rather than by range); both printers'
   column-width bugs (exposed by the longer label) fixed alongside. Re-run:
   **32 + 19 + 12 = 63, exactly** — the table now produces its own headline.
   Two more of `0055`'s own claimed numbers independently reproduced (both
   `wiscaway` files, exact match). **`0059`'s suggested separating
   measurement (crossfloor plan vs `wiscaway2026-08-09R`'s off-axis rate)
   run, and it does not separate the two** — `wiscaway2026-08-09R` (no
   reported cross-floor symptom) has MORE walls over 5° (53) than the
   crossfloor plan (36), correcting `0058`'s "highest in the corpus" framing;
   orthogonality severity should not be read as evidence for the cross-floor
   thread below. **`0037` §3's reachability census also run, folded in for
   free per `0059` §5 item 3**: every mouse/macro hit-test and selection path
   shares one root (`items.py`'s `hit_candidates()`) and none filter by
   `.floor`, versus 100% of `walls.py`'s geometry hot paths, which do. **The
   census found a live one** ([`0061-ruling.md`](handoff/0061-ruling.md)):
   `view.py:244` `PlanView._align_to_wall` scans bare `sc.items()`, not
   `items(pos)`, so — unlike the other reachability sites, which Qt's own
   visibility filtering already masks — it is NOT masked, and a wall drawn on
   the active floor could snap its free end onto an open end on a hidden
   floor, matching Patrick's cross-floor report clause for clause. **Fixed on
   branch `cross-floor-align-fix`** ([`0062-report.md`](handoff/0062-report.md)):
   a fail-first test confirmed RED (`500.0` where `505.0` was drawn) then
   GREEN after `_align_to_wall`/`wall_endpoint_open` both gained the
   `.floor == active` filter every other hot path already had; the
   long-untriaged `fixtures/incoming/crossfloor-snap-2026-08-17.json`
   promoted to `fixtures/` (real corpus evidence, kept; the defect itself
   covered by the synthetic test). **[PR #34](https://github.com/pjm4github/FloorPlanner/pull/34)
   open, AMBER, stopped for Patrick's manual check** — *"with the second
   floor hidden, does a wall you draw still jump to something you cannot
   see?"* [`0063-ruling.md`](handoff/0063-ruling.md) accepts the fix and adds
   `wall_endpoint_open`'s `floor=` param as more than asked (a second,
   previously-unreported half of the same fault, reasoned from the
   mechanism), but flags the fail-first test as a negative assertion with no
   positive-control pairing (D43/positive-control family) — **owed on the
   branch: a control assertion, same scene, active floor, alignment must
   still fire.** Also flags a fourth `fixtures/incoming/` exit as needed
   (promoted as measurement subject, no test) — **added to
   `fixtures/incoming/README.md`.** Three more items named, not built: the
   four masked reachability sites (no receipt yet), `wall_endpoint_open`'s
   `floor=None` default (should invert, but changes two existing callers
   with no receipt). A guide line added to `README.md`'s export section
   pointing at the orthogonality report before exporting. **Item C (the
   repair) is no longer RED** — ruled at [`0066`](handoff/0066-ruling.md),
   read back at [`0079`](handoff/0079-report.md), amended and unblocked at
   [`0082`](handoff/0082-ruling.md), and BUILT at
   [`0083`](handoff/0083-report.md) — see THE QUEUE item 8 below.

8. **THE WALL ORTHOGONALITY REPAIR — BUILT, GATED GREEN, AMBER, STOPPED FOR
   PATRICK'S CHECK.** [`0066-ruling.md`](handoff/0066-ruling.md) item C, read
   back at [`0079-report.md`](handoff/0079-report.md), amended and unblocked
   at [`0082-ruling.md`](handoff/0082-ruling.md) (withdrew the
   refuse-to-start clause, moved the before/after differential onto a stable
   key, made the conflict predicate re-evaluate per wall against the
   document as mutated so far). Built exactly to that spec:
   `validate.py`'s `repair_wall_orthogonality` + `OrthogonalityRepairDialog`
   + Edit ▸ "Repair wall orthogonality…". The candidate population is the
   near-axis census itself (`0 < deg <= 1.0`), not a displacement-bounded
   set — settled by `0079`/`0082` both treating `farmplaceBIGmultifloor`
   `w24` (0066's own 3.000″ headline outlier) as a genuine candidate,
   refused only for conflict. **Two findings measured, neither anticipated
   by either ruling** ([`0083-report.md`](handoff/0083-report.md) §§4-5):
   "61 of 63" does not hold corpus-wide — `fixtures/incoming/crossfloor-snap-2026-08-17.json`
   alone carries 37 near-axis walls, and straightening it introduces two
   genuine new `I14` violations, so `0082`'s own whole-document rollback
   (correct as specified) withholds all 37 — the honest corpus total is
   **22 moved, 4 refused, 37 withheld by one file's rollback** (receipt:
   `docs/evidence/orthogonality_repair_census.py`, new); and a wall the
   repair REFUSES can still have its own displacement change, because it
   shares a vertex with a wall the repair DOES move (measured on
   `wiscaway2026-08-09R`'s `w54`) — a real gap in `0079`/`0082`'s own
   acceptance clause (f), named for a future ruling, not silently tested
   around. Chain receipt run per `0082` §3's own instruction: RED under a
   naive as-loaded predicate (a real six-wall chain, `w53..w59`, ends up
   WORSE — one wall at 3.25° off axis), GREEN under the built one (every
   non-refused wall in the chain lands at exactly 0°). 19 new tests
   (`tests/test_orthogonality_repair.py`), full suite 852 passed, `ruff`
   clean, gate GREEN. Item 3 (user-settable `T`, the graph solve) is
   unaffected and stays RED. **[PR #37](https://github.com/pjm4github/FloorPlanner/pull/37)
   open on `wall-orthogonality-repair`, AMBER, stopped for Patrick's own
   check** (`0066` §7: run the repair on the plan behind `L2.dxf`,
   re-export, recount against Chief's 75 — and does the drawing still look
   like the drawing).

**Full tiered queue (A2–A5, the command-roster census, Phase 5's remainder,
etc.):** [`ROADMAP.md`](ROADMAP.md) §3. **`boat_trailer` and the vehicle
loft** are not in this queue — both behind a read-back, design at
[`floorplanner/viewer/VIEWER_NOTES.md`](../floorplanner/viewer/VIEWER_NOTES.md)
§5.

**Cross-floor snapping/bleed-through — Patrick's own report
([`0035`](handoff/0035-ruling.md), [`0036-ruling.md`](handoff/0036-ruling.md),
[`0037`](handoff/0037-ruling.md)) — GREEN measurement only so far, still not
started as a fix, does not displace items 1–2 above.** [D67](defects/0067-selection-is-not-scoped-to-the-active-floor.md)
-adjacent. `0037`'s named suspect (the v5 load path never re-syncing floor
display state) **does not hold** — measured directly on Patrick's own
submitted plan, both by code reading and by a live headless probe:
`apply_design_to_scene` already calls `win._sync_floor_state()`
(`floorplanner/design/bridge.py:1265`, present since 2026‑07‑26). See
[`0038-report.md`](handoff/0038-report.md). **`0037` §3's narrowed census —
run** ([`0060-report.md`](handoff/0060-report.md), folded into the
orthogonality item above per [`0059`](handoff/0059-ruling.md) §5 item 3):
every mouse/macro reachability path (`items.py`'s `hit_candidates()` and
everything built on it) trusts Qt's visible/enabled state alone, versus
`walls.py`'s geometry hot paths, which all check `.floor` directly — a
structural gap ("a derived property that must be manually re-applied is not
derived — it is cached," `0037` §5), currently masked because
`apply_floor_visibility` does run at load. Not a reproduced bug; no fix
built (AMBER). **Reopens [`0036-ruling.md`](handoff/0036-ruling.md)
§3's own discriminator** (does the saved document change across the
gesture?), still unrun — blocked on two facts neither ruling nor the intake
file states (was `show_others` on; did the wall stay moved after release).
`fixtures/incoming/crossfloor-snap-2026-08-17.json` has no `.txt` companion
note; one handoff old, not yet two.

> **Numbering collision, on the record rather than hidden:
> [`handoff/0036-ruling.md`](handoff/0036-ruling.md) and this session's own
> `handoff/0036-report.md` (on branch `shower-identity-redraws`) are two
> unrelated files sharing one number.** Both legitimately committed on their
> own branches; neither renamed — doing so would break more citations than it
> fixes. Numbering continues forward from `0038`.

**`fp2dxf` (a v5 → Chief Architect DXF exporter, built outside this repo) —
[`0038-ruling.md`](handoff/0038-ruling.md), DONE end to end and MERGED —
[PR #33](https://github.com/pjm4github/FloorPlanner/pull/33) → `main` at
`15bd553`. Patrick's check passed.** Accepted in principle:
pure stdlib, a clean `convert()` API, a real differential-receipt finding
(both doors import as windows). Thickness reads `STD_T` by path (the
D73/D74 disease closed, not repeated), all three library-hygiene fixes
(`SystemExit` → a catchable `ValueError`, `print()` confined to the CLI
entry point with `convert()` returning warnings/summary on
`ConvertResult`, explicit `utf-8` on both writes) — all measured done per
[`0043-report.md`](handoff/0043-report.md), landed on `main` at `5d61f1f`.
**Everything §5's owed list named is now built on the PR branch**: the zip
unpacked and deleted, its sample + sidecars → `fixtures/chief-export/`,
its 16 screenshots → `docs/evidence/chief-export/`, the golden DXF pair
regenerated against `STD_T` (diff stated in full: only `exterior`
6.5″→6.0″ and `railing` 3.0″→2.0″ moved), the README split (workflow
section transcribed, not summarised), the File ▸ Export ▸ Chief Architect
(DXF)… menu action + completion dialog, and a 7-test golden-file receipt.
Gate GREEN, ruff clean. **Patrick's own manual check — Chief Architect
import, confirmed walls/doors/windows arrive as their own kinds — is out
of Code's reach and is the merge condition**, not claimed done. Full
receipt: [`handoff/0050-report.md`](handoff/0050-report.md).

> **A second numbering collision, same session:
> [`handoff/0038-ruling.md`](handoff/0038-ruling.md) and this session's own
> `handoff/0038-report.md`** (written earlier, about the cross-floor
> investigation) **share a number.** Neither renamed. Numbering continues
> forward from `0039`.

---

## 1. Where the work stands

| | |
|---|---|
| **`main`** | **`52a2870`** at this file's cut — this commit lands [`0203-report.md`](handoff/0203-report.md) (this file trimmed, on Patrick's word). R6.c is built on `roofs-r6c-tool-levels`, [PR #69](https://github.com/pjm4github/FloorPlanner/pull/69), AMBER, stopped for his check — see §0. Every earlier PR through #68 is merged (#59 was closed, superseded by #60); §0's table links each tranche's report. |
| **Branches** | **`roofs-r6c-tool-levels` open, AMBER, [PR #69](https://github.com/pjm4github/FloorPlanner/pull/69) waiting on Patrick's check** (its snapshot is the branch's own cut; at the merge, merge `main` into it, take `main`'s snapshot, and re-cut it as the merged state). Otherwise only `main` on the remote: every merged branch was deleted in its merge step, local and remote. |
| **Gate** | full mode, re-run for this commit. GREEN — see this commit's own gate run. The **7 deselected are the PERF LANE** (standing P3.8 flap-class ruling). |
| **Records** | **86 records, 32 open** (D50 CLOSED 2026‑09‑25, R6.0, `closed_by b8475b7`). D75 an accepted limit, D44's precedent; D76 the non-compositing renderer limit, cross-referenced to D69; D77 a tooling gap in `fp3d.py --shot`. D78 CLOSED (fixed 2026‑08‑16, `handoff/0027-ruling.md`). D80 CLOSED (fixed 2026‑08‑22, closed 2026‑08‑23 on Patrick's own check, `handoff/0088-ruling.md`, merged `main` at `ac6d763`). **D81/D82 CLOSED 2026‑08‑30** — `fp2pdf.py`'s door symbols and dimension-fraction formatting, fixed and merged, `handoff/0122-report.md`. **D83/D84 OPEN, filed 2026‑09‑02** — two macro-recorder gaps Patrick found, held for later, not scheduled. **D85 CLOSED 2026‑09‑05** — a very short roof ridge (or a thin-span one) was unselectable because its shape only covered the ridge, not the dashed eave/gable lines; fixed and confirmed on his own check, merged with R3b. `python tools/gate.py --docs` GREEN. |
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
