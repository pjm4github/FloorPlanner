---
# permanent key, independent of GitHub
id: 52
title: "Room-inside-a-room has no representation, and I11 misreports the workaround"

# maps directly onto GitHub Issues fields
state: open
state_reason: null
labels:
  - type:gap
  - area:schema
milestone: null

# ours; becomes body prose after migration
opened: 2026-08-07
closed: null
closed_by: null
rank: 53
related: [41, 48, 49]
state_source: row
github_issue: null
---

# D52 — A room inside a room cannot be expressed, and I11 misreports the workaround

## Symptom

`examples/farmplaceBIGmultifloor.json` fails `check()` with:

    I11 rooms 'Lounge' and 'Toi' overlap

It does not overlap. The file is exempted in `tests/test_schema.py`'s
`KNOWN_UNCLEAN`, which points here.

**`roundedMultifloor.json` had the same fault and no longer does** — Patrick
reshaped the two rooms on 2026-08-07 so they no longer nest, and it came off the
exemption list the same day. That is the cheap answer where the drawing can
absorb it, and it is why this record is a **deferred feature rather than a bug
queued for repair**: the plans that need room-in-room are the ones where
reshaping is not acceptable, and there are not many of them yet.

## Mechanism

**`Toi` is a WC fully enclosed inside `Lounge`.** Measured: its four walls close
properly (every consecutive pair shares a `Vertex` object), and the four probe
points around it — left, right, above, below — all fall inside Lounge.

**A single-ring outline cannot express a hole**, so the drawing carves the
closet out with a **zero-width slit**: Lounge's ring runs into the closet,
around it, and back out along the same segment, revisiting three vertices
(`v14`, `v16`, `v19` in the rounded file). The *area is right* — 366.8 sf =
394.9 − 28.1 — so the geometry says exactly what the drawing means.

**I11 then misfires on the workaround.** Its overlap test is:

    if _pip(cb, pa) or _pip(ca, pb) or cross:

where `ca`/`cb` are **vertex averages**, not area centroids. Measured on the
farmplace file:

| | |
|---|---|
| `_pip(cb, Lounge)` — is Toi's centre in Lounge? | **False** |
| edge crossings between the two rings | **none** |
| `_pip(ca, Toi)` — is Lounge's "centre" in Toi? | **True** |

Lounge's vertex average is (912.5, 821.3), which lands **inside the closet**,
dragged there by the six slit vertices clustered around it. A vertex average is
not a centroid for any non-convex ring, and for a slit ring it can land in the
hole. That single term is the whole failure.

## Evidence

Every repair attempted, and what each produced:

| attempt | result |
|---|---|
| de-spur Lounge to a simple 12-ring | Lounge now genuinely **contains** Toi — I11 still fires, plus 4× I6 |
| drop the `Toi` room record | 8× I6 dangling `r17` sides, I8 — and furnishing `f8` is a **toilet**, which would become a Lounge furnishing |
| shrink Lounge to the face its walls enclose | 366.8 → 181.9 sf, orphans the upper band, cascades I6 |
| the schema's `holes` field | I11 reads `outline` only, so it still fires — and nothing implements holes |
| open/re-save through the app | outlines come from the scene by design (P1.4); the slit survives verbatim |

`detect_room` returns the *same* 210 sf face from both rooms' anchors, so the
detector cannot separate them either.

## Ruling

> **ATTRIBUTION, added 2026‑08‑08 because the ruling below named no author and
> was asked to.** Traced on disk rather than assumed: the record and its ruling
> arrived in `83a3ccc`, whose own message says the five attempted repairs "each
> change what the plan MEANS, **which is the author's call**" — i.e. Code
> deliberately declined to choose a repair. **So the deferral is CODE's, made
> from measurement, and it has never been ratified by Patrick.** The only act in
> this file recorded as his is the `roundedMultifloor.json` reshape, which
> `83a3ccc` names him for explicitly. Git authorship settles nothing either way
> — every commit in this repository carries his git identity, including the ones
> Code writes.
>
> **It therefore reads as ruled and is not.** Deciding that room-in-room is a
> deferred feature rather than a bug is a scheduling call about a plan someone
> drew, and it is his. **Treat the paragraph below as a PROPOSAL awaiting
> ratification**, and the exemption in `KNOWN_UNCLEAN` as resting on it.

**Deferred as a FEATURE, 2026-08-07.** Not scheduled, not a bug to fix now: the
one plan that still needs it is exempted and named, and the workaround
(reshaping so rooms do not nest) is available and was used once already. Two
independent halves, worth separating when it is picked up.

1. **I11's centroid is wrong regardless of this plan.** A vertex average is
   cheap and not a centroid; a true area centroid, or a real polygon-overlap
   test, would clear these files **without touching them**. This is the same
   family as D41 — an invariant meeting a non-simple ring and reporting the
   wrong thing — and it is the half worth doing first, because it is a fault in
   a *deep check that caught the real planc1 corruption* and is currently
   reporting a fault that does not exist.
2. **Room-in-room has no representation.** `holes` exists in the schema and is
   implemented nowhere — not in the outline model, not in `detect_room`, not in
   the invariants, not in either viewer. Until it is, a slit is the only way to
   draw this, and every consumer has to understand slits.

Both were left alone on 2026-08-07 rather than guessed at: the repairs above
each change what the plan *means*, which is the author's call and not a
tool's.

## Receipt

*(Open.)* Acceptance for half 1: these two files pass `check(deep=True)`
unchanged, and `planc1.v5.json` still fails I6 — the validator must not be
weakened into accepting them by accident. Acceptance for half 2 is a design
question, not a test.
