# 0066 — ruling: item C, the orthogonality repair — bounded by DISPLACEMENT, not by angle

**On [`0055-ruling.md`](0055-ruling.md) §4 item C**, owed since 2026‑08‑18 and
reserved at this number since [`0065`](0065-ruling.md) §6. **The input it was
blocked on — B's census — exists, was corrected at
[`0060`](0060-report.md), and I reproduced it independently at
[`0068`](0068-ruling.md) §6.**

**Everything below is measured from `examples/` + `fixtures/` by an
implementation that shares no code with `validate.py`: 20 plans, 960 walls, 63
within 1° of an axis without being on it.**

---

## 1. THE TOLERANCE QUESTION AS ASKED CANNOT BE ANSWERED — IT IS THE WRONG UNIT

[`0055`](0055-ruling.md) §4: *"the tolerance is the whole design — too tight and
it fixes nothing; too loose and it destroys the 45° bay."* **Stated in degrees,
because the instrument reports degrees.**

**A repair does not apply degrees. It moves a vertex. Measured — what the same
band actually does to the drawing:**

| deviation | wall length | **the end moves** | plan |
|---:|---:|---:|---|
| 0.0002° | 450.00″ | **0.002″** | `planc1.v5.json w50` |
| 0.6488° | 90.01″ | **1.019″** | `crossfloor-snap w17` |
| **0.9094°** | 63.01″ | **1.000″** | `farmplaceBIGmultifloor w33` |
| **0.9290°** | 185.02″ | **3.000″** | `farmplaceBIGmultifloor w24` |

> ### THE LAST TWO ROWS ARE THE ARGUMENT. NEARLY THE SAME ANGLE — 0.9094° AND 0.9290° — AND ONE MOVES A WALL END BY AN INCH, THE OTHER BY THREE.
>
> Across the single band *"under 1°"*, the displacement runs **0.0004″ to
> 3.0000″ — nearly four orders of magnitude.** **A degree cut cannot separate a
> correction nobody can see from one that moves a wall three inches**, because
> length is the other half of the product and the angle does not carry it.

**RULED: the repair's tolerance is a DISPLACEMENT, in inches. Degrees stay in
the report, where they belong — they are how the fault is *found*, not how the
fix is *bounded*.**

**And the 45° bay [`0055`](0055-ruling.md) §4 feared for is safe by
construction, not by luck:** a 45° wall's displacement to the nearest axis is
`0.707 × length` — **tens of inches.** The largest displacement anywhere in the
near-axis population is **3.000″**. **The bay is three orders of magnitude
outside any threshold this ruling could sanely pick.**

## 2. THE RAW DATA, PRINTED — because `WORKING_AGREEMENT.md` says a threshold owes it

> *"a measurement that turns on a threshold owes two things beside its number:
> the boundary items named, and the threshold stated as the **judgement it
> is** — with every item's raw value printed, so a different cut can be applied
> to the same data without re-running anything."*

**All 63 implied displacements, inches, sorted:**

```
0.0004 0.0008 0.0008 0.0016 0.0016 0.0016 0.0028 0.0028 0.0030 0.0030
0.0031 0.0034 0.0055 0.0057 0.0057 0.0064 0.0075 0.0131 0.0131 0.0132
0.0142 0.0146 0.0158 0.0201 0.0273 0.0314 0.0320 0.0320 0.0320 0.0355
0.0393 0.0409 | 0.0631 0.0779 0.1145 0.1334 0.1371 0.1489 0.1489 0.1636
0.1752 0.1900 0.1936 0.2218 0.2680 0.2680 0.2680 0.3409 0.4066 0.4066
0.4668 0.4816 0.5271 0.6970 0.8064 0.9978 1.0000 1.0000 1.0192 1.0192
1.5807 1.7184 3.0000
```

**There is no gap. The distribution is continuous from 0.0004″ to 3.0000″, and
nothing in the data picks a cut.** **So the cut is a judgement, and I am stating
it as one.**

**A hypothesis I tested and discarded, said out loud:** several offsets land on
suspiciously round values — `1.0000`, `1.0000`, `3.0000` — which would fit
[`0070`](0070-ruling.md) §5's un-ordered note about `SNAP_STEP = 1.0` leaking
onto a path. **Measured across all 63: three. Not a pattern. The hypothesis does
not survive** and is recorded here so nobody re-runs it.

## 3. THE THRESHOLD — 1/16″, and the reason is drafting, not statistics

> ### **T = 1/16″ (0.0625″).** Below it, moving a vertex cannot change any dimension a residential plan expresses. Above it, the correction is a real edit and the user must see it before it happens.

**Where that lands, and the boundary items named:**

| | | |
|---|---:|---|
| **auto-repairable** (`< 1/16″`) | **32 of 63** | largest corrected: **0.0409″** |
| **reported, not touched** | **31 of 63** | smallest refused: **0.0631″** — `0.0022″` above the cut |

**The two boundary items are 0.0409″ and 0.0631″ and they are named so a
different cut can be argued against the same list without re-measuring
anything.** **1/8″ would take 12 more; 1/4″ would take 24 more.** The list in §2
is the input to that argument if Patrick wants a different number.

## 4. THE HARD PART — A PER-WALL REPAIR IS NOT WELL-DEFINED, AND 14 OF 63 PROVE IT

Vertices are shared (P3.1). Straightening a near-horizontal wall equalises its
two `y` values — **which moves a vertex that other walls also own.**

**The conflict predicate is exact:** moving a vertex in `y` tilts any
**exactly-horizontal** wall at that vertex; moving in `x` tilts any
**exactly-vertical** one.

> **Measured: 14 of the 63 have that conflict. 49 do not.**
>
> ### SO A LOOP THAT "SNAPS EACH NEAR-AXIS WALL ONTO AXIS" PROVABLY TAKES A CORRECT WALL OFF AXIS IN 22% OF CASES. THAT IS THE REPAIR CAUSING THE DISEASE.

**And the consequence that has to be in the acceptance, or it gets reported as a
bug:**

> **A displacement-bounded repair cannot drive the count to zero.** The vertex
> graph is over-constrained: a rectilinear loop whose runs do not sum to zero
> has a residual, and something must absorb it. **What the bound guarantees is
> that the residual is never larger than `T`** — a conflict converts a `0″`
> error into a `< 1/16″` one; it never manufactures a bigger one.
>
> **The acceptance is therefore "no wall is off axis by more than `T`", NOT "no
> wall is off axis."** Anyone who writes the second one has written a test that
> cannot pass.

**RULED for this first delivery: refuse the conflicted walls and report them.**
Solving the vertex graph properly — deciding where the residual goes — is a
real design and it is **its own ruling, not a paragraph in this one.**

**Which end moves:** exactly **one** endpoint, chosen as the one with no
exactly-axis wall attached; if both are free, the one giving the smaller
displacement. **Never both** — splitting the difference doubles the number of
vertices touched and doubles the conflict surface for nothing.

## 5. WHERE IT RUNS — and it must not adopt the failure mode of the disease

[`0055`](0055-ruling.md) §3's own evidence: the drift is produced by
**operations** relocating vertices, and D63/D64 are *"the save writes an outline
corner at a recomputed coordinate."*

> ### A REPAIR THAT RAN AT SAVE OR LOAD WOULD BE THE EXACT CLASS OF FAULT IT EXISTS TO CLEAN UP.
>
> **Never automatic. Never on open, never on save, never on export.**

**Edit ▸ "Repair wall orthogonality…"** — beside the report item
[`0056`](0056-report.md) already added. It **previews** (n walls will move, the
largest by x″, m refused and listed), applies as **one undoable operation**, and
reports what it did.

**And it is interlocked on the machinery that already exists**, because D61,
D63, D64 and D65 are all open and all are geometry moving under operations:
**run the invariants before and after; refuse to start on a document already
failing them; roll back if any check that passed before fails after.** A repair
that can only ever improve a document is worth having; one that can trade one
fault for another is not.

## 6. WHAT THIS DOES **NOT** ESTABLISH

**It does not show the repair fixes Patrick's Chief complaint.** His `L2` is an
**export**, not a corpus file; its 75 sub-2° deviations were measured in DXF and
his plan is not among the 20 I censused. **The corpus's worst case is 3.000″ and
his may be worse.**

> **So the receipt is his own document, not mine:** run the repair on the plan
> that produced `L2.dxf`, re-export, re-count off-axis lines in Chief. **That
> number — before and after, on his file — is the only thing that closes item C**,
> and no corpus statistic substitutes for it.

**[`0055`](0055-ruling.md) §5 also stands unresolved and does not block this:**
whether the 24 walls that kept their id and rotated past 5° were defects or
deliberate edits. **Displacement-bounding sidesteps it entirely** — at 5° those
walls are far outside any threshold here and the repair will not touch them.

## 7. TIER AND ORDER

**A read-back comes first and item C does not start without it** — this mutates
saved geometry, which is the one thing this project has been most often wrong
about.

| | | |
|---|---|---|
| 0 | **Read-back** — the displacement formula and where it lives (one definition, `validate.py`, beside `wall_orthogonality()`); the conflict predicate stated as code; which endpoint moves and why; the preview's exact wording; the interlock's before/after check list; **and the acceptance restated as §4's inequality, not as zero** | **RED until answered.** No code |
| 1 | **The displacement census as an instrument** — `wall_orthogonality()` gains the inches alongside the degrees; the Edit ▸ report shows both | **GREEN.** Measurement only, and it is the preview's data source |
| 2 | **The repair, `T = 1/16″`, conflicted walls refused and listed, undoable, interlocked** | **AMBER** |
| 3 | **A user-settable `T`, and the graph solve for the conflicted 14** | **RED.** Named, not ruled. Neither starts on this ruling |

**PATRICK'S CHECK — and it is the receipt in §6, not a glance:**

> **Open the plan that produced `L2.dxf`. Run Edit ▸ Repair wall orthogonality.
> Export DXF, open in Chief. How many walls does it flag now, against the 75
> before?**
>
> **Second, and it is the one that matters more:** **does the drawing still look
> like your drawing?** Nothing moved that you meant to be where it was.

**This is the last item [`0055`](0055-ruling.md) left open.** A stays as ruled
(read-back owed, with [`0055`](0055-ruling.md) §4's extra clause — which
[`0070`](0070-ruling.md) §3 has since answered from the tree: snapping covers
neither input nor output, **it covers the delta**). B is built and merged.
**C is now ruled, and the number reserved since [`0065`](0065-ruling.md) is
spent.**
