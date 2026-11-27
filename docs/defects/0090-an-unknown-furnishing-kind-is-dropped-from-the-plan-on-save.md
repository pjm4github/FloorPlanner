---
# permanent key, independent of GitHub
id: 90
title: "An unknown furnishing kind is dropped from the plan on save"

# maps directly onto GitHub Issues fields
state: open
state_reason: null
labels:
  - type:defect
  - area:io
milestone: null

# ours; becomes body prose after migration
opened: 2026-11-27
closed: null
closed_by: null
rank: 90
related: []
state_source: ruling
github_issue: null
---

# D90 — An unknown furnishing kind is dropped from the plan on save

## The report

**Recorded by the reviewer, [`handoff/0378-ruling.md`](../handoff/0378-ruling.md)
§5, 2026‑11‑26,** while ruling the path by which the 0376/0377 furnishings reach
`main`:

> *"Twice now a running app that did not know a new kind has dropped it from
> Patrick's plan on save (the wicker set, then four cabinets). An unknown
> furnishing is skipped on load and so is gone on save."*

Both instances happened the same way: a plan was saved by a build of the app
that carried a newer catalog (it held kinds the loading build did not), the
loading build met a furnishing whose `kind` it did not recognise, **skipped it
on load**, and then the next **save wrote the plan back without it** — so the
furnishing was silently lost rather than preserved.

1. **The wicker set** — `wicker_chair`, `wicker_chair_small`, `wicker_table`,
   `wicker_loveseat`, placed in a plan on a build that knew them, lost when that
   plan was opened and re-saved by an older build.
2. **Four cabinets** — four of the 0368 kitchen-casework kinds (`tall_cab`,
   `kitchen_desk`, `corner_wall_cab`, `ceiling_cab`), the same way.

## Why it matters

A load that cannot build a kind should not make the save destroy it. The data
for the furnishing is intact in the file; the loss is entirely in the round
trip through a build that does not recognise the `kind`. A plan edited on one
machine and opened on another — or opened after a downgrade — quietly loses
furniture, with no error and no prompt.

## Not yet diagnosed / not fixed

No fix is ruled (0378 §5: *"No fix is ruled here."*). The shape of a fix is
likely to **carry an unknown furnishing through load and save untouched** —
keep its raw record (kind, pos, rotation, state) as an opaque passenger and
write it back on save, drawing a placeholder (or nothing) rather than dropping
it — but the decision, and whether an unknown kind should warn, is reserved.

## Status

**OPEN.** Filed per 0378 §5 while landing the 0376/0377 furnishings lane, so the
observation is not lost when that work merges.
