---
# permanent key, independent of GitHub
id: 34
title: "A document gap in the (0.6″, 9.0″) band is reported by nothing and closed by nothing - and the one"

# maps directly onto GitHub Issues fields
state: closed
state_reason: completed
labels:
  - type:gap
  - area:geometry
milestone: null

# ours; becomes body prose after migration
opened: null
closed: null
closed_by: null
rank: 25
related: [32]
state_source: row
github_issue: null
---

# D34 — A document gap in the (0.6″, 9.0″) band is reported by nothing and closed by nothing - and the one

## Record

> **Moved verbatim** from the register (`docs/CODE_REVIEW_v2.md`, the row at its
> line 90) on 2026-08-06 — not reworded, not split, not
> reformatted. The register wrote each row as one continuous argument in which
> symptom, mechanism, evidence, ruling and receipt are interleaved, so dividing
> it into sections would have meant interpreting it. See
> [`README.md`](README.md) for the section shape new records take.

**A document gap in the (0.6″, 9.0″) band is reported by nothing and closed by nothing — and the one command that looks like it repairs them only silences the report.** Found by finishing defect 32's measurement instead of stopping at its first plausible reading. **Measured, per file, as *scene* count vs *document* near-vertex gaps, before and after `Edit ▸ Coalesce all walls now`:** `planc1TestV5.json` scene **5 → 0** while document gaps stay **4 → 4** (two of 1.53″, two of 6.003″); `planc1.json` and `symmetricP1.json` each carry **two 6.003″ gaps and warn about neither** — so the channel both cried wolf and missed the wolf. **The two quantities are different:** the scene count describes how walls decompose into items and falls when collinear runs merge; the gap is a property of the file and does not move. **Why this is not simply a bug to fix:** a 6″ gap is very likely deliberate — the schema calls `join_tol_in` a GESTURE tolerance and says outright that *"a wall deliberately stopping 6″ short of another is a legitimate design (a reveal, a pilaster gap), and nothing may silently close it"* — so an automatic repair is exactly what must not be built, and nothing available can tell a reveal from a mistake. **The shape that fits is a REVIEW, not a repair:** list the near-vertex pairs with their distances and let the user close the ones they did not intend, which is the same discipline as P2.1's conversion report. **Phase: argue P4.2** — it is the task that owns join/extract and therefore the only one where "close this gap" is already a first-class user operation; filing it at P4.3 with the `auto_weld` family is the credible alternative.

## Site

`design/bridge.py` (the count), `walls.py` (`normalize_walls`), and no owner for the review UI

## Milestone

~~**unassigned — argue P4.2, alternative P4.3**~~ **CLOSED at P4.2 as the REVIEW the entry demanded — list, never auto-close.** `near_vertex_gaps(doc)` (validate.py) lists the document's pairs in the (`vertex_weld_in`, `join_tol_in`) band with distances, floating rooms exempt; `close_gap(scene, a, b)` (walls.py) welds ONE user-chosen pair, identity-carrying so outlines follow by construction; Edit ▸ Review wall gaps… surfaces it (the P2.1 conversion-report discipline: report to a human, repair on their say-so). Receipts: the listing pins the band and only the band (1.5″ and 6.0″ listed, welded and ≥9″ not); closing the 1.5″ pair fuses it to one `Vertex` and leaves the 6″ reveal untouched; a floating room parked 2″ from a wall lists nothing. Mini-gate item 7 is the UI-half receipt. **CORRECTED AT THE MINI-GATE (2026‑08‑01, second finding):** the first cut folded **wall ends** onto one anchor but left **room outlines** holding coincident-but-distinct twins — the P3.5 invariant broken — so the *next* drag stranded outline corners into dashed diagonals (Patrick: close symmetricP1's gaps, drag the M Bath/Lounge wall, and M Bath/Hall/Lounge tore). Fix: after the fold, every room on the floor re-adopts its walls' corner vertices (`share_outline_vertices`, the load path's own discipline). Receipt, fail-first: `test_close_gap_leaves_outlines_holding_their_walls_corners` asserts the invariant by identity, red against the first cut in a worktree, green on the fix; end-to-end on `symmetricP1` — both 6.003″ gaps closed, zero stranded corners, zero new diagonals through the M Bath/Lounge drag.
