# 0230 — report: the wall-properties dialog — double-click a wall, edit its name, type and end points corner by corner; names are document fields; built on `wall-properties`, stacked on `design-problems`

**Code, 2026‑10‑10.** No merge has happened since
[`0225`](0225-report.md). His word, in full because every sentence of it
is a requirement:

> *"I need a new feature that opens a dialog box when I double click on a
> wall. The dialog box should show all the properties of the wall. The
> wall end points should be editable. The wall name and x/y (in inches/
> or feet and inches) should be editable on a Vertex by vertex basis. The
> should be a checkbox that is on be default that shows enables all other
> walls (and room definations) that touch that virtex are updated when
> the dialog box is OKed (accepted). If the user cancels the dialog box
> then it will revert to the settings that the wall had before the edit
> box opens. I will evenntually want to show the wall in profile including
> the windows when the box is open. You dont need to build a profile view
> at the moment, but make room for that."*

Built on `wall-properties`, stacked on `design-problems` (itself on
`parallel-walls-6in`, PR #77). Three branches now wait on his check; one
PR. Pushed, no PR of its own.

## 1. WHAT IT DOES — his sentences, one by one

| his sentence | what was built |
|---|---|
| *a dialog box when I double click on a wall* | `WallItem.mouseDoubleClickEvent` opens `WallPropertiesDialog` (`floorplanner/wallprops.py`). The press before a double-click had armed a drag; it is disarmed. |
| *show all the properties of the wall* | name, type (the seven, with their standard thickness), thickness, length (feet-and-inches and inches), heading, level, the rooms it borders, its openings with their positions, any other document field it carries (`thickness_in`, finishes), its id |
| *end points editable … name and x/y … on a vertex by vertex basis* | a row per end: the corner's name, X, Y, and beside them the same point written feet-and-inches, live. A plain number is inches; `10'6"` is feet-and-inches — the macro language's own rule |
| *a checkbox, on by default: every wall and room touching that vertex is updated on OK* | **on**, a moved end RELOCATES its corner — the same `relocate_corners` path a corner drag and Align to grid use — so every wall end and room outline holding it moves with it, and it stays one corner; **off**, the end DETACHES onto a new corner and the sharers stay |
| *cancel reverts* | nothing is written until OK: the dialog edits its own fields and `apply()` runs only on accept. OK is one undo step. |
| *room for a profile view* | `WallProfileView`, a widget in the dialog that holds the wall and its openings' spans and paints a placeholder bar with the openings marked, saying it is not built. The elevation drawing goes in there without the layout changing. |

OK refuses, with the field named, a length it cannot read and a wall
that would come out shorter than `MIN_WALL_LEN`.

## 2. WHAT THIS ADDS TO THE DOCUMENT — said because it is a format change

Walls and vertices had no name. **The v5 schema gains one optional field
on each, `name` (string), omitted when empty.** `Design.Wall` and
`Design.Vertex` carry it; `canonicalize` leaves it on the row; a wall's
rides the round trip in `_v5_extra` exactly as `thickness_in` does; a
corner's lives on the live `Vertex` (`vertex.py`, one new slot), is
carried by a relocation (the corner keeps its identity) and dropped by a
detach (a new corner), and is matched back onto the walk's vertex rows
by position at the table's own weld tolerance (`bridge._name_rows`),
since the walk rebuilds those rows from coordinates. Renaming a corner
renames it for every holder, because there is one corner.

Every document without names is unchanged byte for byte; the corpus and
the round-trip identity tests pass unmodified. **This is the one
decision in the tranche that is a schema decision, and it is his to
reverse** — the alternative was to show the ids read-only, which his
sentence does not say.

## 3. THE RECEIPT

`tests/test_wall_properties.py`, 22 tests: the length rule (eight
spellings; four refusals); the sheet's contents on a square of four
shared-corner walls with a room; **OK with the box on** moves the corner
for the other wall and the room's outline, still one corner, the room
still closed, the corner's name seen from the other wall; **OK with the
box off** moves this wall's end alone and the corner splits; **Cancel**
leaves the snapshot byte-identical; a bad length and a vanishing wall
refused with the field named; a type change takes; **the double-click**
delivered as real mouse events opens the sheet on that wall and OK is one
undo step; **the names round-trip** through `design_from_scene` →
`apply_design_to_scene` → `design_from_scene`, schema-valid, the second
document equal to the first, an unnamed vertex carrying no `name` key;
a relocated corner keeps its name and a detached end does not.

Wall, room, group, io, bridge, model and schema suites green; `ruff`
clean; the full gate is the branch's own run.

## 4. NOT IN IT, named

* The profile view itself (his word: not yet).
* Thickness override and finishes are shown, not edited.
* Opening placement is listed, not edited — each opening has its own
  sheet on double-click already.

## 5. STATE

Three stacked branches, one PR: `parallel-walls-6in` (#77) ←
`design-problems` ← `wall-properties`. `main` is this commit.

**For his check:** double-click a wall. Change p2's X to `20'6"` and OK
— the joined wall and room follow. Undo. Do it with the box off — only
this wall moves. Cancel after editing — nothing moves. Save, reopen —
the names are there.

## 6. `fixtures/incoming/`, with ages

Empty.

## 7. WHAT HAPPENS NEXT

His check of the three; his word on landing them — in turn, or folded
into #77. Behind them: the status board, the evidence re-shot.

**Carried:** unchanged from [`0229`](0229-report.md).
