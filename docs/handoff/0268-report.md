# 0268 — report: the PDF plan set renders the plan's DRAWN dimensions in place of the auto rows, and its text annotations while Show ▸ Annotations is on

**Code, 2026‑10‑12.** His words, while he checks PR #88:

> *"1) when dimensioning is drawn on the plan, then render that dimension
> without the auto dimension feature and 2) when annotations are
> displayed then render that annotation for printing to pdf."*

Built on `pdf-drawn-dims`, ONE commit STACKED on `item-annotations-font`
(PR #88's tip), pushed, no PR of its own — the precedent of
[`0255`](0255-report.md): land in turn, or fold into #88 on his word. The
checkout on this branch runs the app with both tranches in it.

## 1. WHAT WAS THERE

`fp2pdf` dimensioned every sheet by itself: two rows along the bottom and
two up the left (every wall endpoint, then the overall), an angled lane
per family for rooms with dimensions on ([`0119`](0119-ruling.md),
[`0120`](0120-ruling.md), [`0130`](0130-ruling.md)). A plan's own
measurements ([`0263`](0263-report.md)) were not on the sheet at all; its
texts were, always, whatever the Show switch said.

## 2. WHAT IS THERE NOW

* **The drawn dimensions, no auto rows.** A level with one or more
  `dimension` annotations, while the plan's Show ▸ Measurements is on,
  draws each as the screen draws it — the extension lines off each
  measured point, one thin line parallel to the measure at its own offset
  and on its own side, a "/" slash at each callout point, the length above
  the line at its label point in the plan's `dimension_units` (feet and
  inches or inches), never upside down — and draws NEITHER the orthogonal
  rows NOR the angled lanes. The title block's dimension-reference note
  reads *Dimensions as drawn on the plan*; the export's summary names the
  count (`sheet P2: upper (1 dimension as drawn)`). The sheet's frame
  takes the drawn lines in, so a measure far off a wall still lands on the
  page.
* **The fallback is unchanged.** A level with no drawn dimensions, or a
  plan with Show ▸ Measurements off (nothing on the screen, nothing on
  the sheet), dimensions itself as before — rows, lanes, the meta's note.
* **The texts follow the switch.** The level's `text` annotations draw
  while Show ▸ Annotations is on, and not while it is off. (The datum is
  the tool's snap point, not drawn.)

`Sheet.drawn_dims()` resolves the records in the SCREEN's frame (y down,
the offset on the measured line's left) and flips each point to the sheet
(y up) afterwards, so the line sits on the side the plan puts it;
`draw_drawn_dims()` draws them; `render()` chooses. The geometry's numbers
are the screen's own (`DRAWN_TICK_IN` 4, `DRAWN_EXT_GAP_IN` 2).

Rendered on his `wiscaway2026-10-11R3.json` with one measure and one text
added on the upper level: sheet P2 carries the measure (23'‑6" on the
right wall, slashes, extension lines), the text, the note, and no rows;
sheet P1 (no measures) its rows as before.

## 3. RECEIPT

`tests/test_fp2pdf.py` (88): seven new — the drawn dimensions render and
the auto rows do not (the lengths, the line's side, the slashes and
extension lines, the vertical one's label angle and point), hidden
measurements fall back to the rows, a plan without any keeps them, the
labels in the plan's units, the texts follow the switch, the frame grows
to hold a far-off measure, `convert` writes the PDF and says so. A
recording canvas reads the sheet's drawing back without decompressing a
PDF stream (reportlab compresses pages). `--quick` passed; gate GREEN.

## 4. WHAT HAPPENS NEXT

His check of PR #88 and of this; land in turn or fold on his word. Named:
DXF export of annotations; a leader annotation; his backlog (0248's items
8 and 9).

**Carried:** unchanged from [`0267`](0267-report.md).
