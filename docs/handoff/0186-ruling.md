# 0186 — ruling: R4g ratified closed; the next arc — clip trace on the roof, dormers, multifloor

**Patrick, 2026‑09‑13:** *"The code looks really good for the single floor
plan."* Next: **dormers**, **ceiling clipping** — *"dashed lines on the roof
where the full height of the walls are clipped by the roof"* — and
**multifloor roof lines.** [`0185`](0185-report.md)'s close-out is accepted
as reported: PR #60 merged at `c52396b`, branches gone, 1287 green.

## 1. THE TWO QUESTIONS [`0185`](0185-report.md) §2 LEFT — answered now

* **Crossed arms that survive stay JOINED — ratified as built.** His own
  check called the result perfect and the v2 reference draws it so; the 4″
  fascia stays undrawn until a real plan makes him want it.
* **The ridge-END-point rule stands as a named limit.** The wide-low-joiner
  edge case waits for a fixture that exercises it, not for speculation.

## 2. R5a — THE CLIP TRACE, ON THE ROOF (small, first)

R3b drew the clip on the **wall** (dashed, where the roof cuts the room
below full height). His sentence puts the same fact on the **roof**: with
the roof layer shown, each roof draws a dashed trace along the locus where
it crosses the covered rooms' wall-top plane — the same `roof_clip_spans`
geometry read from the roof's side, the line inside which rooms lose full
height. **This is also the dormer placement map — which is why it builds
first.** AMBER, one branch; his check: wiscaway with roofs on, the dashed
trace hugging where the R3b wall dashes already are.

## 3. R5b — DORMERS: DESIGN READ-BACK BEFORE CODE ([`0066`](0066-ruling.md) §7's pattern)

Dormers mutate the roof model and pierce the clip machinery just rebuilt —
this starts with **a read-back, RED until answered:** Code proposes, in a
report, no code: the dormer's schema shape (own object vs. child of a
parent roof — note a dormer IS a small roof with two walls and a face, so
the roofs machinery should be reused, not paralleled); how its opening
interacts with `compute_roof_clips` (the parent plane opens where the
dormer sits; the dormer's own planes join by the SAME envelope rules —
no special case unless a fixture forces one); the sketch gesture (drop on
a roof plane at the clip trace, ridge perpendicular to the eave by
default); and what the v1 dormer is (gable dormer; shed/hip named later).
I rule on the read-back, then it builds as its own AMBER tranche.

## 4. R6 — MULTIFLOOR: THE PRINCIPLE NOW, THE BUILD ON HIS FIXTURE

**The building has ONE roofscape.** RULED: composition runs in **absolute
height** — a roof's surface is its level's `elevation_in` plus its own
heights ([`0140`](0140-ruling.md) §3's datum, made absolute) — and the
envelope/prune/under-pass machinery runs over **all live roofs of the
building**, not per level. The same rules, one more term in z; no new
geometry class.

Two things wait on Patrick before this builds: **a multifloor fixture from
him** (a wiscaway-derived pair of L1+L2 roofs is ideal — the record's
fixtures have carried every arc), and **one answer: on a level's plan
view, which roofs draw?** Own level only; or upper-level roofs ghosted
over the lower plan (and lower under upper). One line settles the display
rule; the composition rule above doesn't wait on it.

## 5. ORDER

**R5a → R5b read-back → R5b build → R6** (R6 may start earlier if his
fixture and answer arrive while R5b is in flight — but never two open
AMBER tranches at once). Carried limits from [`0185`](0185-report.md) §2
ride along unchanged: the 0.36 s clip timing, the four sub-inch slivers,
the cut-off-root-corner certification note.

**Carried:** room-label rounding ([`0131`](0131-ruling.md) §2); delta-snap
sites; D61-family; D83/D84 (held); yard items; valley/hip lines as export
plan lines; the roof-plan export sheet.
