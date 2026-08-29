# 0118 — ruling: the PDF tranche — the dimension mess is `round(p, 3)`, and stations are the fix for both D82 and the pile-up

**On [`0117-report.md`](0117-report.md)** (accepted — the merge-now/fix-content-
separately split was Patrick's own call, quoted, and D81/D82 are filed against
code, not symptoms) **and on his next complaint, read from the source:**

> *"when walls are slightly off then there is a mess of dimensions on top of
> each other that is hard to read."*

---

## 1. THE MECHANISM — one line

```python
# fp2pdf.py:_features()
fx.add(round(p[0], 3))          # every wall endpoint, to a THOUSANDTH of an inch
```

Every distinct x becomes a dimension **station**, and `dim_row_x` draws a
segment — extension lines, ticks, a label — **between every adjacent pair.**

> ### A DRIFTED WALL AT 947.9344 BESIDE A CLEAN ONE AT 948.0 PRODUCES TWO STATIONS 0.0656″ APART — AND A FULL DIMENSION SEGMENT, WITH A 45°-ROTATED LABEL, CRAMMED INTO A FRACTION OF A POINT.
>
> Every drifted vertex in the plan mints one. **The mess is the drift family
> (D61/D63/D64/D65) rendered onto paper** — the snap tools you just built are
> the source-side fix; this is the presentation-side one, and a transmittal
> sheet must be legible even on an uncleaned plan.

## 2. THE RULING — quantise the STATIONS, then difference; both defects fall out

**Step 1 — cluster:** stations closer than **1″** merge to their mean.
**The tolerance is the sheet's own resolution, not a new judgement:** after D82
the labels are whole inches, so a segment under 1″ **cannot be expressed on the
sheet at all** — hiding it loses nothing the paper could say. Boundary named:
the corpus's drift offsets run 0.0004″–3.0″; the 1.6″–3″ outliers **survive and
show as honest 2″/3″ slivers** — visible, and exactly the walls to snap.

**Step 2 — round each surviving station to the nearest whole inch, THEN compute
labels as differences of rounded stations.** This is D82's fix done right:

> **Rounding each label independently makes the parts stop summing to the
> overall — the classic drafting bug.** Rounding the stations and differencing
> **telescopes**: row 1's segments sum to row 2's overall **exactly, by
> construction**, and the receipt is that assertion on the real corpus.

`ftin` keeps its 1/16″ form for anything else that calls it; the **dimension
rows** format from whole-inch stations. `20'-6 1/2"` → `20'-7"`.

## 3. D81 — the doors, in the same tranche

Filed correctly: `door_type == "sliding"` can never be true against a catalog of
`LH/RH/FRENCH/BIFOLD/POCKET/SLIDER/DOORWAY/GARAGE-*`. **Fix: one symbol per
catalog value, keyed off the real vocabulary, with `walls.py:_paint_door` as the
reference rendering** — the app already draws every one of these; the PDF
transcribes, it does not invent. An unknown value draws the generic swing **and
is listed in `ConvertResult.warnings`**, not silently absorbed — that is how
`"sliding"` would have been caught the first time.

## 4. TIER AND ORDER — one branch, one check

| | | |
|---|---|---|
| 1 | **§2 — station clustering + whole-inch telescoping labels** (closes D82, fixes the pile-up) | **AMBER** |
| 2 | **§3 — D81's door symbols + the unknown-type warning** | **AMBER, same branch** |
| — | receipts | telescoping asserted corpus-wide; a fail-first on a two-wall doc with a 0.07″ drift pair (two stations → one); one door test per catalog value against `_paint_door`'s vocabulary |

**Patrick's check, one export:**

> **Export the drifted `wiscaway2026-08-09R` plan set.** The bottom dimension
> row reads as separated whole-inch strings — no overlapped labels; row 1 sums
> to row 2 on both axes; and the French and pocket doors on your own plan look
> like French and pocket doors.

**Carried, untouched:** the `L2.dxf` Chief recount (item C's last line), the two
latent delta-snap sites, D61-family.
