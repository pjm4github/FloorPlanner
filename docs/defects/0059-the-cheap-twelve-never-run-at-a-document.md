---
# permanent key, independent of GitHub
id: 59
title: "The CHEAP TWELVE never run at a document boundary either - and they cost nothing"

# maps directly onto GitHub Issues fields
state: open
state_reason: null
labels:
  - type:gap
  - area:schema
milestone: null

# ours; becomes body prose after migration
opened: 2026-08-08
closed: null
closed_by: null
rank: 60
related: [49, 57]
state_source: report
github_issue: null
---

# D59 — The cheap twelve never run at a document boundary either

## Symptom

**Split out of [D49](0049-i11-overlapping-placed-rooms-the-corruption-this.md)
on 2026‑08‑08, on measured grounds rather than preference.** D49 says the app
never runs the **deep** set at load or save. The same is true of the **cheap
twelve**, and that half has a different cost profile, a different objection, and
a worked example that D49's does not cover.

A real plan was saved carrying `I7 opening o29 runs off wall w90
(68.0..116.0 of 72.0)`. Nothing reported it. The fault sat in the file until the
user clicked to name a room, and the application died with no message
([D57](0057-face-at-hands-walls-of-a-report-of.md)).

## Mechanism

Identical to D49's, and that is the point of splitting rather than duplicating:
`verify()` returns `None` unless `verify_enabled()`, and `app.py` sets the env
var only for `--verify-design`. **On a default launch nothing runs — cheap or
deep.** D49 records that mechanism in full.

**What differs is which set would have sufficed.** Measured on
`fixtures/wiscaway2026-08-08.json`:

    check(deep=True)  -> ['I7  opening o29 runs off wall w90 (68.0..116.0 of 72.0)']
    check(deep=False) -> ['I7  opening o29 runs off wall w90 (68.0..116.0 of 72.0)']

**I7 is one of the cheap twelve** — `validate.check`'s own docstring: deep-only
is I5b, I11, I14; always-on is I1–I10, I12, I13.

## Evidence

**THE SPLIT IS THE FINDING.** D49's standing objection — the one that has kept
it from being scheduled — is P1.2's cost argument: *an O(n²) sweep per edit
makes the app unusable*. **That objection does not touch this half at all.** The
cheap twelve are the set already deemed affordable **per mutation** under shadow
mode; running them once at a load and once at a save is strictly less work than
what `--verify-design` already does continuously.

So the two halves have genuinely different open questions:

| | the check | the open question |
|---|---|---|
| **D59** (this) | the **cheap twelve** at load and save | **only what the app DOES with the result** — report, ask, or refuse |
| **D49** | the **deep three** (I5b, I11, I14) at load and save | the cost question stays open, and the report needs an area D52's half 1 must supply first |

**The chain this breaks**, from D57: *saved dirty → nothing said → clicked to
name a room → the process died with no message.* A save-boundary check breaks it
at the first link; a load-boundary check at the second.

**THE BOUNDARY, KEPT INTACT AND UNCLAIMED.** This says a check would have
**REPORTED** the fault. **Whether the user would have acted on the report is
unmeasured, and is not claimed here.** It is also silent about the deep three,
whose cost argument this evidence does not address.

## Ruling

*(Open — actionable, and the only open question is the response.)*

**D49's amendment already answers the response question for overlap, and its
reasoning carries**: *check yes, fix no*; *save asks, it does not refuse*; the
report must be actionable. Nothing in that reasoning is specific to I11 — it is
about not silently changing drawn geometry and not trapping the user with
unsaveable work, and both apply to an opening that runs off its wall.

**Tier AMBER**, and it **moves up the queue on measured grounds**: unlike D49's
half it has a worked example that reached a user as a crash, and no cost
objection standing against it.

## Receipt

*(Open.)* Acceptance: opening `fixtures/wiscaway2026-08-08.json` reports its I7
**at the load boundary, on a default launch, with no environment variable set**
— and a clean plan opens silently. The fixture must still fail I7 afterwards
(`test_the_wiscaway_fixture_is_still_dirty_in_exactly_the_way_that_matters`),
because the check is the fix, not the plan.
