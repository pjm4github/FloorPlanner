---
# permanent key, independent of GitHub
id: 49
title: "I11 - overlapping placed rooms, the corruption this migration was STARTED to fix - is reported"

# maps directly onto GitHub Issues fields
state: open
state_reason: null
labels:
  - type:gap
  - area:schema
milestone: null

# ours; becomes body prose after migration
opened: 2026-08-05
closed: null
closed_by: null
rank: 49
related: [34, 52]
state_source: row
github_issue: null
---

# D49 — I11 - overlapping placed rooms, the corruption this migration was STARTED to fix - is reported

## Record

> **Moved verbatim** from the register (`docs/CODE_REVIEW_v2.md`, the row at its
> line 114) on 2026-08-06 — not reworded, not split, not
> reformatted. The register wrote each row as one continuous argument in which
> symptom, mechanism, evidence, ruling and receipt are interleaved, so dividing
> it into sections would have meant interpreting it. See
> [`README.md`](README.md) for the section shape new records take.

**I11 — overlapping placed rooms, the corruption this migration was STARTED to fix — is reported nowhere in the shipped app.** Filed 2026‑08‑05 at the fragment ruling. Two facts compose into a hole neither has on its own: I11 is **deep-only** (`validate.py:248`, with I5b `:156` and I14 `:302`), so shadow mode's always-on twelve never runs it while editing; and shadow mode is **off by default** — `verify()` returns `None` unless `verify_enabled()` (`design/verify.py:210`) and `app.py:47` sets the env var only for `--verify-design`. So the save refusal that the deep set was supposed to backstop **does not happen on a default launch**. Measured on one corrupt scene, three ways: `FP_VERIFY_DESIGN` unset → **the save WROTE the file** carrying I5b ×1 and I11 ×3; `=1` → refused; `=deep` → refused. This is the invariant that caught the real `planc1.json` corruption (the 591 sf master bath overlapping two other rooms, §2 F5), and in the shipped product nothing would have caught it. **Proposed fix, to be scoped separately: run the DEEP set at document BOUNDARIES — load and save — regardless of shadow mode, and keep the cheap twelve for editing.** The cost argument that produced the split (P1.2: an O(n²) sweep per edit makes the app unusable) does not apply at a boundary crossed once per file; the plan's own words for the deep three are already "run on save, load and import — paid once, where the stakes are highest", which is a description of a design that was never wired to the default path. **It also repairs ruling 2a's premise**, which assumed a save refusal that does not happen.

## Amendment — ruled 2026‑08‑07, recorded 2026‑08‑08

**The Record above is the 2026‑08‑05 filing and is left verbatim.** This section
amends its proposal; where the two differ, this one is the ruling.

**CHECK YES, FIX NO.** Overlap is a symptom whose causes vary, and **no
automatic repair is defensible, because every option silently changes drawn
geometry**. The one repairable cause — a tolerance gap letting a fill leak — is
**already repaired by welding on load** (P2.1). What survives welding is by
definition not a tolerance artefact. **Same reasoning as [D34](0034-a-document-gap-in-the-0-6.md)'s
refusal to auto-close the (0.6″, 9.0″) band.**

**SAVE ASKS, IT DOES NOT REFUSE.** The original proposal said refuse. Amended:
**under deform-to-follow a drag can transiently overlap a neighbour, and a hard
refusal traps the user with unsaveable work at the worst moment.** Report, list
the offenders, and let the user decide.

**THE REPORT MUST BE ACTIONABLE.** Name the rooms **and the overlap area**, and
offer a way to reach them — **select and zoom**. Patrick's own question about
this file was *"why?"*, and a report that only names two rooms cannot answer it.

**DRIVING CASE: `examples/farmplaceBIGmultifloor.json`** — Lounge and Toi
overlap, the app allowed it and said nothing, and its author does not know how
it happened. **This moves D49 from a reasoned hole to a hole that bit.**

### One finding, measured before this was filed — and it is about the acceptance case, not the ruling

The ruling stands as written. But the driving case **cannot also be the
acceptance case**, and the reason is already on disk in
[D52](0052-a-room-inside-a-room-cannot-be.md): on this pair I11 is
**misreporting**. Toi is a WC fully *enclosed* by Lounge, drawn with a
zero-width slit because a single-ring outline cannot express a hole, and I11
fires only because its centroid is a **vertex average** that lands inside that
hole.

Measured 2026‑08‑08 — `docs/evidence/d49-farmplace-overlap-area.json`,
reproduce with the probe beside it:

| | |
|---|---|
| Lounge ring | 18 points, **366.8 sf** (already net of the closet: 394.9 − 28.1) |
| Toi ring | 4 points, **28.1 sf** |
| **true polygon intersection** (`QPolygonF.intersected`) | **0 points, 0.0 sf** |
| I11 `_pip(Toi centre, Lounge)` | False |
| I11 edge crossings | 0 |
| I11 `_pip(Lounge "centre", Toi)` | **True** — the entire failure |
| what I11 reports | `I11 rooms 'Lounge' and 'Toi' overlap` |

**Two consequences, and the second is the sequencing one.**

1. **The overlap area this ruling requires does not exist in I11 today.** The
   check emits a boolean from three terms and no number at all
   (`validate.py`, the `deep` block). Computing an honest area is new work — and
   on the driving case that number is **0.0 sf**, which cannot answer *"why?"*
   because there is nothing there to explain.
2. **A real polygon-overlap test IS D52's half 1**, which that record already
   names — *"a true area centroid, or a real polygon-overlap test, would clear
   these files without touching them"*. So the honest report and the correct
   predicate are the same piece of work; and **once it lands, farmplace stops
   firing I11 and produces no report at all.**

**None of this weakens the ruling.** `planc1`'s 591 sf master bath overlapping
two other rooms is a real overlap, it is why I11 exists, and it is exactly what
a save-time report would have caught. The correction is to the *test case*: the
acceptance plan should be **planc1**, with farmplace used the other way round —
as the case the report must be **silent** about once D52 half 1 is in. Building
the report on today's predicate would ship a message that tells this file's
author their rooms overlap by 0.0 square feet.

**Suggested order, for the read-back rather than as a decision:** D52 half 1
(the predicate) before D49's boundary wiring, or the two together. Taken in the
other order, the first thing the new report does is state a falsehood about the
plan that motivated it.

## MEASURED EVIDENCE FOR THIS RECORD, 2026‑08‑08 — from a crash, not from preference

**A real plan was saved carrying an I7 that nothing reported, and the user later
met it as a silent crash.** `fixtures/wiscaway2026-08-08.json` holds a 48″ door
straddling a welded junction; `check()` says so; nothing in the shipped app ever
ran `check()`. The chain — *saved dirty → nothing said → clicked to name a room
→ the process died with no message* — is broken at its first link by a check at
the save boundary and at its second by one at load. Full account:
[D57](0057-face-at-hands-walls-of-a-report-of.md).

**And the cheap half suffices for it.** Measured:

    check(deep=True)  -> ['I7  opening o29 runs off wall w90 ...']
    check(deep=False) -> ['I7  opening o29 runs off wall w90 ...']

**SO THIS RECORD SPLIT ON 2026‑08‑08.** The cheap-twelve half is
[D59](0059-the-cheap-twelve-never-run-at-a-document.md) — actionable, with a
worked example that reached a user as a crash and **no cost objection standing
against it**, because the cheap twelve are already deemed affordable per
mutation under shadow mode. **This record keeps the DEEP half**, whose cost
question stays open and whose report needs an overlap area that D52's half 1
must supply first.

**I7 is one of the CHEAP TWELVE.** This record is framed around the DEEP set,
and the standing objection to boundary checking has been the O(n²) sweep — an
objection that **does not apply to this instance at all**. Worth separating when
this is picked up: the cheap twelve at a boundary is nearly free and would have
caught this one.

**What this does not establish:** that a report would have been acted on, and
anything at all about the deep three, whose cost argument is untouched.

## Site

`design/verify.py` (`verify_enabled` gating), `planio.py:549,606` (the save path), `app.py:47`

## Milestone

**unassigned — scope separately, before Phase 5**
