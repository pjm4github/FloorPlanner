# 0034 — ruling: the check is ready, the camera is the open question, and I withdraw 0030 §4

**On [`0032-report.md`](0032-report.md) and [`0033-report.md`](0033-report.md).**

---

## 1. FIRST — I WAS WRONG IN [`0030`](0030-ruling.md) §4, AND THE MEASUREMENT SAYS SO

I claimed Patrick's render **contradicted**
[D76](../defects/0076-an-opaque-mesh-inside-a-translucent-body-does.md), because
a dark mark was visible at the middle enclosure with the bodies present.

**Measured on `build_model`'s own meshes:**

```
body  x [-29.25, 29.25]  y [-20.25, 20.25]  z [0.0, 78.0]
bench x [-27.50,-16.50]  y [-18.50, 18.50]  z [0.0, 18.0]
```

**Bench ⊂ body on all three axes. D76 stands, unamended.** Whatever that mark
was, it was not the bench protruding, and **my claim is withdrawn.**

> **THE DEMAND WAS STILL RIGHT, AND THAT IS THE PART WORTH KEEPING.** A
> reviewer's job is not to be correct about a render — it is to refuse to let a
> filed defect and an observation disagree in silence. **The reconciliation
> produced the finding that changed the whole redraw brief**, which no one would
> have gone looking for if the contradiction had been left standing.
>
> **Second time this week I have asserted from a picture what a measurement then
> refuted** (the first was the PR that already existed). **The lesson is not "stop
> reading renders" — it is that a render generates a QUESTION, never a finding.**

## 2. THE OPEN QUESTION IS THE CAMERA, AND NOBODY HAS RULED ON IT

[`0033`](0033-report.md) §5 is honest in the way that earns trust: *"at the
fixture's own camera they are harder to make out … this may not be enough."*

**[`0031`](0031-ruling.md) said "this plan, this camera" to protect the
before/after pair — that is about COMPARABILITY. It said nothing about whether
that camera is the zoom a person actually works at, which is a different
property, and it is the one D74 turned on:**

> *fence and railing rendered at working zoom as the same ladder … it took a
> render at the zoom a person actually works at.*

**The fixture is a 348″ × 138″ room — 29 feet — holding three plumbing
fixtures.** Nobody works on a bathroom framed as a 29-foot hall.

> ### THE CAMERA IS PART OF THE INSTRUMENT, AND AN INSTRUMENT SET FURTHER AWAY THAN THE USER STANDS WILL FAIL A GLANCE TEST THE PRODUCT WOULD PASS.

**So Patrick's check is two questions, not one:**

| | |
|---|---|
| **1** | At this render — **do the three read as different things at a glance?** |
| **2** | **Is this camera the distance you actually work at?** |

**If 2 is NO, the check is not failed — it is not yet run.** The fixture then
gains a **documented camera at working distance**, and **both** renders are
retaken at it, preserving [`0031`](0031-ruling.md)'s comparability while fixing
its representativeness. **Record the camera with the fixture**, so a third
render a month from now is the same experiment.

**If 2 is YES and 1 is NO, the marks are genuinely insufficient** and the redraw
goes another round.

## 3. THE CHAIN IN [`0032`](0032-report.md)→[`0033`](0033-report.md) IS THE BEST WORK IN THIS PROGRAMME

**Measure → the brief changes → build differently.** The D76 reconciliation was
ordered as a loose end; it produced the finding that **a region-shaped mark
inherits D76's invisibility on a translucent body**, and therefore that the mark
must be a **`beside`** shape. **`walk_in_shower`'s bench is the proof that was
already sitting there** — correct geometry, correct material, invisible — and
without that reconciliation all three redraws would have shipped the same
invisible fix.

**And [`0033`](0033-report.md) §4 applied D74 unprompted:** the first curb at
`top=4` was *"too subtle to read … measured by looking, not assumed."* **A first
cut adjusted by looking, before anyone was asked to check it**, is exactly what
that rule asks for.

## 4. THE 3% ALLOWANCE OWES ITS RAW VALUES

Predicate 2's correction — **connected components of top-level rings' bounding
boxes**, rather than a count of rings — is right, and catching `dining_chair`
before it shipped is the census doing its job.

**But the allowance is 3% of the viewBox's smaller dimension, and that is a
line.** [`0012`](0012-ruling.md)'s rule is explicit about what a line owes:

> *inspect the items either side of the line, not the count* — and *print every
> raw value so a different cut needs no re-run.*

**What was inspected: `boat_trailer` (tens of units, far above) and
`dining_chair` (0.25 on 18, far below), plus the six caught. What was NOT
inspected is the near side: which items sit JUST UNDER 3% and were therefore
called connected without anyone looking.**

**Owed, and it is one print statement:** the max component gap for **all 95
items**, as a raw percentage, so the items nearest the line on **both** sides can
be read off. **If nothing sits between roughly 1% and 3%, say so** — a stated
empty band is a real result and closes this permanently.

## 5. THE SIX FRAGMENTED ITEMS — ONE RECORD, NOT SIX

`motorcycle` 2 · `bicycle` 2 · `garden_tractor` 3 · `riding_mower_snow` 6 ·
`drill_press` 2 · `water_softener` 2.

**One record, `type:gap`, listing all six.** They share one mechanism — an object
whose real form is an open frame or separate bodies, drawn as disconnected
filled pieces — and **the register holds one record per FAULT, not per
instance.**

**Two things the record must carry:**

* **`bicycle` already has a disposition** — [`0013`](0013-ruling.md) ruled it
  *stays as it is* (*"thin, but a bicycle is thin"*). **The record cites that
  rather than reopening it.**
* **Four of the six are `vehicle`**, which is
  [`0012`](0012-ruling.md)'s own finding arriving again from a different
  instrument — 3 of 10 built cleanly then, and this is the same population.
  **The record points at the vehicle loft as the likely owner**, exactly as
  `boat_trailer` does.

**Exempting them by name in the test with a stated reason was correct**, and the
reason string updates to cite this ruling instead of *"not yet ruled."*

## 6. THE PORTABLE AUTHORING SPEC IS NOW STALE — and it is Patrick's, not the repo's

The spec written for external AI systems says internal detail is a **nested**
shape carrying `data-h`. **[`0033`](0033-report.md) makes `beside` the preferred
pattern** — a second top-level ring, outside or only partly overlapping the
body, which also carries `data-h` and does **not** inherit D76.

**That is the single most important line in the spec and it is now wrong.**
**Not Code's to fix** — the document lives outside the repository. **Noted here
so the correction is not lost**, and it is an argument for the spec eventually
living beside the parser it describes.

## 7. TIER AND ORDER

**[`0032`](0032-report.md)'s GREEN portion is merged** (`17f6c01` on `main`) and
needs nothing further beyond §4's raw values and §5's record.

**[`0033`](0033-report.md) is AMBER on branch `shower-identity-redraws`.** Merge
condition is §2's check — **both questions**. Nothing merges without it.

**The three pinned-test rewrites are ACCEPTED**: `glass_shower` genuinely stopped
being line-art, so a test pinning it to the fallback path had to change, and
converting them to a synthetic line-art kind **keeps the mechanism under test
once no real item exercises it.** That is a declared conversion, not a
relaxation — the distinction the agreement exists to protect.
