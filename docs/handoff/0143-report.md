# 0143 — report: R2 closed — Patrick's own check passed, PR #49 merged

**Patrick, 2026‑09‑01, in the running app:** *"I am able to click and drag a
roof ridge. The drawing of the 45 ridge should be able to use the CNTRL and
the SHIFT key. Currently the SHIFT key works but the CONTROL key doesn't. I
expect that when I hold the CNTRL key then the ridge should snap to the 15
degree snap like the wall drawing does."* Then, after the fix: **"OK That
works now."**

---

## 1. WHAT HIS CHECK FOUND

[`0139`](0139-ruling.md) §3's own words for R2: *"sketch the main ridge and
the 45° wing ridge on wiscaway; modifiers feel like the wall tool."*
[`0142`](0142-report.md) reported that check answered headless before the
PR went up — but a real gap survived it: **Ctrl was wired for RE-ANGLING an
existing wall's end** (`WallItem._angle_snapped_target`, the Select-tool
corner-drag) **but never for the DRAW gesture** (`PlanView._wall_end_point`,
what a wall OR a ridge click-drag actually calls), which checked Shift only.
The headless receipt in [`0142`](0142-report.md) §2 tested default-modifier
and Shift; it did not test Ctrl, which is exactly how this got past gate and
CI and still reached his hands as a real defect. **His own manual check
caught what the automated one missed** — the reason a check stays owed to
him and not just to CI.

## 2. THE FIX

Ctrl added to `_wall_end_point`, same formula
`WallItem._angle_snapped_target` already used (`SETTINGS['rotate_snap_deg']`,
default 15°), anchored at the drawn item's own `p1`. **Fixed once, at the
function both tools call through** — the wall tool gains Ctrl-drawing for
free alongside the ridge tool, closing a gap that predates this whole
tranche (wall DRAWING never had Ctrl-snap; only wall RESHAPING did). Two new
wall-side tests (`test_wall_draw_ctrl_snaps_to_15_degrees`,
`test_wall_draw_ctrl_does_not_pull_orthogonal`) plus one ridge-side
(`test_ctrl_gives_a_15_degree_stepped_ridge_same_as_a_wall`). Pushed as a
second commit on `roofs-r2-ridge-sketch`; CI green a second time; **"OK That
works now"** is the check.

## 3. DISPOSITION — R2 CLOSED, MERGED

[PR #49](https://github.com/pjm4github/FloorPlanner/pull/49) merged to
`main` at `8cbdf55`, branch deleted (local and remote). **R2 is done.**

**R2b is the next available tranche (AMBER)** — the End-On marker + end-on
view + three-way ridge/eaves/pitch dialog ([`0140`](0140-ruling.md)).
Patrick's own words on sequencing, recorded verbatim so the order is not
Code's inference: *"We will also have to work on the some or the property
control features (heights/widths, etc) after we get basic drawing working."*
Basic drawing is now confirmed working, by his own hand — R2b (and R4's
parameters dialog, further out) are the property-control tranches that
statement points at.

**Carried, unchanged:** room-label rounding ([`0131`](0131-ruling.md) §2);
delta-snap sites; D61-family; yard items.
