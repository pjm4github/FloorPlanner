---
# permanent key, independent of GitHub
id: 70
title: "The asset generator writes a corrupt SVG without complaining, and it fails only at runtime"

# maps directly onto GitHub Issues fields
state: open
state_reason: null
labels:
  - type:gap
  - area:tooling
milestone: null

# ours; becomes body prose after migration
opened: 2026-08-11
closed: null
closed_by: null
rank: 71
related: [46]
state_source: measurement
github_issue: null
---

# D70 — The asset generator writes a corrupt SVG without complaining

## The fault

`_gen_assets.py`'s `svg(w, d, body)` does `"\n".join(body)`, so **`body` must be a
sequence of element strings**. Passing a **single string** joins it **character by
character** and writes a file with one character per line.

**The generator reports success.** Measured while taking the furnishings census
(handoff 0010): a probe entry whose `body` was one string produced

```
wrote 96 furnishing symbols + manifest, 11 tool icons
```

and an SVG that no renderer accepts.

## Why it survives to runtime

**The item looks fine almost everywhere.** With the corrupt symbol on disk it
still reached the catalog, still had a valid manifest entry, still drew a correct
**footprint** in plan, and still built a **3D mesh** — because every one of those
reads the *manifest*, not the SVG.

**Only `catalog.furnishing_renderer()` fails**, returning `None` for an invalid
`QSvgRenderer` — so the plan symbol is **silently blank** inside a correctly-sized
item.

| surface | source | affected |
|---|---|---|
| palette / catalog | `manifest.json` | no |
| plan footprint | `manifest.json` | no |
| 3D mesh | `manifest.json` + `form` | no |
| **plan symbol** | **the SVG** | **YES — blank** |

## THE GATE EXISTS AND ASKS A DIFFERENT QUESTION

`_gen_assets.py` already refuses to write when the data model is incomplete —
`unauthored` (a furnishing with no `SOLIDS` row), `orphans` (a `SOLIDS` row
naming no furnishing), `bad_material` — raising `SystemExit` with counts. **That
is a real, enforced check and it caught nothing here, because it validates the
DATA MODEL and never asks whether the SVG it just wrote is renderable.**

**This is the instrument-boundary shape:** an instrument whose name suggests
*"the assets are well-formed"* answers *"the tables agree"*. Nothing checks the
artifact the generator's own name is about.

## The candidate fix, not taken

**Parse each SVG after writing it** — the generator is already a Qt-free script,
so the cheap form is an XML parse (`xml.etree`) rather than a `QSvgRenderer`,
which would drag Qt into an asset build. **A renderer check would be stronger and
costs a Qt dependency**; an XML parse would have caught this instance, since
one-character-per-line is not well-formed.

**Not decided here.** Which check, and whether it refuses or warns, is a ruling.

## Evidence

Taken in-session while measuring the cost of one new furnishing; the probe was
reverted and the tree left clean. **Reproduction is two lines** in
`_gen_assets.py`: append a `FURNISHINGS` row whose `body` is a bare string rather
than a list, add its `SOLIDS` row, run the generator — it succeeds, and
`furnishing_renderer(<id>)` returns `None`.

## Ruling

*(Open — filed 2026‑08‑11.)* **Found by taking a measurement for something else**,
which is the second time the furnishings area has produced that (D46 —
`make_site_demo.py` minting kinds in no catalog). Filed, not fixed.
