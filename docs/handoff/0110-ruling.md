# 0110 — ruling: "Snap to Grid Orthogonal" — and it corrects a hazard in the plain version

**Patrick:** decimal feet stays; a vertex right-click offers **"Snap to Grid
Orthogonal"** — clicked vertex to nearest grid, the other takes the same
orthogonal coordinate; a 15°-angle equivalent as a **placeholder**.

---

## 1. FORMAT — settled, no change

**`fmt_ft2` stays.** `127.00`, and `127.50` for 127′-6″.
**[`0109`](0109-ruling.md) §4 is closed and does not come back.**

## 2. THE ORTHOGONAL VARIANT IS SAFER THAN THE PLAIN ONE — and that is the finding

**Plain "Snap to Grid" ([`0108`](0108-ruling.md)) rounds each end
independently.** For a near-vertical wall whose two `x` values sit either side of
a grid line, **the two ends round to different columns and the wall comes out
TILTED** — grid-correct and less orthogonal than it started.

> ### "SNAP TO GRID ORTHOGONAL" CANNOT DO THAT. It is the strictly better action, and his second request is a correction to his first.

**The rule:**

* the **clicked** vertex → nearest grid, **both coordinates**
* the **other** vertex → **takes the clicked vertex's shared-axis coordinate**
  (`x` for a wall running in `y`, `y` for one running in `x`), and its own free
  coordinate snaps to grid
* result: **exactly axis-aligned AND both ends on grid**

**The clicked vertex is the anchor**, which removes the *which end moves*
question that made item C hard ([`0079`](0079-report.md) §2(c)) — **he answers it
by where he clicks.**

**Axis chosen by the larger delta**, the same test the repair uses.
**REFUSE when the wall is too near 45°** — there is no orthogonal value to
share, and guessing one would rotate the wall 45°.

**Everything else carries from [`0108`](0108-ruling.md) §3 as amended by
[`0109`](0109-ruling.md) §3:** refuse on degenerate, on an opening running off,
on a new `check()` violation; **report** a neighbour left worse. One undo step.

**The endpoint hit-test already exists** — `near_p1` / `near_p2`,
`walls.py:1774`, used by `mousePressEvent` to pick `"p1"` / `"p2"`.
**`contextMenuEvent` has the same `e.pos()`. Reuse it; do not invent a second
one.**

## 3. THE 15° CASE — the difficulty is arithmetic, not effort

**Measured. A wall can have both ends on a 6″ grid only if `tan(angle)` is
rational.** Across the 24 multiples of 15°:

| angle | both ends on grid? |
|---|---|
| 0, 90, 180, 270 | **yes** — one delta is zero |
| **45, 135, 225, 315** | **yes** — `tan = ±1` |
| **15, 30, 60, 75** and their reflections — **16 of the 24** | **NO. Not at any length.** |

> ### AT 15° THERE IS NO SOLUTION. `tan 15° = 0.267949…` is irrational, so no pair of grid points subtends it — the feature cannot preserve the angle and land on the grid, at any wall length, ever.
>
> **So the future ruling is not "implement the arithmetic." It is a choice:
> keep the ANGLE and let the far end sit off-grid, or keep the GRID and let the
> angle drift.** Nothing else is available.

**He is right that it is more complex, and this is why** — recorded now so
whoever writes that ruling does not begin by rediscovering it.

## 4. THE PLACEHOLDER — disabled, not silent

> **A menu item that does nothing when clicked is a defect.** **Add it
> DISABLED**, with a tooltip: *"Not yet specified — a wall at 15° cannot have
> both ends on the grid; see `0110-ruling.md` §3."*

**Visible as intent, impossible to mistake for broken.**

## 5. TIER AND ORDER

| | | |
|---|---|---|
| 1 | **§2 — Snap to Grid Orthogonal, on the vertex right-click** | **AMBER.** Build this **first** — §2 says it is the safer of the two |
| 2 | **[`0108`](0108-ruling.md) — plain Snap to Grid, on the wall right-click** | **AMBER.** Second, and its tilt case is now a known, named limitation |
| 3 | **§4 — the 15° item, disabled with its tooltip** | **GREEN**, one line, same commit as 1 |
| 4 | **The 15° feature itself** | **RED.** §3 is its input, not its specification |

**Check, both actions in one pass:**

> `wiscaway2026-08-09R`, the wall near x ≈ 78.97 ft. **Right-click its lower
> end, Snap to Grid Orthogonal — both ends land on 79.00 and the wall is
> exactly vertical.** Then try plain Snap to Grid on another and see whether it
> tilts.

**Still queued behind PR #37 and PR #38.**
