# 0036 — report: 0034's four action items, built

**Per [`0034-ruling.md`](0034-ruling.md).** §1 (the withdrawal) and §3/§6
needed nothing from Code — noted, not built. This covers §2, §4 and §5.

---

## 1. §2 — THE WORKING-DISTANCE CAMERA, ADDED ALONGSIDE THE ROOM-SCALE ONE

**Both cameras are now on the record, because they answer the two different
questions §2 named.** [`docs/evidence/shower_glance_working_distance.py`](../evidence/shower_glance_working_distance.py)
builds the model the normal way, then re-points the camera pivot and
distance at the FURNISHINGS' own bounding box rather than the whole room's
(`fp3d.py`'s CLI has no camera-distance flag — `make_view()` always fits the
whole model).

**Before** (pre-redraw artwork, obtained by temporarily copying the three
SVGs from `main` over the working tree, rendering, then `git checkout --` to
restore — not a permanent script, a one-time historical shot):
[`shower-glance-working-distance-before.png`](../evidence/shower-glance-working-distance-before.png).
**After** (current branch):
[`shower-glance-working-distance-after.png`](../evidence/shower-glance-working-distance-after.png).

**At this distance, the marks are unambiguous** — a protruding leaf on each
of the three, clearly a different tone from the body around it. The
room-scale renders (`shower-glance-before.png` / `-after.png`, unchanged,
`0031`'s original camera) stay on the record too, for the comparability
question §2 also named. `fixtures/README.md`'s row now documents both
cameras and how each is reproduced, per §2's "record the camera with the
fixture."

**Both of Patrick's questions are answerable now**: (1) do the three read as
different things at a glance — at which camera; (2) is the room-scale camera
the distance actually worked at, or does the working-distance one replace it
for future checks.

## 2. §4 — THE 3% ALLOWANCE'S RAW VALUES, PRINTED

Closest-pair bounding-box gap, every catalog item with ≥2 top-level shapes,
as a percentage of the viewBox's smaller dimension, sorted:

```
corner_desk         -21.67%   office_set            0.69%
bandsaw             -14.58%   toilet                1.25%
bicycle             -12.50%   dining_chair          1.39%
umbrella_table       -4.17%   jointer               2.75%   <- closest, connected
motorcycle           -3.12%   ------- 3% cutoff -------
office_chair         -2.08%   water_softener        8.33%   <- closest, disconnected
shower               -1.81%   drill_press          13.75%
glass_shower         -1.25%   boat_trailer         24.10%
garden_tractor       -0.93%
walk_in_shower       -0.60%
riding_mower_snow    -0.00%
snowblower           -0.00%
wheelbarrow          -0.00%
```

(Negative = bounding boxes overlap by that amount; positive = a real gap.)

**Nothing sits between roughly 1% and 3%.** `jointer` at 2.75% is the
closest item still called connected; `water_softener` at 8.33% is the
closest still called disconnected — a margin of 5.6 points either side of
the cutoff. **Stated as the empty band it is**, per `0012-ruling.md`'s own
rule. Landed in `tests/test_extrudability.py`'s own docstring so the receipt
travels with the assertion rather than living only here.

## 3. §5 — [D79](../defects/0079-six-catalog-symbols-extrude-as-disconnected.md) FILED, ONE RECORD FOR SIX ITEMS

`motorcycle`, `garden_tractor`, `riding_mower_snow` cite `0012-ruling.md`'s
own `vehicle` finding (3 of 10 built cleanly) and point at the vehicle
loft, exactly as `boat_trailer`'s existing disposition does. `bicycle`
closes by citation to [`0013-ruling.md`](0013-ruling.md) §3 rather than
reopening it. `drill_press` and `water_softener` are left as open questions
— not `vehicle` form, no existing disposition, real gaps (9.6% and 5.4%
respectively) rather than rounding noise.

`tests/test_extrudability.py`'s `FRAGMENTED_EXEMPT` reasons updated from
"not yet ruled" to cite D79 (or `0013-ruling.md` for `bicycle`) by name.

## Gate

`ruff` clean. `tests/test_extrudability.py`, still 3 tests, all pass with
the updated exemption reasons. `python tools/defects_index.py --validate` —
80 records (D79 added), front matter valid. Full suite to follow before
commit.
