---
# permanent key, independent of GitHub
id: 71
title: "Renderability is checkable in a test, where Qt is already paid for"

# maps directly onto GitHub Issues fields
state: closed
state_reason: completed
labels:
  - type:gap
  - area:tests
milestone: null

# ours; becomes body prose after migration
opened: 2026-08-11
closed: 2026-08-15
closed_by: null
rank: 72
related: [70]
state_source: row
github_issue: null
---

# D71 — Renderability is checkable in a test, where Qt is already paid for

## The gap

[D70](0070-the-asset-generator-writes-a-corrupt-svg.md) made the generator parse
every SVG and refuse. **Its limit is stated at the function and is real: an XML
parse proves the file is well-formed, NOT that it renders.** An SVG that parses
but draws nothing is exactly the failure the generator cannot see.

The fix was ruled as a two-horned trade — *parse (weak, Qt-free)* versus
*`QSvgRenderer` (strong, drags Qt into an asset build)*. **There is a third
option and it is better than either horn:**

> **Keep the generator Qt-free — well-formed XML, refuses before writing. Then
> assert RENDERABILITY in a TEST, where Qt is already present and already a
> dependency.**

**Two checks at two layers, each in the place where its cost is already paid.**
The generator stays a plain script that can run anywhere; the suite already
builds a `QApplication` in `conftest`, so `QSvgRenderer(...).isValid()` over the
catalog costs nothing new.

## The shape

A test that walks `furnishing_catalog()` and asserts
`catalog.furnishing_renderer(spec["id"]) is not None` for every entry — using the
**production** accessor rather than constructing a renderer inline, so it pins
the path the app actually takes. **95 entries today.**

**It would have caught D70's instance**, and it catches the class the generator
structurally cannot: a symbol that is well-formed and blank.

## THE FIX, AND A CORRECTION TO THE FILED METHOD

**The record's proposed instrument was `QSvgRenderer(...).isValid()`. Measured
before trusting it (WORKING_AGREEMENT's positive-control rule), and the premise
was wrong.**

| case | well-formed? | `isValid()` |
|---|---|---|
| a real symbol | yes | `True` |
| `<svg viewBox="0 0 10 10"></svg>` — no children at all | yes | **`True`** |
| an `<svg>` whose only child is a tag Qt's SVG module does not implement | yes | **`True`** |
| D70's char-split case (fails to parse) | no | `False` |

**`isValid()` only re-detects XML that fails to parse — exactly what the
generator's `svg_error` already refuses before writing.** Using it alone would
have made this test a second copy of D70's check, not new coverage, which
directly contradicts the record's own stated purpose (*"it catches exactly what
the generator structurally cannot"*).

**The instrument that actually catches "well-formed and blank": render to a
buffer and look for a painted pixel.** `test_the_positive_control__QSvgRenderer_isValid_is_NOT_ENOUGH`
proves the render-and-look check catches both synthetic blanks that `isValid()`
missed, and that a real symbol still passes.

**The positive control then caught a second, unrelated bug in its own first
draft**: `sip.voidptr.__getitem__` returns a length-1 `bytes` per index, which
is **truthy regardless of value** (`bool(b'\x00') is True`), so the first cut of
the pixel scan reported *every* pixel as painted — including a genuinely blank
image. `bytes(ptr)` first, then index, fixes it. **The control is the reason
this was caught before it shipped as a vacuous "always green" check.**

`test_every_catalog_symbol_renders_something` then walks all 95 catalog entries
through **`furnishing_renderer`, the production accessor**, per the record's
original instruction — that part of the method was right. **Fail-first checked**
by blanking a real symbol (`glass_shower.svg` → an empty `<svg/>`) and
confirming the sweep names it; restored from git afterward.

## Ruling

*(Closed 2026‑08‑15 — completed.)* Filed as a small follow-up; fixed as one,
with the method corrected from what was proposed to what measurement showed was
needed. `tests/test_furnishings.py` — three new tests (the positive control,
its "a real symbol still passes" arm folded in, and the catalog sweep).
