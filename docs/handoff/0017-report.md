# 0017 — report: the owed measurement from 0016 §5

**Measurement only. No ruling — Patrick's instruction in
[`0016-ruling.md`](0016-ruling.md) §5 was explicit that this is Code's to
measure and his to rule on:** *"I am not ruling the defect, because I inferred
it from a rule and a picture and this project distinguishes a correct
inference from a taken reading."*

**Per the standing addition in the same ruling — the plan and its contents,
named first:**

* **Plan:** [`../../fixtures/enclosure-form-check.json`](../../fixtures/enclosure-form-check.json)
  — three items, one each, well apart: `walk_in_shower`, `sauna`, `whirlpool`.
* **Render:** [`../evidence/enclosure-form-measurement.png`](../evidence/enclosure-form-measurement.png).
* **Probe:** [`../evidence/enclosure_form_measurement.py`](../evidence/enclosure_form_measurement.py)
  (`--look` writes the plan and prints the render command; without it, prints
  the measurement alone).

---

## The question asked

> For `walk_in_shower`, `sauna` and `whirlpool`, dump each part and state
> whether it produced a raised solid or an opened cap.

## The instrument, and why it is not a re-derivation

**Black-box.** It calls only `build_model` — the unmodified production entry
point — and inspects the mesh it built, rather than re-reading `build_prism`'s
classification lines in a second copy that could drift from them.

**The signal:** a well, by construction, cuts a hole in the body's cap where it
sits; a raised region never touches the cap at all. So: **is there a horizontal
face at the body's full height, directly over the region's centre?** No face
there = the cap is open = a well.

**Positive control run first, per the working agreement's rule** (an
instrument's zero — or here, its uniform answer — is not believed until it is
shown to catch a known case): `bathtub`, a genuine vessel already ruled
correct, must still read as a well. It does.

## The three lines

```
item              region h  body h  outcome
------------------------------------------------------------
walk_in_shower        18.0    78.0  WELL (cap opened)
sauna                 30.0    84.0  WELL (cap opened)
whirlpool             30.0    36.0  WELL (cap opened)

THE THREE LINES: 3 of 3 tall enclosures produced a WELL (cap opened into the top face) for their internal feature.
Confirmed: walk_in_shower (18in < 78in body), sauna (30in < 84in body), whirlpool (30in < 36in body)
```

**All three produced a WELL — an opened cap, not a raised solid.**

## What that confirms, stated against 0016's own table rather than re-argued

| item | 0016's expectation | measured |
|---|---|---|
| `whirlpool` | "well — **correct**" | WELL ✓ — matches, and this is the expected/right outcome for a vessel |
| `walk_in_shower` | "well — **a bench becomes a slot**" | WELL ✓ — confirms the bench is being cut into the enclosure's own ceiling at 78″, not built as a floor-standing block |
| `sauna` | "well — **a stove becomes a hole**" | WELL ✓ — confirms the heater is cut into the roof at 84″, matching the dark square notch visible in the render |

**The premise `form="enclosure"` conflates a VESSEL and a ROOM is now measured,
not merely inferred from a picture.** `whirlpool`'s well is physically right —
a recessed water surface below a rim. `walk_in_shower`'s and `sauna`'s wells are
physically wrong for the same mechanical reason applied to a different shape: a
tall hollow volume where the internal feature should stand on the floor, not
recess into the ceiling.

## The render

Left to right: `walk_in_shower` (translucent, its notch visible near the top,
partly hidden by the glass), `sauna` (the dark square notch in its roof,
exactly as described), `whirlpool` (the recessed water surface, correct for its
form).

## What is NOT claimed

* **Not a fix, and not a ruling on whether one is owed.** The measurement
  answers the mechanical question; whether `enclosure` splits into two forms,
  and how, is Patrick's.
* **Not a claim about `bathtub`, `swim_spa` or any vessel-height item** beyond
  the positive control — those were already agreed correct in 0016's table and
  were not re-measured.
* **Not a claim about `shower` or `glass_shower`** — neither carries an
  internal region, so this question does not apply to them; they are on the
  authoring list for a different reason (0016 §3–4).
