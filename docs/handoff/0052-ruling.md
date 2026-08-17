# 0052 — ruling: the export README lands at `docs/guides/`, the first user-facing doc in this project

**Patrick, 2026‑08‑17:** *"Where is the README for the export going to land?"*

**[`0038`](0038-ruling.md) §6 ruled the SPLIT and never named a destination.**
That is a gap in my own ruling, and this closes it.

---

## 1. MEASURED FIRST: there are no help docs to land it in

**Every document in `docs/` is agent-facing** — `README.md` (the map),
`ROADMAP.md`, `WORKING_AGREEMENT.md`, `V5_MIGRATION_PLAN.md`, `defects/`,
`progress/`, `handoff/`, `evidence/`, `superseded/`.

**No `help/`, `guide/`, `user/` or `manual/` directory exists anywhere in the
tree.**

> **Patrick's original instruction was *"incorporated into the help docs where it
> makes sense."* There are none. This is the first document in this repository
> written for someone USING FloorPlanner rather than building it.**

## 2. THE RULING — `docs/guides/chief-architect-export.md`

**A new `docs/guides/` directory, and naming the category is the point.**

**Not flat in `docs/`**, because every neighbour there answers *how is this
project built and governed* and this answers *how do I get my plan into Chief*.
**Mixing them makes the map wrong** — a reader looking for the agreement should
not have to step over a user guide, and vice versa.

**Not `floorplanner/export/README.md`**, because a user does not browse a package
directory for instructions. **The module already carries its developer docstring;
that is the right doc in the right place, and it is a different document.**

**`docs/README.md` gains one row** naming what `guides/` is for — it is the map,
and a directory the map does not know about is a directory nobody finds.

## 3. WHAT LANDS THERE, AND WHAT DOES NOT SURVIVE

| README section | disposition |
|---|---|
| **§1 integration task** — menu item, `convert()` call, config alignment | **DELETED. It is a spent handoff spec.** |
| **§2 what the converter emits** (rationale) | **guide** |
| **§3 the verified Chief X17 workflow, 16 steps** | **guide — the valuable half** |
| **§4 package contents** | **rewritten** for where things now live, or dropped |
| **§5 known limitations / future work** | **guide** |

**§1 is deleted rather than archived.** `docs/superseded/` exists *"because it
holds material found nowhere else"* — **§1 holds nothing found nowhere else**:
the API is in the code, the placement is in [`0038`](0038-ruling.md) §5, the
thickness decision is in [`0038`](0038-ruling.md) §3 **and** in the module's own
docstring. **A spent spec kept for reference is how `_superseded/` rotted the
first time.**

## 4. THE SCREENSHOTS STAY WHERE THEY ARE, AND THE GUIDE'S PATHS MUST BE REWRITTEN

**They are already at `docs/evidence/chief-export/`** — all 16, placed by the
agent — and they stay there. **They are the receipt for a workflow validated
against software this repository cannot run**, which is what `evidence/` is for.

> **THE TRAP, AND IT FAILS SILENTLY:** the README's links are
> `![…](screenshots/01-import-drawing-dialog.png)`. **From `docs/guides/` that
> path is wrong**, and a markdown image with a bad path **renders as nothing** —
> no error, no broken-link marker, just a guide that has lost its pictures.
>
> **Every one of the 16 links becomes `../evidence/chief-export/…`, and the
> report says it checked them.** `tools/ref_audit.py` reports dangling links and
> **does not enforce them** (*"a lint that fails on correctly-recorded history is
> a lint that gets disabled"*), so nothing will catch this for you.

**One copy, not two.** The guide links to the evidence; it does not get its own
duplicate of the images.

## 5. TWO THINGS THE GUIDE MUST KEEP VERBATIM

**The workflow settings whose wrongness is invisible** — *Create CAD Blocks
**OFF***, *Polylines **OFF***, *Boxes **OFF***, *"Chief Architect layers by
name" with "Import all layer attributes"*. **Get one wrong and CAD-to-Walls
silently does nothing or flattens every layer.**

**And the first-failure story** — both doors arriving as `2640DH` windows.
**That is not history, it is the explanation of why the door symbols look the way
they do**, and without it the next person "simplifies" the swing arc away.

## 6. AND ONE CORRECTION THE GUIDE NOW OWES

**§1's thickness table said `exterior 6.5` pairs with Chief's `Siding-6`.**
[`0038`](0038-ruling.md) §3 rewired the module to `STD_T`, so **the exported
value is now 6.0.**

**Wherever the guide states a wall type mapping, it states the CURRENT number**,
and — since Chief matches within ±1″ and 6.0 against Siding-6's 6 7/16″ is
**0.44″** — **it says that the pairing still holds and why.** A guide carrying
the old number is worse than one carrying none.

## 7. TIER

**GREEN** — documentation placement. **It changes no behaviour and needs no
check**, and it is separable from the AMBER menu item if the agent's PR wants
splitting.
