# 0269 — report: PR #88 merged on his word, the PDF tranche folded in — the item annotations in one font size and one colour; the plan set's drawn dimensions and its texts by the Show switch

**Landed:** PR #88 · d4083ba · 2026-10-12 · AMBER · checked by Patrick in the app: "The export looks good. The Item Font side looks good. commit and push that to main"

**Code, 2026‑10‑12.** The record ([`0197-ruling.md`](0197-ruling.md) §7).
[`0267`](0267-report.md) built his annotation-display clean-up on
`item-annotations-font` (PR #88); [`0268`](0268-report.md) built his two
PDF asks on `pdf-drawn-dims`, one commit stacked on it, no PR of its own.
His check of both, from the stacked checkout:

> *"The export looks good. The Item Font side looks good. commit and push
> that to main."*

Done as said, the fold of [`0257`](0257-report.md)'s precedent:
`item-annotations-font` fast-forwarded to `pdf-drawn-dims`'s tip
(`8c0d013`), `main` (`5824a3f`, 0268 landed) merged in with the snapshot
resolved as the branch's and re-cut, the gate GREEN on the merged tree,
pushed; then the branch landed on `main` at **`d4083ba`**, fast-forward;
[PR #88](https://github.com/pjm4github/FloorPlanner/pull/88) MERGED; both
branches deleted, local and remote.

## 1. WHAT LANDED, in one place

* **The item annotations** ([`0267`](0267-report.md)): one font of nine
  view pixels at any zoom and one colour for every kind — wall, corner,
  opening, room, furnishing, roof — through `callout_font`/`draw_callout`
  in `annotations.py`; the opening's session label on the other side of
  the wall from its size code; the room's painted after the fill; the
  furnishing's unclipped. The offscreen font engine's five-pixel floor
  recorded as a trap.
* **The PDF plan set** ([`0268`](0268-report.md)): a level's drawn
  dimensions, while Show ▸ Measurements is on, printed as the screen draws
  them in place of the auto rows and lanes (the title block says
  *Dimensions as drawn on the plan*; the fallback unchanged); its text
  annotations printed only while Show ▸ Annotations is on.

## 2. WHAT HAPPENS NEXT

Nothing open on a branch. On his words to come: his further tuning of the
annotation tool and the Show menu. Named: DXF export of annotations; a
leader annotation; his backlog (0248's items 8 and 9).

**Carried:** unchanged from [`0268`](0268-report.md).
