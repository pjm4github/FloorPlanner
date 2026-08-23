# 0093 — ruling: off-axis is measured from the nearest INTENDED angle, not the nearest cardinal

**Patrick, 2026‑08‑23, amending [`0092`](0092-ruling.md):** *"The off axis
should only report if it off of the 15 degree snap angle. I dont need that for
walls at 45 degrees for example."*

---

## 1. THE RULE, AND IT IS A BETTER INVARIANT THAN THE ONE IT REPLACES

> ### THE ANGLE CLAUSE APPEARS IF AND ONLY IF THE WALL IS NOT ON AN INTENDED ANGLE.
>
> Deviation is measured from the nearest multiple of the **angle step**, not
> from the nearest cardinal. A deliberate 45° wall is **on** an intended angle,
> so the bar says nothing — which is the point.

**The step is `SETTINGS["rotate_snap_deg"]` (default 15°).** Deliberate reuse,
not a new setting: it is already this app's one *"meaningful angle increment"*,
and a second number meaning the same thing is how the thickness tables happened.
**If it ever needs to differ from the furnishing rotation snap, that is a new
setting and a new ruling — not a quiet second copy.**

## 2. THE GUARD — an arbitrary step breaks every vertical wall

**Measured:**

```
step= 7.0  divides 90: False   cardinals that would FIRE: [90.0, 180.0, 270.0]
step=22.5  divides 90: True    cardinals that would FIRE: []
```

`rotate_snap_deg` is a spin box with range 1.0–90.0, so **7 is reachable** — and
at 7, every vertical wall in the plan starts reporting *"6deg off axis"*.

**RULED: the step must divide 90 exactly. If it does not, fall back to 90** —
cardinals only, today's behaviour — **and do not fail, do not warn on every
selection.** A settings value chosen for furnishings must never make the wall
label wrong.

## 3. WHAT SUPPRESSION ACTUALLY CATCHES — measured, so nobody is surprised

```
east / north / 180 / 270   -> exactly 0 mod 15   suppressed
45 deg, 135 deg            -> exactly 0 mod 15   suppressed
a hand-drawn 30 deg        -> 29.99998843...     FIRES (0.0000116 off)
```

**Cardinals and 45/135 land exactly, because their coordinates are symmetric.
15/30/60/75 drawn by hand do not, and will fire with a tiny deviation.** That is
correct — the wall genuinely is not on 30 — **but it is worth knowing before it
is reported as a bug.** Walls have no angle snap today (`_wall_end_point` forces
orthogonal, Shift gives a free angle), so a 30° wall is always a free-angle wall.

## 4. WHAT THIS DOES NOT CHANGE

**The census, the Edit ▸ orthogonality report, and item C's repair population
stay cardinal-based.** Not ordered here.

**And they do not now disagree with the bar**, because **every cardinal is a
multiple of 15** — so on the entire 63-wall drift population the two measures
give the **identical number**. They differ only on deliberate angled walls,
where the report currently says *"45° off axis"* and the bar will say nothing.

> **Whether the report should adopt the same rule is a real question** — it would
> drop deliberate diagonals out of the census automatically, which is the
> separation [`0055`](0055-ruling.md) §2 had to make by hand. **Named. Not
> ordered.** It moves item C's candidate set and item C is mid-flight.

## 5. ONE THING I DECIDED THAT HE DID NOT SAY

**A clean 45° wall now shows no angle clause at all** — not the deviation, and
not the heading either. That follows from §1's invariant and from
[`0064`](0064-report.md)'s original reason (don't clutter the bar on an ordinary
wall), **but he asked only for the off-axis half to go quiet.**

**If the heading should still show on a non-cardinal wall, say so — one line, one
`if`.** Ruled the quiet way because *clause present = something is off* is the
more learnable rule.

## 6. TIER

**AMBER**, folded into [`0092`](0092-ruling.md)'s change — one commit, not two.
**Check batched with PR #37's:**

> **A wall at 45° says nothing about its angle. A wall you drew freehand says
> how far off the nearest 15° it is.**
