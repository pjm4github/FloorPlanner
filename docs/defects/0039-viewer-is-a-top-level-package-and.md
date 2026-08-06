---
# permanent key, independent of GitHub
id: 39
title: "viewer/ is a TOP-LEVEL package and should live at floorplanner/viewer/"

# maps directly onto GitHub Issues fields
state: closed
state_reason: completed
labels:
  - type:task
  - area:tooling
milestone: null

# ours; becomes body prose after migration
opened: 2026-08-03
closed: 2026-08-04
closed_by: null
rank: 40
related: [41]
state_source: row
github_issue: null
---

# D39 — viewer/ is a TOP-LEVEL package and should live at floorplanner/viewer/

## Record

> **Moved verbatim** from the register (`docs/CODE_REVIEW_v2.md`, the row at its
> line 105) on 2026-08-06 — not reworded, not split, not
> reformatted. The register wrote each row as one continuous argument in which
> symptom, mechanism, evidence, ruling and receipt are interleaved, so dividing
> it into sections would have meant interpreting it. See
> [`README.md`](README.md) for the section shape new records take.

**`viewer/` is a TOP-LEVEL package and should live at `floorplanner/viewer/`.** Filed with the packaging commit (2026‑08‑03), deliberately not built there. The 3D viewer ships as its own top-level package so the packaging change could land without touching `floorplanner/` mid-phase — but a second top-level name in a project that already exports one is a distribution smell: it claims `viewer` on `sys.path` for every install of this app, and nothing else in the tree is addressed that way. **The move, when P4.4 merges:** `packages = ["floorplanner", "floorplanner.design", "floorplanner.viewer"]` and the script entry becomes `floorplanner.viewer.fp3d:main`. Deferred rather than done because it would edit packaging *and* `floorplanner/` while a phase branch is open, and the packaging commit's whole point is that it moves nothing the migration owns. **Its module docstring already says so**, so the code and this row agree. **DONE 2026‑08‑04, the moment the trigger fired** (P4.4 merged at `ae9f0ad`): `git mv viewer floorplanner/viewer` — a rename git tracks as a rename, so the file's history follows it — with `packages = ["floorplanner", "floorplanner.design", "floorplanner.viewer"]`, the script entry `fp3d = "floorplanner.viewer.fp3d:main"`, and every path reference updated (the module's own usage block was changed to read `python -m floorplanner.viewer.fp3d`, on the reasoning that a package module is no longer run as a loose script) **— CORRECTED 2026‑08‑05, and this row is the ORIGIN of the error, not merely a copy of it.** That reasoning was overturned by `VIEWER_NOTES.md` §1's later finding: `-m` imports the parent package, and `floorplanner/__init__.py` star-imports every module, so the `-m` form **transitively imports the whole editor** — destroying the isolation that is the viewer's entire premise. Measured on disk 2026‑08‑05: `fp3d.py`'s usage block reads `python fp3d.py …`, the SCRIPT form, so the claim above was also simply false by the time it was read back. Row 41 inherited the wrong command from here, which is why fixing only row 41 would have left the source intact — the defect‑7 lesson, applied to the record: close the CONDITION, not the instance you happened to be pointed at). The package docstring's "moves once P4.4 lands" line is replaced by the reason it lives there — one top-level name per project — plus the standing rule it must keep: **nothing here imports `floorplanner`**, and a future import of it should be argued, not assumed. Receipts: `import floorplanner.viewer.fp3d` succeeds with no pyqtgraph installed, the console-script and packages metadata parse to the new values, and the census is unmoved.

## Site

`pyproject.toml`, `viewer/`

## Milestone

**DONE (2026‑08‑04)**
