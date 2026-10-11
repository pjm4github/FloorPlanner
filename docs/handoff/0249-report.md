# 0249 — report: 0248's plans A and C built on `roof-shed-form` — the `shed` roof form, and a dormer's generated side or face yielding to a house wall; the house model regenerated with both; AMBER, for his check

**Code, 2026‑10‑11.** No merge has happened since
[`0246`](0246-report.md). His word on [`0248`](0248-report.md) §3:

> *"Implement plan A and C from 0248"*

Built as one commit on `roof-shed-form`, a PR for his check.

## 0. PLAN A — the `shed` roof form

**The record.** `form: "gable" | "shed"` on a roof, default `gable`,
omitted when gable (additive, ROADMAP R‑B, no version bump; a gable
written today is byte-identical to one written yesterday). A shed is
ONE plane off the ridge, down the LEFT side (`span_in[0]`); its right
span and overhang are 0. The schema's `span_in` keeps its exclusive
minimum on both sides for a gable and lets the RIGHT side be 0 on a
shed — an `if/else` on `form` — so the 1″-strip workaround of the
house model is retired and a zero span on a gable is still refused.

**The item.** `RoofItem(form=…)`; its `span_in`/`overhang_in` setters
clamp the right side to 0 on a shed, whatever a grip, a dialog or a
loader hands them; `set_form` goes both ways (a gable given back its
right side takes the left span); the right eave grip does nothing on a
shed. The clip's twin (`RoofGeom.from_record`) carries the form and the
same clamp. The dataclass, the writer and the reader carry the field.

**The dialog.** A *Form* row on the End-On dialog (Gable / Shed). On a
shed the right span and overhang are 0 and locked, "same overhang"
off; back to gable, the right side opens and takes the left span. The
form is written before the spans on apply, so the setters clamp.

**The 3D builder.** A zero-width plane is not built (a degenerate
ring); a shed dormer — its high edge ON the host, both ridge ends alike
— gets a generated side at BOTH ends (the face finder took the end
standing highest; now every end within EPS of the highest). And a
hipped shed's end: the corner on the ridge line sits on the HIP plane,
eaves height less the overhang's drop at the end of the extension, as
`surface_height` already says and the clipped path already built —
the unclipped path had it at ridge height, a flat shelf, found on the
house's porch roof once its right span became exactly 0 (a zero span
no longer overlaps the main roof, so the porch builds unclipped).

Nothing in `compute_roof_clips` changed: every reader already treated a
zero side as a zero-width strip.

## 1. PLAN C — the generated side or face yields to a house wall

`_on_a_wall`: a generated piece's plan segment inside the body of a
house wall of the dormer's level — both ends within half the wall's
thickness (plus ½″) of its centreline — AND running along it (within
10°; a cheek that merely ends against a wall standing across its line,
R2's cheeks at the eaves wall, is not on that wall). Such a piece is
skipped: the wall beneath climbs into the dormer already, with its own
openings, and the generated piece on the same line buried them (0248
§2 items 2 and 3). `build_model` hands each dormer its level's walls in
plan; the three promoted dormer fixtures build byte-identically with
the yield switched off (none has a wall on a generated line).

## 2. THE HOUSE MODEL, regenerated — iteration 5

`fixtures/incoming/house_cutout_work/iter-05.json`: the shed dormer and
the porch roof as `form: "shed"` with a right span of 0; the shed
dormer's front edge ON the house wall, no inset. Schema and invariants
clean. Measured: the wall under the dormer stands with its three
windows cut and nothing generated behind it; the shed dormer has a
side at both ends; the porch roof hipped at both ends. `STATUS.md`
there carries it; `house_cutout.json` is still iteration 4 (the
pre-form document) until he says which to keep.

## 3. THE RECEIPT

* `tests/test_roof_shed_form.py`, 11: the schema (a zero right span
  legal on a shed and on nothing else; `hip` is not a form; today's
  roofs unchanged); the item's clamps, `set_form` both ways, the dead
  right grip, a bad form a gable; the round trip (a gable writes no
  `form`); the dialog (locked right side, both directions, applied);
  the clip twin (one-plane footprint, the surface flat past the ridge);
  one slab and no degenerate plane; a hipped shed's corner on the hip
  plane, a gabled shed with none; a shed dormer's two sides; a cheek
  and a face on a house wall's line not generated while the wall
  climbs and its window stays open; the three dormer fixtures
  unchanged by the yield.
* `--quick` 1553 passed; ruff clean; the full gate GREEN on the branch
  commit.

## 4. TIER

**AMBER** — a new record field with a dialog control, and a change to
what the 3D view draws around dormers. For his check: the End-On
dialog on any roof (the Form row), a shed drawn and saved and reloaded,
and the house model's iteration 5 in the 3D view.

## 5. `fixtures/incoming/`, with ages

* `house_cutout_transparent.png` — his own, 2026‑10‑11.
* `house_cutout.json`, `house_cutout_work/` — mine, 2026‑10‑11 (0248 §0;
  iteration 5 added here).
* `wiscaway2026-10-07R1.json` — his own, 2026‑10‑07; exit his to name.
* `README.md`.

## 6. WHAT HAPPENS NEXT

His check of the PR. Then 0248 §3's B (dormer openings), D (the
equal-height ridge meeting) and E (posts, the porch floor), his to
order. Behind them: the compose cost ([`0237`](0237-report.md) §0).

**Carried:** unchanged from [`0248`](0248-report.md).
