# 0264 — report: his review of 0263 — the item callouts are the items' document ids, on when a plan opens; the measure gets its four knobs (move, rotate about the other, slide the end, slide the label); folded into PR #87's one commit; AMBER

**Code, 2026‑10‑12.** No merge has happened since
[`0263`](0263-report.md) put his four features on `annotations-measure`
(PR #87, AMBER). His review:

> *"1) The "Items callouts" are intended to be the Item Names (IDs) that
> I see in the dialog box when I double click a wall, not the
> measurements of the rooms. We want to show all items on a floor at
> once. This helps the use identify where the issue is when a plan is
> opened and you zoom to a problem. This should be enabled when the plan
> is opened. The user can then uncheck it later. 2) The "Measurements" is
> formatted fine. The select box on the measurement needs to be tight
> around the item. There needs to be 4 selection "knobs" one on each of
> the callout lines that let me drag the. [the spec, with his picture]
> ... The annotation tool and the show menu look fine for now. I will
> come back to that and tune it up later."*

Both built and folded into `annotations-measure`'s one commit (amended,
force-pushed); PR #87 stands, AMBER. The checkout is on it.

## 0. THE CALLOUTS ARE THE DOCUMENT IDS

**What the dialog shows, and what the report names.** The wall dialog's
"Id" row showed the wall's session uid (`W7`) — minted when first read,
never saved. The *Malformed design file* report names the DOCUMENT's
ids (`w89`, `o54`), the ones the validator reads, and its rows zoom to
them. For his purpose — "identify where the issue is when a plan is
opened and you zoom to a problem" — the plan must say the document's
ids, so that is what the callouts say, and the dialog now says the same
(`document_id(item)`: the stamped document id, the session uid only
before any walk).

**Where the ids come from.** A load stamps every item with its record's
id from the file (`doc_id` on walls, corners, openings, rooms,
furnishings, roofs) — the ids the report would name for that file. After
an edit the settle's own walk (the undo snapshot, one walk, not a
second) hands back `ids_out`, `{id(live): [document ids]}` — the ids the
NEXT save writes — and `stamp_document_ids` writes them onto the items;
a wall the walk splits at junctions carries every segment's (`w7/w8`).
Nothing is computed per paint.

**What is drawn.** Every item of the active floor, in the callout ink:
a wall's id and name beside its body (set clear of it, on the side away
from the length label a selected wall keeps); each corner's id and name
at the corner; an opening's id before its size code; a room's id under
its name; a furnishing's under its footprint; a roof's at its ridge's
middle. The wall's LENGTH is no longer a callout: it draws as it always
did, on the selected or drawing wall only.

**On when a plan opens.** `show_callouts` defaults to true, and
`_finish_open` sets it true whatever the file says — the user unchecks
it for the session. (`SETTINGS_VERSION` stays 3; the default's change
moved the fingerprint pin.)

## 1. THE MEASURE'S FOUR KNOBS

Selected, a measure shows four red knobs and nothing boxed around it —
its bounds and hit shape are the line, the callout lines and the label,
the label's box turned with the line. His spec, item by item:

* **a)** the drag-and-drop creation is as it was; on release the gadget
  is highlighted with its knobs.
* **i) knobs 1 and 2** at the callout points: drag one and that point
  moves — up, down, left, right — snapping as the tool snaps (the datum,
  a corner, a jamb, a wall), the line following, parallel to the new
  pair.
* **ii) knob 3** at the line's far end: drag it along the line and the
  far point slides along the measure's own direction, on the grid; the
  direction and the offset stay.
* **iii) knob 4** on the label: drag it along the line and the label
  slides (`label_t`, saved with the record, absent = the middle).
* **iv) Ctrl on knob 1:** the measure rotates about knob 2 — the length
  kept, the angle snapped to the plan's rotation step (15° by default),
  knob 2's callout at its fixed length and orthogonal (the offset is
  unchanged, so it is by construction).
* **v) Ctrl on knob 2:** the roles flip; knob 1 anchors.
* **vi) Shift:** free — no angle snap on a rotate, no item snap on a
  move.

The body drag still slides the measure along its own normal (the offset).

## 2. TESTS

`tests/test_annotations.py` (16): the callout is the document id in the
ink while the layer is on and nothing while off; the ids are stamped by
a load and by the settle's walk; the layer is on when a plan saved with
it off is opened; a selected measure shows the four knobs and its bounds
are tight; knobs 1 and 2 move their point; Ctrl rotates about the other
knob on the snap, flips, and Shift frees; knob 3 slides the end on the
grid and knob 4 slides the label, saved and read back.
`test_config.py`'s pin moved with the default. `--quick` passed; the
full gate GREEN on the amended commit.

## 3. WHAT HAPPENS NEXT

His check of PR #87. The annotation tool and the Show menu are "fine for
now" — his word that he will tune them later is on the record.

**Carried:** unchanged from [`0263`](0263-report.md).
