# 0011 — census: settable wall types and porch railings

**Measurement only, parsed not grepped. Nothing implemented.**

---

## THE HEADLINE — the feature is mostly ALREADY BUILT, in the document and the viewer

**`railing` is not a new type to add. It exists in the schema, in the viewer's
thickness table, in the viewer's height table, in the viewer's colour table, and
in an invariant.** What is missing is confined to **the scene and the UI**.

| layer | railing support today |
|---|---|
| **schema** | **`wall.type` enum already has** `exterior, interior, partition, railing, fence, hedge, retaining`, plus a per-wall **`thickness_in` override** |
| **invariants** | **I7 already enforces a rule about it** — landscape types may carry **only gates** |
| **3D (`build_model`)** | `WALL_T["railing"] = 2.0`, **`WALL_H["railing"] = 36.0`**, `WALL_C["railing"]` — thickness, height and colour, all per type, with the `thickness_in` override honoured |
| **scene (`WallItem`)** | **binary.** `t` returns `EXTERIOR_T (6.0)` if `wall_type == "exterior"` else `INTERIOR_T (4.5)` |
| **UI** | the wall context menu offers **exterior and interior only** |

---

## Q1 — what a wall carries

**Document:** `type` (7-value enum), `thickness_in` (optional override, *"omitted =
the standard for `type`"*), `finish_left` / `finish_right`, plus `v1`/`v2`,
`left`/`right`, `openings`.

**Scene:** `WallItem.wall_type` — a plain string, default `"exterior"` — and a
`t` property. **Thickness is per-TYPE and the type vocabulary is two.** A per-wall
`thickness_in` from the document has **no scene representation at all**.

> **So thickness is global-by-type, not per-wall, on the scene side — and the
> document already says otherwise.**

## Q2 — how a wall is drawn

**One routine**: `WallItem.paint` (`walls.py:1451`), with the solid body built in
`_solid` from `length, t, ang` (`walls.py:1380`).

**Thickness is a DRAWING PARAMETER, read from `self.t`** — it is not baked into
the path construction as a constant.

> **This is the single most important number in the census: teach `t` the type
> table and the plan drawing follows for free.** The 2D ruling is safe — the
> drawing routine *can* express thickness per wall.

## Q3 — what `build_model` emits, and where height comes from

```python
t = float(w.get("thickness_in") or WALL_T.get(wtype, 4.5))     # fp3d.py:549
cap = WALL_H.get(wtype)                                        # fp3d.py:552
h   = wall_height or lv[level_id].get("height_in", 96.0)       # fp3d.py:451
```

**Height is already a per-type lookup with a level fallback.** `WALL_H` maps the
three building types to `None` (meaning *full storey*) and gives each landscape
type its own cap — **`railing: 36.0`**, exactly the ruling's number.

## Q4 — do the invariants inspect a wall's properties? **YES — I7 does**

```python
# I7 openings fit their wall, do not overlap, and only on buildable types
if w["type"] in ("railing", "fence", "hedge", "retaining"):
    for op in ops:                    # only gates belong in landscape walls
        if op["kind"] != "gate":
            E.append(f"I7 {w['type']} wall {w['id']} carries a {op['kind']}; "
                     f"only gates are allowed")
```

**So typing walls does NOT cost the invariant set nothing.** The rule is already
written and already enforced.

**And a dormant duplicate is worth recording while we are here:**
`validate.py:17` defines `STD_T` — the same type→thickness table as the viewer's
`WALL_T`, with **`hedge` differing (18.0 vs 12.0)** — and **`STD_T` is never
read**. Two tables, one dead, disagreeing. Filed as
[D73](../defects/0073-two-wall-thickness-tables-disagree-and-one.md).

## Q5 — do openings care what they sit in?

**In the document, yes.** `opening.kind` includes **`gate`**, described as *"the
landscape counterpart of a door: the ONLY opening kind permitted in a fence,
hedge, railing or retaining wall (enforced on the wall, below)"*.

**In the editor, no — and it cannot make one.** `OpeningItem` knows `'door' |
'window'` (`walls.py:2297`, and every branch downstream tests those two). **No
code path anywhere in `floorplanner/` constructs a `gate`**; the string appears
exactly once in the package, in `validate.py`'s check.

---

## WHICH PROVISIONAL RULINGS THE CENSUS CONTRADICTS

**Four of six, and mostly by being already done.**

| ruling | verdict |
|---|---|
| *"A railing is a wall with a type — not a new entity"* | **CONFIRMED**, and stronger than stated: it is already modelled exactly that way |
| *"Schema: add `wall.kind`, an additive optional enum… record it at the revision marker"* | **CONTRADICTED. Do not add a field.** `wall.type` exists and already contains `railing`. **There is no schema change, so R‑B does not need invoking and no revision entry is owed.** |
| *"Start with two values only, `wall` and `railing`; do not speculatively add half_wall or glass"* | **CONTRADICTED, and the speculation already happened** — seven values exist, four of them landscape. The caution is right in spirit and arrives four years late; **nothing should be added, and nothing need be removed for this feature.** |
| *"A railing TAKES OPENINGS — a gate is an opening in a railing, using the same anchor model with no special case"* | **CONTRADICTED IN ITS LAST CLAUSE.** The document agrees a railing takes openings — but **only gates**, and that IS a special case, already ruled and already enforced by I7. **The real gap is that the editor cannot create a gate at all.** |
| *"Height is per-kind… if wall height is one constant, that constant becomes a lookup"* | **ALREADY TRUE.** `WALL_H` is that lookup and `railing` is already 36.0. **Zero work in the viewer.** |
| *"A railing draws as a thinner solid line pair, no dash, no new colour… if the drawing routine cannot express thickness per wall, say so"* | **THE ROUTINE CAN.** `paint` reads `self.t`. **But the viewer already gives railings their own colour** (`WALL_C`), so *"no new colour"* holds in **plan** and is already violated in **3D** — where it is correct and should stay. |

---

## What the feature actually costs

**Three changes, all in the scene and the UI:**

1. **`WallItem.t`** — replace the two-branch conditional with a lookup by
   `wall_type`, honouring a per-wall override if one is carried. **The plan
   drawing then follows with no change to `paint`.**
2. **The wall context menu** — offer the types, rather than exterior/interior.
   This is where *settable* wall types actually lands.
3. **A `gate` opening kind in the editor** — needed for *"a gate is an opening in
   a railing"*, and it is the only genuinely new thing on the list.

**One question the census raises and does not answer:** the scene has no
representation for the document's per-wall `thickness_in`, so a plan whose walls
carry overrides **round-trips through the editor losing them**. Not measured,
because it is outside the five questions — but it is on the same surface as
change (1) and should be checked before that change is designed.
