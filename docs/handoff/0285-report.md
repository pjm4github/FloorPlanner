# 0285 — report: the plan's annotations in the DXF — drawn dimensions, texts and leaders, by the plan's Show switches

**Code, 2026‑10‑17.** His word:

> *"go ahead with the DXF export of annotations"*

Built on `dxf-annotations`, ONE commit on `main`'s tip, **AMBER** — his
check is opening an exported level in a DXF viewer (or Chief).

## 1. WHAT THE DXF NOW CARRIES

Before this, `fp2dxf` wrote a plan's text notes only (on `FP-NOTES`, among
the opening tags, whatever the Show menu said) and nothing of its drawn
dimensions or leaders. Now, by the PDF's rule ([`0268`](0268-report.md),
[`0270`](0270-report.md)) — **what the plan hides is not exported**:

| Kind | Exported while | Layer | Drawn as |
|---|---|---|---|
| Drawn dimension | Show ▸ Dimensions | `FP-DIMENSIONS` (new) | two extension lines, the dimension line, a slash at each end, the length centred above the line in the plan's units (ft‑in or inches) |
| Text | Show ▸ Annotations | `FP-ANNOTATIONS` (new) | TEXT at its point and rotation, as before |
| Leader | Show ▸ Annotations | `FP-ANNOTATIONS` | the line to the tip, a filled arrowhead (R12 `SOLID`), the shoulder under the text, the text aligned to the shoulder's end |

The datum is not exported (nor is it on the PDF). The level's summary line
counts the annotations written.

**One geometry for both exporters.** A drawn dimension's lines, slashes and
label are now computed once, in a new leaf `floorplanner/export/_annot.py`
(standard library only, loaded by path as `_stdt.py` is), which `fp2pdf`
and `fp2dxf` both use; `fp2pdf.ftin` and its `DRAWN_*` constants are now
that leaf's. `fp2pdf`'s suite (88) is unchanged and green — its output is
the same.

## 2. THE GOLDEN FILES, REGENERATED — THE DIFF

`fixtures/chief-export/L1.dxf` / `L2.dxf`: the LAYER table grows from 11
to 13 entries (`FP-DIMENSIONS`, `FP-ANNOTATIONS`); the sample's one text
note moves from `FP-NOTES` to `FP-ANNOTATIONS`, its point, height and text
unchanged. Nothing else. Both `.openings.json` sidecars byte-identical.

## 3. RECEIPT

`tests/test_fp2dxf.py` +8: a dimension's five lines and centred ft‑in
label, at 18" on the plan's side; its lines equal to the PDF sheet's point
for point; inches when the plan shows inches; a leader's line, shoulder,
arrowhead at the tip and right-aligned text; texts on their own layer; each
Show switch hides its own kinds only; both layers declared; and end to end
from the editor, a dimension, a leader and a text on the plan arriving in
the file the menu writes. Gate GREEN.

## 4. WHAT HAPPENS NEXT

His check. Named: his backlog (0248's items 8 and 9).

**Carried:** unchanged from [`0284`](0284-report.md).
