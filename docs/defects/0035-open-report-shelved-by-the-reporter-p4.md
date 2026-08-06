---
# permanent key, independent of GitHub
id: 35
title: "OPEN REPORT, shelved by the reporter (P4.2 mini-gate, 2026-08-01): residual drag diagonals after"

# maps directly onto GitHub Issues fields
state: closed
state_reason: not_planned
labels:
  - type:defect
  - area:geometry
milestone: null

# ours; becomes body prose after migration
opened: null
closed: 2026-08-02
closed_by: null
rank: 36
related: []
state_source: row
github_issue: null
---

# D35 — OPEN REPORT, shelved by the reporter (P4.2 mini-gate, 2026-08-01): residual drag diagonals after

## Record

> **Moved verbatim** from the register (`docs/CODE_REVIEW_v2.md`, the row at its
> line 101) on 2026-08-06 — not reworded, not split, not
> reformatted. The register wrote each row as one continuous argument in which
> symptom, mechanism, evidence, ruling and receipt are interleaved, so dividing
> it into sections would have meant interpreting it. See
> [`README.md`](README.md) for the section shape new records take.

**OPEN REPORT, shelved by the reporter (P4.2 mini-gate, 2026‑08‑01): residual drag diagonals after the three drag fixes.** After clean-gaps + a down-drag of the M Bath/Master Suite wall, Patrick saw a dashed diagonal running from the moved wall's east end toward the Clst corner (`Screenshot 2026-08-01 175022.png`), reported as persisting "in part" after the mixed-corner fix (`8231b92`), then shelved ("there are still some problems with the drag"). **What is measured:** a headless replay of the exact sequence on the fixed tree — including a second drag from the stepped state, drags back up, and undo-then-redrag — is CLEAN twice over: zero diagonal outline edges AND zero diagonal painted-cue segments (`open_edge_segments`). **What is NOT established:** the code identity of the reporting session (it predates the status-bar version label, so it cannot be verified now) and the exact gesture sequence. Candidate explanations, neither confirmed: (a) a stale process still running pre-`8231b92` code — the label was added (`a1e6083`) precisely because this class of doubt had already cost one round; (b) a gesture sequence the replay does not cover. **Re-open protocol:** reproduce with the status-bar version label visible (requires a launch at ≥ `a1e6083`) and record the gesture sequence; a screenshot then carries its own code identity. Until reproduced that way, no fix is attempted — the last three drag findings were each fixed against a measured reproduction, and this one deserves the same standard. **CLOSED 2026‑08‑02, at the mini-gate pass, on the reporter's own confirmation.** The shelf's substance was neither stale-process nor unreproducible — it was **harvested**: Patrick's macro loop (`fiveRoomDragSplit.fpm`, `fiveRoomDragSplit2.fpm`, committed to `examples/` and pinned verbatim) converted the residuals into findings 5 and 6 — six distinct mechanisms, each fixed against a measured reproduction with a fail-first receipt. At the mini-gate re-run — **all 8 items PASS, fresh launch, status-bar version label verified at the launch sha** — Patrick confirms the shelf is **empty**: nothing remains on the "still some problems with the drag" report beyond the harvested findings 4–6. Closed citing that confirmation — the reporter retires the report, which is what the re-open protocol was for; the clean replay alone never could.

## Site

`walls.py` (`_plan_vertex_moves` + the P4.2 drag work)

## Milestone

~~**open — the P4.2 mini-gate re-run decides**~~ **CLOSED 2026‑08‑02 — shelf confirmed empty by the reporter at the mini-gate pass; residuals harvested as findings 5–6, fixed and pinned in P4.2**
