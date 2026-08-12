# 0010 — ruling: furnishings

**On the census in [`0010-census-furnishings.md`](0010-census-furnishings.md).**
**Nothing starts until Patrick's Phase 6 park-or-finish answer.** These settle the
shape so that when work begins it does not begin with an argument.

---

## A THIRD OF THE CATALOG RENDERS AS A BOX

**28 of 95 items** name a form that is recognised and not built, so they are
drawn as a default box. That is the sentence that sizes this work, and it is
recorded here, at the top, deliberately.

---

## Order of value — ruled from the census numbers, not from preference

### ONE — the `prism` generator

**Extrude the symbol's real SVG outline.** It is already recognised by
`KNOWN_FORMS`, used by nothing, and **consumes data that already exists for every
item** — the plan symbol, whose viewBox is already in inches at the item's true
footprint.

**Largest 3D uplift per unit of work in the project, and it needs no new
authoring at all.**

> **MEASURE FIRST: how many of the 28 fallback items have an outline `prism`
> could actually use?** Not every symbol is a single closed path — some are line
> art, some are several disjoint shapes. **That number sizes the win before
> anything is built**, and it is the read-back this item opens with.

### TWO — the remaining form generators, in descending item count

The census already has the counts. Take them in order and **stop when the
remainder is not worth a function**:

| form | items | |
|---|---:|---|
| `vehicle` | 10 | |
| `enclosure` | 7 | |
| `seat` | 6 | |
| `bed` | 4 | |
| `basin` | 1 | ← likely below the line |

### THREE — parameterisation

**35 of 95 names carry a size**, and four families are pure size variants
(`Base Cabinet` ×2, `Pantry` ×3, `Wall Cabinet` ×3, `Vanity Base` ×2).

**Collapsing those is worth more than any tool for adding entries, because it
shrinks the catalog while widening its coverage** — a parameterised cabinet
covers widths nobody thought to enumerate.

**This is a READ-BACK before implementation.** It touches the catalog format and
therefore **every consumer**: the palette, the plan symbol's viewBox, the 3D
`build_model`, the manifest, `groups.json`, and the saved documents that name a
`kind`.

### FOUR — AI-assisted symbol drafting

**Last, for a measured reason.** The mechanical floor is already **two edits and
one command**, so a tool competes against **artwork judgement, not against
effort**.

---

## THE AI RULING — AUTHORING TIME ONLY

**On disk before anyone builds toward it.**

> **A tool drafts an SVG body from a description; Patrick reviews it; it is
> committed as data and is deterministic thereafter. IT DOES NOT RUN AT PLAN
> TIME.**

Three reasons, each independently sufficient:

* **geometry entering a document must be determined and checkable** — the whole
  invariant apparatus assumes the document says what it means;
* **two users asking the same thing must get the same result**;
* **an offline desktop application must not need a network to place a chair.**

**The prices action is the precedent for the MECHANISM** — ask, parse strictly,
apply — and it already exists end to end (`catalog.py`: provider list, stored
key, prompt builder, strict parser, applier).

**The difference is what the output IS.** Prices produce **a number in a field**;
this produces **geometry**. So it goes through **review and a commit**, not
straight into the catalog.

---

## Sequencing

**Nothing starts until Patrick's Phase 6 park-or-finish answer.** When it does,
item ONE opens with its measurement — *which of the 28 have a usable outline* —
and not with code.
