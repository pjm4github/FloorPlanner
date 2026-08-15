# 0021 — report: the vessel/enclosure split, built — and one thing the render cannot show

**Per [`0020-ruling.md`](0020-ruling.md), this is Code's report, opening the PR
at its AMBER stop. AMBER — nothing merges without your check.**

**Per [`0016-ruling.md`](0016-ruling.md) §6's standing rule, the plan and its
items, named first:**

* **Plan:** [`../../fixtures/enclosure-form-check.json`](../../fixtures/enclosure-form-check.json)
  — three items, well apart: `walk_in_shower`, `sauna`, `whirlpool`.
* **Renders:** [`../evidence/enclosure-form-measurement.png`](../evidence/enclosure-form-measurement.png)
  (before) and [`../evidence/enclosure-form-measurement-after.png`](../evidence/enclosure-form-measurement-after.png)
  (after) — same plan, same camera.
* **Probe:** [`../evidence/enclosure_form_measurement.py`](../evidence/enclosure_form_measurement.py).

---

## 1. THE §2 CONTROL, FIRST, AS ORDERED — both sides shown working

Before touching any production code: `bathtub` reads WELL, and `sofa`'s back —
already proven RAISED by PR #29's own tests — reads RAISED. Both sides of the
instrument demonstrated, not just the one every case under test also expected.

## 2. THE SPLIT, BUILT

**`KNOWN_FORMS` gains `vessel`.** `build_prism` now takes the item's real
catalog form and asks one question: *does this form allow a recess?*

* **`vessel`** (`bathtub`, `swim_spa`, `whirlpool`) — unchanged from before the
  split: a region below the body's height cuts into the cap (a well).
* **`enclosure`** (`shower`, `walk_in_shower`, `glass_shower`, `sauna`) — a
  region is now **always** a solid, **never** a recess, regardless of its
  height relative to the body.

**Categorical, not a threshold.** The split is on the catalog's `form`, not on
a height comparison — the exact thing [`0012-ruling.md`](0012-ruling.md)
already ruled out once for a different pair of symbols.

## 3. A SECOND BUG, FOUND BY DUMPING THE MESH — NOT BY THE PROBE

**The first cut of the fix reused the existing "sits on the body" extrusion
formula for an enclosure's region** (`body_h → region_h`), which is correct
for furniture (a pillow rising above a mattress) and **wrong for a room**: it
built `walk_in_shower`'s bench spanning **18″ to 78″** — a column hanging near
the ceiling — instead of **0″ to 18″**, standing on the floor.

**The roof-over probe did not catch this, and could not have.** It only asks
*"is there a face at the body's full height over the region's centre"* — a
question about the **cap**, which this bug never touched (the bench, wherever
it landed, still left the cap alone). The bug was found by dumping the built
mesh's own bounding box directly:

```
before the fix:  furnishings:stone  z[18.0, 78.0]
after the fix:   furnishings:stone  z[ 0.0, 18.0]
```

**Fixed with a third bucket** (`grounded`, alongside `wells` and `on_body`):
an enclosure's region now extrudes from the floor (`z0`) to its own height,
the same formula `beside` parts already used. Recorded because the instrument
family this project keeps caught the CLASSIFICATION bug and had nothing to say
about the EXTRUSION bug one layer down — a reminder that a control proves the
question it was built to answer, and no more.

## 4. THE THREE LINES, RE-MEASURED AFTER THE FIX

```
item              region h  body h  outcome
------------------------------------------------------------
walk_in_shower        18.0    78.0  RAISED (cap intact)
sauna                 30.0    84.0  RAISED (cap intact)
whirlpool             30.0    36.0  WELL (cap opened)
```

**`whirlpool` still reads WELL — correct, a vessel.** `walk_in_shower` and
`sauna` now read RAISED — the roof is unbroken, and the bug in §3 confirms the
solid is in the right place, not merely off the cap.

## 5. THE MATERIALS SPLIT, BUILT ALONGSIDE IT

**`build_prism` now returns `(body_parts, region_parts)`, not one flat list.**
`build_model` colours each with its own material — `spec["material"]` for the
body, `spec["region_material"]` for the region (falling back to the body's
when the catalog states none, which is every item outside this ruling).

| item | body material | region material |
|---|---|---|
| `bathtub` | `porcelain` (unchanged) | `water` |
| `swim_spa` | `porcelain` *(was `water` — the whole tub was translucent)* | `water` |
| `whirlpool` | `porcelain` *(was `water`)* | `water` |
| `walk_in_shower` | `glass` (unchanged) | `stone` |
| `sauna` | `wood` (unchanged) | `metal` |
| `shower`, `glass_shower` | `glass` (unchanged) | *(no region)* |

**Whole catalog re-built as a sanity check**: 95 of 95 furnishings, 0 notes,
only `glass_shower` still falls back to a box (unchanged — it has no closed
shape at all).

## 6. WHAT THE RENDER SHOWS, AND ONE THING IT DOES NOT

**`sauna`'s roof is unbroken** — the dark notch from the "before" render is
gone. **`whirlpool` now shows a solid porcelain body with a distinct
translucent water surface** — exactly what you asked for on the render.

**`walk_in_shower`'s bench is NOT visible in the render, and it is not a
geometry problem.** Measured directly on the built mesh:

```
furnishings:glass   z[ 0.0, 78.0]   (the body, translucent)
furnishings:stone   z[ 0.0, 18.0]   (the bench, opaque, correct position)
```

The bench is the right size, the right material, standing on the floor. It
does not appear in the render **at any glass transparency tested** — alpha
0.35 (shipped) and 0.12 (a synthetic test, restored afterward) both show the
same plain glass box. **The `fp3d.py` CLI viewer does not composite an opaque
interior mesh through a translucent body**, independent of how transparent the
body is. Noted against [D69](../defects/0069-an-auxiliary-control-panel-on-the-3d-view.md)
— not fixed here, not scope for this task, exactly as your own §7 anticipated
for `sauna`'s case and this turns out to be the sharper instance of.

**So the check's row 1 cannot be read from the picture as designed.** The
geometric receipt above stands in its place.

## 7. THE CHECK, AS DESIGNED, WITH ROW 1 ADJUSTED

On [`../evidence/enclosure-form-measurement-after.png`](../evidence/enclosure-form-measurement-after.png):

| | item | question | how to answer it |
|---|---|---|---|
| 1 | `walk_in_shower` | a solid bench, on the floor | **not visible in the render** — see §6's mesh numbers instead |
| 2 | `sauna` | is the roof unbroken (no dark notch)? | **look at the render** |
| 3 | `whirlpool` | solid colour top/sides, translucent round pool | **look at the render** |

## 8. THE LIMIT FILED ALONGSIDE THE SPLIT

[D75](../defects/0075-a-recessed-floor-feature-is-not-representable.md) — an
enclosure's region can only stand on the floor, never recess into it (a shower
pan, a floor drain). No catalog item needs this today; filed as an accepted
limit, D44's precedent, per your §5's own instruction to state it now rather
than discover it later.

## Gate

`ruff` clean; `tests/test_viewer_model.py` and `tests/test_furnishings.py`
pass unchanged (32 tests, none touched); full suite 674 passed outside `gui`.
Full gate to follow before the PR opens.
