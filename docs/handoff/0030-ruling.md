# 0030 — ruling: the glance test FAILS today, and one thing in the render contradicts D76

**Patrick's render, 2026‑08‑16 — the three enclosures left to right: `shower`,
`walk_in_shower`, `glass_shower`, on the current `main` (`156135f`), before any
redraw exists.**

**This is a BASELINE, not an acceptance.** Nothing has been redrawn — measured:
no commit since `156135f`, `_gen_assets.py` unmodified, and the two SVGs showing
as modified are CRLF phantoms with **zero content changed**. **The acceptance
check on the redraws remains Patrick's**, unchanged by this.

---

## 1. THE VERDICT — NO

> **They read as ONE BOX AT THREE SIZES.** Three translucent boxes in a row,
> differing only in proportion. **Nothing on any of them says "shower"** — no
> door, no curb, no threshold, no head, no drain. Out of context they would read
> as display cases.

**The only mark in the frame is one small dark object at the middle enclosure.**
One detail, on one of three.

**So [`0016`](0016-ruling.md) §2's finding is now confirmed by a render rather
than by reading SVG source**, which is the stronger form of the same claim:
**identity is carried by footprint, footprint is a scalar, and a scalar fails at
a glance.**

## 2. THIS IS THE FAIL-FIRST RECEIPT, AND IT ARRIVED BEFORE THE WORK

**Recorded because the ordering is the valuable part.** A baseline taken *after*
a redraw is an argument about whether things improved; taken *before*, it is the
red half of a fail-first pair, and the redraw's receipt is now simply *"run this
again."*

**Same camera, same plan, same three items.** State which plan in the report —
this render is not
[`../../fixtures/enclosure-form-check.json`](../../fixtures/enclosure-form-check.json)
(that one carries `sauna` and `whirlpool`, not three showers), and the after-shot
must be the same one or the pair proves nothing.

## 3. THE BRIEF IS STRONGER THAN "MAKE THEM DIFFERENT FROM EACH OTHER"

[`0016`](0016-ruling.md) §2 asked for a categorical mark so the three could be
told apart. **The render says the requirement is larger than that:**

> ### NONE OF THE THREE READS AS A SHOWER AT ALL. Distinguishing them from each other is not sufficient if all three remain unidentifiable.
>
> **Each needs a mark that names its KIND**, not merely one that differs from its
> neighbour's: a door panel, a curb or threshold, a drain, a head. **Three
> different-but-meaningless marks would pass a comparison and fail the glance
> exactly as footprint does now.**

**And it makes the plan symbol more correct**, which is the tell
[`0014`](0014-ruling.md) §2 named for the seats: a shower enclosure genuinely
*has* a door and a curb, and a bare rectangle says it does not.

## 4. THE RENDER CONTRADICTS [D76](../defects/0076-an-opaque-mesh-inside-a-translucent-body-does.md), AND THAT NEEDS RECONCILING BEFORE THE REDRAWS

D76 states, and [`0021`](0021-report.md) §6 measured, that **an opaque mesh
inside a translucent body does not composite at any alpha tested** — 0.35
shipped, 0.12 synthetic. That is why `walk_in_shower`'s bench was declared
unviewable and why [`0022`](0022-ruling.md) §3 demanded a bodies-omitted render
to see it at all.

**In this render a dark opaque object IS visible at the middle enclosure, with
the bodies present.**

> **BOTH CANNOT BE TRUE AS STATED.** Either D76 is narrower than its own title —
> it may depend on view angle, on depth order, or on the mesh being wholly
> enclosed — **or that object is not entirely inside the body** and is visible
> because it protrudes.
>
> **Measure which, and amend D76 or amend the render's caption accordingly.**
> This is not pedantry: **D76 is currently the reason a whole class of interior
> detail is considered invisible**, and if it is wrong the redraw brief changes —
> interior marks become viable and the bodies-omitted workaround stops being
> necessary.

**Cheap to settle:** the bench's world extents are already known
(`z[0.0, 18.0]`); compare its footprint against the enclosure's and say whether
it is contained.

## 5. `walk_in_shower` — THE CENSUS STILL DECIDES, AND THIS RENDER DOES NOT SETTLE IT

[`0029`](0029-ruling.md) §3 expected the census might take it off the list. **The
render neither confirms nor refutes that**: it has the frame's only mark, which
is a point in its favour, but §4 means we do not yet know whether that mark is
visible *because it works* or *because it protrudes*.

**Order unchanged: predicate and census first, then the list, then the redraws.**

## 6. TIER

**Unchanged.** Predicate and census **GREEN**; redraws **AMBER**, one check.

**§4's reconciliation is GREEN** and comes with the census — it is a measurement
on an existing mesh, not a change to anything.
