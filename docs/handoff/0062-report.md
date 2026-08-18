# 0062 — report: `_align_to_wall`'s cross-floor snap, fixed — AMBER, PR open

**On [`0061-ruling.md`](0061-ruling.md).** The fail-first test built and
confirmed RED, then the fix, confirmed GREEN. The wider hardening pass
`0061` §4 names is not built — scoped down and named, §3 below. The
`fixtures/incoming/` exit is taken, named, §4 below.

---

## 1. THE FAIL-FIRST TEST — RED before the fix, GREEN after

`tests/test_floors.py::test_align_to_wall_does_not_snap_to_a_hidden_floor`,
next to the two tests already covering `walls.py`'s floor-scoped snap
helpers. A synthetic scene, not the real fixture — see §4: a two-wall,
two-floor scene with an open end at `(500, 500)` on a hidden `"Upper"`
floor, then `win.view._align_to_wall(None, QPointF(505, 300), horizontal=True)`
called directly — the production predicate, not a restatement of it.

**Run before the fix:**

```
AssertionError: a new wall's endpoint snapped to an open end on a hidden floor
Obtained: 500.0
Expected: 505.0
```

Exactly the bug: the free coordinate (505) jumped to the hidden floor's
coordinate (500) rather than staying where it was drawn. **After the fix,
same test, same assertion — passes.**

## 2. THE FIX — the filter every other geometry hot path already has

`floorplanner/view.py`, `PlanView._align_to_wall`: added `active =
active_floor()` and `w.floor != active` to the existing `isinstance`/
`exclude` guard on the `sc.items()` loop — the identical shape
`nearest_wall_endpoint`/`nearest_wall_body` (`walls.py`) already use.

`floorplanner/walls.py`, `wall_endpoint_open`: gained an optional `floor=`
parameter (its sole caller now passes `active_floor()`) so the *is this end
already joined* check is also scoped to the active floor's own network,
rather than a wall on another floor being able to mark an active-floor end
as "not open" by coincidental proximity.

**Full regression pass, not just the new test:**
`pytest tests/test_floors.py tests/test_view.py tests/test_walls.py` (incl.
`gui`) — 65 passed. `ruff check floorplanner/view.py floorplanner/walls.py
tests/test_floors.py` — clean. Full gate on the branch: GREEN,
`collected=779` (778 + this one new test).

## 3. WHAT `0061` §4 ALSO NAMED, AND WHY IT IS NOT BUILT HERE

`0061` §4 names four more unfiltered `scene.items()`/`items(pos)`/`items(area)`
sites (`hit_candidates`, the rubber-band select, the two macro paths) as "the
same class" and says they "should be fixed in the same pass." **Not done
here, and the reason is in `0061`'s own §2:** it draws the line itself —
*"that argument [masking] holds for `items(pos)` — `view.py:305` and `:309`
... `view.py:244` is `sc.items()`, not `items(pos)`. Nothing masks it."*
`hit_candidates` (`items(pos)`) and the rubber-band select (`items(area,
...)`) are both position/area-scoped queries of the same kind `0061` itself
found masked by Qt visibility — not the unmasked, bare-iteration class
`_align_to_wall` was. Fixing them has no fail-first receipt behind it the
way `_align_to_wall` now does: no reproduction was attempted, and "add a
filter that changes nothing observable today" is exactly the kind of
change AMBER's own bar (*"changes what a gesture produces"*) doesn't
obviously clear or fail — safer to name it as follow-on hardening than
bundle an unreceipted change into this PR. **Named, not silently dropped:**
worth its own small pass, each site with the same test shape `0061` asks
for, once this fix has had its manual check.

## 4. THE `fixtures/incoming/` EXIT — taken and named

`fixtures/incoming/crossfloor-snap-2026-08-17.json` → `fixtures/crossfloor-snap-2026-08-17.json`
(`git mv`), entry added to [`fixtures/README.md`](../../fixtures/README.md).
**The choice, stated once:** the *defect* is covered by the synthetic
case — the minimal scene above reproduces the exact mechanism
deterministically, which a 151-wall real plan with no `.txt` note describing
what Patrick was doing cannot improve on. The *file* is kept, not deleted —
it is real corpus evidence independent of this bug (the corpus's worst
orthogonality outlier, cited across four handoffs), and `fixtures/`, unlike
`incoming/`, permits a fixture no test names. `docs/evidence/orthogonality_census.py`
sweeps `fixtures/` recursively regardless of subdirectory, so its own
numbers (§ the previous commit) are unaffected by the move — re-run,
confirmed identical total (948 walls, 63 headline).

## 5. WHAT REMAINS

- **Patrick's manual check — the merge condition, per `0061` §6**: *"with
  the second floor hidden, does a wall you draw still jump to something you
  cannot see?"* Draw near a hidden floor's dangling wall end; the endpoint
  must stay where drawn.
- **Item C's ruling** — still `0061`'s own, still owed, still not this
  report's to write. `0061` §6 says its own table (`0060`'s reachability
  census) is now the input it needed.
- **The four masked sites named in §3** — a follow-on hardening pass, not
  urgent, not built.

## 6. TIER AND WHERE IT LIVES

**AMBER**, per `0061` §6: *"it changes what a gesture produces."* Built on
branch `cross-floor-align-fix`, gated GREEN, PR opened — **stopped for
Patrick's manual check, not merged.**
