---
# permanent key, independent of GitHub
id: 87
title: "The PDF and DXF exporters refuse every plan with a roof -- version 6 read as not a v5 document"

# maps directly onto GitHub Issues fields
state: closed
state_reason: completed
labels:
  - type:defect
  - area:io
milestone: null

# ours; becomes body prose after migration
opened: 2026-10-11
closed: 2026-10-11
closed_by: null
rank: 87
related: [81, 82]
state_source: ruling
github_issue: null
---

# D87 — The PDF and DXF exporters refuse every plan with a roof

## The report

**Patrick, 2026‑10‑11:** *"When I try and save them it says 'This is not
version 5' or something close to that. Fix that so it saves the PDF
drawings."*

## The mechanism, measured

`design_document()` writes `"version": 6` the moment a plan has a roof
(`bridge.py`, R‑B's additive bump: 6 is 5 plus an optional `roofs` block,
and the schema's own enum is `[5, 6]`). Both exporters' first line was
`doc.get("version") != 5` → `ValueError("not a floorplanner-design v5
document")`, which `export_pdf_path` / `export_dxf_path` show in a message
box. So **every plan with a roof — every plan of his since the roofline arc
— could not be exported to PDF or DXF.** The 3D viewer's CLI printed the
same complaint as a warning and carried on.

Since 2026‑09‑05 (R3, the first roof written at version 6); unreported
until now because the Chief Architect export was last checked on a plan
without a roof ([`handoff/0115-ruling.md`](../handoff/0115-ruling.md)).

## The fix

`SUPPORTED_VERSIONS = (5, 6)` in `fp2pdf.py` and `fp2dxf.py` — the schema's
enum, not a widening past it: 7 is still refused, and the message now
names the format and version it saw. The plan sheets do not draw roofs,
so a 6 reads exactly as a 5. `fp3d.py`'s warning says v5/v6.

**Receipt:** `tests/test_fp2pdf.py` — a version‑6 document with a roof
converts to the same sheets with no warning; 7 is refused; and his exact
path, `export_pdf_path` on a plan with a roof built in the window, writes
the file. `tests/test_fp2dxf.py` the same for DXF. All three RED without
the two constants. Closed at the landing recorded in
[`handoff/0236-report.md`](../handoff/0236-report.md).
