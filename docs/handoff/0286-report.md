# 0286 — report: the Chief workflow's step 10 rewritten — importing `L2.dxf` onto a second floor; folded into PR #97 with his own screenshot edits

**Code, 2026‑10‑17.** His word, after his check of [`0285`](0285-report.md)
in Chief:

> *"The DXF import into Chief Architect works well. There is an outstanding
> question though: How do I import L2.dxf, for example, into a second floor
> (or a second layer)? … add a section that described how to setup a second
> floor then import the L2.dxf exported floor."*

## 1. THE ANSWER, IN ONE LINE

A **floor**, not a layer: Chief's layers are display layers shared by every
floor, so each `<level>.dxf` goes onto its own Chief floor, and the floor
it lands on is whichever floor Chief is **showing** at import.

## 2. THE README (on `dxf-annotations`, PR #97)

Step 10 of *The verified Chief Architect X17 import workflow* is now a
procedure, a–h: which file is which floor (FloorPlanner's **Floors** menu
shows each floor's elevation and height; the file is named by the level
id); finish floor 1 first; match floor 1's Finished Ceiling to its
FloorPlanner height (optional; Chief's platform adds a few inches in 3D);
**Build ▸ Floor ▸ Build New Floor…**, derive from floor 1, confirm floor 2
is showing; delete the derived placeholder walls on **this floor only**;
import `L2.dxf` with the identical settings and **never move it** (one
shared origin is what stacks the floors); CAD to Walls on floor 2; check
with the Reference Floor display. A third floor and a basement in a
sentence each. **What is verified is said in the step:** the two dialogs of
d and the result in h (existing screenshots); the rest follows Chief's
standard floor handling and has not been re-captured.

Also corrected in the same section, all made stale by 0285: step 7 (the
file now carries dimensions, as plain lines and text); step 8 (never assign
`FP-DIMENSIONS` / `FP-ANNOTATIONS` / `FP-NOTES` in CAD to Walls); the
cleanup sweep (it deletes the exported dimensions and notes too); Known
limitations (annotations are exported); the QC step renumbered 11.

## 3. HIS OWN EDITS, INCLUDED ON HIS WORD

His in-progress edits to the same section were in the working tree: steps
1–9 renumbered, with a new menu step (`00-import-drawing-dxf-menu.png`)
and a "click next" step (`01p5-import-drawing-dialog-next.png`), and
`01-import-drawing-dialog.png` / `04-layer-mapping.png` re-captured. Asked,
he chose to include them in PR #97 with step 10 (which refers to his
numbering). Two unreferenced images he had staged at the repository root
(`img.png`, `img_1.png`) were left out, unstaged, on disk.

## 4. WHAT HAPPENS NEXT

His check of PR #97 (the export, and now the README's floor procedure).

**Carried:** unchanged from [`0285`](0285-report.md).
