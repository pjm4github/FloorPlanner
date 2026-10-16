# 0277 — report: PR #91 merged on his word; the garage roof's dead knob — a dormer whose face stands past its host's eaves — fixed on `dormer-knob`

**Landed:** PR #91 · 7319fe4 · 2026-10-16 · AMBER · checked by Patrick in the app: "the drag-speed seems fine on #91"

**Code, 2026‑10‑16.** Two of his words, one report.

## 1. PR #91 MERGED

> *"go ahead with the knob fix, and the drag-speed seems fine on #91"*

His check of [`0276`](0276-report.md)'s branch passed; read as the word to
land it. `drag-speed` landed on `main` at **`7319fe4`**, fast-forward (one
commit on `main`'s tip, no fold needed);
[PR #91](https://github.com/pjm4github/FloorPlanner/pull/91) MERGED; the
branch deleted, local and remote. On `main` now: the roof clip trace and
the wall dashes cached on what they read, the settle walk held through a
roof gesture, the settle walk's idle re-arm loop gone.

## 2. HIS QUESTION, AND THE ANSWER

> *"look at the design in wiscaway2026-10-13R1.json ... The roof on the
> garage that has the gable end over the garage door is unresponsive when
> I try and click and drag on the control knob near the top ridge where it
> joins the roof. Am I using the controls correctly or is there a bug on
> the control?"*

He was using it correctly. The garage roof (`rf7`, ground floor, at 45°)
is recorded as a **dormer** of the main roof `rf8`, so its upper end is
derived where its ridge meets `rf8`, and that end's knob sets the **ridge
height** (R5b; 0195-ruling.md §2's clamp keeps the end on the host's
rising side). Measured on his file:

* the knob is the topmost item under the cursor and receives the press;
* the drag is refused at every move: the reach was measured **from the
  gable face**, and the face stands **312″ from `rf8`'s ridge where
  `rf8` reaches only 264″** — 48″ outside its footprint — so the reach
  read 0.0 and `drag_end` returned, saying nothing;
* yet the ridge meets `rf8` normally a few feet further in (190″ at 216″
  from the face, 210″ at 264″, 220″ at 288″), and the End-On dialog
  accepted a new ridge height on the same roof.

A garage gable projecting past the main roof's eaves is an ordinary
house; the knob's rule was too strict for it.

## 3. THE FIX — on `dormer-knob`, ONE commit on `main`'s tip, AMBER

* `roofclip.entry_along(rf, origin, direction)`: the distance along a ray
  at which it first enters a roof's footprint (0.0 inside, None never) —
  half-inch steps, then bisection, `rising_reach`'s own method.
* `RoofItem.drag_end`, the dormer's back end: the reach is measured **from
  where the ridge enters the host**; the knob is clamped between that
  entry and the crest, as before between the face and the crest. A face
  inside the host behaves exactly as it did (entry 0.0).
* **A refused drag says why** (`RoofItem._refuse_drag`, the status bar):
  "this roof's ridge never crosses its host roof", or "the host roof does
  not rise along this ridge" — never silence again.

On his file, after the fix: the knob dragged 84″ toward the face takes the
garage roof to 156″ long (ridge 165″); dragged back, 240″ (ridge 200″).

## 4. RECEIPT

`tests/test_dormer_knob.py` (6), on a synthetic house with the same
arrangement (a gable face 38″ past the host's overhung eave): the entry
distance, the fixture's face outside the host, the knob moving the ridge
and the back end landing where dragged, the crest clamp kept, a face
inside the host unchanged, a refused drag's status message. The shipped
code's refusal is shown on his own file (§2). The dormer, dormer-tool,
grip and shed suites unchanged and green; `--quick` passed (1642); gate
GREEN.

## 5. WHAT HAPPENS NEXT

His check of the garage knob in the app. Named from 0276: the wall-and-
room drag hold; 0275's step 4.

**Carried:** unchanged from [`0276`](0276-report.md).
