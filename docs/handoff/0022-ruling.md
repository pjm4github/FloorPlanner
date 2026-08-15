# 0022 — ruling: the control is accepted, and row 1 is not discharged by a number

**Patrick's, 2026‑08‑15**, on [`0021-report.md`](0021-report.md).

---

## 1. THE CONTROL IS ACCEPTED — both sides shown, which is what [`0018`](0018-ruling.md) §2 asked for

`bathtub` reads WELL and `sofa`'s back reads RAISED. **The instrument has now
emitted both of its strings**, so *"3 of 3 produced a WELL"* became a
measurement rather than a sentence about a function that had only ever said one
thing. Nothing further owed on that point.

## 2. §3 IS WORTH MORE THAN THE FIX IT DESCRIBES

The bench built at **18″–78″ — a column hanging near the ceiling** — instead of
0″–18″, and **the probe could not have caught it.**

> ### AN INSTRUMENT BUILT TO ANSWER A CLASSIFICATION QUESTION IS STRUCTURALLY BLIND TO A CONSTRUCTION ERROR ONE LAYER DOWN.
>
> `roof_over` asks *is there a face at the body's full height over the region's
> centre* — a question about **the cap**. The misplaced bench never touched the
> cap, so it was **outside the instrument's domain, not merely missed by it.**
> The classification was right and the construction was wrong, and one control
> cannot cover both.

**Code's own sentence is the keeper and I am adopting it verbatim:** *"a control
proves the question it was built to answer, and no more."* **Land it in
[`../WORKING_AGREEMENT.md`](../WORKING_AGREEMENT.md)** beside the positive-control
family — it is that family's fourth member, and the first where the instrument
was **correct** and still silent.

**And the thing that did catch it — dumping the built mesh's own bounding box —
is the cheaper instrument.** A z-extent is a direct reading of the artefact,
where `roof_over` is an inference from one sampled face.

## 3. ROW 1 IS NOT DISCHARGED BY THE MESH NUMBERS

`z[0.0, 18.0]` proves the bench is **in the right place**. **It does not prove
the bench looks like a bench** — its proportion against the enclosure, whether
it reads as a fixture or as a slab, whether a person would name it. **That
residue is exactly what AMBER exists for**, and
[`0013-ruling.md`](0013-ruling.md) already ruled on this shape:

> **a green gate and a strong number are evidence about the code, not about the
> tier.**

**Accepting a geometric receipt in place of the look would be that ruling
reversed** — and it would be the second check in two days written so that only
the *fault* was observable ([`0018`](0018-ruling.md) §7).

### THE REMEDY IS AN EVIDENCE RENDER, NOT A SUBSTITUTED NUMBER

> **Produce one render of the same fixture with the ENCLOSURE BODIES OMITTED**,
> from the evidence probe — **not** from production code, and **not** a viewer
> flag.

**It invents nothing**, which is why the `--stack` objection does not reach it:
that refused a flag that would have **supplied a number the document does not
contain**. This hides a part that is known, present and measured, in order to
photograph another part. **A diagnostic view of real geometry is evidence; a
rendering that fills in an unknown is not.** The distinction is the whole of it.

**If that render proves impractical**, merge on rows 2 and 3 with **row 1
carried as EXPLICITLY UNCHECKED in the merge note and in the progress entry** —
named, never quietly dropped, and run retrospectively the first time the viewer
can show an interior.

## 4. THE NON-COMPOSITING IS ITS OWN RECORD, NOT A NOTE ON D69

Filed against [D69](../defects/0069-an-auxiliary-control-panel-on-the-3d-view.md)
it becomes a line inside a **feature request for a control panel**. It is not
that. **It is a rendering limitation with a general statement:**

> **AN OPAQUE MESH INSIDE A TRANSLUCENT BODY DOES NOT COMPOSITE, AT ANY ALPHA
> TESTED (0.35 shipped, 0.12 synthetic).**

**That reaches every future item of this shape** — anything inside glass, a
cabinet interior, a fixture within a shower — and it silently defeats manual
checks, which is how it was found. **Open it as its own record**, cross-referenced
to D69 rather than buried in it, and cite this ruling as the occasion.

## 5. MATERIALS — ACCEPTED, with one question left to Patrick's eye

The body/region split lands as ruled, and the fallback to the body's material
where no region material is stated is the right default.

**One item is a judgement, not a defect:** `swim_spa` and `whirlpool` bodies are
now **`porcelain`**. A whirlpool surround plausibly is; **a swim spa is more
often acrylic.** Not ruled — **row 3 of the check is where it gets answered**,
and if it reads wrong it is a one-word catalog change.

## 6. [D75](../defects/0075-a-recessed-floor-feature-is-not-representable.md) — ACCEPTED

Filed in the same commit as the split, as [`0018`](0018-ruling.md) §5 required,
on D44's precedent. Nothing further.

## 7. THE CHECK AS IT NOW STANDS

| | item | question | how |
|---|---|---|---|
| 1 | `walk_in_shower` | a solid bench, on the floor, that reads as a bench | **the §3 evidence render** — not the mesh numbers, not the current picture |
| 2 | `sauna` | roof unbroken, the dark notch gone | the render |
| 3 | `whirlpool` | solid top and sides, translucent round pool — **and is `porcelain` right?** | the render |

**Tier unchanged: AMBER.** Merge condition is rows 2 and 3 passing plus row 1
either answered or explicitly carried.

## 8. HOUSEKEEPING — the protocol diagram

**[`channel-commands.svg`](channel-commands.svg) is on disk beside this file**,
written by Cowork as a **new** file. **Add a link to it from
[`README.md`](README.md)** — Cowork did not, and will not, edit that file:
the agreement's *"Cowork no longer edits ANY FILE IN THE REPO DIRECTLY"* stands
on three doc-loss incidents whose mechanism is a stale staged copy, and
`README.md` is **currently modified in the index**, which is precisely the
state that rule was written to protect.

> **THE RULE RECONCILES CLEANLY WITH THE CHANNEL, AND IT IS WORTH SAYING WHY:
> creating a NEW numbered file carries no stale-read risk — there is nothing to
> read. Editing an existing one carries all of it.** That is why the reviewer
> writes `NNNN-ruling.md` directly and hands every other edit over as an
> instruction.
