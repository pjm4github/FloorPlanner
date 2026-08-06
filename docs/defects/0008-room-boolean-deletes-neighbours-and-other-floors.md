---
# permanent key, independent of GitHub
id: 8
title: "room_boolean deletes neighbours' and other floors' walls, forces \"interior\""

# maps directly onto GitHub Issues fields
state: closed
state_reason: completed
labels:
  - type:defect
  - area:geometry
milestone: P3.5

# ours; becomes body prose after migration
opened: null
closed: null
closed_by: null
rank: 8
related: []
state_source: row
github_issue: null
---

# D8 — room_boolean deletes neighbours' and other floors' walls, forces "interior"

## Record

> **Moved verbatim** from the register (`docs/CODE_REVIEW_v2.md`, the row at its
> line 73) on 2026-08-06 — not reworded, not split, not
> reformatted. The register wrote each row as one continuous argument in which
> symptom, mechanism, evidence, ruling and receipt are interleaved, so dividing
> it into sections would have meant interpreting it. See
> [`README.md`](README.md) for the section shape new records take.

~~`room_boolean` deletes neighbours' and other floors' walls, forces `"interior"`~~ **FIXED at P3.5.** Two faults, one cause: the op worked from a **re-traced boundary** rather than from what the rooms said they were made of. Its inputs' walls came from `bounding_walls()` — a proximity query over the whole scene with **no floor filter** — and the op removes everything it is handed, so a combine took the wall a third room shared with an input (breaking that room open) and any wall of any other floor whose body touched the band. And every result wall was built `"interior"`, so a combine downgraded 6″ exterior walls to 4½″ ones. Fix: inputs come from each room's **outline** (`room_walls`), a wall still bordering a non-input room is kept, and each result edge inherits type and floor from whichever input wall runs along it (exterior wins a tie). Two regression tests, both verified to fail against the old code before being kept.

## Site

`mainwindow.py` (`_selected_room_shapes`, `room_boolean`, `_source_edge`)

## Milestone

**P3.5 (done)**
