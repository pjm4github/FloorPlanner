---
# permanent key, independent of GitHub
id: 46
title: "tools/make_site_demo.py mints furnishing kinds that exist in no catalog, so a SHIPPED EXAMPLE"

# maps directly onto GitHub Issues fields
state: open
state_reason: null
labels:
  - type:defect
  - area:tooling
milestone: null

# ours; becomes body prose after migration
opened: 2026-08-05
closed: null
closed_by: null
rank: 26
related: []
state_source: row
github_issue: null
---

# D46 — tools/make_site_demo.py mints furnishing kinds that exist in no catalog, so a SHIPPED EXAMPLE

## Record

> **Moved verbatim** from the register (`docs/CODE_REVIEW_v2.md`, the row at its
> line 91) on 2026-08-06 — not reworded, not split, not
> reformatted. The register wrote each row as one continuous argument in which
> symptom, mechanism, evidence, ruling and receipt are interleaved, so dividing
> it into sections would have meant interpreting it. See
> [`README.md`](README.md) for the section shape new records take.

**`tools/make_site_demo.py` mints furnishing kinds that exist in no catalog, so a SHIPPED EXAMPLE contains objects the app cannot place.** Filed 2026‑08‑05 on the `viewer-furnishings` branch, where deleting the 3D viewer's private `FURN` table removed the only definition these kinds have ever had. **Measured:** `make_site_demo.py:96‑99` places `shrub` ×4, `tree`, `bench` and `planter` into `examples/site_demo.json`; none of the four is in `assets/furnishings/manifest.json`, so `furnishing_spec()` returns `None`, the editor cannot place them from the palette, and a load reports them under `unknown_furnishings`. The viewer's `FURN` table gave them footprints and colours **that the editor never had**, which is why nobody noticed: the two disagreed about what the catalog contains, and the viewer was the more generous of the two. Since VF(4) they render as magenta default boxes and are named in the report — **7 objects in the shipped example** — which is the honest state, because *a viewer that renders objects the editor cannot create is the viewer lying*. **This is a TOOL DEFECT NOW, not merely a gap P5.2 will fill:** the example is committed and is what a new reader opens first. **Two ways to close it, and they are not equivalent:** add the four to the catalog as real symbols in `_gen_assets.py` (artwork, and it pre-empts P5.2's landscape-catalog decision — deliberately refused here), or have the tool place only kinds the catalog defines and regenerate the example. The second is available today and does not spend a decision that is not yet due.

## Site

`tools/make_site_demo.py:96‑99`; `examples/site_demo.json`

## Milestone

**unassigned — argue at P5.2, or close cheaply before it**
