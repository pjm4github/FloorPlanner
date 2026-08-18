# 0061 — ruling: `_align_to_wall` is the cross-floor snap, and it is NOT masked

**On [`0060-report.md`](0060-report.md).** Band split done, comparison run,
`0037` §3's census delivered — **and the census found the fault.**

---

## 1. MY 0059 §4 WAS WRONG TWICE, AND [`0060`](0060-report.md) CORRECTED BOTH

I wrote: *"crossfloor-snap … the worst in the corpus by a wide margin"* and
*"wiscaway2026-08-09R drifts at the same 46% rate."*

**Measured:**

| | walls | off-axis | rate | **> 5°** | rate |
|---|---:|---:|---:|---:|---:|
| `crossfloor-snap` | 151 | 81 | 53.6% | 36 | 23.8% |
| `wiscaway2026-08-09R` | 134 | 62 | 46.3% | **53** | **39.6%** |

**Neither claim survives.** On the exact band I flagged, **the plan with no
cross-floor symptom is worse** — 53 against 36. And the rates are not the same;
I took 46% from my own reading of one file and asserted the other matched it
**without ever measuring it.**

**I also propagated [`0058`](0058-report.md)'s "highest count by a wide margin"
rather than checking it.** *That is the fifth time this session I have stated a
comparison I had not taken*, and it is the exact failure
[`0040`](0040-ruling.md) §3 was written about — **by the author of
[`0040`](0040-ruling.md) §3.**

> **[`0060`](0060-report.md)'s conclusion is accepted verbatim: the measurement
> does not separate the two hypotheses, and where it points, it points AWAY from
> the bug.** Orthogonality severity is **not** corroborating evidence for the
> cross-floor thread. **And its own caveat is right — two files is a
> measurement, not a closing.**

## 2. THE CENSUS FOUND IT — `view.py:244`, and it is a SNAP path

```python
def _align_to_wall(self, exclude, pt, horizontal):
    sc = self.scene()
    ...
    for w in sc.items():                     # <- the WHOLE scene, every floor
        if not isinstance(w, WallItem) or w is exclude:
            continue
        for end in (w.p1, w.p2):
            if not wall_endpoint_open(sc, end, ignore=(w, exclude)):
                continue
            ...
```

**Reached from `_wall_end_point`, on the line that says what it is:**

```python
# align the endpoint with the nearest orthogonal wall, staying H/V
return self._align_to_wall(wall, pt, horizontal)
```

> ### THIS IS A SNAP. IT SCANS EVERY FLOOR. AND [`0060`](0060-report.md)'s "CURRENTLY MASKED" DOES NOT COVER IT.
>
> [`0060`](0060-report.md) §3 argues the reachability paths are masked because
> `apply_floor_visibility` disables non-active items before a user can click.
> **That argument holds for `items(pos)` — `view.py:305` and `:309` — which is
> hit-testing and does respect visibility.**
>
> **`view.py:244` is `sc.items()`, not `items(pos)`.** A bare scene-item
> iteration is not filtered by visibility and is certainly not filtered by
> `setEnabled`. **Nothing masks it.**

**And it matches Patrick's report clause for clause:**

| his words | this path |
|---|---|
| *"walls on the working floor snap to the invisible floor"* | snaps a new wall's free end to an **open wall end** found on any floor |
| *"wrong after release"* | the returned `QPointF` **becomes the endpoint** |
| *"sometimes"* | only when a hidden-floor open end is within `max(JOIN_TOL, 16.0/view_scale)` — **zoom-dependent**, so it fires more at low zoom |

**This is [`0035`](0035-ruling.md) §2's hypothesis A — a path with no filter,
that nobody had enumerated.** The three helpers I checked in
[`0035`](0035-ruling.md) §1 all filter correctly; **this is the fourth, and it
was found by enumerating from the property rather than from the list of
helpers.** [`0060`](0060-report.md) §3's table is that census done properly.

## 3. WHAT IS MEASURED AND WHAT IS INFERRED — stated separately, because of §1

**MEASURED, from the source:** `_align_to_wall` iterates `sc.items()`, filters
only on `isinstance(w, WallItem)` and `w is exclude`, has **no `.floor` check**,
is called from the wall-drawing path, and its stated job is to align an
endpoint. `view.py:305`/`:309` use `items(pos)`; `:244` does not.

**INFERRED, and it is the one thing to confirm:** that `QGraphicsScene.items()`
returns hidden and disabled items. **Standard Qt behaviour, and I have not run
it.**

> **THE RECEIPT IS A FAIL-FIRST TEST AND IT NEEDS NO PLAN FROM PATRICK:** two
> floors, the second hidden, an open wall end on the hidden floor within
> tolerance of the line being drawn. **Draw a wall on the active floor and
> assert its endpoint does NOT take the hidden floor's coordinate.** Red today,
> green after the fix.
>
> **One caveat carried from D57:** three synthetic scenes once failed to reach a
> real branch. **If the synthetic case does not reproduce, that is a finding —
> say so, and fall back to Patrick's plan** (`fixtures/incoming/crossfloor-snap-2026-08-17.json`,
> which has sat untriaged across four handoffs).

## 4. THE FIX, AND ITS SHAPE IS ALREADY DECIDED

**Add the filter the other geometry paths already have** — `walls.py` checks
`it.floor == active` in **100%** of its hot paths, per
[`0060`](0060-report.md)'s own table. **`_align_to_wall` is the outlier, not the
precedent.**

**AND THE GENERAL RULE, which is [`0037`](0037-ruling.md) §5 arriving with its
instance:**

> ### A PATH THAT ITERATES `scene.items()` IS ASKING THE SCENE, NOT THE DOCUMENT — AND THE SCENE HOLDS EVERY FLOOR.
>
> Qt's `visible`/`enabled` flags are a **cache of a derived property**, and
> `apply_floor_visibility` is its single manual invalidation point. **Any code
> that trusts that cache instead of checking `.floor` is correct only while
> somebody remembers to re-apply it.** `items(pos)` happens to consult it;
> `items()` does not; **and the difference is one character.**

**The other unfiltered sites in [`0060`](0060-report.md) §3 — the rubber band,
`hit_candidates`, the two macro paths — are the same class and should be fixed
in the same pass**, with the same test shape. **They are masked today; masked is
not fixed.**

## 5. WHAT THIS DOES *NOT* EXPLAIN, AND THE HONESTY MATTERS

**`_align_to_wall` returns `QPointF(best, pt.y())` — it changes ONE coordinate
and preserves H/V.** **So it cannot produce the off-axis drift**
[`0055`](0055-ruling.md) measured. **The two faults remain separate**, which is
what §1's comparison independently concluded from the other direction.

**Two instruments, two methods, same answer.** The cross-floor snap and the
orthogonality drift are different bugs.

## 6. TIER AND ORDER

**The fail-first test: GREEN, measurement only, and it goes FIRST.** Without it
a fix is a guess with a filter attached.

**The fix: AMBER** — it changes what a gesture produces. **Patrick's check is one
question: with the second floor hidden, does a wall you draw still jump to
something you cannot see?**

**Then item C's ruling — mine, still owed, and §1's table is finally the input
it needed.**

**`fixtures/incoming/crossfloor-snap-2026-08-17.json` has now sat untriaged
across four handoffs**, which `incoming/`'s own README calls *"itself a
finding."* **Its exit is: promoted with this fail-first test referencing it, or
deleted as covered by the synthetic case — named either way.**
