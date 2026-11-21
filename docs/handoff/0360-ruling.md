# 0360 — ruling: the dormer edge-ordering table is the case list; build one review image per BUILDABLE row, keyed by its ID

**Reviewer (Cowork), 2026-11-21.** A new piece of spec work, on Patrick's
word; it answers no report. Read with
[`../DORMER_EDGE_ORDERINGS.md`](../DORMER_EDGE_ORDERINGS.md) (new, untracked,
in the tree) and [`../DORMER_CONTROL_SPEC.md`](../DORMER_CONTROL_SPEC.md).
Code lands the table and this ruling by path. Not run by me: anything — no
gate, no pytest, no build of any case.

**Tier: evidence only.** One generator script, design files, PNGs and an
index under `docs/evidence/`. **No product code changes under this ruling**
(§7).

## 1. What Patrick asked for

Four plan edges position a dormer on its host roof:

> "A represents the host roof eave, B represents the dormer eave over the
> dormer face, C represents the face wall on the dormer and D represent the
> wall on the level under the dormer that the host roof sits on."

Each edge has a plan distance from the dormer anchor (apex). The table lists
every ordering of the four, ties included: 75 rows, `W01`–`W75`. The work is
three stages, and **only stage 1 is owed now**:

1. **This ruling.** Build an example design and a picture for each buildable
   row, so Patrick can check by eye that the four edges sit where the row
   says.
2. **Patrick's, later.** He adds a rules column to the table: what the face,
   balcony, cantilever, roof skirt and floor-under-balcony do for each row.
3. **A later ruling.** Code goes through the dormer code against those rules,
   using the same cases.

The IDs are the thread through all three:

> "I want the example test cases to reference the ID in the table so that I
> can manually look that over."

## 2. Which rows are built

- **Build every row whose `Buildable` is `yes`: 26 rows.** The table lists
  their IDs under "Buildability".
- **Build nothing for a row marked `no`.** No design, no image. Patrick:

  > "mark the row as unbuildable with the reason for that marked in the
  > table. keep that row but dont build the roof/dormer that way."

- **The `Buildable` column is my reading, accepted by Patrick, and it is two
  rules only:** `D > A` (the host eave would be inside the LV1 wall) and
  `C > B` (the dormer eave would be inside its own face wall; spec R3a).
  Ties are buildable: a tie is a zero overhang.
- **If the code disagrees with the column, that is a finding, not a fix.** A
  `yes` row Code cannot build, or a `no` row the app builds happily: report
  the ID, the four numbers and what the app said. Do not bend a case to get a
  picture, and do not skip one silently.
- **Do not edit the table.** It is Patrick's document. A correction to it is
  a line in your report.

## 3. The base design — the same for every case

Patrick's words:

> "a simple gable dormer on a 1 level (LV1) floorplan with a 12-12 pitch roof
> on that LV1 that will become the host roof"

- One level, LV1. A plain rectangular plan. One gable roof on it at 12:12.
  That roof is the host.
- One **gable** dormer furnishing on the host, square to the host eave (no
  rotation), symmetric, everything not named here at its default.
- **Only the four distances change from case to case.** Choose the base
  dimensions once so that all 26 cases fit inside the limits the app already
  has (the anchor on the roof between eave and ridge; the dormer ridge not
  above the host ridge, [`0359`](0359-ruling.md); the dialog's caps). Say what
  you chose and why.

## 4. The four distances

- All four are measured in plan from the anchor, along the dormer's ridge
  direction toward the face. All four are positive.
- **Edges the row ties are EXACTLY equal** — the same number, not within a
  tolerance. **Edges the row separates differ by at least 12 in**, so the
  order is visible in the picture.
- My reading of how the edges map onto what exists, from the defaults in
  `dormer_geometry.py` — **unverified, confirm or correct it in the report**:
  `B − C` is `face_overhang_in`; `A − D` is the host roof's eave overhang
  past the LV1 wall; `A` is what `host_extent` / `host_eave_in` already
  carry; `D` is the LV1 exterior wall the P4 "wall below" probe finds.
- **State, for each case, how each of the four numbers was READ BACK from
  the built design** — not the number the script set. A case whose read-back
  does not reproduce the row's six pairwise relations (`A vs B` … `C vs D`)
  is a failed case: report it, keep its files, do not tune it until it
  passes without saying so.

## 5. What is produced — everything named by ID

All of it under **`docs/evidence/0360-dormer-orderings/`**:

| File | What it is |
| ---- | ---------- |
| `make_cases.py` | The one headless generator. It READS the table from `docs/DORMER_EDGE_ORDERINGS.md` (ID, ordering, `Buildable`) — it does not carry its own copy of the cases. Deterministic; re-runnable for stage 3. |
| `Wnn.json` | The design file for the case, loadable in the app. |
| `Wnn.png` | The review picture (below). |
| `INDEX.md` | One row per ID, all 75: ID, ordering, the four read-back distances, the app's own face classification (`dg.classify_face`), any findings the dormer raised, a link to the PNG — or, for a `no` row, the table's reason and no link. Last column `Patrick's check`, left EMPTY. |

**The picture.** One PNG per case, holding:

- the **plan view**, with the four edges marked `A`, `B`, `C`, `D` and their
  distances, and the anchor marked;
- a **3D view** of the same design, from a side that shows the dormer face,
  its eave, the host eave and the LV1 wall together;
- a caption: the ID, the ordering string exactly as the table writes it, and
  the four read-back numbers.

The `A`–`D` marks and the caption are drawn by the generator on the captured
image. They are not a product feature and nothing is added to the app to make
them.

**The app's face classification and findings are recorded as facts, not
judged.** Whether "cantilever" or "balcony" is the RIGHT answer for a row is
stage 2, and it is Patrick's.

## 6. Order of work — four cases first, then stop

1. **Read-back first.** Build these four and nothing else:
   `W01` (`A > B > C > D`, no ties), `W05` (`A > D > B > C`, the face set
   back inside the wall line), `W09` (`B > C > A > D`, the face past the host
   eave) and `W75` (`A=B=C=D`, everything tied).
2. **Report at the next free number and STOP.** The report carries: the base
   design and its dimensions, the edge mapping (§4) confirmed or corrected,
   how the picture is captured, the four cases with their numbers, and
   anything about the remaining 22 you already expect to go wrong.
3. **AMBER — Patrick's check.** He looks at the four pictures. Format and
   mapping are settled on four cases, not discovered on twenty-six.
4. **On his word, the other 22**, the full `INDEX.md`, and a second report.

## 7. What this ruling does NOT ask for

- **No change to `floorplanner/`.** If a case shows the dormer code doing
  something that looks wrong, that is exactly what the pictures are for:
  report it with its ID. It is fixed, if it is a fault, under a later ruling
  with Patrick's rule beside it.
- **No rules.** Do not decide what a row SHOULD do, and do not add a rules
  column.
- **No tests yet.** Stage 3 turns the cases into tests, once there are rules
  to assert.
- **`docs/DORMER_EDGE_ORDERINGS.xlsx` is superseded by the `.md`.** Patrick
  is deleting it himself. Do not commit it and do not read the cases from it.

## 8. Patrick's check (stage 1)

For each picture, against its row in the table:

1. The ID and the ordering in the caption match the row.
2. In the plan view, `A`, `B`, `C` and `D` are on the right edges: host eave,
   dormer face eave, dormer face wall, LV1 wall.
3. Their order outward from the anchor is the row's order, and tied edges
   coincide.
4. The 3D view shows the same arrangement as the plan.

A picture that passes gets his mark in `INDEX.md`'s last column. One that
fails goes back through the reviewer with its ID, not to Code directly.
