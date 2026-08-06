---
# permanent key, independent of GitHub
id: 17
title: "Deleting a room's own perimeter wall is silently a no-op"

# maps directly onto GitHub Issues fields
state: closed
state_reason: completed
labels:
  - type:defect
  - area:geometry
milestone: P4.1

# ours; becomes body prose after migration
opened: null
closed: null
closed_by: null
rank: 17
related: []
state_source: row
github_issue: null
---

# D17 — Deleting a room's own perimeter wall is silently a no-op

## Record

> **Moved verbatim** from the register (`docs/CODE_REVIEW_v2.md`, the row at its
> line 82) on 2026-08-06 — not reworded, not split, not
> reformatted. The register wrote each row as one continuous argument in which
> symptom, mechanism, evidence, ruling and receipt are interleaved, so dividing
> it into sections would have meant interpreting it. See
> [`README.md`](README.md) for the section shape new records take.

~~**Deleting a room's own perimeter wall is silently a no-op.**~~ **FIXED at P4.1 — by deletion, not repair.** `fracture_delete_wall` kept every stretch running along a room perimeter and rebound it, so the user pressed Delete and nothing happened — no wall removed, no message. Measured at P0.4: 4 walls in, 4 walls out, 0 open edges. **The closing coda, measured at the P4.1 read-back (2026‑07‑31), is the final argument for deletion over repair: the no-op had aged into misinformation.** Post-P3.7 the fracture path measured 4 bound walls + **1 open edge** — fracture deletes the original wall and mints a replacement segment, the outline still names the dead wall, and `open_edges()` counts an edge whose wall left the scene as open — so the "no-op" painted a dashed open cue over an edge a wall actually covers. Fix: `delete_wall` (P4.1) deletes outright; the room survives by construction through its stored outline and the vacated edge genuinely opens. The fracture family (`fracture_delete_wall` + `_merge_intervals`, 66 lines) is deleted; receipt is characterization 2b flipping xfail→pass on exactly the call-site switch (513/6 → 514/5, nothing else moved).

## Site

`walls.py` (`delete_wall`; fracture deleted), `mainwindow.py` (`delete_selected`)

## Milestone

**P4.1 (done)**
