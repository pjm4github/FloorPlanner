---
# permanent key, independent of GitHub
id: 32
title: "The unwelded-ends warning gave advice that cannot work, and blamed the wrong cause"

# maps directly onto GitHub Issues fields
state: closed
state_reason: completed
labels:
  - type:defect
  - area:ui
milestone: null

# ours; becomes body prose after migration
opened: null
closed: null
closed_by: null
rank: 23
related: [34]
state_source: row
github_issue: null
---

# D32 — The unwelded-ends warning gave advice that cannot work, and blamed the wrong cause

## Record

> **Moved verbatim** from the register (`docs/CODE_REVIEW_v2.md`, the row at its
> line 88) on 2026-08-06 — not reworded, not split, not
> reformatted. The register wrote each row as one continuous argument in which
> symptom, mechanism, evidence, ruling and receipt are interleaved, so dividing
> it into sections would have meant interpreting it. See
> [`README.md`](README.md) for the section shape new records take.

**The unwelded-ends warning gave advice that cannot work, and blamed the wrong cause.** Found at **Gate 3**. The opened-with message said the scene *"disagrees with itself as it arrived… Expected of a plan loaded from a legacy file… Edit > Coalesce all walls now closes them."* **Measured on `planc1TestV5.json` — a v5 file, not a legacy one — which opens with 5 unwelded ends:** the command drops the scene count **5 → 0**, and **the saved document is byte-identical before and after (62 vertices either way)**. Save and reopen and **the 5 are back**. **CORRECTION, 2026-07-31 — my first reading of *why* was wrong and is withdrawn.** I wrote "nothing was broken in the document". Not so: the document carries a genuine **1.53″ gap** — (248.43, **654.0**) and (248.43, **655.53**) are both vertices in the emitted file, twice over — so there *is* something there. What is true is narrower and worse: the command silences the **scene-side count** by merging collinear runs, which removes the ends that would weld **without moving a coordinate**, so the gap survives untouched. The count and the gap are different quantities, and only the count moved. That mis-reading is registered as **defect 34**, which is the repair gap this entry wrongly closed. **On the narrow question this entry began with:** `normalize_walls` closes the whole (0.6″, 9.0″) band where a gap really exists — measured at 0.7/1.5/3.0/6.0/8.5″, all closed; ≥9.5″ correctly not. What was missing was a true message. Reworded to state the observation, name the two causes that look alike from there, and promise a repair only where one is possible. **One test changed** (`test_unwelded_ends_warns_and_strict_raises`: the pinned phrase `"disagrees with itself"` was deleted with the framing; it now quotes the stable half of the sentence).

## Site

`design/bridge.py` (`_warn_unwelded`)

## Milestone

**Gate 3 (fixed, pre-merge)**
