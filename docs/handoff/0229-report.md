# 0229 — report: the "Malformed design file" report takes you there — a list of every violation, each one zooming the view to the place it names; built on `design-problems`, stacked on `parallel-walls-6in`

**Code, 2026‑10‑07.** No merge has happened since
[`0225`](0225-report.md). His word, with the screen (the message box on
opening a v5 file: *"This v5 file reports 2 invariant violation(s); it has
been opened unchanged. I6 wall w89 sides ['r20'] != outline users ['r13',
'r20']; I7 openings o54/o53 overlap on w127"*):

> *"I need a feature that lets me zoom into an area of a design that has
> been opened when I get an error. For example when I get this error I
> want to be able to click on the error items and have the tool take me to
> the point on the design and zoom in"*

Built on `design-problems` (stacked on `parallel-walls-6in`, PR #77 —
one AMBER PR at a time; land in turn or fold, his word). Pushed, no PR of
its own.

## 1. WHAT IT DOES

Opening a v5 file that fails `check()` no longer puts up a modal message
box with the first three violations run into one sentence. It opens a
**non-modal window, "Malformed design file"**, with the same head line
and **every violation as a row**. Selecting a row — click, arrow keys,
double-click or the *Zoom to* button — **switches to the level the
problem is on and fits the view to the place it names**, grown to at
least 10′ square with a 3′ margin so the surroundings show. A line under
the list says what was found (*"At o53, o54, w127 on level 'default'"*)
and, when a message names something the document does not hold, says
that too. The status line carries the first three as before, so a
scripted caller reads what it always did.

## 2. HOW IT KNOWS WHERE — one thing worth knowing

**A scene item does not carry the document's id.** `w89` in the message
is the canonical id, renumbered by geometry at every save
(`bridge.apply_design_to_scene`); a live `WallItem`'s uid is its own. So
the place is resolved **against the document that was opened**, not the
scene: `floorplanner/design/locate.py`, Qt-free, reads a vertex's
coordinates, a wall's two vertices, an opening's wall and anchor along
it (the same `from`/`offset_in` rule `fp3d.opening_span` uses), a room's
outline corners, a furnishing's position; a room named in quotes (I11)
resolves by name. Which ids a message names is
`validate._invariant_key`'s own rule, imported, so the two cannot drift.
The level comes back as its NAME, which is what `switch_floor` takes.

`MainWindow.zoom_to_spot(spot)` is the navigation itself, on the window
(in `planio.py`, which owns the open path), so a macro or a test can call
it without the dialog.

## 3. THE RECEIPT

`tests/test_design_problems.py`, sixteen tests. Qt-free: eight message
shapes placed on a synthetic two-level document (a wall, a vertex, an
opening on its own span — not its wall's, two overlapping openings, a
room by id and by name, a furnishing, a wall on the upper level); what
the document does not hold is reported in `Spot.missing`, not guessed; a
message naming nothing placeable gives None. With the window: a v5
document with two violations (an opening overlap on `default`, an orphan
vertex on `upper`) opens unchanged, the dialog lists both, selecting the
orphan's row switches to `upper` with the vertex in view, selecting the
overlap's row comes back to `default` with the openings in view; a clean
file opens with no dialog; and `fixtures/wiscaway-2level-stacked-floor.json`'s
one real violation (`I6 wall w90 …`, frozen into the fixture) is placed
and shown.

Full gate GREEN on the stack: see the branch's own run.

## 4. NOT IN IT, named

* The violations the SAVE path refuses on (*"Not saved: the plan has
  invariant violations"*, `planio.py`) still go to the status line only.
  The same dialog would serve, with `design_document()` as the document;
  his to order.
* The legacy *"Converted to the v5 format"* report is unchanged — a
  conversion report, not a list of places.
* Nothing is highlighted on the canvas beyond the zoom; a flash or a
  selection of the named items would need the id→item mapping the
  document does not give (§2).

## 5. STATE

`design-problems` stacked on `parallel-walls-6in` (PR #77, his check
pending), both pushed. `main` is this commit.

**For his check:** open the file from his screen; the window lists both
violations; click each.

## 6. `fixtures/incoming/`, with ages

Empty.

## 7. WHAT HAPPENS NEXT

His check of both; his word on landing them. Behind them: the status
board (read-back first), the evidence re-shot (his display).

**Carried:** unchanged from [`0228`](0228-report.md).
