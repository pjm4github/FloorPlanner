# Session snapshot — read this first

**Re-cut 2026‑08‑05 END OF P4.5, on branch `p4.5-groups-zorder` @ `c20c55a`.** P4.5 is **code-complete**; what remains is Patrick's ten-item mini-gate and the merge. This file exists so a fresh session can start from disk instead of from a chat summary. It is an **index and a state marker, not a second copy of the record** — where it points at another document, that document is authoritative and this one must not be trusted over it.

---

## 1. Where the work stands

| | |
|---|---|
| **Branch** | `p4.5-groups-zorder`, branched from `main@adaa519`, **39 sub-commits `fbbebf4` … `c20c55a`**, each at a full green gate. **PR open, held for the mini-gate.** |
| **`main`** | `adaa519` — P4.1, P4.1b, P4.2, P4.3, P4.4 all merged and ticked; the 3D viewer packaged and its popup merged (PRs #4–#8). |
| **Census** | **633 collected** (625 passed, 7 deselected, 1 xfailed), ruff clean, `vacuous=0`, **`end_assign=0`**, every sum reconciling in all three modes. |
| **Working tree** | clean (only untracked screenshots). |

**P4.5 is the second designated MINI-GATE task — its PR does not merge until Patrick runs the gate.**

---

## 1a. The three branches are RESOLVED — 2026‑08‑05

| branch | disposition |
|---|---|
| **`p4.5-groups-zorder`** | `5316d35` — **clean, green, pushed.** Everything below landed here. |
| `p4.5-defect23-wip` | **absorbed.** `4e967c0` cherry-picked at P4.5(30) with its F401 fixed; the scratch branch is now history, not a parking place. |
| `p4.5-align-wip` | **discarded, as its own commit message predicted.** Rewritten at P4.5(32) against the finished gather; its code did not survive, its measurements did. |

**Defect 23 is closed and both parked xfails are hard passes.** The clipped band
went from three stranded rooms (Garage 0 of 9 corners against 6 of 9 walls) to
20 of 20 coherent. Neither xfail flipped on the mechanism alone — and in **both**
cases the test was wrong, not the mechanism: one compared walls-moved to
corners-moved when *a run of k walls has k+1 corners*, the other asked for a
delta that yields a non-crossing quadrilateral. Both are recorded in the
Progress log, because "the receipt did not flip" was carried for a day as
evidence against a mechanism that was working.

**The fragment ruling (2026‑08‑05).** Diagnosis: **masking** — `fragment`'s
product was already broken (20 `Vertex` objects on 10 points, `room_owns_walls`
false for all nine pairs) and split-on-write hid it by detaching the group's
walls from every outline. Remedy accepted in principle, **deferred**: register
**row 47**, the first task after P4.5 merges. Evidence:
`docs/evidence/defect23-fragment.json`, reproducible with the probe beside it.

**Two gaps larger than fragment, both filed, neither P4.5's:** **row 48** — the
invariants have never checked the scene the user edits, because
`design_from_scene` welds on the way out; **row 49** — I11 speaks *nowhere* in
the shipped app, since it is deep-only and shadow mode is off by default, so
the save refusal ruling 2a assumed does not happen.

**ONE PIECE STOPPED, deliberately, and it needs a ruling: deleting the `p1`/`p2`
setters.** The completeness proof it existed for is already delivered — `grep`
returns **zero** writers in `floorplanner/`. But `Vertex.moved_to` is the only
thing that increments the split counter and the setters are its only callers,
so deleting them freezes `split_count()` at 0 and turns **six** live watches
(`test_topology_ops` ×2, `test_wall_move` ×3, `test_view` ×1) into tautologies
that still read as coverage. See the P4.5(34) Progress-log entry.

**Also still open on the working branch:** defect 11's runtime z-order collapse
(unchanged, still needs the bounded event counter).

---

## 1b. Superseded — what the previous cut said was in flight

| branch | head | state |
|---|---|---|
| **`p4.5-groups-zorder`** | `8d7a914` | **clean, green, pushed.** The working branch. Everything below is parked OFF it so it stays shippable. |
| `p4.5-align-wip` | `5f679e9` | **parked, semi-disposable.** Holds the `align_rooms_to_grid` + `_translate_shape` fix (both relocate corners instead of assigning `p1`/`p2`). **To be REWRITTEN against defect 23's widened gather** — the code will not survive, the measurements in its commit message are the part that matters. |
| `p4.5-defect23-wip` | `4e967c0` | **parked RED.** Holds defect 23's deform-to-follow mechanism: `_corner_records` no longer splits a corner an outside wall also holds. Two faults open, one trivial and one unruled — see below. |

**Why the align work is parked behind defect 23.** Fixing align/distribute exposed a tear the old code was accidentally hiding: A and B share a party wall, B moves, so A's wall goes to x=150 while A's outline stays at 120. Split-on-write had been destroying identity, and destroying identity is what kept the neighbour intact — **a bug was masking a bug, so the correct fix presents as a regression.** The gather must widen first; then align and distribute inherit it and the tear cannot occur.

**Defect 23's state, measured.** The mechanism works: on the clipped-band case (2 of a room's 4 walls grouped, moved −400/+300) the outline went from **unchanged (stranded)** → **all 4 corners moved (rigid — the opposite error)** → **3 of 4 moved, 1 stayed (deform, correct)**. The middle state came from the legacy-repair branch minting records for corners the group never held; a fully-owned room still gets those (it travels whole), a partly-held room attaches to existing records only.

**Two faults open on `p4.5-defect23-wip`:**
1. **ruff F401** — `floorplanner.vertex.Vertex` is now unused in `items.py`, having existed only for the removed split. Trivial.
2. **UNRULED, and it must not be silenced:** `tests/test_rooms.py::test_fragment_groups_each_piece_with_its_own_walls` errors at `win` teardown with **`I11: 1 -> 3, I5b: 0 -> 1`**. Deform-to-follow makes the fragment operation deform rooms into overlapping regions and a self-intersecting outline. Whether `fragment` should extract first, or whether deform-to-follow needs a guard where the deform is degenerate, is **a ruling, not a repair** — adjusting the fragment op to make the error go away would be choosing semantics silently.

**NEITHER XFAIL FLIPPED.** `test_a_clipped_band_leaves_every_room_coherent` and `test_a_bake_that_crosses_an_outline_reports_at_the_gesture` both still xfail after the mechanism change, so it is **not sufficient** for them. This was predicted to flip them and did not — recorded as a failed prediction rather than left to be rediscovered.

**Also still open on the working branch:** `view.py:402`'s `_temp_wall.p2` (the last `p1`/`p2` writer), deleting the setters as the census's completeness proof, and **a tenth mini-gate item ruled but not yet written down**: exercise Align to grid and Distribute on a plan with shared party walls, checking rooms follow their walls and that a subsequent wall drag strands nothing.

---

## 2. What has landed on this branch

**The rulings first** (`fbbebf4`), before any code, per the standing rule.

**The four `group() is None` guards, retired one sub-commit each**, in the ruled order — **visibility before permission**:
1. `graph_from_scene` (`ac86173`) — the planner can see grouped walls.
2. `merge_wall` (`3ae48eb`) — a grouped wall may merge.
3. `weld_scene` (`e9aa54a`) — grouped ends snap. (Smaller than the census claimed: the *share* half had already opened at guard 1.)
4. `_edge_wall` (`53dd0e0`) — a room may re-bind to its own grouped wall. Differential receipt: **307 of 307 edges unrecoverable before, 0 after**.

**`duplicate_wall` is dead** (`ef22470`) — a group holds the real walls; `merge_all` on ungroup removed; the `rigid` carve-out retired (`9c7dcdc`) with its expired justification kept verbatim.

**Register row 36 CLOSED AT SOURCE** (`a298e78`): the release-merge rebind binds a room to a survivor only when the survivor spans an edge the room's outline names. Both producer paths measured; both watches converted from tripwires to ordinary regression tests.

**New register rows, all filed not fixed:** **41** (I5b misses a *pinched* loop; corpus fixtures recorded with the `fp3d --dump` reproduction), **42** (the drag has the same self-intersection exposure; three appliers named as a Phase‑6 consolidation candidate), **43** (sweep the suite for negative assertions — Phase 6), **44** (the invariants check *consistency*, not *history* — an **accepted limit**, with the differential-receipt consequence), **45** (`_edge_wall` answers by geometry — a known survivor; the walk/finder divergence named as **latent**, protected by call graph rather than semantics).

**Tooling/process added:** `tools/record.py` (anchored doc edits that verify they landed) and the gate's `vacuous=` check.

**Defect 3 is done** (`52a6aed`): groups serialize; `canonicalize` learned groups; `test_group_survives_roundtrip` flips to a hard pass.

---

## 3. What remains in P4.5

1. **Defect 11 — the runtime z collapse. STOPPED at a scope-changing measurement; needs a ruling before restarting.** The collapse hangs `test_drag_split_macro_keeps_every_room_rectilinear` at macro line 1 (the first drag), bisected to `geometry.py` alone, and **the trigger is the magnitude of the z step** — `(n−old) × 1.0` completes, `× Z_STACK_BAND` (100) hangs. Ruled out: no loop in the new code; the only `zValue()` read in the tree is `levels.py`'s idempotent floor-band delta; the macro's `_drag` has no convergence loop; `faulthandler` produced no traceback in three attempts. **The work was reverted** — nothing of it is on the branch. A separate, independently-correct fix was found and also reverted with it: `raise_to_front` assigns z absolutely while `bring_to_front` applies a delta, so each silently undoes the other's terms (the floor band included). Proposed next step: instrument the drag with a bounded event counter to find the consumer, rather than choosing constants to avoid a symptom.
2. **~~The P3.1 split-on-write shim~~ — GONE at P4.5(40).** The `p1`/`p2` setters, `_carry_anchors`, `Vertex.moved_to` and the whole split counter (`split_count`, `split_sites`, `note_vertex_splits` and its two logs) are deleted — 178 lines out. The operation survives as **`WallItem.detach_end`**, named for which of the two things it is. **The guarantee moved to the gate**: `end_assign=0` fails on any coordinate assignment to a wall end in `floorplanner/`. **The opening census MISSED FIVE writers** of the form `setattr(w, attr, p)` — a census by spelling finds only that spelling, and the deletion is what made the true count visible.
3. **~~The identity-churn sites~~ — DONE at P4.5(32).** `align_rooms_to_grid` and `_translate_shape` run on `relocate_corners` over the **finished gather**, which widens scene-wide to every room *and every wall* holding a corner being moved. Receipt is the **unselected neighbour**: sharing 4-of-4 → 2-of-4 → 4-of-4, open edges 2 → 0.
4. **~~The parked xfails~~ — BOTH ARE HARD PASSES** (P4.5(30), P4.5(31)). The only `xfail` left is the deliberate one against **row 47**.
5. **Patrick's mini-gate — TEN items** (item 10, ruled 2026‑08‑05: Align to grid and Distribute on a plan with shared party walls — rooms follow their walls, and a subsequent wall drag strands nothing), plus the **"deliberately still broken — do not report these"** list now in the plan beside the mini-gate ruling: **fragment (row 47)** and defect 11's hang. The cross-cutting dashed-edge watch **exempts the fragment gesture and nothing else**. Originally nine items (the eight from the read-back plus new **item 1**: group the whole plan of 20 rooms, move, ungroup, expect **zero new objects** and instant timing), **plus the cross-cutting watch: at every step, no room may show a dashed open edge where a wall actually exists.**
6. **PR into `main` as a merge commit**, after the mini-gate passes.

**Standing instruction: run the remainder as ONE BATCH and report once**, when the branch is ready for the mini-gate. Sub-commit per piece, differential receipt per piece, full gate throughout. Stop mid-sequence only for (a) a ruling not already held, (b) a measurement that changes a piece's scope, or (c) a finding that contradicts something already decided. Process observations go in the log; do not stop for them, and do not add Working-agreement entries unless a rule would have prevented a defect actually hit.

---

## 4. What to read, in order

1. **`CLAUDE.md`** — architecture and house rules.
2. **`docs/V5_MIGRATION_PLAN.md`** — Working agreement (census doctrine, the P4.5-era rules), Status table, P4.5 task text with its **corrected acceptance**, and the Progress log's P4.5 blocks.
3. **`docs/CODE_REVIEW_v2.md`** — the register; rows 36 and 3 closed here, 41–45 new.
4. **The four-guard sequence's commits** — each carries its own differential receipt and the row‑36 watch result.

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
