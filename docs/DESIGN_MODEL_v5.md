# Design model v5 — the room is the durable unit

**Supersedes `DATA_MODEL_v5.md` / `plan-schema.v5.json`** (moved to `docs/_superseded/`). That draft made a room a *face* of the wall complex, so a room existed only while a closed loop of walls existed. This revision inverts the dependency:

> **A room owns its outline. Walls are an optional binding onto the edges of that outline.**
>
> Delete a wall → the edge's `wall` becomes `null`. The room keeps its shape, area, name, schedule properties and every furnishing it owns.
>
> **Vertices are the only place coordinates live.** Move a wall → its two vertices move → every room and wall referencing them follows. Nothing to synchronise, nothing that can drift.

---

## 1. The model

```
levels[]      id, name, elevation_in, height_in, kind: storey|site
vertices[]    id, level, x, y                  ← THE ONLY COORDINATES IN THE DOCUMENT
walls[]       id, level, v1, v2, type, thickness_in?, left, right,
              finish_left, finish_right, openings[]
rooms[]       id, level, name, category, outline[], holes[], placement{},
              area_accounting?, nominal_size?, label, properties
furnishings[] id, level, kind, room|null, pos, rotation, state{}
groups[]      id, level, name, members[], rotation
```

The outline is the load-bearing idea:

```jsonc
"outline": [
  { "v": "v12", "wall": "w7"  },   // corner v12; wall w7 runs v12 → v13
  { "v": "v13", "wall": null  },   // corner v13; OPEN edge — no built fabric here
  { "v": "v14", "wall": "w9"  }
]
```

One structure carries the room's geometry (area = shoelace of the corners, perimeter = sum of edge lengths, corners = the vertices), its enclosure state (which edges are built), and its binding into the plan (which walls it shares). Traversal direction is derived from `wall.v1 == e.v`, never stored, so it cannot desync.

`wall.left` / `wall.right` are a **maintained index** — the O(1) answer to "which rooms does this wall bound", plus the hook for per-side finishes and door swing. They must agree exactly with the outlines that name the wall (I6). With x right and y down, `left` is the `(dy, −dx)` side: the side on your left walking v1→v2 on screen.

**There is no `open` wall type and no `OpenWall` class.** An edge with `wall: null` *is* the open edge — which is exactly the v4 gap that corrupted your file (§6).

---

## 2. The five workflows

### A. A room with furnishings, a name and dimensions, as a movable unit

`placement.state: "floating"` is a **declared and checked** claim. I12 requires that no wall on the outline serves a second room and no vertex it uses is touched by any wall outside it. That is precisely the condition under which the room can be translated, rotated or duplicated by touching only its own vertices — nothing else in the document can notice. `nominal_size` records the typed intent ("8 × 4 raised bed"); the outline stays authoritative. Furnishings name the room via `furnishing.room`, so they travel with it.

### B. Walls shared with other rooms

Two rooms name the same wall id on the edges facing each other; the wall's `left`/`right` hold the two room ids. One wall, one geometry, two rooms. In `symmetricP1.json`: 62 walls shared by two rooms, 20 bounding one.

### C. Draw walls → label rooms → add furnishings

Drawing snaps each endpoint onto a nearby vertex and splits any wall it crosses, keeping the graph planar. "Label this room" traces the enclosing face of the wall graph around the click and writes it as the outline with every edge bound. Faces of a planar subdivision are disjoint, so rooms created this way **cannot overlap**. That is not hypothetical — `migrate_to_design_v5.py --clean` does exactly this and resolved 19 of your 20 rooms straight out of the wall graph.

### D. Move a room and its contents to open canvas

**Extract** privatizes the room's walls and vertices (`placed → floating`), then **move** translates it. The destination needs no walls at all. Contrast with today, where `Rooms ▸ Refresh rooms (drop unwalled)` (`mainwindow.py:589‑593`) literally **deletes** any room that isn't enclosed.

### E. Move a wall; adjoining rooms resize  ← *new*

This is the one the vertex model exists for. Moving a wall is **moving its two vertices**. Both adjoining rooms' outlines reference those same vertices, so both resize; the perpendicular walls meeting at those corners stretch or shrink because they reference them too. Demonstrated on the real file (`tools/demo_move_wall.py`, no arguments needed):

```
wall w24  exterior  (186,864)-(396,864)   left=Lounge  right=Front Porch
move by (+0, +12) -- editing exactly 2 vertices (v23, v25) and nothing else

  room             before sf  after sf    delta
  Front Porch          689.9     672.4    -17.5  <-- resized
  Lounge               190.8     208.2    +17.5  <-- resized
  ...all 18 others unchanged...
  TOTAL               4474.5    4474.5     +0.0

after the move -- JSON Schema: PASS   Invariants: PASS
```

No room record was touched. No wall record was touched. No area was recomputed and stored. Two numbers changed.

**The one rule that needs care — the split rule.** If a wall *collinear* with the one being dragged continues past an endpoint, moving that vertex would shear the continuation. The operation must first split: insert a new vertex at the old position, leave the continuation on it, and re-point the dragged wall at a fresh vertex. Symmetrically, if a drag brings a vertex onto another wall's body, that wall splits at the new vertex to restore planarity. Both are pure topology edits the schema already expresses; neither touches a room record beyond the outline entry whose `v` changed.

**Openings survive the resize** because they are anchored to a named end (`{"from": "v1", "offset_in": 12}`). A door dimensioned 12″ off the north corner stays 12″ off the north corner when the wall lengthens. Dimension it from the other end and it tracks that end instead — which is the choice an architect actually makes on a drawing, and which v4's absolute `s` could not express at all.

---

## 3. Landscape: beds and lawn zones are rooms

Confirmed as the model. A planting bed, lawn zone, patio or gravel court is a `room` with `category: "site"`, so it gets an area, a perimeter, a schedule, ownership of its plants, and the same extract/move/duplicate behaviour as any interior room. No new object type.

| Landscape thing | v5 representation |
|---|---|
| Planting bed, lawn zone, patio, gravel court | `room`, `category: "site"` |
| Fence, hedge, retaining wall, railing | `wall`, `type: fence` / `hedge` / `retaining` / `railing` |
| Gate | `opening`, `kind: "gate"` — the **only** opening kind the schema permits in a landscape wall |
| Unfenced boundary between two zones | outline edge with `wall: null` |
| Plants, benches, planters | `furnishing`, owned by the zone via `furnishing.room` |
| A bed you are still positioning | `category: "concept"`, `placement.state: "floating"` |
| Site plan as its own layer | `level.kind: "site"` |

Schedule fields for site rooms sit alongside the interior ones in `room_properties`: `surface`, `plant_palette[]`, `irrigation`, `sun_exposure`, `slope_pct`, `drainage`, `edging` (the landscape analogue of baseboard). Landscape walls carry no `finish_left`/`finish_right` — the schema rejects them.

**Overlap is checked within a class, not globally** (I11). `interior` + `exterior` form one class — a porch may not overlap a bedroom. `site` is its own class, so a lawn zone may legitimately run beneath a deck. `concept` is exempt entirely, which is what makes shuffle mode safe.

**Area rolls up by `area_accounting`** — `conditioned` / `unconditioned` / `site` / `excluded` — defaulted from `category` and overridable per room. `symmetricP1.json` sets Garage explicitly to `unconditioned`, which is why its conditioned total is 2,367 sf rather than 3,235 sf.

`examples/site_demo.json` is a working 60′ × 40′ garden proving it holds: a patio, a rose bed, a lawn and veg beds (2,400 sf, exactly the site area, no gaps and no overlaps), a perimeter fence with a gate, a retaining wall shared by the rose bed and lawn, a hedge shared by the lawn and veg beds, three unfenced boundaries as open edges, and an 8′ × 4′ "Trial Bed" floating as a concept room. Schema PASS, invariants PASS.

---

## 4. Operation semantics (specification, not implementation)

**Delete a wall `w`.** For every outline edge where `edge.wall == w`, set it to `null`. Delete `w` and its openings. Drop vertices no wall and no outline still uses. *No room changes shape, loses its name, or loses a furnishing.*

**Move a wall.** Apply the split rule at each endpoint, then translate the two vertices. Affected rooms = those whose outline references either vertex (an O(1) lookup against a derived vertex→rooms index).

**Bind / unbind an edge.** Bind: an edge whose two corners coincide with a wall's endpoints may name that wall; update `left`/`right`. Unbind: set `null`; update `left`/`right`. Both O(1) and reversible.

**Extract a placed room** (`placed → floating`):
1. Bound edge whose wall has two rooms → copy the wall (new vertices, openings copied), leave the original with the neighbour, point the edge at the copy.
2. Bound edge whose wall serves only this room → give the wall fresh vertices of its own.
3. Any remaining outline vertex still touched by an outside wall → replace with a private copy.
4. `state = "floating"`, `extracted_from = <level>`.

I12 then holds by construction. The plan keeps every wall it had.

**Move / rotate a floating room.** Transform every vertex used only by this room's outline and private walls, and every furnishing whose `room` is this room. Increment `placement.rotation`. Closed operation — no neighbour can be dragged, no wall can tear.

**Join / place a floating room**, the inverse: weld outline vertices onto plan vertices within `vertex_weld_in`; merge private walls that have become coincident with plan walls (dedup openings) and re-point the edges; split any plan wall a new vertex lands on; recompute `left`/`right`; `state = "placed"`; run `auto_coalesce` **only over the touched degree-2 vertices**.

**Shuffle mode** (`settings.editing.shuffle`) forces `auto_coalesce`, `auto_weld` and `auto_bind` off. Floating rooms drag past and through each other and through the plan without merging, welding or silently binding. Leaving shuffle mode auto-joins nothing — the user joins rooms explicitly.

**Duplicate a room.** Copy the outline onto fresh vertices, copy private walls and openings, copy furnishings with new ids and the same relative offsets, `state = "floating"`. A one-room design file is therefore a room template, and the schema already validates it.

---

## 5. Invariants

Thirteen checks, all O(n) except I5b and I11 which are O(n²) in room count and belong on save/import rather than after every command. `tools/validate_design.py` implements all of them.

| | Invariant | Prevents |
|---|---|---|
| I1 | Ids unique document-wide | Aliasing |
| I2 | Every reference resolves, to the same level | The cross-floor leaks (`_WallIndex`, `weld_all` have no floor filter today) |
| I3 | `wall.v1 ≠ wall.v2` | Degenerate walls |
| I4 | **No two walls on one `(level, v1, v2)` pair** | The coincident-copy explosion — structurally impossible |
| I5 | Outline is a closed loop of same-level vertices; each bound wall spans exactly that edge | Rooms with no shape; torn loops; walls bound to the wrong edge |
| I5b | Outline is a simple polygon | Self-intersecting perimeters (what the flood-fill trace produced) |
| I6 | `left`/`right` agree with the outlines naming the wall | Drifting bidirectional refs — **the check that caught your file** |
| I7 | Openings fit their wall, don't overlap; only gates in fences/hedges/railings/retaining | The seven `except ValueError: continue` sites that silently delete a door, including on load |
| I8 | `furnishing.room` exists, same level | The `pos()` vs `scenePos()` disagreement between `rooms.py:651` and `dialogs.py:36` |
| I9 | Group members exist, share the level, no nesting | Cross-floor groups |
| I10 | No orphan vertices | Leaks from delete/undo |
| I11 | **No two `placed` rooms of the same overlap class overlap** | Overlapping rooms — while letting a lawn run under a deck and letting concept rooms sit anywhere |
| I12 | A `floating` room is genuinely independent (no shared wall, no shared vertex) | A "movable unit" that would silently drag a neighbour |
| I13 | `concept` rooms are floating; site levels hold only `site`/`concept` rooms | Category drift |
| I14 | **The document is welded** — no wall end sits within `vertex_weld_in` of another wall's body or end without being that same vertex | Unwelded corners and half-attached T-junctions. This is what makes weld-on-load a *legacy-only* operation (§7) |

---

## 5a. Two tolerances, and why they must not be the same number

v4 conflated these, which is how a 1.5″ gap ended up saved in a file.

| | `vertex_weld_in` = **0.6″** | `join_tol_in` = **9.0″** |
|---|---|---|
| What it is | **Modelling precision.** Two coordinates this close *are* one vertex. | **Gesture tolerance.** How close the user must get before the editor offers to weld. |
| Where it applies | Invariant I14 — a document violating it is malformed | Interactive drag-release, and the one-time legacy import weld |
| Can it be relaxed? | No. It is a statement about representation. | Yes, freely. It is a statement about aim. |

A wall deliberately stopping 6″ short of another — a reveal, a pilaster gap, a shadow line — is a legitimate design. **Nothing may silently close it**, which is why I14 uses 0.6″ and not 9″. And under v5 an intentional gap is harmless: rooms carry stored outlines, so a gap no longer leaks a flood-fill into the next room the way it did in v4.

---

## 6. Results on your data

| | `planc1.v5.json` (faithful) | `symmetricP1.json` (cleaned) | `site_demo.json` |
|---|---|---|---|
| Outlines from | stored `perimeter_corners` | traced from the wall graph | authored |
| Vertices / walls | 65 / 83 | 62 / 82 | 14 / 14 |
| Rooms | 20 | 20, all **placed**, 0 open edges | 5 (4 placed + 1 concept) |
| Openings | 39 | 39 | 1 gate |
| JSON Schema | **PASS** | **PASS** | **PASS** |
| Invariants | **23 errors** — preserves the source's corruption | **PASS** | **PASS** |

The faithful migration is the regression fixture: it proves the converter does not launder its input.

### The M Bath divider was never missing — it was 1.5″ short

`--clean` now runs a **weld pass** reproducing `WallItem.join_endpoints` (`walls.py:948`) as a one-time operation: an endpoint within 2″ of another endpoint snaps onto it, and an endpoint within `JOIN_TOL = 9.0″` of another wall's *body* is extended along its own axis to meet it, forming a real T-junction.

Your file is full of divider walls that stop at y = 655.5 instead of reaching the corridor wall at y = 654 — a **1.5″ gap**. The editor welds those on every draw release and on load, but the welded coordinates are never written to the file. So the saved centreline graph stays open, the flood-fill leaks between spaces, and room detection produces garbage.

**31 endpoints welded.** The results:

| Room | before | after |
|---|---|---|
| M Bath | 591.6 sf, 24 corners, self-intersecting, swallowing Great Room and Hall | **182.0 sf, 11 edges** |
| Hall | 243.5 sf, 18 corners (the two spaces merged) | **61.5 sf, 9 edges** |

19 of 20 rooms now trace directly from the wall graph; the Garage keeps its stored outline but every edge still resolves to a real wall, so it has **zero open edges**. No wall was invented and no room needed the concept-room fallback.

House total: 4,474.5 sf — 2,367.0 conditioned, 2,107.6 unconditioned (Garage, Front Porch, Rear Porch).

**Two stacked duplicate doors removed.** The source has *three* identical 60″ doors at exactly `s = 356.0` on one 564″ exterior wall — the signature of coalesce absorbing openings without dedup (finding #8 of the code review).

**This weld gap is a live bug, not just a data problem.** Every plan the app has ever saved has it. Whatever replaces `serialize()` must write welded coordinates, or add the weld to the load path and mark the document dirty.

---

## 7. Files

| File | Role |
|---|---|
| `floorplanner/design/design-schema.v5.json` | The design-file JSON Schema (2020-12). `format: "floorplanner-design"`, `version: 5`. Vendored into the package at P0.7 (pointer: `docs/design-schema.v5.md`). |
| `docs/DESIGN_MODEL_v5.md` | This document. |
| `tools/migrate_to_design_v5.py` | v1–v4 → v5. Default = faithful; `--clean` = weld, re-trace outlines, repair. |
| `tools/validate_design.py` | Schema + all thirteen invariants + a derived area/perimeter/accounting report. |
| `tools/demo_move_wall.py` | Proves workflow E: move a shared wall, both rooms resize, document still valid. |
| `tools/make_site_demo.py` | Generates the landscape example. |
| `provenance` block | Written by `--clean`; see §7b. |
| `examples/symmetricP1.json` | The cleaned design. Passes everything. |
| `examples/site_demo.json` | Landscape design — beds, lawn, patio, fence + gate, hedge, floating trial bed. |
| `examples/planc1.v5.json` | Faithful migration — the "does not launder its input" fixture. |
| `examples/planc1.json` | **Unchanged** legacy v3 corruption fixture. |

Suggested test wiring:

```python
def test_symmetric_p1_valid():   assert validate_design.check(load("symmetricP1.json")) == []
def test_site_demo_valid():      assert validate_design.check(load("site_demo.json")) == []

def test_faithful_migration_preserves_corruption():
    errs = validate_design.check(load("planc1.v5.json"))
    assert any(e.startswith("I6") for e in errs)      # must not silently repair

def test_clean_welds_and_repairs():
    doc, rep = migrate(load("planc1.json"), clean=True)
    assert validate_design.check(doc) == []
    assert rep["endpoints_welded"] == 31
    assert 175 < area_of(doc, "M Bath") < 190        # not 591

def test_move_wall_resizes_both_neighbours():
    doc = load("symmetricP1.json")
    before = areas(doc)
    move_wall(doc, "w24", 0, 12)                     # two vertices, nothing else
    after = areas(doc)
    assert validate_design.check(doc) == []
    assert sum(after.values()) == pytest.approx(sum(before.values()))
    assert len([k for k in after if after[k] != before[k]]) == 2

def test_v5_files_are_welded():                       # I14 -- no weld on load
    for f in ("symmetricP1.json", "site_demo.json"):
        assert [e for e in validate_design.check(load(f)) if e.startswith("I14")] == []

def test_i14_is_not_vacuous():                        # nudging a shared corner apart
    doc = load("symmetricP1.json"); split_a_shared_vertex(doc, by=0.3)
    assert any(e.startswith("I14") for e in validate_design.check(doc))

def test_legacy_import_records_provenance():
    doc, _ = migrate(load("planc1.json"), clean=True)
    assert doc["provenance"]["endpoints_welded"] == 31
    assert any("M Bath" in n for n in doc["provenance"]["notes"])

def test_delete_wall_keeps_room():
    doc = load("symmetricP1.json")
    delete_wall(doc, "w24")
    assert area_of(doc, "Lounge") == 190.8           # unchanged
    assert validate_design.check(doc) == []          # open edge is legal
```

## 7a. DECIDED — the weld runs on load, and legacy files open dirty

Confirmed. The spec:

**Opening a legacy v1–v4 `floorplanner-json` file:**

1. Parse to the legacy structures.
2. **Weld** at `join_tol_in` (9.0″), reproducing `WallItem.join_endpoints` (`walls.py:948`): an end within 2″ of another end snaps onto it; an end within 9″ of another wall's *body* extends along its own axis to meet it.
3. Planarize — split every wall at each junction and crossing.
4. Trace room outlines from the wall graph around each label anchor; fall back to the stored `perimeter_corners`, with unresolved edges left `wall: null`.
5. Convert openings from absolute `s` to `{from, offset_in}`; drop stacked duplicates.
6. Assign each furnishing an owning room.
7. Write `provenance` (§7b) and **mark the document dirty**.
8. Tell the user plainly — not a silent repair. Something like:

   > *Converted from the v3 format. 31 wall ends were welded to close gaps the old format could not store. 2 rooms changed size as a result: M Bath 591.6 → 182.0 sf, Hall 243.5 → 61.5 sf. 2 duplicate doors removed. Save to keep these corrections.*

The user can then Save (accept), Save As (keep the original), or close without saving (nothing on disk changes — the legacy file is never modified in place).

**Opening a v5 file: no weld pass, ever, and never dirty on open.** This is guaranteed rather than assumed: I14 asserts the document is already welded at `vertex_weld_in`, and the validator runs on load. A v5 file that fails I14 is a bug in whatever wrote it, and should be reported as a malformed document rather than silently re-welded.

That asymmetry is the whole point of promoting "welded" from a hopeful post-condition to a checked invariant.

### 7b. `provenance` — the audit trail

Because the load-time weld moves real coordinates, the converted document records what happened, written once at import and never mutated. It is stable, so it is safe inside the dict equality used for the dirty flag.

```json
"provenance": {
  "migrated_from": { "format": "floorplanner-json", "version": 3 },
  "tool": "migrate_to_design_v5.py",
  "mode": "clean",
  "endpoints_welded": 31,
  "openings_deduped": 2,
  "notes": [
    "Hall: stored 243.5 sf -> traced 61.5 sf",
    "M Bath: stored 591.6 sf -> traced 182.0 sf",
    "2 stacked duplicate opening(s) removed"
  ]
}
```

Six months from now, "why is M Bath 182 sf when the old file said 591?" has an answer inside the file.

Native v5 documents carry no `provenance` block.

---

## 8. Still open

1. **`nominal_size` vs drawn.** Worth surfacing "drawn 11′-6″ vs intended 12′-0″" in the room properties dialog, or purely a creation aid?
3. **Site levels vs one shared level.** `site_demo.json` puts the garden on its own `site` level. If you would rather draw the garden on the same level as the ground floor, I11's class separation already allows it — but then `level.kind` stops carrying the distinction and `room.category` does all the work. Worth deciding before the importer is written.
