---
# permanent key, independent of GitHub
id: 22
title: "A group move orphans every room outline it carries"

# maps directly onto GitHub Issues fields
state: closed
state_reason: completed
labels:
  - type:defect
  - area:groups
milestone: null

# ours; becomes body prose after migration
opened: null
closed: null
closed_by: null
rank: 32
related: []
state_source: row
github_issue: null
---

# D22 — A group move orphans every room outline it carries

## Record

> **Moved verbatim** from the register (`docs/CODE_REVIEW_v2.md`, the row at its
> line 97) on 2026-08-06 — not reworded, not split, not
> reformatted. The register wrote each row as one continuous argument in which
> symptom, mechanism, evidence, ruling and receipt are interleaved, so dividing
> it into sections would have meant interpreting it. See
> [`README.md`](README.md) for the section shape new records take.

~~**A group move orphans every room outline it carries.**~~ **FIXED as a P3.5-followup.** `GroupItem.bake` assigned new COORDINATES to every member wall end — split-on-write by P3.1's ruling, so each end came away on a fresh `Vertex` — and rebuilt each carried room's corner list beside it, minting a third set. The two agreed numerically and shared nothing, so after a bake a room's outline no longer held its walls' corners and the next wall drag left the room behind. **Measured on `symmetricP1`: 140/140 shared corners → 0/140, and a party-wall drag then resized nothing (−18.20 / +9.50 sf before, +0.00 / +0.00 after).** `_apply_rotation` had the identical defect. **Not a P3.5 mistake so much as a P3.5 consequence:** `refresh_rooms` re-bound and re-shared after every group move, so deferring bake's conversion to P4.5 was safe exactly as long as detection existed — P3.5 changed the deferral's premise. Fix: both paths move through one set of CORNER RECORDS and relocate each corner once, so walls and outlines follow by construction (the plan's own `move_vertices`); a corner a non-member wall also holds is SPLIT first, so the group moves and the outsider does not. **Found by a manual smoke test, not by the suite** — every group test tops out at ~5 members and none asserted on `unwelded_ends`; both gaps closed with five new tests.

## Site

`items.py` (`bake`, `_apply_rotation`, `_corner_records`)

## Milestone

**P3.5-followup (done)**
