---
# permanent key, independent of GitHub
id: 13
title: "Detection result depends on view zoom"

# maps directly onto GitHub Issues fields
state: closed
state_reason: completed
labels:
  - type:defect
  - area:geometry
milestone: null

# ours; becomes body prose after migration
opened: null
closed: null
closed_by: null
rank: 14
related: []
state_source: row
github_issue: null
---

# D13 — Detection result depends on view zoom

## Record

> **Moved verbatim** from the register (`docs/CODE_REVIEW_v2.md`, the row at its
> line 79) on 2026-08-06 — not reworded, not split, not
> reformatted. The register wrote each row as one continuous argument in which
> symptom, mechanism, evidence, ruling and receipt are interleaved, so dividing
> it into sections would have meant interpreting it. See
> [`README.md`](README.md) for the section shape new records take.

**Detection result depends on view zoom** (from the deleted `test_zzprobe`). **HALF CLOSED at P3.5, half RETARGETED — and it was reproduced first**, per the task's rider 3 (*a defect closed by the disappearance of its measuring instrument is not closed*). Measured at zooms 0.25×–4× on the `detach_wall_from_room` path **before** deleting anything: **detection was already identical at every zoom** (same area, same corners, 5/5 runs) — it never read the view. **The drag was not**: the same scene-space gesture gave 0 open sides at 0.25× and 1 at 0.5×–4×, and left the wall's far end at y=120 versus y=60. The zoom terms are the drag's — `mousePressEvent`'s `20.0 / _view_scale()` endpoint catch radius and `_project_to_orthogonal`'s `16.0 / view_scale` stick. **Detection half:** closed and now structural — `topology.enclosing_face` is a question about the wall graph with no pixel, cell or canvas in the answer (`test_detection_does_not_depend_on_the_view`). **Drag half:** unassigned, exactly as the P2.3 regression row was left — it is a tolerance question about a mouse gesture, and the honest place is whichever task next touches the drag (**P4.2** extract/join is the nearest). **DRAG HALF CLOSED at P4.2, by the ruling taken at the read-back:** *a gesture tolerance may pick the TARGET; committed geometry must derive from scene-space rules.* Applied: the `16.0/scale` projection stick converts to the fixed scene-space `WALL_PROJECT_STICK` (9″ — the vocabulary's own value, == `join_tol_in`, the same radius draw-release snaps within); the `20.0/scale` endpoint **catch radius stays** zoom-scaled, because it only decides what you grabbed and commits no geometry. Receipt, fail-first: `test_wall_move.py::test_orthogonal_stick_is_zoom_independent` — against the unfixed tree the same drag stuck at 0.25× and fell to the grid at 1.0×; green on exactly the one-line change, with a positive control proving the stick still sticks.

## Site

detection: `rooms.py` (deleted); drag: `walls.py` (`_project_to_orthogonal`, fixed; `mousePressEvent` catch radius kept by the ruling)

## Milestone

**P3.5 (detection) · P4.2 (drag, done)**
