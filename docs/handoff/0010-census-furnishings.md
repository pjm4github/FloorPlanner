# 0010 — census: furnishings

**Measurement only. No design, no code, no proposal.** The probe furnishing added
to take the cost measurement was **reverted** and the tree is clean (`git status`
empty, 689 tests passing, assets byte-identical after regeneration).

**Why it is a census and not a specification:** this is the area where a
specification has twice been written describing code already in the tree.

---

## THE FINDING — the cost of one new item is **TWO EDITS IN ONE FILE, PLUS ONE COMMAND**

Measured by **adding a real furnishing and counting what had to be touched**, not
by reading:

| step | what |
|---|---|
| 1 | one tuple appended to **`FURNISHINGS`** in `_gen_assets.py` — `(id, name, category, width_in, depth_in, body)` |
| 2 | one row added to **`SOLIDS`** in the same file — `(height_in, elevation_in, form, material)` |
| 3 | run **`python _gen_assets.py`** |

**That is the whole cost.** It produced the SVG, the manifest entry, and
membership of the **"All"** palette group automatically, and the item then
appeared on all three surfaces with **no application code changed**:

```
1 PANEL   in catalog: True · spec resolves · in group ['All'] · SVG renderer VALID
2 PLAN    drawn, footprint 30 x 18 in, matching the catalog
3 3D      1 furnishing mesh, 12 triangles, no "unknown kind" note
```

**`GROUPS` is a fourth, OPTIONAL edit** in the same file — only needed to place
the item in a room-type section rather than leaving it in "All".

### So `CLAUDE.md`'s claim is TRUE — tested, not quoted

> *"The app loads catalogs dynamically — adding a symbol needs no app-code
> change."*

**Confirmed by adding one.** The claim was flagged as a *survival justification*,
the class the working agreement says to measure rather than repeat; it survives
the measurement. **The one qualification is that "no app-code change" is not "no
code change"** — `_gen_assets.py` *is* code, and the artwork is authored in
Python, not drawn in an editor.

---

## A DEFECT FOUND BY TAKING THE MEASUREMENT

**The generator writes a corrupt SVG without complaining, and the failure only
appears at runtime.**

`svg(w, d, body)` does `"\n".join(body)`, so `body` must be a **sequence of
element strings**. Passing a **single string** joins it *character by character*.
The first probe did exactly that. The generator reported success —
`wrote 96 furnishing symbols + manifest` — and wrote a file with one character
per line. The item still reached the catalog, still had a manifest entry, still
drew a footprint and still built a 3D mesh; **only `furnishing_renderer()`
returned invalid, so the plan symbol was silently blank.**

**The generator has a completeness gate and it does not cover this.**
`_gen_assets.py` already refuses to write when `FURNISHINGS` and `SOLIDS`
disagree (`unauthored` / `orphans` / `bad_material` → `SystemExit`) — a real,
enforced check. **It validates the DATA MODEL and never asks whether the SVG it
just wrote is renderable.**

**Filed as [D70](../defects/0070-the-asset-generator-writes-a-corrupt-svg.md).**

---

## Q1 — how a furnishing is defined today: **A CATALOG, generated from code**

**`assets/furnishings/manifest.json`, 95 entries**, each:

| field | |
|---|---|
| `id` · `name` · `category` · `file` | identity, palette label, section, SVG file |
| `width_in` · `depth_in` | the true plan footprint, in inches |
| `height_in` · `elevation_in` | 3D extent; `elevation_in` is the underside, so a wall-hung item builds like a floor-standing one, higher up |
| `form` · `material` | which solid generator and which appearance |
| `price` | USD, filled at runtime by the AI tool |

**The manifest is GENERATED** — `_gen_assets.py` is the source of truth, and
`assets/` is never hand-edited. Two sibling files come from the same run:
`groups.json` (palette sections) and `materials.json`.

**Per-user price overrides live outside the asset tree** (`config_dir()/
furnishing_prices.json`) and win over the bundled price, so AI-updated prices
survive regeneration.

---

## Q2 — the 2D symbol: **authored as Python, one place**

The artwork is **drawing code**, not an imported asset: each `FURNISHINGS` row's
`body` is a list of SVG elements built with helpers (`R()` for a rounded rect,
and siblings). `svg()` wraps them with a **viewBox in inches** equal to the
item's real footprint, which is what makes symbols render at true scale.

**Adding one item touches one place** — the `FURNISHINGS` list — for the symbol.

---

## Q3 — the 3D form: **NOT one box per item, but two of nine forms are built**

**Said plainly, because it changes what "add the 3D components" means.** The
catalog names a `form` per item and `fp3d.py` dispatches on it:

```
KNOWN_FORMS = box, slab, seat, bed, basin, enclosure, vehicle, planting, prism
BUILT_FORMS = box, slab
```

| form | items | status |
|---|---:|---|
| `box` | 56 | **built** |
| `slab` | 11 | **built** — a top on legs |
| `vehicle` | 10 | recognised, **falls back to a box** |
| `enclosure` | 7 | recognised, falls back |
| `seat` | 6 | recognised, falls back |
| `bed` | 4 | recognised, falls back |
| `basin` | 1 | recognised, falls back |

**67 of 95 items are on a built form; 28 fall back to a default box** — and the
fallback is **reported**, not silent. `prism` (extruding the symbol's true SVG
outline) is recognised, used by nothing, and recorded as the second pass in
`VIEWER_NOTES.md` §5.

**So the work is BUILDING, not authoring.** The data model is complete — every
item already carries `form`, `material`, `height_in`, `elevation_in`, enforced by
the generator's gate. What is missing is **seven generator functions**, and each
one upgrades every item naming that form at once.

---

## Q4 — parameterisation: **none. Each size is its own entry**

`width_in`/`depth_in` are **fixed per catalog entry**; nothing takes a dimension
at placement time. **35 of 95 entries carry a size in their NAME** — `Gas
Fireplace 4'`, `Dining Table 6'`, `Base Cabinet 24"`, `Large Screen TV 75"` — and
four families exist purely as size variants: `Base Cabinet` ×2, `Pantry` ×3,
`Wall Cabinet` ×3, `Vanity Base` ×2.

**The suspicion behind the question is confirmed.**

---

## Q5 — the AI menu: **one action, and it does not touch furnishings as objects**

```
&AI ▸ Update furnishing prices…
```

**That is the entire menu.** It asks a model for current purchase prices for the
whole catalog and writes them to the `price` field
(`catalog.apply_furnishing_prices`). **Nothing generates or imports a
furnishing.** The catalog's shape, artwork and 3D data are untouched by it.

The machinery beside it is worth knowing because it is the nearest precedent for
an authoring tool: a provider list, an API key stored via `save_api_key`, a
prompt builder (`default_pricing_prompt`), a strict response parser
(`parse_price_json`), and an applier. **The pattern for "ask a model, parse,
apply to the catalog" already exists end to end.**

---

## What this census does NOT answer

**Whether furnishing authoring belongs in the AI tool set is a design question
and is deliberately not answered here.** What the numbers bound is the shape of
the work:

* the **2D symbol** is Python drawing code — generating it is a text-generation
  problem with an existing prompt/parse/apply precedent
* the **3D form** is **not** per-item authoring — it is **seven missing
  generator functions**, and no amount of per-item work substitutes for them
* the **cost floor is already two edits and a command**, so any tool is competing
  against a low bar for the *mechanical* part and against **artwork judgement**
  for the rest
