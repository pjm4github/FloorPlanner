---
# permanent key, independent of GitHub
id: 44
title: "The invariants check CONSISTENCY, not HISTORY - a resurrected wall passes all fifteen, and no"

# maps directly onto GitHub Issues fields
state: open
state_reason: null
labels:
  - type:limit
  - area:schema
milestone: null

# ours; becomes body prose after migration
opened: null
closed: null
closed_by: null
rank: 44
related: [22, 41]
state_source: row
github_issue: null
---

# D44 — The invariants check CONSISTENCY, not HISTORY - a resurrected wall passes all fifteen, and no

## Record

> **Moved verbatim** from the register (`docs/CODE_REVIEW_v2.md`, the row at its
> line 109) on 2026-08-06 — not reworded, not split, not
> reformatted. The register wrote each row as one continuous argument in which
> symptom, mechanism, evidence, ruling and receipt are interleaved, so dividing
> it into sections would have meant interpreting it. See
> [`README.md`](README.md) for the section shape new records take.

**The invariants check CONSISTENCY, not HISTORY — a resurrected wall passes all fifteen, and no reachable widening would catch it.** Asked at P4.5 (2026‑08‑04) as the standing practice now requires: *would deep verify have caught this?* **Measured, through the real path with the fix reverted and the revert verified:** grouping a room whose outline named an absorbed wall re-parented that wall into the scene — scene walls 4 → 5, document walls 4 → 5, `doc0 != doc1`, and `check(doc, deep=True)` returns **CLEAN**, schema **valid**. **Silence.** **Why, and this is the part worth keeping:** the resurrected wall is not a *duplicate* (I4 wants identical endpoints; this is a parallel wall 5″ away), not an unwelded end (I14's band is 0.6″), and not an overlap (I11 is room-vs-room). More fundamentally **the document is internally consistent** — the room's outline names the wall again, so every reference resolves and every relationship holds. The document is simply not the one the user's merge produced. **No invariant can express that**, because the fault is not a structural property of the document but a difference between the document and its own history. **So this is an ACCEPTED LIMIT, not a gap**, and that distinguishes it from row 41 (where I5b *could* in principle be widened to cover pinched loops). The defence against this class is not an invariant but the discipline that already caught it: a predicate that hands back a dead object is a bug at the predicate. **Recorded so the limit's shape is known rather than assumed** — the third time this question has been asked, and the first time the answer is "nothing could have". **THE CONSEQUENCE, which reaches further than this row: a static check cannot see a TRANSITION fault, but a DIFFERENTIAL RECEIPT can.** An invariant judges one document against the rules; a history-fault is only visible as a difference between two documents, so the defence for that whole class lives at the **delta layer**, not the invariant layer. This suite has been using differential receipts all along without naming the class: **defect 22's per-room shared-corner column table** (140/140 → 0/140), **the 3D popup's byte-identical `design_document()`** across an open, **the `merge_all` filing** (scene items moved, saved file byte-identical, which is what turned a suspected defect into a non-defect), and **every fail-first receipt** — red before, green after, which is a delta stated as a pair of runs. Naming it makes it schedulable: when a change alters what an operation *does*, the receipt has to be a difference, because no amount of green `check()` can say the result is the document the gesture *should* have produced.

## Site

`design/validate.py` (all fifteen); the class, not a site

## Milestone

**accepted limit — recorded, not scheduled**
