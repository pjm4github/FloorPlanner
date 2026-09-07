# 0160 — ruling: 0158/0159 verified — R4b hangs on one look, the outline

**On [`0158`](0158-report.md)/[`0159`](0159-report.md), both measured against
the branch (`roofs-r4b-parameters`, PR #55) before ruling.**

---

## 1. VERIFIED, AND TWO DECISIONS ENDORSED

The tree matches the reports: `selection_outline()` at `roofs.py:740`, painted
in place of the bounding box at `:789`; 43 tests in `test_roof_params.py`; the
per-side span fields in the dialog; and the End-On canvas **does** draw both
sides from their own span (`dialogs.py:827`, citing [`0154`](0154-ruling.md)
§2 verbatim) — so the asymmetric-slope obligation is met, not just claimed.

Two judgment calls in [`0158`](0158-report.md) §2 are **endorsed as ruled
precedent**, not merely tolerated:

* **`nearest_eaves_wall` keeps its segment form so the R4a migration replays
  a document's historical geometry exactly.** A migration is not the place
  for a content correction — the dialog is the correction path for a roof
  that came in inflated. That is the right reading of the agreement.
* **Pitch's canonical side is LEFT (`span_in[0]`)** for the three-way
  recompute — one editable pitch, two drawn slopes. Consistent with
  [`0154`](0154-ruling.md) §2; the convention is documented where it lives.

## 2. THE GATE — unchanged, and only one thing behind it

**AMBER stands. The three [`0158`](0158-report.md) fixes are already checked
by Patrick; the selection outline is the one item left for his eye:**

> Select the 45° wing's roof — the outline hugs it, oriented with the ridge,
> corners on the eave corners. And once on an orthogonal roof, where it is
> simply the footprint rectangle.

On his word: **merge PR #55, delete the branch in the merge step, and R4c
starts** — whose eave-edge grips must drag exactly the two `span_in` values
the dialog now edits, a receipt named here so R4c cannot grow a second span
convention.

## 3. ONE HYGIENE LINE

`branch -a` here still shows `origin/roofs-r3b-clip-line`, which
[`0153`](0153-report.md) reported deleted remotely. Likely an unpruned
tracking ref (no network from this seat to confirm) — **Code: `git fetch
--prune`, and one line in the next report saying which it was.**

**Carried:** D83/D84 (held); room-label rounding ([`0131`](0131-ruling.md)
§2); delta-snap sites; D61-family; yard items.
