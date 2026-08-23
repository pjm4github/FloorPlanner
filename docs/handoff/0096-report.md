# 0096 — report: the status-bar angle clause built — `0092`/`0093`/`0094`

**On [`0092`](0092-ruling.md)/[`0093`](0093-ruling.md)/[`0094`](0094-ruling.md), one commit as ordered.**

## What changed

`mainwindow.py`'s `_wall_label_text` (and a new `_angle_snap_step_deg`
helper): the clause fires iff the wall is off `SETTINGS["rotate_snap_deg"]`'s
own grid (default 15°, the same grid `_angle_snapped_target`'s Ctrl-drag
already snaps to), not the nearest cardinal — falling back to 90° (cardinals
only) if the configured step doesn't divide 90 exactly. When it fires, both
numbers show: heading fixed-decimal (`.4f`), deviation significant-figures
(`.3g`) — `angle 269.0710deg (0.929deg off axis)`. Suppressed entirely
(heading included) below `1e-9°` — 0094's own tolerance, between its
measured ~4e-15° round-trip noise and the corpus's smallest real drift,
2.04e-4°.

## Receipt

`tests/test_selection.py`: an off-grid wall shows both numbers exactly;
a deliberate 45° wall (on the 15° grid) shows nothing at all, not even
heading; the round-trip test now reads the *deviation* back out and
asserts it never parses as zero (0092's own invariant); a 7-way
parametrized test builds a wall through the real Ctrl-drag angle snap at
0/15/30/45/60/75/90° and asserts none of them shows a clause — this is
what caught the ~4e-15° noise 0094 itself found before it shipped; an
arbitrary 7° step (doesn't divide 90) falls back to cardinals-only,
silently. Full suite 859 passed, `ruff` clean, gate GREEN.

## Tier and check

**AMBER**, batched with PR #37's check, per `0092` §4 / `0093` §6 / `0094`
§5:

> Select an off-axis wall — does the bar show both which way it points
> and how far off it is, and does the second number never read zero? A
> wall at 45° says nothing about its angle. A wall you drew freehand says
> how far off the nearest 15° it is. Ctrl-drag a wall end to 30° — the
> bar must say nothing about its angle.

Branch: `wall-label-angle-clause`.
