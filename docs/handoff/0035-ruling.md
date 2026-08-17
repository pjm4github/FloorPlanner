# 0035 — ruling: cross-floor snapping, and per-floor totals that must not inherit D55

**Patrick, 2026‑08‑17, two items — one defect and one feature.**

> **When I have 2 floors and am working on only one, then the walls on the
> working floor sometimes snap to the the invisible floor. This should never
> happen when only one floor is visible. Only the visible floor should be able
> to accept snaps / wall closures and other geometry operations.**

---

## 1. THE OBVIOUS ANSWER IS WRONG, AND THAT IS THE MOST USEFUL THING I CAN SAY

**The three paths anyone would suspect ALREADY FILTER.** Read on disk:

```python
nearest_wall_endpoint()   active = active_floor()
                          if ... and it.floor == active:   # weld only to active-floor walls
nearest_wall_body()       active = active_floor()
                          if ... and it.floor == active:   # weld only to active-floor walls
coincident_walls()        if ... or w.floor != wall.floor: # coalesce stays on one floor
```

`nearest_wall_body` is the T-junction fuse — *"a wall end that stops at or inside
the body of another wall snaps onto that wall's centreline"* — which is exactly
the behaviour Patrick describes, **and it is filtered.**

> ### SO A CENSUS THAT GREPS FOR FLOOR FILTERS WILL COME BACK CLEAN AND THE BUG WILL STILL BE THERE.
>
> `CLAUDE.md` asserts these hot paths filter, and they do. **An enumeration
> starting from that list returns its own contents** — the spelling-, predicate-
> and container-shaped censuses, a fourth time. **It must not be run that way.**

## 2. THE CENSUS ENUMERATES FROM THE PROPERTY, AND THERE ARE **TWO** HYPOTHESES

**The property:** *every path that reads geometry from another item and uses it
to place, move, weld, fuse, merge or close the item under the gesture.* **Not
"the helpers `CLAUDE.md` names."**

**And it must test both of these, because they produce the same symptom:**

| | hypothesis | where it would live |
|---|---|---|
| **A** | **A path with no filter** — a query nobody enumerated | the drag, `weld_scene`, `normalize_walls`, `merge_all`, `_compute_wall_junctions`, `bind_room_walls`, `graph_from_scene`, `_WallBBoxIndex`, room detection, extract/join |
| **B** | **The DATA is mis-tagged, and every filter is working correctly** | `it.floor` set at creation from `active_floor()`; a load, a migration, a paste, a duplicate or a floor switch that leaves an item carrying the wrong floor |

> **HYPOTHESIS B IS THE ONE THAT WILL BE MISSED.** If a wall on the hidden floor
> carries `floor == <the active floor>`, **every filter above passes it
> correctly** and the fault is in the tagging, not the query. **A census of query
> paths cannot see it at all.** [D50](../defects/0050-a-level-s-elevation-is-destroyed-by.md)
> is already a fault of that family — a level property destroyed by a round trip.
>
> **Cheap test that separates A from B in one step:** on Patrick's plan, dump
> every wall's `floor` tag against the level it visually belongs to. **If a
> mismatch exists, stop — it is B, and no amount of filtering will fix it.**

## 3. IT NEEDS A REPRODUCTION BEFORE IT NEEDS A FIX

**Patrick's observation is currently the only evidence, and *"sometimes"* is in
it.** An intermittent cross-floor snap with no saved case is the shape that
produces three predicted fixes and no closure — this project has that history
twice on one row.

**Owed: the plan it happened on**, dropped in
[`fixtures/incoming/`](../../fixtures/incoming/README.md) — the intake exists
exactly so a broken plan can be reported without its reporter having to
characterise it first. **With the two floors as they were, and which wall snapped
to what.**

## 4. [D67](../defects/0067-selection-is-not-scoped-to-the-active-floor.md) IS ADJACENT AND OPEN — check whether it is the same root

*"Selection is not scoped to the active floor — an inactive floor is drawn AND
draggable."* **If an inactive floor's items are reachable by a gesture, the
question of which floor a snap consults is downstream of a bigger one.** Do not
file a new record until it is known whether this is D67 wearing a different
symptom.

## 5. THE FEATURE — per-floor totals, and a total

> **Floor AAA: 3880 sf, $260K**
> **Floor BBB: 1200 sf, $129K**
> **Total: 5080 sf, $389K**

**Accepted in shape.** Upper right, real time, per floor, plus a total row.

**And the current behaviour is itself a finding:** `_update_totals` sums
**every `RoomItem` in the scene with no floor filter at all** —

```python
sqft = sum(it.area_sqft for it in self.scene.items()
           if isinstance(it, RoomItem) and it.properties.get("include_sqft", True))
```

**so today's single figure already mixes both floors into one number** and calls
it "Totals". The feature is therefore **a correction as much as an addition**,
and the report should say so rather than presenting it as new capability.

**`include_sqft` is respected today and keeps being respected**, per floor and in
the total.

## 6. IT SITS ON [D55](../defects/0055-area-totals-double-count-overlapping.md), WHICH IS OPEN — and that is the ruling

**D55: *"Area totals DOUBLE-COUNT overlapping regions — the totals bar sums rooms
independently."*** The number in that label is already wrong whenever two rooms
overlap.

> ### SHIPPING PER-FLOOR TOTALS OVER AN OPEN D55 TURNS ONE WRONG NUMBER INTO N WRONG NUMBERS, AND THEN SUMS THEM INTO AN N+1TH.
>
> **The total row is the worst of them**, because it is the one Patrick will
> quote — and a per-floor breakdown makes the figures look *more* authoritative
> exactly as they become more numerous.

**So: D55 IS FIXED FIRST, OR IT IS FIXED AS PART OF THIS.** Not after. The
correct area of a floor is the area of the **union** of its included rooms, not
the sum of their areas — and once it is per-floor, the union is computed per
floor and the total is the sum of the per-floor unions.

**One thing D55's fix must state:** whether two rooms overlapping **across
floors** is even a case. It is not — floors are independent — **and saying so is
what keeps the total row a plain sum.**

## 7. ONE CONSTRAINT FROM [D15](../defects/0015-update-totals-full-scans-on-every-scene.md)

That record closed *"`_update_totals` full-scans on every `scene.changed`"*, and
the fix is the 180 ms debounce still in `mainwindow.py`.

**Per-floor totals must be ONE bucketed pass, not one pass per floor.** A scan
per floor re-opens a closed record on a plan with six levels, and it would do it
quietly.

## 8. TIER AND ORDER

**The census and the floor-tag dump: GREEN, measurement only** — and it can start
immediately, since it does not touch the branch awaiting Patrick's check.

**Any fix to the snapping: AMBER** — it changes what a gesture produces.

**The totals feature: AMBER**, and it **does not start until D55 is ruled**, per
§6.

**Neither displaces [`0033`](0033-report.md)'s check or grid snap.** The redraws
are still the live item.
