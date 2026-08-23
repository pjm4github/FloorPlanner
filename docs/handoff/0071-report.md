# 0071 — report: D80 bisected, root-caused, fixed — PR #36 open, batched

**On [`0070-ruling.md`](0070-ruling.md).** §5's full order done: the bisect,
the A/B, the fail-first receipt, the one fix, D80 filed, both intake files
promoted. Numbered `0071` — `0066` stays reserved for item C.

---

## 1. THE BISECT — replayed `w7offgrid.fpm` one line at a time, both ways

Built a headless script (`QT_QPA_PLATFORM=offscreen`, matching this
project's own scratch-script pattern) that runs `win.run_macro(line)` one
line at a time and dumps every `WallItem`'s `p1`/`p2` after each, flagging
the first coordinate that is not congruent to `0 mod wall_snap_in`.

**Run 1 — default settings** (`wall_snap_in=6.0`, `auto_weld`/`auto_coalesce`
both on, matching `fixtures/w7offsetFloorplan.json`'s own saved settings):
first off-grid vertex appears at line 6, `CLICK 63 359 DRAG 206 360` —
**a fresh wall DRAW, not a move.** Four more walls go bad at lines 7, 11, 12,
14 as the interior partition loop completes.

**Run 2 — the A/B, `auto_weld`/`auto_coalesce` both OFF:** **identical
pattern, same lines, same walls.** This is `0070` §5 item 2's decisive
result: *"if the vertices land on grid, the seed is in the normalisation...
if they still drift, it is the draw path."* They still drift, unchanged by
turning weld/coalesce off entirely — **the seed is the draw, not
normalisation.**

The exact off-grid VALUES my replay produced differ from `0070`'s own
measurement on the archived file (this implementation's headless window
never had the same view transform Patrick's session did — `CLAUDE.md`'s own
"macro replay geometry matters" note, and `0070` §1 already flagged it could
not run the macro at all). **The mechanism reproduces identically; the
digits don't need to, and the fix doesn't depend on them matching.**

## 2. THE MECHANISM, NAMED EXACTLY

Line 6 draws a new wall starting near an existing wall's BODY (a T-junction,
not an endpoint) — the outer rectangle's left side, `(60,300)`-`(60,420)`.
`PlanView._snap_start` (`view.py`):

```python
q = nearest_wall_endpoint(self.scene(), sp, tol)
if q is None:
    q = nearest_wall_body_point(self.scene(), sp, tol)   # <- raw projection
return q if q is not None else wall_snap(sp)              # <- snap only here
```

`nearest_wall_body_point` returns the exact geometric projection of the
click onto the host's centreline (`walls.py:171`) — never rounded to the
grid. `wall_snap()` only runs in the fallback, when nothing is nearby at
all. The new wall's start point silently inherits whatever fraction the
click landed on along the host's length, and the default (non-Ctrl)
move/slide path (`0070` §3) snaps the *displacement*, never the
*destination* — so nothing downstream can ever correct it.

**This is `0070` §4's open question, answered**: the first bad step is a
DRAW at a T-junction, not a MOVE. `view.py:230`, row 1 of `0070` §3's own
table.

## 3. THE FIX — one site, per `0062`/`0063`'s standing rule

`_snap_start` now calls `nearest_wall_body` (not `_point`) to get both the
host wall and the projected point, and a new `_grid_snap_t_junction` snaps
the position ALONG the host to the grid, leaving the coordinate ACROSS it
untouched — the point stays exactly on the host's centreline. Only for an
axis-aligned host (horizontal or vertical, `abs(dy) < 1e-6` /
`abs(dx) < 1e-6`); a diagonal host has no single grid position to round a
point onto, so that case is unchanged from before.

**Scoped to this one call site.** `nearest_wall_body`/`nearest_wall_body_point`
themselves are untouched — the other three call sites (`walls.py:558,980,1040`,
weld/fuse machinery) are unaffected, matching `0062-report.md` §3 /
`0063-ruling.md` §2's rule against fixing sites with no receipt behind them.

**Re-ran both bisect configurations against the fix: every wall in both runs
now lands exactly on grid** (`60/300/348/390/420/108/204` — all exact
multiples of 6), confirming the resolved coordinates land on the same grid
lines `0070` §2 named as the intended targets (`y=348`, `y=390`).

## 4. THE RECEIPT — checked to actually discriminate, not assumed

Three new tests in `tests/test_walls.py`:

- `test_t_junction_start_snaps_along_the_host_wall_to_grid` — unit-level,
  calls `win.view._snap_start(...)` directly against a synthetic T-junction.
- `test_t_junction_start_on_a_diagonal_host_is_unchanged` — the negative
  control for the diagonal-host exemption.
- `test_w7offgrid_macro_lands_every_vertex_on_the_snap_grid` — the macro
  itself is the reproduction (`0070` §5 item 3's own instruction), replayed
  on a blank canvas, asserting every produced vertex is on-grid.

**Confirmed RED against the unfixed code, GREEN after — reverted the fix
locally, re-ran, both new tests failed with the exact off-grid values,
restored, both passed.** Full regression: `pytest -m "not gui and not slow"`
(732 passed) and `-m gui` (55 passed) both green, `ruff` clean, full gate
GREEN, `collected=796`.

## 5. THE INTAKE EXIT AND D80

Both files promoted from `fixtures/incoming/` to `fixtures/` under exit 1
(`fixtures/README.md`'s new entry), the fail-first test naming them, per
`0070` §6. [D80](../defects/0080-a-fresh-wall-started-at-a-t-junction-inherits.md)
filed — **open**, fix built and gated GREEN, closes once Patrick's manual
check passes and a ruling says so, not before.

## 6. WHERE THIS LIVES — [PR #36](https://github.com/pjm4github/FloorPlanner/pull/36), AMBER, batched

Branch `t-junction-grid-snap`, gated GREEN, PR opened, stopped — nothing
merged. Per `0070` §7's own table, batched with PR #34 and PR #35's manual
checks, all three now one app session:

> 1. **PR #34** — *"With the second floor hidden, does a wall you draw still
>    jump to something you cannot see?"*
> 2. **PR #35** — a wall you believe is straight must say nothing about its
>    angle; a wall you believe is crooked must not claim an exact cardinal.
> 3. **PR #36** — *"With snap set to 6″, draw and then slide an interior
>    wall inside an existing room. Does every corner land on a 6″ line?"*
> 4. **One line for the record** — is the status-bar label what you asked for?
> 5. **`0068` §4** — off-axis walls: heading, or how far off axis?

## 7. WHAT REMAINS

- **Item C** — `0066`, Patrick's, not attempted.
- **`0070` §5's un-ordered note** — `grid_snap`'s default step (`SNAP_STEP =
  1.0`) and `items.py:71`/`478` calling it with the default, not
  `wall_snap_in`: a second, finer grid on a path nobody has enumerated. Not
  investigated here, named as `0070` left it.
- **The follow-on hardening pass** — `0062` §3's four masked reachability
  sites, `0063` §5's `wall_endpoint_open(floor=None)` default.

## 8. TIER

**GREEN** — the bisect and A/B are measurement; the fail-first test and D80
filing are GREEN by `0070` §7's own table; the fix itself is **AMBER**, on
PR #36, not merged.
