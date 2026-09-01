# 0140 — ruling: the End‑On dialog IS the drawing — R2b spec sharpened by Patrick's sketch

**Patrick, 2026‑08‑31, with a sketch** (committed as
`docs/evidence/roof-endon-sketch.png`, the R2b spec image): right-click on the
ridge-end marker pops the dialog; the dialog looks like the sketch; *"When I
change 2 of the 3, the 3rd item is changed. The item that changes is the last
item edited"* — set R, set H ⇒ P computed; then set P ⇒ R computed. Moving the
ridge and eaves **left/right is wanted but deferred, his word.**

---

## 1. THE DIALOG — a live end-on drawing with three values on it

Per the sketch: **the roof triangle drawn over the level's wall stack, end-on
along the ridge axis**, with `R` (ridge), `H` (eaves), and `P` (pitch)
annotated on the drawing itself and editable beside it. Editing any value
redraws the triangle live. **Opened from a right-click menu item on the
marker** — the marker's plain click/drag stays reserved for moving it between
ridge ends ([`0139`](0139-ruling.md) §1). Selecting any ridge still reaches
the same dialog ([`0139`](0139-ruling.md) §2); one dialog, two doors.

## 2. THE RECOMPUTE RULE — his example confirms [`0139`](0139-ruling.md) §2, verbatim

His queue is exactly the ruled rule: **the two most recently edited fields are
the inputs; the least recently edited is derived.** Set R, set H ⇒ P (P never
edited, oldest); set P ⇒ R (now oldest). No change to the ruling — recorded
so the receipt can quote his own example as the test case, literally: that
R→H→P→R sequence is the acceptance test's edit script. **At first open, with
no edit history, P is the derived field** — the stored heights are the
primaries ([`0138`](0138-ruling.md) §2).

## 3. THE DATUM — amended by the sketch

[`0139`](0139-ruling.md) §2 said heights enter *relative to the wall top*.
**The sketch says otherwise: both `R` and `H` arrows run from the ground line
of the wall stack** — the roof level's base (`elevation_in`). **Amended: R and
H are measured from the level's base**, as drawn; the wall-top height appears
on the drawing as reference so the "relative to the wall(s)" reading stays
visible. Same rule for the 45° wing — the datum is the roof's own level, not
the plan's.

## 4. DISPOSITION

**All of this is R2b** ([`0139`](0139-ruling.md) §3) — no new tranche, a
sharper spec for the one already staged. **On record as deferred: ridge and
eaves horizontal repositioning** (joins yard items). **R1 remains Code's start
point, untouched by any of this.**

**Carried:** item C's Chief off-axis count; room-label rounding
([`0131`](0131-ruling.md) §2); delta-snap sites; D61-family.
