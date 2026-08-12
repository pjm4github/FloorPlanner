---
# permanent key, independent of GitHub
id: 73
title: "Two wall-thickness tables disagree, and the one in validate.py is never read"

# maps directly onto GitHub Issues fields
state: closed
state_reason: completed
labels:
  - type:defect
  - area:schema
milestone: null

# ours; becomes body prose after migration
opened: 2026-08-11
closed: 2026-08-11
closed_by: null
rank: 74
related: [45]
state_source: measurement
github_issue: null
---

# D73 — Two wall-thickness tables disagree, and one is dead

## The fault

**Two type→thickness tables exist and they do not agree:**

| type | `validate.py:17` `STD_T` | `viewer/fp3d.py:51` `WALL_T` |
|---|---:|---:|
| exterior | 6.0 | 6.0 |
| interior | 4.5 | 4.5 |
| partition | 3.5 | 3.5 |
| railing | 2.0 | 2.0 |
| fence | 2.0 | 2.0 |
| **hedge** | **18.0** | **12.0** |
| retaining | 8.0 | 8.0 |

**`STD_T` is never read.** It is defined at module level in `validate.py` and
referenced nowhere in `floorplanner/` — measured while taking the wall-types
census (handoff 0011).

**And a third definition exists in the scene**, in a different shape:
`WallItem.t` is a two-branch conditional over `EXTERIOR_T` / `INTERIOR_T`
(`config.py:43-44`) that knows nothing of the other five types.

## Why it matters more than a dead constant usually would

**The schema says the thickness table is normative.** `wall.thickness_in` is
documented as *"Override; omitted = the standard for `type`"* — so *"the standard
for `type`"* is a real contract, and **three different answers to it live in the
tree**, one of them dead and one of them disagreeing.

**A dead table is also a trap in the direction of looking authoritative.**
`STD_T` sits at the top of `validate.py`, the file that owns the invariants — the
most plausible place a reader would look for the normative table, and the one
place whose copy has no effect at all.

## What is NOT claimed

**No plan is known to be wrong because of this.** `hedge` is a landscape type; no
corpus plan uses one, and the viewer's value is the one that renders. This is
recorded as a **divergence and a dead definition**, not as a rendering fault.

## THE FIX — one table, the duplicates DELETED

**The model's table is normative**, and it is `STD_T` in `validate.py`: the
schema calls *"the standard for `type`"* a contract, and the model layer is where
a contract the schema names belongs. Both duplicates are now **readers**:

* **`viewer/fp3d.py`'s `WALL_T` is deleted** and replaced by a loader.
* **the scene's two-branch conditional is deleted** — `WallItem.t` now resolves
  **override if present, else `STD_T[type]`**.

**Deleted rather than synced**, because three tables that are synced become three
tables that disagree again.

### `hedge` is 18.0 BECAUSE IT IS THE MODEL'S VALUE

**Not because 18 is a better number for a hedge.** The rule decided it, not
taste. **Checked for a dependency on 12.0 before applying it:** the corpus holds
**one** hedge wall, **no test asserts a hedge thickness**, and the only consumer
was the viewer's renderer. The visible effect is that one wall in `site_demo`
renders 50% thicker.

### A measured constraint the fix had to route around

**`import floorplanner.design.validate` drags in the Qt bindings** — measured —
because `floorplanner/__init__.py` star-imports the editor. `fp3d.py` is
deliberately Qt-free (numpy only; `--dump`, `--obj`, `--list-levels` run headless
in CI), so it **loads the module BY PATH** rather than importing it. The module
imports only `json`, `math` and `pathlib`, which is what makes that safe.

**That is why "put it in the model layer and import it" was not enough on its
own**, and the reason is recorded at both ends rather than in this record alone.

## Ruling

*(Closed 2026‑08‑11 — completed.)* Found while taking the wall-types census, not
by a failure. **Fixed as the prerequisite for settable wall types**, which is
what made the direction obvious: both consumers of the table were about to
change anyway.
