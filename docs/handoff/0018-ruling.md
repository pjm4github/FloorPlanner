# 0018 — ruling: the form splits, and 0017's control was pointed the wrong way

**Patrick's, 2026‑08‑15**, on [`0017-report.md`](0017-report.md).

---

## 1. WHAT 0017 DID RIGHT, because it is most of the report

**Black-box against `build_model`**, rather than re-reading `build_prism`'s
classification in a second copy that could drift — the one-definition rule
applied to an instrument. **The plan is named and its contents listed**, which is
0016 §6's standing rule followed the first time it applied. **The probe and the
render are committed**, so the measurement can be re-run rather than believed.
**No ruling authored.** All of that stands.

## 2. THE CONTROL IS POINTED THE WRONG WAY, AND THE THREE LINES DO NOT YET MEAN WHAT THEY SAY

The instrument has two answers: `WELL (cap opened)` and `RAISED (cap intact)`.
Everything it was run on returned the first:

| run | expected | got |
|---|---|---|
| `bathtub` — the control | WELL | WELL |
| `whirlpool` | WELL | WELL |
| `walk_in_shower` | WELL | WELL |
| `sauna` | WELL | WELL |

> **THE CONTROL SHARES ITS EXPECTED ANSWER WITH EVERY CASE UNDER TEST, SO IT
> TESTS THE ONE DIRECTION THAT CANNOT FAIL.** `bathtub` shows the instrument can
> say WELL. **Nothing shows it can say anything else.** A `roof_over()` that
> always returned `False` — a mis-mapped centroid landing outside the mesh, a
> viewBox-to-inches transform off by a factor, a bug in the face lookup —
> produces this exact output, control included.

**This is the third member of a family this project already keeps.** The
positive control catches **an instrument reporting nothing**. The
identical-cases rule catches **one reporting a plausible something**. This one
catches **an instrument that can only report ONE OF ITS TWO ANSWERS** — and the
tell is that the control was chosen for the answer the experiment expected
rather than the answer it did not.

> ### A CONTROL MUST BE CHOSEN FOR THE ANSWER YOU ARE *NOT* EXPECTING.
>
> One run, on a known **raised** region — a bed's pillow, or a `sofa` back now
> that PR #29 closed it — **must read `RAISED (cap intact)`**. Until it does,
> *"3 of 3 produced a WELL"* is a sentence about a function that has only ever
> emitted one string.

**AND THIS IS NOT PEDANTRY, BECAUSE THE SAME INSTRUMENT MUST PROVE THE FIX.**
The fix's receipt is *"the sauna's heater now reads RAISED"* — measured by this
probe. **An instrument that has never emitted `RAISED` cannot establish that
receipt**, so the control is a prerequisite of the repair, not a tax on the
diagnosis.

## 3. THE FINDING ITSELF SURVIVES, ON A SECOND INSTRUMENT

**The conclusion is not hanging on the probe.** The render shows a dark square
notch in the sauna's roof where a stove should stand, and that is a different
instrument agreeing with the first. **Two instruments of different kinds
agreeing is worth more than either**, which is why §4 rules now rather than
waiting.

What §2 blocks is quoting *"3 of 3"* as a measurement. What it does not block is
the decision.

## 4. THE RULING: `enclosure` SPLITS, AND IT SPLITS CATEGORICALLY

> **ADD A `vessel` FORM. `bathtub`, `whirlpool` and `swim_spa` become
> `vessel`; `shower`, `walk_in_shower`, `glass_shower` and `sauna` stay
> `enclosure`, which from now on means a room you walk into.**
>
> **A VESSEL'S INTERNAL REGION IS A RECESS. AN ENCLOSURE'S IS A SOLID STANDING
> ON THE FLOOR.** The above/below test stays exactly as it is for `vessel` and
> stops applying to `enclosure`.

**Three catalog rows, and `KNOWN_FORMS` at `floorplanner/viewer/fp3d.py:603`
gains one value.**

**NOT A HEIGHT THRESHOLD**, though the split is visible as one — 20/36/40
against 78/78/78/84. **A threshold there is the `lawnmower`/`snowblower`
mistake** ([`0012-ruling.md`](0012-ruling.md)), and a vessel and a room are
different **kinds**, not points on an axis. This is the categorical-channel rule
at the level of the catalog rather than the picture.

**`data-h` is untouched** and still carries a height and nothing else, so
[`0014-ruling.md`](0014-ruling.md) §4's boundary holds and the test that walks
every SVG stays green. **The fact lives in the catalog because it is a property
of the KIND, not of the drawing** — one normative source per fact, the thickness
table's discipline.

## 5. THREE THINGS TO GET RIGHT WHILE BUILDING IT

**FIRST, `form` IS CATALOG-SIDE ONLY — no schema question arises.** Measured:
no file in `examples/` or `fixtures/` contains a `"form"` key. So this is not a
document change, R‑B is not needed, and nothing versions.

**SECOND, THERE ARE TWO UNRELATED `form` COLUMNS IN THIS CODEBASE AND A GREP
CONFLATES THEM.** The furnishing form (`fp3d.py`) and `spec.form` in
`floorplanner/walls.py:1526` — `"ticks"`, `"scallop"` — which is D74's wall
decoration and has nothing to do with this. **Enumerate the consumers of the
FURNISHING form specifically**, or the census returns the wall table and reads
as thoroughness.

**THIRD, THE LIMIT IS STATED WHEN THE SPLIT LANDS, NOT DISCOVERED LATER.** After
this, **a room with a RECESSED floor feature is not representable** — a shower
pan, a floor drain, a sunken threshold. No such item exists in the catalog
today. **File it as `type:limit` in the same commit**, on D44's precedent, so it
is an accepted limit rather than a gap nobody knows the shape of.

## 6. THE MATERIAL COLUMN IS CARRYING TWO FACTS, AND WHICH ONE IS DECIDED PER ROW

**Patrick, on the render, 2026‑08‑15:**

> **The whirlpool should have a solid color on the top and sides but a
> translucent round pool area. The Walk in shower should have a solid bench on
> the inside that sits on the floor.**

**This is a second defect, not a detail of the first, and it was invisible until
the geometry was looked at.** The catalog gives each item ONE material, and the
seven read:

| item | material | which fact the column is naming |
|---|---|---|
| `bathtub` | `porcelain` | **the body** — and it has no water at all |
| `swim_spa` | `water` | **the contents** — so the whole tub is translucent |
| `whirlpool` | `water` | **the contents** — so the whole tub is translucent |
| `shower` · `walk_in_shower` · `glass_shower` | `glass` | **the body** — correct, and the bench has no material of its own |
| `sauna` | `wood` | **the body** — and the stove has none |

> ### ONE COLUMN IS CARRYING TWO FACTS AND WHICH ONE IT NAMES IS DECIDED PER ROW, BY WHOEVER WROTE IT.
>
> `bathtub` names its surround; `whirlpool` names its water. **Both are called
> `material` and they are not the same fact.** That is why the render is wrong in
> two different directions at once — the whirlpool is translucent where it should
> be solid, and the shower's bench is nothing at all.
>
> **This is the D73/D74 disease in its general form**: one channel asked to carry
> two facts, resolved by convention instead of by structure. **The remedy is the
> same one — one normative source per fact.**

**THE RULING: MATERIALS ATTACH TO PARTS, NOT TO ITEMS.** A body material and a
region material, both in the catalog. **And the vessel/enclosure split decides
which is which, with no further information:**

| form | body | region |
|---|---|---|
| **`vessel`** | solid surround — `porcelain`, and whatever `swim_spa` and `whirlpool` should surround themselves with | the declared contents — **`water`, translucent** |
| **`enclosure`** | the declared shell — **`glass` translucent, `wood` opaque** | **solid** — a bench, a stove |

> **THAT THE SAME SPLIT DECIDES BOTH THE GEOMETRY AND THE MATERIAL IS THE
> STRONGEST EVIDENCE YET THAT IT IS THE RIGHT CUT.** A patch that fixed the
> recess and left the materials alone would have been an ad-hoc repair; one line
> falling out of the same distinction twice is a distinction the domain actually
> has.

**`data-h` IS STILL UNTOUCHED.** A material is a property of the KIND, not of the
drawing, so it belongs in the catalog beside the height — not as a second
`data-` attribute, which [`0014-ruling.md`](0014-ruling.md) §4's test would fail
by design and correctly.

**ONE BOUNDARY, STATED SO IT IS NOT DISCOVERED LATER:** one region material per
item covers **all seven** cases here, because none has two regions wanting
different materials. **An item that acquires a second region needing a different
material is the trigger to revisit this**, and that sentence is the whole of the
limit — it is not a reason to build a per-region table now.

## 7. TIER, AND THE CHECK — CORRECTED BEFORE IT WAS RUN

**AMBER.** It changes what the 3D view produces for `sauna` and
`walk_in_shower`.

**My first wording was *"does the sauna's stove stand on the floor"*, AND IT IS
NOT A CHECK THAT CAN BE PERFORMED.** The sauna is opaque wood, closed and
capped — visible in the render it was written from. **After the fix the stove is
a solid inside a closed opaque box, so there is nothing to look at.** The only
reason the defect is visible *today* is that the bug cuts a hole in the roof:
**the fault is observable and the correct state is not**, which is the worst
shape a manual check can have.

**Recorded rather than quietly reworded, because the general form is worth
more than the correction:**

> ### A CHECK MUST NAME SOMETHING THE CORRECT STATE MAKES VISIBLE — not merely something the FAULT makes visible.
>
> A check keyed to the fault's signature passes the moment the signature
> disappears, and **a region silently dropped produces the same picture as a
> region correctly built.** Same family as a negative assertion establishing its
> precondition: *"the hole is gone"* cannot distinguish repaired from removed.

**THE CHECK, IN THREE PARTS, ON ONE RENDER of [`../../fixtures/enclosure-form-check.json`](../../fixtures/enclosure-form-check.json)** —
the fixture 0017 already built, against
[`../evidence/enclosure-form-measurement.png`](../evidence/enclosure-form-measurement.png)
as the before:

| | item | question — Patrick's words where he gave them | why it is the one that answers |
|---|---|---|---|
| 1 | **`walk_in_shower`** | **"a solid bench on the inside that sits on the floor"** | **The verdict lives here.** Its body is translucent glass, so the interior is visible from outside — the only one of the three where the CORRECT state can be seen |
| 2 | `sauna` | Is the roof unbroken — the dark square notch gone? | Corroborating only, and weak on its own for the reason above |
| 3 | **`whirlpool`** | **"a solid color on the top and sides but a translucent round pool area"** | **The control, and now a positive one.** It no longer asks only that something did *not* change |

**ROW 3 CHANGED CHARACTER WHEN PATRICK DESCRIBED IT.** It was *"is the water
surface still recessed"* — a check that the fix did not over-apply, and a
negative. **It is now a description of a correct state nobody has ever seen**,
which is a better instrument for exactly the reason §7's own rule gives: a
negative row cannot distinguish repaired from removed, and this one now can.

**All three rows are positive**, and they fail in three different directions —
geometry (row 1), the fault's signature (row 2), materials (row 3). That is the
same discipline §2 demands of the probe, one layer up.

**One consequence worth filing separately:** the sauna's interior is
unobservable in the viewer today, and **an item whose 3D correctness cannot be
verified by looking is one where the picture has stopped being evidence.**
[D69](../defects/0069-an-auxiliary-control-panel-on-the-3d-view.md) — the
component-toggle panel — is the record that would fix it. **Not scope for this
task**, and it should be noted against D69 that a manual check has now wanted it.

**Order:** the §2 negative control first — one run, and it is owed before the
fix because the fix's receipt depends on it. Then the split. **Then** the three
redraws, which were already waiting on this ruling. **`boat_trailer` stays held
out** pending the vehicle-loft decision, as 0017's re-cut has it.
