---
# permanent key, independent of GitHub
id: 70
title: "The asset generator writes a corrupt SVG without complaining, and it fails only at runtime"

# maps directly onto GitHub Issues fields
state: closed
state_reason: completed
labels:
  - type:gap
  - area:tooling
milestone: null

# ours; becomes body prose after migration
opened: 2026-08-11
closed: 2026-08-11
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

## THE FIX — an XML parse, and it REFUSES

**Ruled: parse, and refuse.** `svg_error(text)` runs `xml.etree.ElementTree.
fromstring` and returns a message or `None`. **Both writers use it** — the
furnishing loop *and* the tool icons, which build their SVG inline rather than
through `svg()`; **one writer skipped would have been the whole gap**.

**It refuses BEFORE writing anything**, matching the data-model gate's existing
shape: every symbol is built and validated, then the batch is written. A
half-written asset tree is worse than none.

**The message names the known cause**, because the fix is one character:

```
assets not written -- 1 malformed SVG(s):
  d70_probe.svg: body is a str, not a list of elements (not well-formed ...)
```

**THE LIMIT IS STATED AT THE FUNCTION, not hidden:** an XML parse proves the file
is **well-formed XML, not that it renders**. `QSvgRenderer` would be stronger —
it would also reject an SVG that parses but draws nothing — and it would drag Qt
into an asset build that is deliberately Qt-free. That trade is the ruling, and
it is recorded where the next reader will meet it.

### Receipt — three arms, and nothing was written in any of them

| arm | result |
|---|---|
| a furnishing `body` as a bare string (**D70's exact cause**) | **refused**, exit 1, no `.svg` written |
| a furnishing with a **truncated element** (not the string case) | **refused**, exit 1 |
| a **tool icon** with a bare-string body | **refused**, exit 1, no `.svg` written |

A normal run is unaffected: `wrote 95 furnishing symbols + manifest, 11 tool
icons`, and the regenerated assets are **content-identical** to the committed
tree.

**Pinned by `tests/test_gen_assets.py`** — four tests, exercising `svg_error`
compiled out of the source rather than imported, because the generator writes
assets **at import** and importing it in a test would regenerate the tree as a
side effect. The bare-string case is reproduced **the way the generator produces
it** (`"
".join(body)` over a str) rather than by hand-writing broken XML, so
the test pins the defect and not a straw man.

## Evidence

Taken in-session while measuring the cost of one new furnishing; the probe was
reverted and the tree left clean. **Reproduction is two lines** in
`_gen_assets.py`: append a `FURNISHINGS` row whose `body` is a bare string rather
than a list, add its `SOLIDS` row, run the generator — it succeeds, and
`furnishing_renderer(<id>)` returns `None`.

## Ruling

*(Closed 2026‑08‑11 — completed.)* **Found by taking a measurement for something
else**, which is the second time the furnishings area has produced that (D46 —
`make_site_demo.py` minting kinds in no catalog). **Fixed with an XML parse that
refuses**, per the ruling; the renderer-strength alternative is recorded above
with its cost rather than left as an unexamined option.
