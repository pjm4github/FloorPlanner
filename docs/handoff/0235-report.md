# 0235 — report: the PDF (and DXF) exporters refused every plan with a roof — a version‑6 document read as "not v5"; fixed on `pdf-v6`, D87 filed and closed with it

**Code, 2026‑10‑11.** No merge has happened since
[`0234`](0234-report.md). His word:

> *"I need to fix the PDF writer so that I can save PDF file. When I try
> and save them it says 'This is not version 5' or something close to
> that. Fix that so it saves the PDF drawings."*

## 1. THE MECHANISM — measured, one line in each exporter

`design_document()` writes **version 6** as soon as a plan has a roof
(`bridge.py`: `"version": 6 if roofs else 5` — R‑B's additive bump, and
the schema's enum is `[5, 6]`). `fp2pdf.convert` and `fp2dxf.convert`
both opened with `doc.get("version") != 5` → `ValueError("not a
floorplanner-design v5 document")`, which the menu handler puts in a
message box. **So every plan of his with a roof — every plan since the
roofline arc began — could not be exported to PDF or DXF**, and the
message blamed the file. The 3D viewer's CLI printed the same complaint
as a warning.

Unreported until now because the exporters were last checked on his
plans before roofs existed ([`0115`](0115-ruling.md): the Chief import
check, 2026‑08‑30; R3's first version‑6 write, 2026‑09‑05).

## 2. THE FIX

`SUPPORTED_VERSIONS = (5, 6)` in both exporters — the schema's own enum,
no wider: 7 is still refused, and the message now says what it saw
(`format=…, version=…`). The plan sheets do not draw roofs, so a 6 reads
exactly as a 5. `fp3d.py`'s CLI warning says v5/v6. Nothing else moves.

**D87 filed and closed in the same tranche** —
[`defects/0087-…md`](../defects/0087-the-pdf-and-dxf-exporters-refuse-every-plan-with-a-roof.md),
`closed_by` to be the landing commit, related to D81/D82 (the exporter's
last two).

## 3. THE RECEIPT

* `tests/test_fp2pdf.py`: a version‑6 document with a roof converts to
  the same single sheet with no warning; version 7 is refused naming it;
  **his exact path** — four walls and a roof in the window,
  `design_document()` at 6, `export_pdf_path` writes the file and the
  status line does not say *failed*; the old refusal test's regex updated
  to the new message.
* `tests/test_fp2dxf.py`: the same for DXF, 6 converts and 7 is refused.
* **Three RED without the two constants**, 97 green with them; viewer
  suites green; `ruff` clean; the full gate the branch's own run.

## 4. TIER

**GREEN** — no new semantics, nothing the user must learn, no format
change: the exporters accept the document the application already
writes. It merges on green CI under the standing authority, so he can
save PDFs now rather than after a check; his check is the saving itself.

## 5. `fixtures/incoming/`, with ages

* `wiscaway2026-10-07R1.json` — his own, file dated 2026‑10‑07, not read,
  not edited; no note; exit his to name.
* `README.md`.

## 6. WHAT HAPPENS NEXT

The PR merges on green CI; the landing recorded with its `**Landed:**`
line, D87's `closed_by` filled in. Then his word.

**Carried:** unchanged from [`0234`](0234-report.md).
