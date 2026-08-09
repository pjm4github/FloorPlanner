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

### RULED BY PATRICK, 2026‑08‑08. Outcome ratified, FRAMING REJECTED.

**The outcome stands: `farmplaceBIGmultifloor.json` is NOT to be repaired, and
the exemption stays.** But the reason it stays is not the one recorded on
2026‑08‑07, and the difference matters enough to strike the old wording rather
than annotate around it.

**~~Deferred as a FEATURE, 2026‑08‑07.~~ STRUCK.** *Overlapping rooms are an
**UNMODELLED STATE**, not a feature.* Calling them a feature would let the next
reader treat the **area double-count** as intended behaviour — and it is not
intended by anything; it is [D55](0055-area-totals-double-count-overlapping.md),
filed the same day off exactly this plan's arithmetic. A "deferred feature" is
something the product has decided to do later. This is something the model
cannot currently say, which a drawing works around with a slit, and which the
totals bar then silently miscounts.

**And the file is VALUABLE, not merely tolerated.** It is now the **only plan
in the tree that exercises overlapping rooms**, and A1 has just demonstrated
that overlap is a state the app genuinely reaches — `room_boolean` exists to
resolve it, `fragment` is the operation that does, and
`fixtures/fragment2room.json` reaches it by ordinary drawing. A plan holding a
state the app can produce and the model cannot express is the most useful input
this validator has. **Repairing it would delete the only evidence.**

*(Provenance, since the previous ruling named no author and was asked to: the
2026‑08‑07 deferral arrived in `83a3ccc`, whose own message says the five
attempted repairs "each change what the plan MEANS, **which is the author's
call**" — Code declined to choose a repair and then deferred the whole question
anyway. Git authorship settles nothing; every commit here carries Patrick's
identity. That deferral was therefore Code's and unratified. **This section
replaces it and is Patrick's, dated 2026‑08‑08.**)*

**The two halves below survive the reframing unchanged**, and are worth
separating when picked up.

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

**Half 1 has a second consumer as of 2026‑08‑08.** [D49](0049-i11-overlapping-placed-rooms-the-corruption-this.md)'s
amendment requires a save-time report naming the rooms **and the overlap area**.
I11 emits a boolean from three terms and no number, and on *this* file the true
polygon intersection is **0.0 sf** — so the honest report and the correct
predicate are the same piece of work, and it is half 1.

## Receipt

*(Open.)* Acceptance for half 1: these two files pass `check(deep=True)`
unchanged, and `planc1.v5.json` still fails I6 — the validator must not be
weakened into accepting them by accident. Acceptance for half 2 is a design
question, not a test.
