# 0319 — ruling: a FURNISHINGS LANE is open in the reviewer session, on Patrick's word; it is fenced off from Code's dormer/elevation work, and nothing in it has been touched yet

**Reviewer (Cowork), 2026-11-14.** Patrick, today: *"we will work on new set of
furnishings for the project. Make a markdown note that Claude Code can read and
see that you are working on the furnishing section that does not overlap with
the work CC is doing."* This file is that note. It is a lane claim, not a
verdict on any report — it takes 0319 because 0319 was the next free number;
**Code's in-flight dormer report takes 0320.**

## 1. STATE AS READ FROM DISK (not from a summary)

- `main` at `2696bc4` (merge of `full-elevation`, 0318). `.gate-result.json`:
  GREEN, full, collected 2135, written 2026-11-12T19:12.
- **Code has uncommitted work in the tree**: `floorplanner/cameras.py`
  (dormer faces tiered last in the house-elevation paint order, ~l.717) and
  `floorplanner/viewer/fp3d.py` (`_hidden_overhang_pieces`, ~l.1370-1460: host
  roof clipped to at-or-below a covering dormer's eaves). No report for it yet.
- The gate result predates those edits, so the tree is not currently covered by
  a green gate. That is Code's to re-run; it is noted, not ruled on.

## 2. WHAT THE LANE IS

Patrick will direct, in this order: (1) a read of how furnishings are built,
stored, created, rendered and catalogued; (2) more realistic 3D for furnishings
he selects; (3) new furnishings he selects, in categories he selects.

**Files the lane expects to touch** (to be confirmed by step 1, and corrected in
the next number if wrong):

| file | what |
|---|---|
| `_gen_assets.py` | the furnishing generator (assets are generated, never hand-edited) |
| `assets/furnishings/**` | regenerated output only: SVGs, `manifest.json`, `materials.json` |
| `floorplanner/catalog.py` | the catalog |
| `floorplanner/viewer/fp3d.py` | **furnishing regions only** — catalog/SVG reading (~l.160-520), "furnishing solids" (~l.1827-2250), the `# ---- furnishings` block of `build_model` (~l.3018-3160) |
| `tests/test_furnishings.py`, `tests/test_gen_assets.py`, furnishing cases in `tests/test_viewer_model.py` | tests |

**Out of the lane, Code's:** `cameras.py`, `roofs.py`, `roofclip.py`, `dialogs.py`,
and everything in `fp3d.py` outside the three regions above — roofs, dormers,
walls, openings, terrain. The lane will not touch them.

## 3. THE ONE SHARED FILE: `fp3d.py`

Both sides have business in it. The regions are ~370 lines apart at the nearest
point and do not share a function, so edits should not conflict textually — but
it is ONE working tree, and that is where the risk is:

- **Code: commit by path, never `git add -A` / `commit -a`**, while this lane is
  open — a sweep would fold furnishing edits into a dormer commit (or the
  reverse).
- **Code: before any `checkout` / `stash` / `restore` / `reset`**, look for
  uncommitted changes in the lane's files. They are the reviewer session's and
  one command from gone (WORKING_AGREEMENT, P0.6). Commit them as their own
  commit first, or stop and tell Patrick.
- **If Code needs to edit a furnishing region, or the lane needs a line outside
  one, that is a stop** — say so in the next number rather than doing it.

## 4. THIS DEPARTS FROM A STANDING RULE — NAMED, NOT SLID PAST

WORKING_AGREEMENT (P0.6, widened 2026-08-04): *"Cowork no longer edits ANY FILE
IN THE REPO DIRECTLY."* The project instructions say the same: reviewer, not
implementer. Steps 2-3 as Patrick described them have this session editing
furnishing code. **That is his exception to make and it is recorded here as
his stated intent, not as a rule change** — scoped to the furnishing files in §2,
and it needs his plain "yes" before the first code edit (asked in chat today).
Until then this session reads only.

How the exception stays safe, if he confirms it:

- Edits are made **in place through the device shell**, never by
  stage-edit-commit-back — the stale-staged-copy mechanism that cost P0.4-P0.6
  is not used at all.
- **This session runs no git.** Code commits the lane's work, by path, on a
  branch of its own, after a fresh gate.
- **Tier: AMBER.** New and re-modelled furnishings are user-visible. Patrick's
  look at the 3D view is the merge condition; checks will be batched.
- **The implementer is not its own reviewer.** Lane work is not ruled on by this
  session. The gate plus Patrick's AMBER check stand in; Code is free to object
  in a report.
- `assets/` stays generated: the generator is edited and re-run, and
  `test_gen_assets` must agree.

## 5. OWED

- **Code:** commit this file as a doc-only commit; add its README line; number
  the dormer report 0320.
- **Reviewer:** the next number in this lane reports the step-1 read and
  confirms or corrects the §2 file list **before** anything is edited.
- **Not done here:** no repository code, asset or test has been changed. This
  file is the only thing written.
