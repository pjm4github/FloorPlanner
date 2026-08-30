# 0122 — report: [PR #43](https://github.com/pjm4github/FloorPlanner/pull/43) merged — D81/D82 closed; the 45° labeling gap confirmed as [`0119`](0119-ruling.md)/[`0120`](0120-ruling.md)'s own scope, next as its own effort

**Patrick, direct, 2026‑08‑30:** *"the pdf-dimention-and-door-fix looks pretty
good. lets merge that. The walls at 45 degrees are not labeled correctly yet
in the PDF but lets merge then setup another focused effort to clean that
up."*

## 1. What passed

`0118`'s check (station clustering + telescoping whole-inch labels, door
symbols keyed off the real catalog) — approved as built, no further changes
asked. **Merged: [PR #43](https://github.com/pjm4github/FloorPlanner/pull/43)
→ `main` at `36fb6b5`.**

## 2. What's still open — not a regression, the next tranche's own subject

**The 45° wall labeling Patrick names is [`0119`](0119-ruling.md) §1's own
measured gap, not a new finding:** an angled wall's length appears nowhere on
the sheet today, and an opening in one is absent from every dimension string
(`_features()`'s opening-centreline code only fires for
`abs(uy) < 1e-6`/`abs(ux) < 1e-6` — axis-aligned walls only). `0118` never
touched this path; `0119`/`0120` exist specifically to close it (aligned
dimension lanes, `0120`'s room/`show_dimensions`-driven placement superseding
`0119` §2). **Confirmed, not re-diagnosed** — Patrick's own observation lands
exactly on the gap already on record.

## 3. Disposition

**D81 and D82 closed** — both defect records updated (`state: closed`,
`state_reason: completed`, `closed: 2026-08-30`), citing this report and PR
#43's merge. `docs/defects/INDEX.md` regenerated.

**The 45° fix is queued as its own focused effort, per Patrick's own framing
here** — `0119`'s §3 `dim_row_along` refactor (GREEN, no visible change)
first, then `0120`'s room-driven angled-lane feature (AMBER, its own branch,
its own check). Order unchanged from `0119` §4 / `0120` §4; both explicitly
require `0118`'s station machinery, now merged, so nothing blocks starting.
