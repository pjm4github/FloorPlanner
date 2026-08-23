---
# permanent key, independent of GitHub
id: 80
title: "A fresh wall started at a T-junction inherits an un-snapped position along the host wall"

# maps directly onto GitHub Issues fields
state: open
state_reason: null
labels:
  - type:defect
  - area:geometry
milestone: null

# ours; becomes body prose after migration
opened: 2026-08-22
closed: null
closed_by: null
rank: 80
related: []
state_source: row
github_issue: null
---

# D80 — A fresh wall started at a T-junction inherits an un-snapped position along the host wall

**Filed per [`handoff/0070-ruling.md`](../handoff/0070-ruling.md) §5 item 5 —
Patrick's own reproduced report**, his second in this thread
(`fixtures/w7offgrid.fpm` / `fixtures/w7offsetFloorplan.json`, promoted from
`fixtures/incoming/` under exit 1). Bisected, root-caused and fixed in
[`handoff/0071-report.md`](../handoff/0071-report.md) (see that file for the
full receipt trail).

## The finding

`PlanView._snap_start` (`view.py`), when a click lands near an existing wall's
BODY rather than its endpoint, returns `nearest_wall_body_point()`'s result —
the raw geometric projection of the click onto the host wall's centreline —
**verbatim**, with no grid-snap applied. `wall_snap()` only runs in the
fallback branch, when nothing is nearby at all.

A fresh wall started this way (a T-junction against an existing wall) silently
inherits whatever fraction-of-an-inch the click happened to land on along the
host's length, and **no later operation can ever remove it**: the default
(non-Ctrl) move/slide path snaps the *displacement*, not the destination
(`0070-ruling.md` §3), which preserves an existing off-grid offset exactly,
forever.

## Reproduction

`fixtures/w7offgrid.fpm` replayed on a blank canvas with `wall_snap_in = 6.0`
(matching `fixtures/w7offsetFloorplan.json`'s own settings) produces two
walls whose shared T-junction vertices sit at fractional inches — measured
independently by `0070-ruling.md` (`347.5515`, `389.0628`) and, on this
implementation's own bisect, at different but structurally identical values
(the exact fraction depends on the click's mapping through the current view
transform; the fault does not). **Reproduced identically with `auto_weld`/
`auto_coalesce` both on and off** — ruling out weld/coalesce normalisation as
the seed; the fault is in the draw path itself, confirmed by replaying the
macro one line at a time and finding the first off-grid vertex appears the
moment the T-junction wall is first drawn, not on any later move.

## Fix

`_snap_start` now asks `nearest_wall_body` (not `_point`) for both the host
wall and the projected point, and a new `_grid_snap_t_junction` helper snaps
the position *along* the host to the grid while leaving the coordinate
*across* it untouched — so the returned point stays exactly on the host's
centreline. Only for an axis-aligned host (horizontal or vertical): a
diagonal wall has no single grid position to round the point onto, so that
case is returned unchanged. Scoped to this one call site
(`view.py:_snap_start`) — `nearest_wall_body`/`nearest_wall_body_point`
themselves are untouched, so the other three call sites (weld/fuse
machinery, `walls.py`) are unaffected, per `0062-report.md` §3 /
`0063-ruling.md` §2's standing rule: fix the site the bisect names, not
every site that shares a helper.

## Receipt

Fail-first: `tests/test_walls.py::test_t_junction_start_snaps_along_the_host_wall_to_grid`
and `::test_w7offgrid_macro_lands_every_vertex_on_the_snap_grid` both
confirmed RED against the unfixed code, GREEN after — a real differential,
not asserted. A third test,
`::test_t_junction_start_on_a_diagonal_host_is_unchanged`, is the negative
control for the diagonal-host exemption. Full regression: `pytest -m "not
gui and not slow"` and `-m gui` both green, `ruff` clean.

## Ruling

*(Open — filed 2026‑08‑22. Fix built and gated GREEN, AMBER tier per
`0070-ruling.md` §7 item 3 — batched with PR #34/#35's manual check, not
merged. Closed once Patrick's check passes and a ruling says so.)*
