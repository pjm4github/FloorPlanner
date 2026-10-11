# 0239 — READ-BACK: the gable end that projects UP — what his design shows at the west junction, the mechanism, and the rule as I read it; nothing built

**Code, 2026‑10‑11.** No merge has happened since
[`0238`](0238-report.md). His instruction, on `short-angle-roof.json`,
now `fixtures/short-angle-roof.json`:

> *"lets look at the eaves overhang. In this test case the upper roof
> that hangs over the wall is projected down to the roof below. When the
> gabel ends overhang the walls the should not project the roof down.
> Instead the gable end that they cover should be projected up. In the
> test case I want to see the lower roof intersect the upper flow then
> the gable ends of that floor project up to the second floor roof."*

A read-back, because the sentence names a rule the model does not have
yet, and because the measurement below says the picture he describes
has a cause that is not where the words point.

## 0. AN INSTRUMENT, first

`fp3d.py --shot` needs a real display (D77), so until now the 3D view
could only be checked on his screen. [`docs/evidence/render3d.py`](../evidence/render3d.py)
builds the fp3d model (Qt-free) and paints its triangles with Qt's 2D
painter, offscreen — depth-sorted, lit, from a given azimuth and
elevation, with an optional plan window to zoom on a corner. Not the
GL view, but the same meshes. Three pictures of his design are beside
it; every claim below is read off them and off the numbers.

## 1. WHAT THE JUNCTION IS — measured

The second-floor box is `L2` walls `w25`–`w28`: x 120–354, y 120–360,
base 96″. Its roof `rf4` has its ridge from **x=108 to x=366** — **the
ridge ends 12″ beyond each gable wall**: a 12″ gable (rake) overhang on
both ends, with no eaves overhang (its eaves at y=120 and 360 sit on
the `L2` long walls, at 156″). The west short roof `rf1` (ridge 216″,
footprint x 30–120) runs in under that overhang: at x 108–120 its
surface is **below** `rf4`'s everywhere (216 under 276 at the ridge, 96
under 156 at the eaves).

What the model does there today
([`short-angle-roof-3d-west-junction.png`](../evidence/short-angle-roof-3d-west-junction.png),
[`…-slice.png`](../evidence/short-angle-roof-3d-west-junction-slice.png)):

| element | today |
|---|---|
| `L2`'s west gable wall `w26` (x=120) | **climbs to `rf4`'s ridge** (271.5″ = 276 − the cap) — the gable tranche's rule, already doing what his last sentence asks |
| `rf1`'s own west gable walls `w2`/`w3` (x=42) | climb to `rf1`'s ridge, 211.5″ |
| `rf4`'s gable overhang, x 108–120 | built as roof, its two slab ends open at x=108 (the gable tranche), hanging 12″ out over `rf1` |
| **`rf1` under the overhang, x 108–120** | **NOT BUILT.** `rf1` is hidden under `rf4` there, so the clip leaves it out of `rf1`'s visible region, and `fp3d` meshes only the visible region: `rf1`'s roof stops at x=108 with a vertical cut face, 12″ short of the gable wall it should meet |

So the picture he describes — *"the upper roof … is projected down to
the roof below"* — is, in the model, the upper roof's open gable-end
slab faces at x=108 standing over a 12″ gap where the lower roof has
been cut away. The lower roof does not reach the wall; the upper roof's
overhang is all there is at that line.

**One thing his words name that is already true:** *"the gable ends of
that floor project up to the second floor roof"* — `w26` does, to the
ridge. What is missing is the roof under it.

## 2. THE RULE, as I read it — and where it has to live

**A lower roof's OWN footprint is built to its own end, even where a
higher roof hides it from above, wherever that higher roof merely
overhangs it — where nothing of the higher level encloses the space
underneath.** The lower roof then runs under the overhang to the gable
wall; the gable wall projects up from it to the upper roof (as `w26`
already does); where the two roof surfaces meet there is a valley
(*"intersect the upper floor"*); where they do not meet, the lower roof
passes under the overhang's edge, as on a real house.

Where it cannot be: the clip's visible region, which is the PLAN view —
from above, the overhang does cover `rf1`, and the plan is right to show
`rf4` there. The 3D builder is where the lower roof's hidden ground
exists physically. Today `fp3d` meshes `clip.region.cells` and nothing
else; the change is that it also meshes a roof's own-footprint cells
that the clip hid **when they are not inside the covering roof's level**
— outside that level's wall loop.

**How "under an overhang" is decided — the question in the read-back.**
The roof model has no overhang on a gable end: the ridge end *is* the
rake tip (the gable tranche, [`0224`](0224-report.md)). So the builder
must read the walls: a hidden cell of `rf1` under `rf4` is built if its
centroid is **outside every room/wall loop of `rf4`'s level** (the
second floor's footprint). On his design: x 108–120 is outside the `L2`
box (x ≥ 120) → built; `rf1`'s extension east of 120 under `rf4` is
inside the box → not built (it is the joined end's closing ground,
hidden inside the second floor, exactly as now). Eaves overhangs come
free: a cell under `rf4`'s eaves overhang (none in this file, 0″) is
outside the box the same way.

**The two alternatives, and why not:** (a) make `rf1` win the ground in
the clip — wrong for the plan, which must show the roof on top; (b) a
new `gable_overhang_in` field on the roof record — a format change for
a quantity the walls already state, and the same question would come
back for eaves overhangs.

## 3. WHAT I WOULD BUILD, on his word

1. In `fp3d.py`'s roof builder: for a clipped roof, after its visible
   cells, the cells of its own footprint that the clip hid **and** whose
   centroid lies outside the covering level's wall loops — meshed as
   roof at the roof's own surface. The wall-cap (`_wall_under_roofs`)
   unchanged: `w26` already climbs; the `L1` walls under `rf1` stay
   capped by `rf1`.
2. A test on his fixture: `rf1`'s mesh reaches x=120; `rf4`'s overhang
   slab still above it; nothing of `rf1` east of 120; `rf2` the mirror
   at 354–366; the gable fixture and the three-ridge fixtures unchanged.
3. The pictures re-rendered beside the old ones.

AMBER: it changes what the 3D view draws. Plan view unchanged.

## 4. QUESTIONS, each with the answer I would take

* **"Outside the covering level's wall loop" — is that the right test
  for "overhang"?** It is the only one the document carries. If he
  wants a roof to have an explicit gable overhang later, the field can
  be added then and this rule reads it first.
* **Where the lower roof WOULD rise above the upper one under its
  overhang** (a steep lower roof under a shallow upper eave), the valley
  is where they meet and the lower roof is cut at it — the clip's seam
  already says where. I would build to the seam, not through it.
* **Does the plan view change?** No. If he wants the lower roof's lines
  dashed under the overhang in plan, that is a separate, smaller
  tranche.

## 5. `fixtures/incoming/`, with ages

* `wiscaway2026-10-07R1.json` — his own, 2026‑10‑07; exit his to name.
* `README.md`.

## 6. WHAT HAPPENS NEXT

His word on §3–§4. Behind it: the compose cost
([`0237`](0237-report.md) §0).

**Carried:** unchanged from [`0238`](0238-report.md).
