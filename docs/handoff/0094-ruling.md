# 0094 — ruling: walls DO have an angle snap — and it breaks [`0093`](0093-ruling.md)'s exactness test

**Patrick, 2026‑08‑23:** *"There is an angle snap when I drag with the CNTRL key
pressed."*

**He is right and [`0093`](0093-ruling.md) §3 is wrong.**

---

## 1. THE CORRECTION

```python
# walls.py:1878  _endpoint_target
if mods & Qt.KeyboardModifier.ControlModifier:
    return self._angle_snapped_target(sp)

# walls.py:1891  _angle_snapped_target
"""Ctrl-drag: swing the dragged end around the anchored end in fixed
angular increments (SETTINGS['rotate_snap_deg'], default 15 deg), with a
grid-snapped length -- so the user can build 45 deg and other off-axis
walls, not just lengthen along the existing axis."""
```

Reached from **`_endpoint_target`** (a wall end) and **`_corner_target`** (a room
corner). [`0093`](0093-ruling.md) §3 said *"walls have no angle snap today."*
**I had the DRAW path open (`view.py`'s `_wall_end_point`) and generalised from
it to the STRETCH path 1,600 lines away.** Sixth time this run I have asserted
something checkable without checking it.

**AND IT STRENGTHENS §1 RATHER THAN WEAKENING IT.** I called
`SETTINGS["rotate_snap_deg"]` a *"deliberate reuse"* of a furnishing setting.
**It is not a reuse at all — it is already the wall angle snap.** The label now
measures deviation against **the same grid the tool snaps to**. One number, one
meaning.

## 2. THE MEASURED CONSEQUENCE — the snap does not survive a round trip

**Simulated `_angle_snapped_target`: swing to the increment, grid-snap the
length, read the heading back with `atan2`:**

| target | endpoint | heading read back | `% 15 == 0` |
|---:|---|---|:--:|
| 0° / 45° / 90° / 135° | symmetric | exact | **yes** |
| **15°** | `(86.933324, 23.293714)` | `14.999999999999996` | **no** |
| **30°** | `(77.942286, 45.000000)` | `29.999999999999996` | **no** |
| **60°** | `(45.000000, 77.942286)` | `59.99999999999999` | **no** |
| **75°** | `(23.293714, 86.933324)` | `74.99999999999999` | **no** |

> ### A WALL BUILT BY THE ANGLE SNAP, AT EXACTLY THE INCREMENT THE SNAP OFFERS, WOULD BE REPORTED AS OFF AXIS BY 4e-15 DEGREES.
>
> Clutter on the walls the feature exists to make — and
> [`0093`](0093-ruling.md) §1's own invariant broken on its first real user.
> **Cardinals survive exact equality; 15/30/60/75 cannot, because their
> coordinates are irrational and `atan2` is not asked to undo a rotation.**

**My §1 broadened the grid from four angles to twenty-four, and exact equality
only ever worked because the old four were symmetric.**

## 3. THE FIX — a tolerance, and the data says where to put it

**Suppress the clause when the deviation is at or below `1e-9` degrees.**

| | |
|---|---|
| representation noise, measured above | **~4e-15°** |
| smallest REAL drift in the corpus ([`0066`](0066-ruling.md) §2) | **2.04e-4°** |
| **the cut** | **1e-9°** |

**Five orders of magnitude above the noise, five below the smallest real signal.**
There is no value in that gap and nothing physical can land there. **Stated as
the judgement it is, with both boundaries named** — `WORKING_AGREEMENT.md`'s own
requirement of a threshold.

**The same tolerance governs the printed number**: below it, no clause at all —
not `(4e-15deg off axis)`.

## 4. NOT AFFECTED

**The census, the report and item C's population are unchanged** — they measure
from cardinals, and a 30° wall is 30° from a cardinal, far outside the near-axis
band. **No number in [`0066`](0066-ruling.md) or [`0084`](0084-ruling.md)
moves.**

**But if the report ever adopts the 15° grid** ([`0093`](0093-ruling.md) §4's
named question), **it inherits this exact problem** and this tolerance with it.
Recorded so that question is not re-answered from scratch.

## 5. TIER

**AMBER**, still one commit with [`0092`](0092-ruling.md)/[`0093`](0093-ruling.md).
**Receipt:** a wall built through `_angle_snapped_target` at each of
0/15/30/45/60/75/90 shows **no** angle clause — RED today under exact equality
for four of the seven.

**Check unchanged, one line added:**

> **Ctrl-drag a wall end to 30°. The bar must say nothing about its angle.**
