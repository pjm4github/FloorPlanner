# 0135 — ruling: door symbols by type, windows made real — the Chief import tranche

**Patrick, 2026‑08‑31, from Chief Architect X17 with the imported DXF on
screen:** *"This is pretty close but the door types dont carry the geometry of
the drawing. Fix that so that the export uses the correct meaning format for
the type of door. Also the windows dont show up either."*

---

## 1. ROOT CAUSE, MEASURED — the slider branch is dead code

`fp2dxf.py:388`: `op.get("door_type") == "sliding"` — but the app's vocabulary
is `config.py:158` `DOOR_TYPES = ["LH","RH","BIFOLD","POCKET","SLIDER",
"FRENCH","DOORWAY","GARAGE-1","GARAGE-2"]`, and the R2 document stores exactly
those (census: 11 DOORWAY, 9 LH, 7 RH, 4 FRENCH, 2 SLIDER, 1 BIFOLD, 2 GARAGE,
1 gate; 25 windows). **`"sliding"` matches nothing, ever.** So every door of
every type exports as the one hinged leaf+arc — including the 11 DOORWAYs,
which get a phantom swinging leaf they don't have. Windows export as bare
gap-spanning lines and nothing else. That is the whole symptom.

## 2. THE ORDER — one symbol per type, exhaustive over the vocabulary

[KB‑00170](https://www.chiefarchitect.com/support/article/KB-00170/using-cad-to-walls-from-an-imported-dwg-dxf.html)
(the article the file's own header cites) read: **layer mapping is the primary
classifier; swing arcs "help to identify a door"; door/window lines must not
be CAD blocks.** The header's "Chief classifies by symbol shape" claim
overstates it. So: everything stays plain lines/arcs on `FP-DOORS`/`FP-WINDOWS`,
and the geometry becomes conventional per type:

* **LH/RH, gate** — leaf+arc as today, from the stored `hinge`/`swings_toward`
  (both present in the document; `hinge:"none"` keeps the default-handedness
  rule already commented).
* **FRENCH** — two half-width leaves + two arcs, opposite jambs.
* **SLIDER** — the existing two-panel branch, keyed on `"SLIDER"`.
* **BIFOLD** — chevron pair per leaf. **POCKET** — panel line recessed into
  the wall cavity. **GARAGE-1/2** — gap + full-width panel line.
* **DOORWAY** — gap lines only, **no leaf, no arc.**
* **WINDOW** — gap lines + glass line(s) at the centerline (the conventional
  triple-line symbol), still on `FP-WINDOWS`.

**The receipt that kills this defect class:** dispatch is exhaustive over
`DOOR_TYPES` itself — a test importing the list from `config.py` fails the
moment a new type exists without a symbol. Plus per-type geometry assertions
(DOORWAY emits zero arcs; FRENCH emits two; window emits its glass line) on R2.

## 3. ONE QUESTION + THE CHECK

**Patrick:** in the CAD to Walls dialog, was `FP-WINDOWS` mapped to Windows?
If it wasn't, re-import once with it mapped — that result decides whether the
window symptom was geometry or dialog, and belongs in the report either way.

**AMBER, one branch.** The check is yours, in Chief: re-export R2, re-import —
doors show their own type's symbol, doorways don't swing, windows appear.
**And while Chief is open: the `L2.dxf` recount — the board's oldest line.**

**Carried:** 0134's check result unreported (PR #46 merged — one word if the
PDF looked right); room-label rounding (0131 §2); delta-snap sites; D61-family.
