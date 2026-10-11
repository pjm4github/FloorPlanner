# 0254 — report: iteration 10 of the house — the dormers' windows; a first-floor gable wall climbed through the second storey, fixed on `roof-gable-climb-level`; AMBER, for his check

**Code, 2026‑10‑11.** No merge has happened since
[`0253`](0253-report.md), which recorded his order:

> *"We need to do another iteration starting at 10 to make sure that
> windows in the dormers are properly rendered and match the
> house_cutout_transparent.png."*

## 0. MEASURED FIRST — why the gable faces were solid

The gable dormers' (the bays' gables') second-floor windows were in the
record, on the bay front walls, and every shot showed the gable faces
solid while the shed dormer's three read as openings. A ray through the
left gable's window at its centre met wall: four triangles, a piece 72″
wide rising from 90″ to 266.5″ — the FIRST-floor bay wall's header
(above its 72″ window, head at 90″), climbing as a gable wall straight
through the second storey and its window to the rake.

The gable climb ([`0223`](0223-report.md) §3) had no level: an exterior
wall perpendicular to a roof's ridge climbed into that roof whatever
level the roof stood on. The dormer climb had one since R6.b ("a wall
a storey below a dormer does not climb through the floor between");
the gable's did not. One level is what the gable-end check plan has, so
it never showed.

## 1. THE FIX — the gable climb stays on the wall's own level

`_wall_under_roofs` carries each territory's level alongside its dormer
flag; `owner_of` returns it; `climb = to_top and (dormer or (same_level
and gable_wall_of(geom)))`. A roof of another level caps the wall like
any other roof where it is lower than the wall's top, and otherwise
leaves it at its own height. `tests/test_gable_climb_level.py` (2): a
two-storey body with a second-floor gable roof — the first-floor front
wall tops at its own 120″, its window open and its header standing; the
second-floor wall climbs to the rake with its window open; and the
single-storey gable-end check plan climbs exactly as before. The three
promoted dormer fixtures have no first-floor gable wall under a
second-floor roof (`rf4`'s rakes stand over the short roofs, not over
walls), so nothing there moves.

## 2. ITERATION 10 — the windows matched to the picture

With the fix, the gable windows render. Then the sizes: the picture's
dormer windows are tall and sit on the knee wall — the gables' now
"4860" and the shed dormer's three "2460", sills at the 48″ eaves.
Schema and invariants clean. Published as
`fixtures/incoming/house_cutout.json`; shot with the app's view at the
two iteration-9 viewpoints and a close-up on the dormers
(`iter-10-q3d-gables-close.png`). The log is `STATUS.md` there.

## 3. THE RECEIPT

* `--quick` 1566 passed; ruff clean; the full gate GREEN on the branch
  commit.

## 4. TIER

**AMBER** — it changes what the 3D view draws for a two-storey house
with a gable roof on the upper floor: the lower gable wall no longer
rises through the storey above. For his check: iteration 10 in the 3D
view — the gable windows open, the shed dormer's three open, the
first-floor wall ending at its own top.

## 5. `fixtures/incoming/`, with ages

* `house_cutout_transparent.png`, `house_cutout_1stfloor.png` — his own,
  2026‑10‑11.
* `house_cutout.json` (iteration 10), `house_cutout_work/` — mine,
  2026‑10‑11.
* `wiscaway2026-10-07R1.json` — his own, 2026‑10‑07; exit his to name.
* `README.md`.

## 6. WHAT HAPPENS NEXT

His check of the PR and his look at iteration 10. Then 0248's E and the
hip run on his word. Behind them: the compose cost
([`0237`](0237-report.md) §0).

**Carried:** unchanged from [`0253`](0253-report.md).
