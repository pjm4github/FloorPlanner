# 0136 — report: [`0135`](0135-ruling.md)'s DXF door-symbol-by-type + real windows built — and the golden fixture itself carried the defect

**Built exactly to [`0135`](0135-ruling.md) §2, on branch `fp2dxf-door-symbols`.**

---

## 1. Root cause, and a second finding the ruling didn't anticipate

`fp2dxf.py:388`'s `door_type == "sliding"` never matched — same class as
D81's `fp2pdf.py` finding, independently present here because DXF geometry
(`DxfR12`'s LINE/ARC entities) shares no code with the PDF exporter's
reportlab calls. Fixed with `_door_symbol(kind, door_type)`, exhaustive
over `config.py:DOOR_TYPES`, and `_swing_leaf()`, the DXF analogue of
`fp2pdf.py`'s own `leaf` closure — same geometry, different primitives.

**`fixtures/chief-export/sample_design.json` — the golden fixture itself —
carried the exact bug it was meant to exercise.** `oD2`'s `door_type` was
the literal string `"sliding"` (not `"SLIDER"`); `oD1`/`uD1`'s was
`"hinged"` (not `"LH"`/`"RH"`) — neither a real catalog value. `oD2`'s
slider geometry was already correct only because it happened to satisfy
the OLD (dead) check by coincidence; `oD1`/`uD1`'s wrong label never
affected geometry at all (hinge/swings_toward carry that). **Corrected in
the same commit as the code fix, not filed separately** — this is the
defect's own root cause manifesting in the fixture, not a tangential
cleanup this project's own rule against folding-in would otherwise refuse.

## 2. Per-type geometry, as ruled

`LH`/`RH`/`""`/gate → the existing leaf+arc, unchanged shape. `FRENCH` →
two half-width leaves from opposite jambs. `SLIDER` → the existing
two-panel branch, now correctly keyed on `"SLIDER"`. `BIFOLD` → chevron
pair. `POCKET` → one line recessed into the wall cavity before the
opening. `GARAGE-*` → one full-width panel line. `DOORWAY` → gap lines
only, no leaf, no arc — closes the "phantom swinging leaf on 11 DOORWAY
openings" symptom `0135` named directly. `window` (a `kind`, not a
`door_type`) → the existing gap lines plus a new glass line at the
centreline — windows previously exported as bare gap-spanning lines,
indistinguishable from an unclassified opening; that is the "windows
don't show up" symptom.

An unrecognized `door_type` still draws a generic swing but is named in
`ctx.warn()` — the same discipline D81 established for `fp2pdf.py`, not
silently absorbed a second time.

## 3. Receipts

**Exhaustive dispatch**: a test importing `config.py:DOOR_TYPES` fails the
moment a catalog value has no symbol. **Per-type geometry**, as `0135` §2
named: DOORWAY emits zero `ARC` entities; FRENCH emits exactly two; a
window emits a third `FP-WINDOWS` `LINE` beyond its two gap lines.
**Corpus corroboration** on `wiscaway2026-08-30R2.json` (the file `0135`
§1's own census counted): 9 LH + 7 RH + 1 gate + 4 FRENCH → 25 arcs,
computed by hand from the census and matched exactly against the real
`convert()` output, zero warnings.

**Golden-file regeneration, diff stated in full** (0038-ruling.md §7's own
discipline): `oD2`/`oD1`/`uD1`'s NOTES tag text corrected to the real
catalog name; two new glass `LINE` entities on `FP-WINDOWS` (one per
window, `L1` and `L2` each carry one); `oD2`'s own slider-panel geometry
**unchanged** (the coincidence in §1). Both `.openings.json` sidecars:
only the `door_type` field's text changed, stations untouched.

15 tests in `tests/test_fp2dxf.py` (was 7): the exhaustive-dispatch
receipt, a regression test naming `"sliding"`/`"hinged"` directly as the
fixture's own former bugs, three per-type geometry assertions, an
unrecognized-type warning test, and the R2 corpus corroboration. `pytest
-m "not gui and not slow"`: 955 passed. `ruff` clean. Gate GREEN, full
mode.

## 4. The one open question — his to answer

**`0135` §3, carried, not guessed:** in the CAD to Walls dialog, was
`FP-WINDOWS` mapped to Windows? If not, one re-import with it mapped
decides whether the "windows don't show up" symptom was ever geometry at
all, or partly a dialog step — belongs in his own check report either
way, alongside the fix now built.

## 5. Disposition

**AMBER, branch `fp2dxf-door-symbols`, PR to follow.** Fresh `L1.dxf`/
`L2.dxf` for `wiscaway2026-08-30R2.json` generated and sent directly (not
committed — R2's own DXF pair is not a golden fixture, `sample_design.json`
is) so Patrick can re-import without re-running the export himself. The
check, per `0135` §3:

> Re-export R2, re-import — doors show their own type's symbol, doorways
> don't swing, windows appear.

**And, while Chief is open — the board's oldest line, per `0135` §3's own
closing note:** the `L2.dxf` recount ([`0066`](0066-ruling.md) §6/§7),
still entirely his own manual step, no code blocking it.

**Carried:** `0134`'s PDF-tranche check result still unreported (PR #46
merged; one word if the re-exported PDF looked right); room-label rounding
([`0131`](0131-ruling.md) §2); delta-snap sites; D61-family.
