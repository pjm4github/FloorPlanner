# 0247 — report: his word on 0241 §2 — the overhang rule stays as it is on the three-ridge and two-level fixtures; nothing built

**Code, 2026‑10‑11.** No merge has happened since
[`0246`](0246-report.md). [`0241`](0241-report.md) §2 named two places
the overhang rule reaches that the order had expected unchanged — the
three-ridge fixtures (slivers of `rf1`'s eaves strip under `rf3`'s
soffit at the notch outside the walls) and the two-level stacked
fixture (the first-floor roof under the second-floor roof where the
second floor has no walls) — and offered the one-line narrowing (a
covering roof of a higher level only). His word:

> *"Keep the rule as it is for the three-ridge and two-level fixtures."*

So the rule stands as merged in PR #81: a hidden cell of a roof's own
footprint is built wherever its centroid lies outside every wall loop
of the covering roof's level, whatever level that roof is on. The tests
that pin those two fixtures' measured additions
(`tests/test_roof_overhang_3d.py`) are the record of what he kept.
Nothing to build; the narrowing is not taken and not owed.

## 1. `fixtures/incoming/`, with ages

* `wiscaway2026-10-07R1.json` — his own, 2026‑10‑07; exit his to name.
* `README.md`.

## 2. WHAT HAPPENS NEXT

His next design, or the compose cost ([`0237`](0237-report.md) §0, the
patch at `docs/evidence/roofclip-adjacency-memo.patch`) as its own
tranche.

**Carried:** unchanged from [`0246`](0246-report.md).
