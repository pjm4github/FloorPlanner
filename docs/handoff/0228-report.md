# 0228 — report: two parallel walls one grid step apart stay two walls — a gesture merges at A6's 3″, built on `parallel-walls-6in` for his check

**Code, 2026‑10‑07.** No merge has happened since
[`0225`](0225-report.md). His word: *"start on the parallel walls 6" apart
merging."* The item is [`0210`](0210-report.md) §6:

> *"Two parallel same-type walls 6″ apart merge into one. His macro's last
> two lines draw exactly that and the first wall disappears. It is the
> auto-coalesce tolerance, older than A6, and it means a 6″ gap between
> parallel walls cannot be drawn today."*

## 1. THE MECHANISM, measured

On a draw release (`PlanView.mouseReleaseEvent`) and on a drag release
(`WallItem.mouseReleaseEvent`), `merge_wall` fuses the wall with any
same-type parallel wall whose line is within `perp_tol` — and `perp_tol`
defaulted to `wall_snap_in`, the 6″ grid step. Headless, two interior
walls drawn one above the other:

| drawn gap | walls after |
|---|---|
| 2″, 3″ | **1** (the second lands on the grid at 6″, then merges) |
| 6″ | **1** |
| 9″ | 2 |

So on the default grid the nearest two parallel walls could stand was
12″: the step itself was swallowed.

## 2. THE FIX — A6's own split, applied once more

A6 ([`0207`](0207-report.md) §4.3, [`0208`](0208-report.md)) gave a
GESTURE its own tolerance, `GESTURE_WELD_IN` = 3″ — *under one grid step
by construction, so a 6″ reveal survives* — and left `JOIN_TOL` at 9″
for the explicit passes. The merge now follows the same rule: **the two
gesture sites pass `perp_tol=GESTURE_WELD_IN`**; `merge_all` (the legacy
loader) and Edit ▸ Coalesce all walls (`normalize_walls`) keep the
grid-step default. Two lines of code, each with its comment. The rule's
wording, which 0210 §6 gave, is unchanged: *a wall gesture lands on the
grid; within 3″ of another wall's end or line it goes to that instead;
Shift turns both off.*

**Not changed, and worth knowing:** a v5 document is applied faithfully
on load (`load_data`) and is not merged there at all; only the legacy
`Project` loader merges on open. Found writing the control below, which
first tried to pin "load still merges" and could not.

## 3. THE RECEIPT

`tests/test_grid_snap_default.py`, section 6, four tests:

* two interior walls drawn at y=120 and y=126 → **two walls** (RED before);
* a wall slid by its body to one grid step from a parallel one → **two
  walls**, the slid one still in the scene (RED before);
* **positive control:** a wall drawn 2″ from a placed off-grid parallel
  one → **one wall** — the merge is still there at the gesture tolerance;
* **what does not change:** two placed walls 5″ apart, Edit ▸ Coalesce →
  **one wall**, the explicit pass at its grid-step tolerance.

Full A6 suite green with them; `ruff` clean; the full gate is the
branch's own run.

**One pinned count moved, said because it did:**
`test_macro2_convert.py`'s table had `dragWallFuseStraggler.fpm` ending
at 18 walls — at that test's 1400×1000 replay geometry, not the macro's
own ([`0226`](0226-report.md) §1's trap). There one slide used to merge
into a parallel wall 6″ away; it now stays, 19 walls, both engines
agreeing. The macro's real pin at its recorded geometry
(`test_extract_join.py`, 16 walls, the baseline) is unchanged.

## 4. STATE

Branch `parallel-walls-6in`, one PR, AMBER for his check. `main` is this
commit.

**For his check:** draw two interior walls one grid step apart — both
stay. Draw one on top of another — they merge. Slide a wall to one step
from a parallel one — it stays.

## 5. `fixtures/incoming/`, with ages

Empty.

## 6. WHAT HAPPENS NEXT

His check. Behind it: the status board ([`0019`](0019-ruling.md),
read-back first) and the `roofs-r3-planes-gables.png` re-shot (his
display).

**Carried:** unchanged from [`0227`](0227-report.md).
