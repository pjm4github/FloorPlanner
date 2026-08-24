# 0102 — report: `0100-ruling.md` §1 built — the report names walls Patrick can find

**On [`0100-ruling.md`](0100-ruling.md) §1, composed with [`0101-ruling.md`](0101-ruling.md)'s
map.** Numbering collision, on the record: this session's own read-back
landed as `0101-report.md`, sharing its number with Patrick's own
`0101-ruling.md`. Neither renamed; numbering continues from `0102`.

## What changed

`bridge.design_from_scene(..., report=rep)` now populates
`rep["wall_items"]`: `{final canonical wall id: WallItem}`, exactly the
composition `0101-ruling.md` §2 named (the `src` out-param `_walls_of`
already builds, correlated through `canonicalize()`'s renumbering by
Python object identity on the wall dict itself — `canonicalize` mutates
the same dicts in place, never copies).

**Found while wiring it: the natural first draft accumulates this map
per-level, like its sibling `of_item` beside it — which is correct for
`of_item` (consumed within that same level's iteration) and silently wrong
here (`wall_items` is read once, after the whole roster loop, against the
fully accumulated `walls` list). A two-floor plan would have kept only the
last floor's walls. Caught with a fail-first test before it shipped, not
after.**

`OrthogonalityReportDialog`'s rows now carry both ids and the endpoints in
feet: `default: W7 · w19 (interior) at (46.50, 35.50) -> (48.00, 34.00)ft —
45.00deg off axis (would move 3.000" if straightened)` — matching `0100`
§1's own ruled shape, with the existing displacement clause kept rather
than dropped.

**Not built:** click-to-select, the shared row widget, modeless dialogs,
Coalesce's preview, or the gaps-dialog treatment (`0100` §§2-4) — those
still need the remaining read-back answers this session's own
`0101-report.md` only proposed, not ruled on. The repair preview (PR #37)
gets the same label fix next, on its own branch, since `0098` §2 named it
as the other thing blocking that check.

## Receipt

New fail-first test (`test_wall_items_covers_every_floor_not_just_the_last_0101`,
`tests/test_design_bridge.py`) — confirmed RED against the per-level
accumulator (4 of 8 walls mapped), GREEN after moving it outside the
roster loop. New dialog test pins the exact row format. Full suite 852
passed, `ruff` clean, gate GREEN.

## Tier

**AMBER** — `0100` §6's own tier, not `0098`'s earlier GREEN read on the
coordinates-only version; this shows both ids, which changes what the
user sees beyond a report gaining a column. Branch:
`wall-report-id-fix`. Batched with PR #37's check, once that PR's own
preview gets the same fix.
