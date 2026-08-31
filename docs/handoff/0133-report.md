# 0133 — report: [PR #45](https://github.com/pjm4github/FloorPlanner/pull/45) merged, three ghost branches deleted; the cleanup tranche (0129/0130/0132) starting next

**On [`0129`](0129-ruling.md)/[`0130`](0130-ruling.md)/[`0131`](0131-ruling.md)/
[`0132`](0132-ruling.md) — all read before acting on any.**

## 1. Done, per 0129 §1–2

- **PR #45 merged** → `main` at `abe5e6e`. Branch deleted (`--delete-branch`).
- **Three ghost branches deleted, local and remote** — `dim-row-along-refactor`,
  `export-menu-pdf`, `pdf-dimension-and-door-fix`, each confirmed `git log
  main..<branch>` empty (0 commits ahead) before deletion, matching `0129`
  §2's own measurement.
- **Branch deletion now folded into the merge step itself** going forward —
  noted so it stops being a step that can lapse.

## 2. Next — the cleanup tranche, per 0129 §3 / 0130 / 0132

One branch, one check, building now:

- **(a)** grid-aware station filtering, reading the document's own
  `wall_snap_in` (default 6.0 only when the settings block is absent).
- **(b)** verify lane labels already use `ftin` (0118/0127's own machinery) —
  confirm, not assumed.
- **(c)** title-block note → "All dimensions to wall centerlines".
- **(d)** openings — already out everywhere, reaffirmed, no new work.
- **0130's amendment**: each row/lane dimensions only walls at its own
  angle — no 45°/135° corner leaks into the X/Y rows, no orthogonal corner
  into a lane; each family's row 2 telescopes within its own extent.

**Check file per 0132: `wiscaway2026-08-30R2.json` / `R2g.pdf`** (two levels,
15 show-dims rooms, `wall_snap_in: 6.0`) — supersedes R1 as the tranche's
before/after baseline. Both promoted from `fixtures/incoming/` under exit 1
when the tranche lands, per `0132` §2.

**Carried, per `0132` §3:** the room-label rounding question (Patrick, one
line), the `L2.dxf` Chief recount, the delta-snap sites, D61-family.
