---
# permanent key, independent of GitHub
id: 41
title: "I5b does not report a self-intersection the walk has planarised into a pinched loop"

# maps directly onto GitHub Issues fields
state: open
state_reason: null
labels:
  - type:gap
  - area:schema
milestone: null

# ours; becomes body prose after migration
opened: null
closed: null
closed_by: null
rank: 42
related: []
state_source: row
github_issue: null
---

# D41 — I5b does not report a self-intersection the walk has planarised into a pinched loop

## Record

> **Moved verbatim** from the register (`docs/CODE_REVIEW_v2.md`, the row at its
> line 107) on 2026-08-06 — not reworded, not split, not
> reformatted. The register wrote each row as one continuous argument in which
> symptom, mechanism, evidence, ruling and receipt are interleaved, so dividing
> it into sections would have meant interpreting it. See
> [`README.md`](README.md) for the section shape new records take.

**I5b does not report a self-intersection the walk has planarised into a *pinched* loop.** Found at P4.5 §2a while writing the gesture-time check, by asking whether the scene check and the document check agree — they do not, and the measurement is exact. A room outlined `(0,0) (120,0) (0,96) (120,96)` self-intersects; the scene predicate says so. But `design_from_scene` planarises, so the two crossing walls are split at their intersection `(60,48)` and the room emits as a **six**-corner loop that visits `(60,48)` **twice**. `validate._seg_cross` is a **proper**-crossing test by deliberate design — its own docstring says it must not fire on the collinear edges two rooms legitimately share — and a loop that *touches* itself at a shared vertex is not a proper crossing. Measured: `check(doc, deep=True)` returns `[]` on that document. **Consequence, and why it changed code in P4.5:** the gesture-time message must NOT promise "the plan cannot be saved", because sometimes it can be — a message that reads as false at a real value is exactly the 06c2145 failure. The message now states the remedy only. **Not fixed here, deliberately:** widening I5b means deciding whether a pinched loop is a violation of I5b or of a new invariant (a loop visiting a vertex twice is *degenerate* rather than *crossing*), and that is a validate.py semantics change with corpus implications, not a P4.5 errand. Pinned by `test_the_gesture_check_catches_what_i5b_can_miss`, which fails the day I5b is widened so the message can be strengthened deliberately. **MEASURED INSTANCES IN THE CORPUS — the gap is not hypothetical, and it has fixtures (added 2026‑08‑04).** A loop can be non-simple by *touching* as well as by *crossing*, and the shipped examples contain the touching kind. Reproduce with the viewer's geometry pass, which names them because it must clean them before it can triangulate:<br>`python floorplanner/viewer/fp3d.py examples/symmetricP1.json --dump`<br>`python floorplanner/viewer/fp3d.py examples/planc1.v5.json --dump`<br>*(the SCRIPT form, corrected 2026‑08‑05: `python -m floorplanner.viewer.fp3d` imports the parent package and therefore the whole editor, which is exactly the isolation `VIEWER_NOTES.md` §1 exists to keep — a reproduction that drags in the code under test is not the reproduction it claims to be.)*<br>Measured: **`symmetricP1.json` — `WIC`, 1 zero-width spur**; **`planc1.v5.json` — `Hall` 4, `M Bath` 6, `WIC` 1**. Both files return **zero I5b errors** under `check(deep=True)` (planc1.v5 reports 23 errors of other kinds, none of them I5b), so these pass the invariant while being non-simple. **Why this matters to the eventual ruling:** `symmetricP1.json` is the **reference clean file** and is corpus-frozen — so "is a spurred loop an I5b violation?" cannot be answered without also deciding whether the frozen reference is to be re-cut, which is a corpus decision as much as an invariant one. The fixtures now exist to decide against rather than argue in the abstract.

## Site

`design/validate.py` (I5b, `_seg_cross`); fixtures `examples/symmetricP1.json`, `examples/planc1.v5.json`

## Milestone

**unassigned — argue at the invariant's own read-back**
