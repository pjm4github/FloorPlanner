# Session snapshot — read this first

**Re-cut 2026‑08‑06, on `main` @ `4b379fc`, immediately after the P4.5 merge.** **PHASE 4 IS COMPLETE.** This file exists so a fresh session can start from disk instead of from a chat summary. It is an **index and a state marker, not a second copy of the record** — where it points at another document, that document is authoritative and this one must not be trusted over it.

---

## 1. Where the work stands

| | |
|---|---|
| **Branch** | `main` @ `4b379fc` — no work branch open. |
| **`main`** | P4.1, P4.1b, P4.2, P4.3, P4.4 and **P4.5** all merged and ticked (PRs #2, #3, #4, #5, #6, **#10**); the 3D viewer packaged and its popup merged (PRs #4–#8). |
| **Census** | **633 collected** (625 passed, 7 deselected, 1 xfailed), ruff clean, `vacuous=0`, **`end_assign=0`**, every sum reconciling in all three modes. |
| **CI on `main`** | green — py3.10, py3.13, deep invariants, ruff (run `31067224148`). |
| **Working tree** | clean (only untracked screenshots). |

**P4.5 merged 2026‑08‑06 at PR #10** (merge commit `4b379fc`, two parents, not squashed) on **Patrick's mini-gate — all ten items run and passed**, including item 10 (Align to grid and Distribute on a plan with shared party walls) and the cross-cutting dashed-edge watch.

**The two WIP branches are deleted, local and remote.** Their heads are recorded in the plan's Progress log because that is now the only handle: `p4.5-align-wip` **`5f679e9`** (discarded — rewritten at P4.5(32) against the finished gather) and `p4.5-defect23-wip` **`4e967c0`** (absorbed — cherry-picked at P4.5(30)).

---

## 2. THE OPEN QUEUE, in order

Everything here was carried out of Phase 4 **deliberately and with a row**, not dropped.

1. **Register row 47 — `fragment` must produce floating rooms via `extract`. THE FIRST TASK, ahead of grid snap.** `room_boolean` (`mainwindow.py:982‑996`) builds a complete wall loop per region with no dedup, then groups it; nothing welds them. **This is a SECOND duplication site that `duplicate_wall`'s death never reached, so P4.5's retirement of copy-on-group is incomplete and the row states by how much.** Measured (`docs/evidence/defect23-fragment.json`, reproduce with the probe beside it): 20 distinct `Vertex` objects on 10 geometric points; `room_owns_walls` **false for all nine (group, room) pairs**; dragging a fragment clear moves **4 of 4 walls and 0 of 16 outline corners**; four dashed edges each with a real wall on them; `check(deep)` CLEAN throughout and **the save succeeds**. Pinned by `test_fragment_groups_each_piece_with_its_own_walls`, the suite's only remaining `xfail`, which flips when this lands.
2. **Defect 11's RUNTIME z-order collapse — in P4.5's charter and it did NOT land.** Only 11a did. It hangs `test_drag_split_macro_keeps_every_room_rectilinear` at the first drag, bisected to `geometry.py`, and the trigger is the **magnitude** of the z step (`×1.0` completes, `×Z_STACK_BAND` hangs); the work was reverted, so nothing of it is in the tree and it is **not reproducible from disk**. **Next step: instrument the drag with a bounded event counter to find the consumer — do not choose constants to avoid a symptom.** **The agreed rule (ruling 4) carries forward whole:** z = `floor_term + stack_term + type_term`; the backdrop's −1e9 becomes a **type term**, not a magic number; `bring_to_front`'s full-scene max scan dies with it; and the band arithmetic becomes **named constants** with `max(type_term) < STACK_BAND` and `max(stack_term) < FLOOR_BAND` written beside them and **pinned by a test** — without that it is three schemes again the first time someone raises a type constant. **The SERIALIZATION half is separately blocked** on a schema ruling with version implications (v5 has no stacking-index field on room, wall, furnishing or group, and all four set `additionalProperties: false`), and returns to Patrick as its own decision.
3. **Register row 48 — the invariants have never checked the scene the user edits.** `design_from_scene` **welds on the way out**, so a scene whose corners are not shared at all emits a document that passes all fifteen (measured: 20 → 10 vertices, 16 → 12 walls, `merged=4`, `check(deep)` CLEAN). Row 44's sibling one layer down. Proposed instrument, to be scoped: a **scene-level** check that geometric coincidence implies identity.
4. **Register row 49 — I11 speaks nowhere in the shipped app.** Deep-only *plus* shadow mode off by default compose into a hole neither has alone, and I11 is the invariant that caught the real `planc1.json` corruption this migration was started for. Measured on one corrupt scene: `FP_VERIFY_DESIGN` unset → **the save wrote the file** with I5b ×1 and I11 ×3; `=1` → refused; `=deep` → refused. Proposed fix: run the deep set at **document boundaries** (load, save) regardless of shadow mode, keeping the cheap twelve for editing.
5. **Grid snap.**
6. **Phase 5 — Landscape** (P5.1 site levels/categories/area accounting, P5.2 landscape wall types + gates, P5.3 site schedule fields + reports).

**Patrick will ask separately for the consolidated feature-and-phase document. Do not start it unprompted.**

---

## 3. What Phase 4 settled, in one place

- **Rooms are movable units** (P4.2): `extract_room` lifts a room out of the network (I12 by construction), `join_room` welds it back; a placed room's label-drag *is* extract → move → join.
- **Groups move the real items** (P4.5): `duplicate_wall` is dead, all four `group() is None` guards retired (**visibility before permission**, one sub-commit each), `merge_all`-on-ungroup gone, the `rigid` carve-out retired with its expired justification kept verbatim. Group the whole 20-room plan, move, ungroup → **189 → 189 scene items, zero new objects**, against the review's ≥106 duplicate walls and ≥149 duplicate openings on that gesture.
- **Deform-to-follow** (defect 23, ruled §2a): a room the band only partly took follows the corners that moved — *because the corner moved*, not because anything holds it back. Clipped band: Garage **0 of 9 → 7 of 9** corners, PKT Off 0 → 5, Util 0 → 3.
- **One gather, three gestures**: `rooms_holding` (in `rooms.py`) is the single definition used by the group bake, Align to grid and Distribute, and it widens to every room **and every wall** holding a moved corner.
- **The P3.1 split-on-write shim is gone**: `p1`/`p2` setters, `_carry_anchors`, `Vertex.moved_to`, `split_count`, `split_sites`, `note_vertex_splits` — 178 lines. The operation survives as **`WallItem.detach_end`**, named for which of the two things it is (`Vertex.at` = a new corner; `relocated_to` = the same corner moved). **The guarantee moved to the gate: `end_assign=0`.**
- **Defects closed in Phase 4:** 17, 25, 30, 34, 35, 13 (drag half), 36, 37, 3, 11a, 23. **Filed not fixed:** 47, 48, 49, plus 41, 42, 43, 44, 45.

---
## 4. What to read, in order

1. **`CLAUDE.md`** — architecture and house rules.
2. **`docs/WORKING_AGREEMENT.md`** — the Working agreement (census doctrine; the P4.5-era rules, of which the newest are **a bug can mask a bug**, the **fifth vacuity shape** (unsatisfiable), **telemetry retires with what it measured**, and **grep for identifiers, parse for shapes**). *Extracted verbatim from the migration plan on 2026‑08‑06 — the rules outlive the migration.*
3. **`docs/V5_MIGRATION_PLAN.md`** — the Status table with the **Phase 4 complete** mark, and the Progress log's P4.5 blocks ending at the merge entry.
4. **`docs/CODE_REVIEW_v2.md`** — the register. Rows 3, 11a, 23 and 36 closed at P4.5; **rows 47, 48, 49 are the open queue** and row 11 carries the z rule for the half that did not land.
5. **The P4.5 sub-commits** — each carries its own differential receipt; the four-guard sequence also carries the row‑36 watch result.

---

## 5. The rules that bind the work

Unchanged, plus these added during P4.5 (all in the Working agreement): **a green signal is only evidence about what it measures** (with the artifact→check table); **retire visibility before permission**, and enumerate a view's consumers first — those that scope themselves by it are permission grants in disguise; **a task that changes what an operation does owes a differential receipt** alongside the green gate; **vacuity has three shapes**, only tautology is machine-detectable; **negative assertions are where vacuity concentrates**, so preconditions are mandatory there; **verify a probe — and a record edit — actually landed**; **measure survival justifications** like any other claim; **in a test, call the production predicate rather than restating it**; and **a tidy-up pass that outlives its mess only touches things nobody asked it to**.

**~~Carried over from the viewer-furnishings branch~~ — DONE 2026‑08‑05.**
Row 41's reproduction stated `python -m floorplanner.viewer.fp3d …`, the form
`floorplanner/viewer/VIEWER_NOTES.md` §1 documents as **breaking the viewer's
isolation** (`-m` imports the parent package, hence the whole editor). It could
not be fixed from the branch that found it, which did not own
`CODE_REVIEW_v2.md`; merging `main` in gave this branch both files, and the row
now states the script form. Kept here rather than deleted because it is the
worked example of the rule above: *a record edit belongs on the branch that
owns the file*, and the wait was one merge long.

---

## 6. Things that will waste your time if you don't know them

- **A running app keeps the code it imported** — the status-bar version label shows the launch identity; restart before re-testing.
- **`gh` is not on `PATH`**: `& "C:\Program Files\GitHub CLI\gh.exe"` (PowerShell) or `"/c/Program Files/GitHub CLI/gh.exe"` (bash).
- **`.gitattributes` now forces LF**, so the CRLF phantom-diff class is closed structurally — but the working tree still checks out CRLF, so multi-line `\n` patterns in ad-hoc scripts still match nothing. Use `tools/record.py`, which handles it once and verifies.
- **`git commit` after `git add` commits the WHOLE index** — use `git commit <paths>` when anything else is staged.
- **Macro replay geometry matters**: a `.fpm` replays correctly only at the window geometry it was recorded at; each pinned test states which.
- **The suite's console is cp1252** — no non-ASCII in test output.
