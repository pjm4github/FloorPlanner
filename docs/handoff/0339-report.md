# 0339 — report: 0337's ruff fixed; the stair delta (0335) and the 0338 delta (fixtures, island slots + plan symbol, grab bars, the stairwell cut) gated and committed by path on one branch, AMBER

**Code (Claude Opus 4.8), 2026-11-15.** Answers [`0338-ruling.md`](0338-ruling.md),
and closes the commit [`0337`](0337-report.md) held open. Tier: **AMBER** — the
gate decides the branch commit; the merge waits on Patrick's check (`0335` §5 +
`0338` §7), not here.

## 1. The gate — the combined 0335 + 0338 delta in the tree

`0338` §6: the two deltas share `stair_geometry.py`, so they land together. Full
(OFF+ON), everything in the working tree, after restoring the icon LF noise
(`0338` §1 / §4):

```
Gate-Census: collected=2441 ruff=clean vacuous=0 end_assign=0 snapshot=current
Gate-OFF: 2434 passed, 7 deselected, 3 warnings in 124.20s (0:02:04)  -> sum 2441  OK
Gate-ON:  2434 passed, 7 deselected, 11 warnings in 147.06s (0:02:27)  -> sum 2441  OK
Gate-Verdict: GREEN (every sum reconciles against --collect-only)
```

**GREEN. No failures, ruff clean.** 2441 collected = 2378 (last cycle's
stair-only count) + 63 from the `0338` tests (`test_fixtures`,
`test_fixtures_viewer`, `test_stairwell`, and the 7 Qt cases appended to
`test_cabinet_item` — `_paint_plan_symbol` among them, which `0338` §4 says had
never executed). OFF and ON both reconcile to 2441; 2434 pass, the 7 deselected
are the perf lane. The ruff that was RED in `0337` §1 is clean (`0338` §1's fix).

## 2. What committed, and where

The mailbox lands on `main`; the code lands on ONE branch off that mailbox
commit (`0338` §6; the hook refuses a new `docs/handoff/NNNN-*.md` off `main`,
`0337` §2 — the same split as last cycle, now accepted in `0338` §1).

- **On `main` (the mailbox commit):** `docs/handoff/0335-ruling.md`,
  `0336-ruling.md`, `0337-report.md`, `0338-ruling.md`, this `0339-report.md`;
  the regenerated `docs/STATUS.md` + `docs/handoff/README.md`; the re-cut
  `docs/SESSION_SNAPSHOT.md`.
- **On `stairs-0338` (branched off that commit):** the combined code / schema /
  assets / tests / evidence by path —
  - stair (0335): `floorplanner/parametric/stair_geometry.py`, `stairs.py`,
    `stair_view.py`, `dialog.py`;
  - fixtures + island + grab bar + stairwell cut (0338):
    `floorplanner/parametric/cabinet_geometry.py`, `cabinets.py`, `registry.py`,
    `floorplanner/items.py`, `floorplanner/viewer/fp3d.py`, `_gen_assets.py`;
  - shared: `floorplanner/design/design-schema.v6.json` (`$defs/stair_state` +
    `$defs/fixture_state`), `docs/furnishing-spec/STAIRS_STATE_AND_USAGE.md`;
  - generated assets: `assets/furnishings/{manifest,materials,groups}.json`,
    `assets/furnishings/grab_bar.svg`;
  - tests: `tests/test_stair_validation.py`, `test_stair_viewer.py`,
    `test_stair_rails.py`, `test_fixtures.py`, `test_fixtures_viewer.py`,
    `test_stairwell.py`, `test_cabinet_item.py`, `test_viewer_model.py`;
  - evidence: `docs/evidence/0335-stair-rails/`, `docs/evidence/0338-fixtures/`.

**`dialog.py` carries Code's own fix** (the scroll area + tight rows + screen
clamp, Patrick 2026-11-15, "dialog box looks great"), folded into the stair
delta as it shares that lane. **Not committed:** `assets/icons/*` (restored to
HEAD — `0338` §1), `docs/gallery/*`, `docs/screenshot.png`, `fixtures/incoming/*`,
and the unrelated untracked `docs/StyleGuides/`, `gen/`, `docs/macro-spec/…/gen/`.

## 3. The `fp3d.py` floor / ceiling hunk — read before gating (`0338` §3)

~180 lines changed, the stairwell cut among them. What it does: `stair_openings`
collects, per PARAMETRIC stair, the world-frame stairwell quads and the foot/head
heights (legacy stairs — no parameters — return nothing and cut nothing);
`holes_at(z_lo, z_hi)` selects the quads a surface at that height passes through.
A floor slab over a stairwell, and that storey's interior ceiling, are then built
as CONVEX PIECES — each floor/ceiling triangle minus each quad via
`_cut_holes` → `_minus_convex` (Sutherland–Hodgman half-plane peel of a convex
ring against a convex hole) → `_ngon_prism` (a prism over a convex ring of any
length, also now used for n-gon cabinet parts like the toilet bowl). **Every room
with no stairwell over it takes the OLD indexed-slab path unchanged** (the
`else:` branch is the prior code verbatim), and the ceiling cut happens before the
existing roof clip, so a plan with no parametric stair is unaffected. Coherent;
the coordinate transform matches the world frame `(x, -plan_y)` the rest of the
builder uses. Render not asserted (D77); `tests/test_stairwell.py` pins the cut
on the data.

## 4. Patrick's check (one sitting — `0335` §5 + `0338` §7)

Run from `stairs-0338`. **Stairs:** U-stair gap 4.5 widens the plan symbol, the
flights part, the foot stays; left side = Wall gives a wall handrail inside, a
guard outside and round the landing; the validation box loses "handrails not
modelled," and stating the opening + both landings 36 leaves only the code
notice; an existing parametric stair shows rails in 3D. **Fixtures:** toilet, tub,
bookshelf, gas fireplace, grab bar in 3D, each double-clickable; fireplace Lit
off/on, Surround = brick; the tub no longer holds water. **Island:** set one slot
Bar sink, another Range, change Seats — the plan symbol and the 3D both follow.
**Stairwell:** a two-storey plan with a parametric stair is open in the floor
above and in the ceiling below over the stair. On your OK, `stairs-0338` merges.

## 5. Owed

- **Reviewer (Cowork):** any fixes from §1. No git.
- **Patrick:** the one-sitting check (§4).
- **Code:** on Patrick's OK, merge `stairs-0338` to `main` and record it.

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01XVitzXNKQWS64xhKKpacra
