# 0359 — ruling: a dormer whose ridge is above the host's ridge is an ERROR, and is not built

**Reviewer (Cowork), 2026-11-17.** Answers [`0358`](0358-report.md). The
`dg` / kind changes are in the tree on `dormer-item`, un-gated; Code gates
and commits by path. Stand-in runner: 51 of 51. Not run: ruff, real pytest.

## 1. The rule — Patrick's word decides it

> "The ridge of the roof is under the dormer (which should be an error ;()"

- **`dormer.above_host_ridge` is an ERROR.** Condition: the dormer's ridge
  height is above the host's ridge height (both in the dormer level's datum).
  **Equal is allowed** — ridge to ridge is an ordinary cross gable. The
  message names a half-width that fits.
- **`dormer.level_host` is an ERROR** too: the host does not rise along the
  dormer's ridge (it faces up the slope, or its face is past the main ridge).
- **The straddle is not a second rule.** On a plane rising at the host's
  slope, a ridge higher than the host's meets it only beyond the host's own
  ridge line — so "astride the main ridge" IS `above_host_ridge`; and a face
  beyond the ridge reads a non-rising host, which is `level_host`. If Code
  can build a dormer that straddles the main ridge and trips neither, that
  is a counter-example: report it with its numbers.
- `dormer.no_host` and `dormer.buried` stay WARNING. My 0356 "reported, not
  a fault" was about a WINDOW above the ceiling line, not this; the ADVISORY
  here was my phase-1 call and it was wrong.

## 2. One rule for the dialog and the builder

`dg.unbuildable(st, host_z_face, host_slope, host_ridge_in)` returns
`OVER_RIDGE`, `FACES_UPHILL` or `None`. The kind raises its two ERRORs from
it and puts it in `derived["unbuildable"]`.

**Phase 3: REFUSE.** When `dg.unbuildable(...)` is not `None`, `fp3d` builds
no dormer roof and makes NO cut in the host — as for no host — and writes one
line to `model.notes` naming the dormer and the reason. No second test of the
condition in `fp3d`: call `dg`.

## 3. What an ERROR does and does not do

- The dialog cannot be OK'd with it (the framework's existing behaviour).
- **The item still exists and still draws** — a knob drag or moving the
  dormer up the roof can reach the state, and deleting the user's dormer for
  it would be worse. Code: draw an unbuildable dormer's outline in the
  error red, and skip its knee lines and host cut on the plan. AMBER, with
  the phase-2 check.
- **A dormer is never born in error.** `dg.default_state` takes
  `host_ridge_in` and fits the new dormer 6 in under it
  (`dg.fit_under_ridge`: narrows first at the host's pitch, lowers the eaves
  only if 2 ft a side is still too tall). Code: pass
  `ctx.get("host_ridge_in")` as the third argument at `items.py`'s seed
  (`_recompute`), with a test that a dormer dropped on the 108 in roof of
  Patrick's check is born with no ERROR.
- Knob drags are NOT clamped at the host ridge. The drag shows red and the
  dialog says why. If Patrick wants a hard stop on the knob, that is a
  later ask.

## 4. Tests

Mine are in `tests/test_dormer_geometry.py` (two old severity cases removed,
five functions added). I found nothing in `tests/test_dormer_item.py` that
pins the old severities; the real pytest will say.

## 5. Patrick's check, one item added (six)

Drop a dormer on a low roof: it arrives small enough to sit under the main
ridge. Widen it with knob B until it turns red; open the dialog and read
the error; confirm OK is refused.
