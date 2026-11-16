# 0349 — ruling: 0348 accepted — the report reads. Two findings from the first design passes: I11 misfires on L-shaped rooms; the 3D panel is now too small

**Reviewer (Cowork), 2026-11-16.** Answers [`0348`](0348-report.md). Passes
0005 and 0006 (`wiscaway-c01`) ran against PID 27380; the header, verdict,
room labels and both plans read. Accepted.

## 1. I11 (room overlap) reports overlaps that are not there — a defect record, not a fix order

Pass 0005: `I11 rooms 'FOYER' and 'PORCH' overlap`, `I11 rooms 'OFFICE' and
'BH2' overlap`. Neither pair overlaps; each shares edges only. In both, one
room is an L. `validate.check` (I11) tests the MEAN OF A ROOM'S CORNERS
against the other polygon (`_pip(cb, pa) or _pip(ca, pb)`), and for a
concave room that mean can lie outside the room and inside its neighbour.
Collinear corners move it further. Splitting each L into two rectangles made
the same geometry PASS (0006) — which is the evidence.

- **Open a defect record.** Reproduction: two rooms, one an L wrapping the
  other's corner; `plan_validate` on `wiscaway-c01/0005.plan.json` shows it.
- **No fix is ruled here.** A correct test (an interior point, or true
  polygon intersection area) changes what the app accepts on load: AMBER,
  and Patrick has not asked for it. The reviewer works round it.

## 2. The 3D panel

0348 §1.4 cured the crop; the house is now about a fifth of the panel's
width (`wiscaway-c01/0006.report.png`). Frame the model to fill roughly 80 %
of the panel — fit to the model's bounds rather than a fixed zoom. GREEN,
tooling. Restart and report the PID.

## 3. Owed

- **Code:** §1 the record; §2.
- **Reviewer:** candidate 02 on Patrick's review of candidate 01.
