# 0127 — ruling: Patrick's three check findings on the 45° lanes — [`0120`](0120-ruling.md) amended, one receipt reversed

**Numbering note: authored and dated as `0124`, renumbered `0127` on landing
— `0124`/`0125` had already been taken by Code's own reports before this
file reached disk. Neither renamed after commit; this is the one-time fix
before either existed in the shared record.**

**Patrick, direct to Code, 2026‑08‑30, on `DIM45.png` /
`wiscaway2026-08-30R1.json`** (both in `fixtures/incoming/`, screenshot read):

> *"1) I dont want the positions of the doors listed in the dimensions. 2) The
> 45 degree callouts should be snug against the outermost 45 degree walls as
> would be the case if they landed on the RED line in the image. 3) The
> callouts should not cross over the drawing in the 45 degree rooms. These
> should match the way the callouts are done on the regular rooms."*

His instruction outranks the ruling (`ca3c6b7`). All three adopted.

---

## 1. DOORS OUT — and one receipt flips

[`0119`](0119-ruling.md) §1 / [`0120`](0120-ruling.md) §2.3 ordered opening
centrelines **into** the lanes as "the second deliverable." **Withdrawn for the
angled lanes.** Stations are **wall endpoints only**.

> **The receipt reverses with it:** [`0120`](0120-ruling.md) §4's
> *door-station-present* test now asserts the door station **absent**. A spec
> amendment that leaves the old test standing green is how a reversal gets
> silently unreversed later.

**One question, not guessed:** the bottom/left rows also carry opening
centrelines — from the original `fp2pdf` template's own spec (*"row 1 …
every opening centerline"*). **"The dimensions" read literally covers those
too. Patrick: do the orthogonal rows drop door stations as well, or keep
them?** The angled lanes drop them either way, now.

## 2. SNUG + NO CROSSING ARE ONE RULE, NOT TWO — the orthogonal rows already state it

Measured at `fp2pdf.py:612/624`: the bottom row's extension lines start at
**`ext_base` — the geometry bbox edge** — and run the short distance out to the
row. **They never cross the plan.** The 45° lanes failed both findings by
missing that one convention: baseline anchored far away, extension lines run
from each station clear across the garage wing (the hatch in the screenshot).

**RULED, the rotated equivalent of `ext_base`:**

* **Lane baseline** = the family's own **outer envelope** — the maximal
  perpendicular extent of the participating rooms' geometry — plus `DIM_LANE`.
  **That is Patrick's red line, by construction.**
* **Extension lines start at that envelope**, not at each wall — outward only,
  never through geometry.
* **His two red lines are the two lanes:** the 45° and 135° families each get
  their own baseline on their own side of the wing, exactly as X owns the
  bottom edge and Y the left.

**Receipts:** every extension-line start point lies outside the family
geometry's extent (the no-crossing assertion); the lane baseline's offset from
the outermost participating wall equals `DIM_LANE` within tolerance (the snug
assertion) — both on `wiscaway2026-08-30R1.json` itself, which is the
reproduction and should be **promoted from `incoming/` under exit 1** with
these tests naming it. `DIM45.png` → `docs/evidence/`, cited by this file.

## 3. TIER

**AMBER, same branch, same in-flight work** — this is check feedback folded
into the build it checked, not a new item. The re-check is the same export:

> **Lanes hug the red lines, nothing crosses the wing, no door positions —
> and one room's dimensions OFF still removes its edges.**

**Carried:** §1's orthogonal-row door question (Patrick, one line), the
`L2.dxf` Chief recount, the delta-snap sites, D61-family.
