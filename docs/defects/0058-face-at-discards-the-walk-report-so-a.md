---
# permanent key, independent of GitHub
id: 58
title: "face_at DISCARDS the walk report, so a straddling opening is recorded and thrown away"

# maps directly onto GitHub Issues fields
state: open
state_reason: null
labels:
  - type:gap
  - area:geometry
milestone: null

# ours; becomes body prose after migration
opened: 2026-08-08
closed: null
closed_by: null
rank: 59
related: [57, 25, 49]
state_source: report
github_issue: null
---

# D58 — `face_at` discards the walk report

## Symptom

`face_at` calls `_walls_of`, which **detects** an opening that no wall segment
can hold and writes it into the report — the message and the id both:

    rep["openings_failed"].append(
        f"{oid}: {o['kind']} {o['code']} on the wall at ... is cut by a "
        f"junction -- anchored {round(off, 1)}\" from {frm}, and no segment "
        f"can hold it")
    rep["openings_failed_ids"].add(oid)

`face_at` passes a fresh report in, never reads it, and lets it fall out of
scope. **So the detection path knows about a broken opening and says nothing.**

## Mechanism

`bridge.py`, `face_at`: the report is an argument `_walls_of` requires, not a
result `face_at` wants. Before D57 it was `defaultdict(int)` — which is a fair
statement of the intent (*"I do not care about this"*) and is exactly why it was
never noticed that `_walls_of` **writes** to it rather than only counting.

The working caller, `design_from_scene`, takes `report=` from its caller and
surfaces it: `rep["openings_failed"]` reaches a user-facing warning
(`bridge.py`, the `%d opening(s) could not be placed` path) and
`openings_failed_ids` is read by `verify` to exempt an I7 that was properly
filed. **`face_at` participates in neither.**

## Evidence

Split out of [D57](0057-face-at-hands-walls-of-a-report-of.md) rather than
fixed with it, on the ruling that *a crash fix which also changes what gets
reported is two changes wearing one commit*.

Measured on `fixtures/wiscaway2026-08-08.json`, whose door `o29` straddles the
welded junction at `v90`:

| caller | sees the straddler? | says anything? |
|---|---|---|
| `design_from_scene` | **yes** — `openings_failed` has 1 entry | yes: warns, and `verify` reads the ids |
| `face_at` | **yes** — same branch, same message built | **no** — the report is discarded |

So the information exists at the moment the user clicks to name a room, and is
thrown away; the user then meets the same fault later, through
`check(deep=True)` on a save, or not at all.

## Ruling

*(Open — filed, not fixed. Deliberately.)*

**Not a straightforward "surface it".** Detection runs on a *gesture* — one
click of the Room tool — and `face_at` is also the one-shot lift used by CSV
import, paste, the macro `room` token and legacy load. Warning from all of them
on every click, for a fault the user may already know about, is a different
product decision from warning once when a document is written.

Three shapes, and the choice is not the code's:

1. **Return it** — give `face_at` an optional `report=` out-param, exactly as
   `design_from_scene` has, and let each caller decide. Cheapest, changes
   nothing by default, and does not answer *who* should speak.
2. **Speak at the gesture**, as P4.1b's doorway message does (`report_doorway_landings`)
   — the precedent exists and is the same family of fault.
3. **Leave it to the document boundary**, which is [D49](0049-i11-overlapping-placed-rooms-the-corruption-this.md).
   The strongest argument for this one is that **I7 is in the CHEAP TWELVE**, so
   a boundary check catches it without paying the deep set's cost — see D57's
   evidence.

## Receipt

*(Open.)* Acceptance depends on which shape is chosen. Common to all three: on
`fixtures/wiscaway2026-08-08.json`, the straddling opening is **reachable** from
the detection path rather than silently dropped — asserted by reading it, not by
the absence of a crash.
