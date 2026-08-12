---
# permanent key, independent of GitHub
id: 71
title: "Renderability is checkable in a test, where Qt is already paid for"

# maps directly onto GitHub Issues fields
state: open
state_reason: null
labels:
  - type:gap
  - area:tests
milestone: null

# ours; becomes body prose after migration
opened: 2026-08-11
closed: null
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

## Ruling

*(Open — filed 2026‑08‑11, as a small follow-up rather than done in D70's pass.)*
**Not urgent**: D70's gate closes the failure that actually occurred, and this
closes the one that could.
