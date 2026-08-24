# 0100 — ruling: one visible wall number, and click-a-row-to-find-it

**Patrick:** *"I need to have the Wall numbers on the display and the Wall
numbers on the report match and further more when I click on a row in the report
and the repair orthogonality and the coalesce walls I want the wall to be
highlighted on the canvas so I can find them."*

**Both accepted. The first cannot be met the obvious way, and the third surface
is not the same change as the other two.**

---

## 1. THE IDS CANNOT BE UNIFIED — and the tree says why, in its own words

`design/canonical.py`:

> *"**ids, renumbered in geometric order.** Without this they encode emission
> order. `design_from_scene` visits the scene's walls; the importer visits the
> file's; `apply_design_to_scene` turns each split segment into its own wall and
> so reorders the next walk. **Same plan, three different id assignments.**"*

`design/bridge.py:1139`: *"those are canonical (renumbered by geometry at every
save), and a live uid is persistent. **P3.1 settled that the two id spaces stay
separate** and `canonicalize` bridges them."*

> ### THE DOCUMENT ID IS GEOMETRIC SO THAT THE SAME PLAN COMPARES EQUAL WHOEVER EMITTED IT. THAT IS LOAD-BEARING FOR THE CENSUS, THE GOLDEN FILES AND EVERY CORPUS COMPARISON IN THIS PROJECT.
>
> **Making one id serve both jobs breaks canonicalisation. Not ordered, not
> negotiable.**

**So the direction is forced, and only one direction is available:** the report
already pays for a full `design_from_scene` lift and can keep the
document-id → `WallItem` correspondence as it builds. **The status bar cannot** —
computing a document id live is the per-event `Design` lift P3.4 forbids on the
edit path.

**RULED: the REPORT adopts the number the user can see.**

```
W7 · w19 (interior) at (46.50, 35.50) -> (48.00, 34.00)ft — 45.00deg off axis
```

**`W7` is the session uid and matches the status bar — that is Patrick's
requirement.** `w19` stays beside it because it is the durable reference: the
one in the saved file, the census, the exports and every defect record.
**Neither is redundant; they answer different questions.**

## 2. THE THREE SURFACES ARE NOT THE SAME CHANGE — measured

| surface | today | what it needs |
|---|---|---|
| **Wall orthogonality report** | `OrthogonalityReportDialog(self).exec()` — a modal block of text | row list + selection |
| **Repair preview** (PR #37) | already lists moved / refused | row list + selection |
| **Coalesce all walls now** | **not a dialog at all** — `normalize_walls()` runs, then a `QMessageBox` summary | **a preview it does not have** |

> ### COALESCE ACTS FIRST AND REPORTS AFTER. THERE ARE NO ROWS TO CLICK BECAUSE BY THE TIME THE TEXT APPEARS THE WALLS ARE ALREADY MERGED.
>
> Giving it clickable rows means giving it a **preview** — *"these runs will
> merge"* — before it acts. **That is a change to what the command does**, not a
> dialog tweak, and it is the shape the repair dialog already has. **Worth
> doing, and it is its own item.**

**`Review wall gaps…` is the fourth of this family** and already interactive
(*"the user closes chosen pairs one at a time"*). **It gets the same treatment or
it becomes the odd one out** — named, and I would take it.

## 3. MODALITY — the part that is easy to miss

`.exec()` is **modal**: the canvas is unreachable while the dialog is open, so a
highlighted wall cannot be looked at. **These dialogs become modeless
(`.show()`)**, and that is a real behaviour change with real consequences:

* the document can be edited underneath an open report — **the report must
  either refresh or say plainly that it is a snapshot taken at a time**;
* a wall a row names can be deleted while the row still points at it — **a dead
  reference must degrade to "no longer present", not raise**;
* headless callers pass `interactive=False` already (`_report`'s convention) and
  **must keep working**.

## 4. ONE WIDGET, NOT FOUR

Four dialogs listing walls with click-to-select is four chances to diverge —
**this project's whole recurring fault in UI form.** **One wall-row list widget:
it takes `(WallItem, text)` pairs, and clicking a row selects the item and
centres the view on it.** Each dialog supplies rows and nothing else.

## 5. READ-BACK FIRST, AND IT IS OWED BEFORE ANY CODE

* the `WallItem` ↔ document-id map: where it is built, how long it stays valid,
  what happens when the scene changes under it
* whether centring the view on click is wanted, or selection alone
* the dead-reference behaviour of §3
* whether Coalesce gains a preview **in this item or its own**
* what `Review wall gaps…` does

## 6. TIER

**AMBER throughout** — every part changes what the user sees.

**And it goes in front of PR #37's check**, which
[`0098`](0098-ruling.md) §2 already blocked for the same reason: **a preview
naming walls Patrick cannot find is not checkable.** §1's label is the minimum
that unblocks him; §2–§4 are the feature he asked for.

**Order: §1's label, then the shared widget on the report and the repair
preview, then Coalesce's preview, then gaps.**
