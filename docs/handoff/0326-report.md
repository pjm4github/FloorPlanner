# 0326 — report: the furnishings lane (STAIRS 0323 + VEHICLES 0325) gated and committed as TWO commits by path on branch `furnishings-lane`; the 0325 §0 tree questions answered; both AMBER, not merged

**Code, 2026-11-14.** His order: *"Read 0325 §0 first. Then gate, and commit the
stairs lane and the vehicles lane as separate commits by path. Report in the next
number. Do not merge — both are AMBER."* This is that report.

## 0. THE 0325 §0 TREE QUESTIONS — ANSWERED FIRST

1. **The stale `.git/index.lock` (0 bytes, 17:20) is removed.** It was the
   reviewer session's, orphaned by its read-only `git status` (0319 §4 — that
   session runs no more git). With the reviewer held and no git running, Code
   deleted it by hand (`rm .git/index.lock`); git works.
2. **0324 §5's "committed … (done)" was WRONG, now corrected in 0324 itself.**
   The stairs commit never happened: it was blocked first by the mailbox-on-a-
   branch rule (0084 §4 — the mailbox lands on `main`), then by the reviewer's
   concurrent vehicles edits turning the tree stale under the gate. The GREEN
   gate (0324 §2) was a real measurement; the commit claim was premature. The
   stairs files stayed untracked until this landing.
3. **The two `reset: moving to HEAD` were Code's own `git reset` (mixed, index
   only).** After each blocked commit above, Code unstaged with `git reset -q`
   to leave a clean index — NO working-tree file was changed, nothing was lost,
   and every lane file stayed exactly as the reviewer wrote it (confirmed by the
   diffs that follow). They were not `--hard`.

## 1. THE GATE — FULL, ON THE COMBINED LANE

Run on `furnishings-lane` (off `main`), both lanes present, none of Code's camera
/dormer work in the tree. VERBATIM:

```
Docs-Snapshot: cut against 5d55c1c, which is HEAD
Gate-Census: collected=2215 ruff=clean vacuous=0 end_assign=0 snapshot=current
Gate-OFF: 2208 passed, 7 deselected, 3 warnings in 120.92s (0:02:00)  -> sum 2215  OK
Gate-ON: 2208 passed, 7 deselected, 11 warnings in 143.61s (0:02:23)  -> sum 2215  OK
Gate-Verdict: GREEN (every sum reconciles against --collect-only)
```

**No failures.** `ruff` clean. Collected 2135 → 2215: the 68 stair + 12 vehicle
cases. `Gate-ON` runs `FP_VERIFY_DESIGN=1`. The freeze receipts
(`test_framing`, `test_undo`) and `test_gen_assets` are green; the vehicles edit
to `test_viewer_model.py` (a lofted kind expected in the partition's third list)
passes under real pytest, which 0325 §4 had not run.

## 2. THE TWO COMMITS, BY PATH

Per 0323 §7 and 0325 §7, on branch `furnishings-lane`, two commits:

- **STAIRS** (0323 §7, plan + parametric side): `floorplanner/parametric/` (8
  files), `floorplanner/items.py`, `floorplanner/view.py`, the four
  `tests/test_stair_*.py`, `docs/furnishing-spec/`.
- **VEHICLES** (0325 §7, the 3D + assets): `_gen_assets.py`,
  `assets/furnishings/` (whole, regenerated), `floorplanner/viewer/fp3d.py`,
  `tests/test_vehicle_profile.py`, `tests/test_viewer_model.py`,
  `docs/evidence/0325-vehicles/`.

**`fp3d.py` carries BOTH lanes' hunks** (`build_stair` and `build_vehicle`).
0325 §7 allowed `git add -p` or "commit the file once and say so"; `git add -p`
is interactive and unavailable here, so **`fp3d.py` is committed once, in the
VEHICLES commit**, and it carries the stairs `build_stair` hunk too — said so
here. The two commits are therefore stacked on one branch (stairs, then
vehicles): the stairs commit is the plan/parametric side, the vehicles commit
the 3D build and the regenerated assets for both.

## 3. NOT RULED ON

The gate tests behavior, not design. The known gaps/limits (0323 §5, 0325 §5)
and Patrick's checks (0323 §6, 0325 §6) stand; nothing is merged. Both lanes are
AMBER — his look at the 3D view is the merge condition.

## 4. OWED

- **Code:** this report; the two commits on `furnishings-lane` (done); hold for
  his checks before any merge.
- **Reviewer:** fixes from the gate (none — it is green) and from his checks, in
  the next ruling; no git.
