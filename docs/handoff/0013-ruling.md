# 0013 — ruling: prism's tier, and the two small calls

**Patrick's, 2026‑08‑13**, on
[`0013-report-prism-receipt.md`](0013-report-prism-receipt.md). Quoted rather
than summarised.

---

## 0. THE TIER — prism is AMBER, and it landed without its check

> **CONFIRM PRISM's STATE — is it merged, or on a branch awaiting a check? It
> changes what the 3D view looks like for 27 of 95 items, which is AMBER by the
> charter, and I do not want it landing on the strength of a count.**

**It was merged.** Committed straight to `main` at `8724740` and pushed, with no
branch, no PR and no check. **Confirmed, not defended.**

**Backed out at `72e49cb`** and re-applied on `prism-plan-symbol` at a PR.
`main`'s history keeps both the landing and the backing-out.

### The error, stated as a rule rather than as an apology

**The tier was not misread — it was not consulted.** The work had a ruled
receipt (*re-measure, do not claim*); the receipt came back strong (28 → 1); and
**a strong number was allowed to stand in for a tier decision.** Those are
different questions:

| the question | what answers it |
|---|---|
| *did it work?* | the re-measurement |
| *does it look right to the person who lives with it?* | **the AMBER check, and nothing else** |

**Twice in two days a count has looked like enough.** The first was the 25%
coverage threshold, and it was **caught** — by inspecting either side of the
line. This one was **not caught; it was reported**, after the fact, by the
reviewer. The instrument rule was already on disk. What was missing was applying
it to **the decision to merge** and not only to the measurement.

> **A GREEN GATE AND A STRONG NUMBER ARE BOTH EVIDENCE ABOUT THE CODE. NEITHER
> IS EVIDENCE ABOUT THE TIER.** The tier is a fact about who the change affects,
> and it is settled before the work starts, not by how well the work went.

## The check, and it serves twice

> **If it is not merged, Patrick's look serves twice: it is both the AMBER check
> and the input to the reserved decision. Give him the plan and the view; do not
> summarise what he should see.**

**Plan:** `fixtures/prism-check.json` — one of every one of the 28 affected
kinds, grouped by form, in a room. Built by `fixtures/prism-check.json.py` from
the catalog, so it cannot go stale against it.

**View:** `python floorplanner/viewer/fp3d.py fixtures/prism-check.json`
Renders of the same plan either side of the change are at
`docs/evidence/prism-check-before.png` and `-after.png`.

**No reading of them is offered here.** What is stated is which items are in the
plan and where; what they look like is the thing being asked.

## 1. THE RESERVED DECISION STAYS RESERVED

> **THE RESERVED DECISION STAYS RESERVED until he has looked.** `seat`, `bed`,
> `basin` and `enclosure` are 17 of 18 extruding from real outlines, and what a
> dedicated generator would add is structure the plan symbol cannot contain — a
> seat back, a tub's well. **Whether that is worth four functions is a judgement
> about how the room reads, and no measurement substitutes for it.**

**Nothing is to be built against those four forms**, and the re-measurement is
**not** to be read as having decided it.

## 2. `boat_trailer` stays extruding, and goes on the authoring list

> **`boat_trailer` stays extruding and goes on the authoring list. You were
> right not to add a threshold to catch it — that would be a coverage threshold,
> and the instrument whose failure is already recorded in the working agreement.
> Five disconnected slabs is an artwork problem with an artwork fix.**

**No code change.** The authoring list stands at **two**: `glass_shower` (no
fill at all) and `boat_trailer` (fills, but no body).

## 3. `bicycle` stays as it is

> **`bicycle` stays as it is. Your reasoning is correct and worth keeping: a
> bicycle IS thin, and a 24x68 box says something far more wrong. A prediction
> refuted by looking rather than by counting is the third time the picture has
> outranked the number on this feature.**

**The three times, since the ruling counts them:**

1. the decoration channel's first cut — every test true, the drawing still wrong
   at working zoom;
2. `boat_trailer` — the read-back's prediction **confirmed** by the render;
3. `bicycle` — the same read-back's prediction **refuted** by the render.

**Two of the three went against the earlier written judgement**, which is what
makes the pattern worth recording rather than merely noting.

## 4. The y-flip

> **The y-flip assertion on the mower's deck is the right place to have spent
> the care — a sign error there mirrors every asymmetric item and looks entirely
> plausible, which is the worst combination available.**

Recorded here because *"wrong and plausible"* is a class, not an incident: it is
where a test earns the most, and it is the same shape as the mirrored-symbol
fault the deleted furniture table shipped for months.
