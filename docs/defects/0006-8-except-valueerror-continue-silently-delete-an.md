---
# permanent key, independent of GitHub
id: 6
title: "8 except ValueError: continue silently delete an opening, incl. on load"

# maps directly onto GitHub Issues fields
state: closed
state_reason: completed
labels:
  - type:defect
  - area:io
milestone: P3.6

# ours; becomes body prose after migration
opened: null
closed: null
closed_by: null
rank: 6
related: []
state_source: status-table
github_issue: null
---

# D6 — 8 except ValueError: continue silently delete an opening, incl. on load

## Record

> **Moved verbatim** from the register (`docs/CODE_REVIEW_v2.md`, the row at its
> line 71) on 2026-08-06 — not reworded, not split, not
> reformatted. The register wrote each row as one continuous argument in which
> symptom, mechanism, evidence, ruling and receipt are interleaved, so dividing
> it into sections would have meant interpreting it. See
> [`README.md`](README.md) for the section shape new records take.

~~**8** `except ValueError: continue` silently delete an opening, incl. on load.~~ **CLOSED at P3.6 (R5).** All eight file into one `openings_failed` vocabulary and reach a human by context: load-path entries join the open/conversion report, edit-path entries a status line naming the edit, said once. **The v4 LOAD site (`planio.py`) is the one the defect text singles out** — a v5 load has reported a dropped opening since P1.5 while a v4 load said nothing, and that asymmetry is what closes here. Pinned by a v4 plan carrying a 96" door on a 40" wall. **The "13" is corrected at the P3.6 read-back and was never the count of opening drops:** measured at the migration baseline `841264e`, 13 is the count of *every* `except ValueError` in `floorplanner/`, of which 7 wrapped an `OpeningItem(…)`. Today 17 total, 9 wrapping `OpeningItem`, **8 still silent** — `bridge.py:834` was converted to a reported list at P1.5. The other four at baseline are catalog price parsing ×2, `macro._is_num`, and dialog handlers that already report; feeding those into an opening-error list would be wrong.

## Site

`planio.py:169` (load) · `mainwindow.py:1082`, `:1177` (paste) · `rooms.py:749` (privatize), `:1046` (`duplicate_wall`) · `walls.py:333` (merge), `:587` (split), `:675` (fracture)

## Milestone

**P3.6**
