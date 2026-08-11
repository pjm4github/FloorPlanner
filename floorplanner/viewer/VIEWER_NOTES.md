# floorplanner/viewer — notes

**What lives here:**

| file | role | needs |
|---|---|---|
| `fp3d.py` | the geometry core, plus a pyqtgraph/OpenGL viewer and the headless CLI | numpy; pyqtgraph + PyOpenGL only to open a window |
| `fp3dq.py` | the same model rendered by **Qt Quick 3D** — AO, shadows, PBR materials | PyQt6 QtQuick3D + QtQuickWidgets (both ship in the standard wheel) |
| `VIEWER_NOTES.md` | this file |

Both read v5 design documents directly. `fp3dq.py` imports `build_model` from
`fp3d.py` **unchanged** — see §5.

---

## 1. Architecture, and why it is split this way

`fp3d.py` has two halves and the seam between them is load-bearing.

| half | contents | depends on |
|---|---|---|
| **geometry** | `clean_ring`, `triangulate`, `parse_wwhh`, `opening_span`, `build_model`, `shade_faces`, `export_obj` | `numpy` only |
| **presentation** | `make_view`, `Plan3DWidget`, `main` | PyQt6, pyqtgraph, PyOpenGL |

`build_model(doc) -> Model` is the whole domain translation: v5 JSON in, a list
of coloured triangle meshes out. It imports no Qt, so it is testable headless
and runs in CI without a display. Everything below it is a renderer that can be
replaced without touching the part that knows what a wall is. **This has now
been tested rather than asserted** (§5).

**Nothing here imports `floorplanner`.** The viewers read saved JSON directly,
so they cannot affect the editor and cannot be broken by editor refactors. Note
the one wrinkle since the move into the package: `from floorplanner.viewer.fp3d
import build_model` transitively imports the whole editor, because
`floorplanner/__init__.py` star-imports every module in dependency order.
Running the files **as scripts** imports no parent package and keeps the
isolation; running `python -m floorplanner.viewer.fp3d` does not. Prefer the
script form, and set the PyCharm run configuration's working directory to the
repo root so relative paths like `examples/foo.json` resolve.

---

### The toggle boundary — settled 2026‑08‑11, before the control panel exists

**A toggle that changes WHICH GEOMETRY EXISTS is a `build_model` parameter. A
toggle that changes what is DRAWN from geometry already built is view-side.**
**Floor scope is the first kind** — `build_model` already takes `levels`, exactly
as it already takes `furnishings=False`, so the pattern is established rather
than invented.

**This is recorded here, beside the seam, because a filter written into either
shell would be wrong**: there are two renderers and **both import `build_model`
unchanged**, so a shell-side filter would scope one renderer and not the other.
The control panel ([D69](../../docs/defects/0069-an-auxiliary-control-panel-on-the-3d-view.md))
is presentation: it sets `build_model`'s parameters and **re-builds**; it does
not reach into meshes. Building it as a mesh filter is the obvious wrong turn and
this paragraph exists to prevent it.

**THE GENERAL FORM, which decides any toggle without re-arguing this:**

> **If turning it off would change the TRIANGLE COUNT, it is a parameter.**

So **openings are geometry** — they cut wall meshes, and hiding them changes what
`build_model` must produce, not what the shell draws. **Floors and furnishings
are geometry** and are already parameters (`levels`, `furnishings`). **A
wireframe or palette switch is view-side** — same triangles, drawn differently.

## 2. Conventions

* **Units are inches** throughout, per the v5 schema.
* **Plan coordinates are x right, y DOWN** (Qt scene). `fp3d`'s world flips y,
  so `world = (x, -y, z)` with z up. Without the flip the plan renders mirrored
  when viewed from above. Qt Quick 3D is Y-up, so `fp3dq` rotates once more on
  the way in: `(x, y, z) -> (x, z, -y)`.
* **Openings are dimensioned from a named end** (`anchor: {from, offset_in}`),
  never as an absolute distance from `p1`. `opening_span` resolves `v1` / `v2` /
  `center` to a span along the wall. This mirrors the schema's own reasoning:
  an offset from a named end survives the wall being stretched, split, or
  reversed; an absolute `s` survives none of those.
* **Colour has two sources, and the split is the point.** `WALL_C` by wall
  type and `FLOOR_C` by room category live in `fp3d.py`, because both are
  typed by the **document**. Furnishing colour does not: it comes from
  `assets/furnishings/materials.json`, keyed by the `material` name each
  catalog entry carries, and neither viewer states a furnishing colour,
  size, height or roughness of its own. See the palette caveat in §5:
  **these values are tuned for `fp3d`'s baked flat shading and read much
  darker under Qt Quick 3D's PBR lighting.** The palette is
  renderer-dependent; that is a finding, not a bug.
* **The furnishing catalog is READ, never restated.** `load_catalog()` reads
  `manifest.json` and `materials.json` as data — no `floorplanner` import, so
  the isolation above is untouched — and resolves them by walking **up** from
  the module to the directory holding `assets/`, so it works as a script, as
  an import, and from any working directory. A missing catalog is **reported**
  and the item drawn at a default box; it is never raised and never silently
  guessed. `fp3d.py` used to carry its own `FURN` table of footprints and a
  `FAMILY_C` of colours, and `fp3dq._pbr` its own roughness/metalness by mesh
  name. Both are gone: **58 of the 95 catalog kinds were missing from `FURN`
  altogether, and of the 37 it shared, 22 disagreed on footprint — three by
  transposing width and depth, so the item rendered rotated 90°.** A second
  definition of catalog data does not merely duplicate it; it drifts.
* **Every face is wound outward.** `_box` normalises the winding of whatever
  quad the caller hands it, and the floor builder emits top faces `+z` and
  bottom faces `-z`. This is not cosmetic: signed lighting renders an
  inward-wound face black, so the winding is fixed at source rather than
  papered over with `abs()` in the shading maths. Both renderers depend on it.

---

## 3. Hard-won: shaders in pyqtgraph

**The rule: do not write fixed-function GLSL for pyqtgraph.**

An earlier version of `fp3d.py` registered a custom shader using `gl_Normal`,
`gl_Color`, `gl_FrontColor` and `ftransform()` — the desktop fixed-function
convention that pyqtgraph's own older shaders use. It failed on a machine
reporting **OpenGL 4.6 / GLSL 4.60 on Intel UHD Graphics**, i.e. a fully
capable desktop context:

```
ERROR: 1:4: 'gl_Normal' : undeclared identifier
ERROR: 1:5: 'gl_FrontColor' : undeclared identifier
ERROR: 1:8: 'ftransform' : function is not known
sources = [b'#version 100\n', b'... my shader ...']
```

Recent pyqtgraph compiles shaders as **GLSL ES 1.00 (`#version 100`)** with
explicit attributes — `a_position`, `a_normal`, `a_color` — and uniforms for the
matrices, so that one source works on desktop GL, GL ES, and core profiles
alike. It does this regardless of what the driver could support. The
fixed-function identifiers do not exist in that dialect, so the capability of
the card is irrelevant.

Two consequences worth remembering:

1. **If a real shader is ever needed in the pyqtgraph path**, it must be written
   in pyqtgraph's attribute convention, matching the version header pyqtgraph
   prepends — not in classic desktop GLSL, and not in modern `#version 330 core`
   style either.
2. **A compile failure cannot be caught where the shader is registered.**
   Registration succeeds; compilation happens later inside `paintGL`, which is
   why a `try/except` around registration caught nothing and the console filled
   with repeated tracebacks. A guard has to live where the failure occurs.

**What `fp3d.py` does instead.** The key / fill / sky lighting rig is
deliberately *world-fixed* — the sun must not swim while you orbit — so it does
not depend on the camera and can be computed once. `shade_faces()` does the
arithmetic in numpy and hands per-face RGBA to `MeshData(faceColors=...)` with
`shader=None`. No GLSL is compiled, so no driver or pyqtgraph version can
refuse it. Because every surface in a floor plan is flat, a per-pixel shader
would compute the same value for every pixel of a face anyway; baking costs
nothing visually there. `--flat` falls back to pyqtgraph's own shader as an
escape hatch.

**GPU split in `fp3d.py`:** geometry and lighting are CPU, once, at load.
Transform, rasterisation, depth test and blending are GPU, every frame. Draw
calls stay flat as plans grow because meshes are merged by material family, so
the per-frame cost is pyqtgraph's Python loop, not the card.

---

## 4. What the viewers report, and why

`fp3d.py --dump` prints stats and a report; `-v` adds the routine items. The
severity split is deliberate and follows the same discipline as the editor's own
reporting:

* **notes** — things that could not be drawn as the document states them:
  degenerate outlines (repeated corners, zero-width spurs), partial
  triangulation, openings that do not fit their wall, unknown furnishing kinds.
* **info** — routine tidying that carries no meaning: collinear corners, which
  every split wall produces. Reporting these as faults would be crying wolf.

This has already paid: on `symmetricP1` it flags **WIC** for a zero-width spur
(the outline runs out to a vertex and back along the same line — zero area, and
it stalls ear clipping dead), and on the `planc1.v5` corruption fixture it
independently flags **Hall** and **M Bath**, the two rooms whose corruption
started the v5 migration. An unknown furnishing kind draws at a default size in
**magenta** rather than a plausible grey box, for the same reason: wrongness
should be visible.

---

### The viewer as a second opinion on the invariants

The viewer reads **the same documents the editor does** and fails **differently**,
and that difference is the whole reason `--dump` is worth running. The editor's
invariants ask *is this document legal*. The geometry pass asks *can this be
drawn* — and it must clean an outline before it can triangulate one, so it names
degeneracies no invariant is looking for. Two independent readers of one file,
failing on different things, is a check; two readers sharing a definition is not.

```
python floorplanner/viewer/fp3d.py <plan.json> --dump -v
```

**Anything listed under "needed attention" is a claim no invariant makes.** That
is the value and equally the limit: a clean `--dump` is not a legality verdict,
and a legal document is not necessarily a drawable one.

Standing results on the shipped corpus, reproducible with the line above:

| file | flagged |
|---|---|
| `examples/symmetricP1.json` | `WIC` — 1 zero-width spur |
| `examples/planc1.v5.json` | `Hall` 4 · `M Bath` 6 · `WIC` 1 |

All seven are **the same class**: a room outline that is non-simple by
*touching* rather than by *crossing*. `I5b` does not catch it — its
proper-crossing test is deliberately built **not** to fire on the collinear
edges two rooms legitimately share, and a loop that merely revisits one of its
own vertices is not a proper crossing. So these files pass `check(deep=True)`
on that invariant while being non-simple.

The measured instances, the reasoning, and the open question of whether a
touching loop is an `I5b` violation at all live in the register's row on
**non-simple outlines that `I5b` does not report** (`docs/CODE_REVIEW_v2.md`).
They are not restated here, and the row is referred to by description rather
than by number on purpose: it is filed on the P4.5 branch, and a number quoted
from here would be a broken pointer the day this branch merges first.

---

## 5. The renderer decision — settled 2026-08-04

**Two renderers, one geometry core. Both stay.**

`fp3dq.py` was written as a spike to compare Qt Quick 3D against pyqtgraph. It
worked on the first clean run, and the comparison resolved decisively.

### What was tested

`fp3dq.py` imports `build_model` from `fp3d.py` with **no modification** — same
call, same arguments. Everything renderer-specific is roughly 200 lines below
it. The geometry / presentation seam described in §1 was a design claim until
this point; it is now a measured one.

### What Qt Quick 3D gives that pyqtgraph cannot

Verified on screen against `symmetricP1.json`:

* **Real-time shadow maps** — wall shadows falling across floors from a
  consistent sun.
* **Ambient occlusion** — every wall/floor junction darkens. This is the depth
  cue that separates a diagram from a render, and it is the single largest step
  toward the "dollhouse" presentation images.
* **PBR materials** — `PrincipledMaterial` with roughness and metalness, so
  glass, porcelain and stainless read differently without hand-written shading.

All of it is **declarative**: `aoEnabled` plus three tuning numbers on
`SceneEnvironment`, `castsShadow: true` on the light. These are precisely the
things `fp3d.py` cannot reach without hand-written GLSL in the dialect §3
describes — which is the whole argument.

Performance was comfortable on Intel UHD integrated graphics at ~2,900
triangles with shadows and AO enabled.

### The split, and why both survive

| | keeps |
|---|---|
| **`fp3d.py`** | the geometry core (`build_model`, `clean_ring`, `triangulate`, the report), plus the headless CLI: `--dump`, `--obj`, `--list-levels`. None of it needs a GPU or a QML runtime, so it can run in CI or as a pre-commit check on a plan file. |
| **`fp3dq.py`** | the presentation view, and the intended basis for the in-app popup. |

Deleting `fp3d.py`'s viewer would cost the ability to inspect a plan on a
machine with no working GL, which is worth more than the duplication costs.

### Caveat found immediately: the palette is renderer-dependent

`FAMILY_C` and friends were tuned against `fp3d.py`'s baked flat shading. Under
PBR lighting with roughness ~0.85 and a single key light, the same values come
out **much darker** — beds, dressers and vehicles read as near-black slabs.
Either the two renderers need separate palettes, or the Qt Quick 3D path needs
a brightness compensation (raising base colours ~30–40% is the starting
experiment). Decide this deliberately; otherwise it gets rediscovered every
time the two are compared side by side.

### Remaining distance to the reference images

Now mostly **assets, not architecture**:

1. **Furniture as real models.** The catalog would carry a glTF per kind
   alongside its 2D symbol; the manifest's `width_in`/`depth_in`/`height_in`
   become the fallback and the placement bounds — they are already the single
   source, so nothing has to be reconciled first. This is the largest
   remaining item and it is an asset problem more than a code one.
2. **Textures.** Wood grain, tile, rugs, counters. Cheap once UV coordinates
   are generated, which for axis-aligned walls and floors is close to trivial.
3. **Materials from the document.** Drive colour from
   `room.properties.floor_finish` / `wall_finish` and `wall.finish_left/right`
   via a `FINISH_C` table keyed on the catalog's strings, with an unrecognised
   finish falling back *visibly*. Worth doing only once finishes actually vary —
   every room in `symmetricP1` currently says `Hardwood` / `Painted Drywall`, so
   today this would look data-driven while carrying no information.
4. **Better built geometry.** Mitred wall joins, door leaves and swings, window
   frames and glass, stair treads, countertops and cabinet runs. All derivable
   from the document as it stands.
5. **A cutaway camera.** The reference images are orthographic-ish dollhouse
   views with the ceiling removed — which is already the case here, since no
   ceilings are generated.

6. **The rest of the `form` generators.** Each catalog entry names a `form`;
   `build_solid()` builds `box` and `slab` (a top on legs), and every other
   recognised form — `seat`, `bed`, `basin`, `enclosure`, `vehicle`,
   `planting` — is built as a box and **said so in the report's info
   channel**, which is what makes this a known gap rather than a silent guess.
   A form nothing recognises is treated exactly like an unknown kind: box
   shape, magenta, named in the notes. The design for the two that matter is
   §5a below.

An **offline render** path (export glTF, render headless in Blender/Cycles for
presentation images) remains open and would share `build_model` too. That is the
reason to keep that function Qt-free and renderer-agnostic no matter what
happens above it.

### §5a — Better furnishing solids: two problems, two answers, and they are not the same one

Asked at the end of the `viewer-furnishings` branch (2026‑08‑05): *what has to
be in place before a `Car` is more than a box?* The answer splits cleanly in
two, and conflating them is the expensive mistake, because **one needs no
change to anything and the other changes the vertex format**.

#### (a) FLAT models — a faceted car of ~100 faces. Needs no structural change at all.

**`Mesh` does not change. No normals array, no UVs, no stride change.** §3's
argument holds facet for facet: every surface in a plan is flat, so lighting
baked per face costs nothing visually — and a low-poly faceted model is
*nothing but* flat surfaces. The baked per-face rig is not a limitation being
worked around here; it is the correct renderer for this class of model.

**The symbol already carries the geometry, and this is the finding.** A top
view extruded once (`prism`) gives a cookie-cutter: a car-shaped slab with a
flat top, because a top view carries no roofline. But the symbols are not
silhouettes — measured on `car.svg`, which is `72 × 180` inches:

| element | what it is |
|---|---|
| rounded rect `70 × 178`, `rx 16` | the body footprint |
| rounded rect `56 × 92` at y 50–142, `rx 9` | **the roof outline** |
| two cross lines at y 70 / y 122 | the pillars |
| two `7 × 4` tabs at x 0.5 / 64.5 | the mirrors |

It is already a **two-level contour drawing**. What it lacks is not artwork,
it is a **z for each outline** — so the uplift is mostly metadata, not
redrawing.

**The shape that fits is a LOFT between stacked rings**, not one extrusion:
body ring z 0→18; a skirt from the body ring up to the roof ring z 18→30,
whose sloped quads *are* the windscreen and the rear glass; roof ring z 30→56;
four wheels as short prisms. Flattening each rounded rect to ~24 points gives
~24 side faces per ring, ~48 triangles of skirt, plus caps and wheels —
**about 150 triangles per car**, which is the ~100 that was asked for.

**Cost, measured against what is on disk:** `symmetricP1` is 3,224 triangles
today; 50 furnishings at ~150 each puts it near 10,000. Qt Quick 3D was
comfortable at 2,900 with shadows and AO on Intel integrated graphics, and
`fp3d`'s per-frame cost is the Python draw-call loop, which **does not grow** —
meshes still merge by material.

**THE VIEWER MUST NOT PARSE SVG, and the reason is this branch's own history.**
An SVG is a data file, so reading one would not break the isolation rule — but
parsing arbitrary path syntax is a large new surface, and worse, it would make
the 3D profile a *second reading* of the artwork. That is exactly the drift
that put 22 wrong footprints and three transposed ones in the deleted `FURN`.
`_gen_assets.py` already holds the geometry as Python primitives
(`R(1, 1, 70, 178, 16, …)`), so **it emits the rings itself**, to a third
generated asset beside the other two:

```
assets/furnishings/profiles.json   {kind: [{z0, z1, material, ring: [[x, y], …]}, …]}
```

Rings already flattened to polylines, already centred in the item's local
frame, in inches. The viewer reads it exactly as it reads `manifest.json` and
`materials.json`. **The 2D symbol and the 3D profile then come from one
authoring statement and cannot disagree** — which is the whole point.

**What comes free, and is worth not re-deciding:** `triangulate()` already
ear-clips the caps and `clean_ring()` already reports a badly authored ring in
the same channel that reports a bad room outline; `vehicle` is already in
`KNOWN_FORMS` and already routes through
`build_solid(form, place, w, d, h, z0)`, whose `place()` carries rotation and
position so a generator thinks only in local axes — so **no new vocabulary and
no new dispatch**; and body/glass/wheels as separate rings with separate
materials emit separate meshes that the existing merge collapses **across**
items, so twenty cars still cost one body draw call and one glass draw call.

**The honest limit, recorded so nobody chases it through this door:** a contour
stack cannot give a curved windscreen or true wheel arches. It gives a
faceted, architectural-model car. That is the whole of what this design
delivers, and it is enough.

**Suggested order:** `profiles.json` for `car` alone (the two rings it already
has, plus wheels) → the `vehicle` branch in `build_solid` → fail-first receipt
(12 triangles → ~150, plus a test that the loft is a *loft*: the roof ring is
inset from the body ring at mid-height, the same discriminating shape as
`test_slab_is_a_top_on_legs`) → the rest of the vehicles → then `prism`, which
is this same machinery with **one** ring, for the flat-topped kinds: planters,
islands, L-shaped desks, round tables.

#### (b) SMOOTH models — glTF chairs and sofas. This one does change the vertex format.

Separated from (a) deliberately: the two look like one task and are not. Here
is the census, taken 2026‑08‑05 so the session that does it does not repeat it.

**`Mesh` is read at 9 sites, all inside these two files** — `fp3d.py`: the
bbox (`:687`), the triangle stat (`:693`), `export_obj` (`:703‑708`),
`make_view` (`:793‑809`); `fp3dq.py`: the entry loop (`:277‑284`). Nothing
else in the repo touches it, so widening it is a contained change.

**Two channels you would assume are missing are already plumbed.** Per-*face*
colour exists: `Mesh.color` is a BASE colour and `shade_faces()` returns an
`(M, 4)` array, one RGBA per triangle, to `MeshData(faceColors=…)`. Per-*vertex*
colour exists too: `_interleaved()` packs `pos(3) + normal(3) + colour(4)`
float32 per vertex and `scene.qml` sets `vertexColorsEnabled: true` — today the
producer fills it with one colour tiled. **Colour variation is not what gates
realism.**

**Three things do, and only the first is a real foreclosure:**
1. **Normals are flat, derived from winding.** Both renderers cross-product per
   triangle and repeat across its three vertices. A glTF supplies *smooth*
   normals and `Mesh` has nowhere to put them, so they would be **discarded on
   import** and the model would render faceted however good it is. This is the
   one place the present shape throws away information a real model carries.
2. **No UVs anywhere.** `_make_geometry` fixes a 40-byte stride with three
   attributes; textures need `UV(2)`, so stride 48, a fourth attribute, and a
   UV array on `Mesh`.
3. **One material per mesh — and here the current design is already right.** A
   sofa is fabric, wood and metal, so it emits one mesh per material, and
   merge-by-material then collapses them across items. The strategy that
   exists for flat plans is the correct one for multi-material models. No
   change.

Also: `export_obj` writes no material library, so the OBJ path already loses
colour. That function is the natural seam for a glTF *exporter* later.

**Do not widen `Mesh` speculatively.** A field nothing reads is the same
disease as a table nothing maintains, and it is how an abstraction gets shaped
for a consumer that turns out to want something else. Take (1) and (2) in one
commit, with a loader that consumes them, in the session that has a model to
load.

---

### In the app: the 3D popup (added 2026-08-04)

Right-click blank canvas -> **3D view...** opens the current plan in a modal
dialog. It embeds `Plan3DQuickWidget(model, ...)`, extracted from `fp3dq.main()`
for exactly this: the command-line tool and the popup render through **one**
widget and **one** QML document, so a fix to either reaches both and there is no
second implementation to drift.

**Read-only is the contract, not a courtesy.** The popup reads the document
from `design_document()` -- the same producer the save path writes -- and
touches nothing else. No file is written, no scene item changes, and the dirty
flag cannot move. The walk's unwelded-ends warning is suppressed for that one
call **on purpose**: that report belongs to the edit that tore the network, and
the 180 ms debounce walk owns the channel and will say so within a frame.
Opening a viewer is not an edit and must not speak in the edit channel.
Pinned by `tests/test_viewer_popup.py`, which asserts the dirty flag, the
document, the scene counts and the status line across an open, with any
warning promoted to an error.

**The surface-format constraint, and why it lives in `app.py`.**
`QSurfaceFormat.setDefaultFormat(QQuick3D.idealSurfaceFormat(4))` must run
**before the QApplication is constructed** -- Qt reads the default format when
the GUI application initialises, so setting it later is silently too late and
the scene renders without MSAA (or not at all). That single ordering fact
forces the call into `floorplanner/app.py:main()`, the one place guaranteed to
be earlier, and it therefore CANNOT move into the viewer where the rest of the
Qt Quick 3D code lives.

It is wrapped in `try/except ImportError`, and that guard is load-bearing: the
3D stack is an **optional** dependency, so an unguarded import at the app's
entry point would make `pip install -r requirements-viewer.txt` mandatory for
everyone just to launch the editor. With the guard, a machine without it starts
exactly as before and only the 3D view is unavailable -- and asking for it says
so ("3D view needs pip install -r requirements-viewer.txt") rather than raising
a `ModuleNotFoundError` into a Qt callback, which is defect 26's failure class.

A test asserts both halves on the source: the call precedes the QApplication,
and it sits inside an `except ImportError`.

## 6. Hard-won: Qt Quick 3D specifics

* **Geometry hand-off is an interleaved, non-indexed vertex buffer** through a
  `QQuick3DGeometry` subclass: position(3) + normal(3) + colour(4) float32,
  40-byte stride, vertices duplicated per face. Measured at ~347 KiB for
  `symmetricP1` across 12 meshes — trivial, but it is manual packing that
  pyqtgraph does not require (it takes `vertexes=` / `faces=` numpy arrays).
* **Colour semantics differ between the two paths.** `fp3d` uploads *pre-lit*
  colour (the rig baked in); `fp3dq` uploads *base* colour and lets the engine
  light it. Do not copy shading code between them.
* **Python objects must be kept alive manually.** QML holds no Python reference
  to the geometry objects handed over as context properties, so they must be
  parked somewhere (`win._keep = (...)`) or they are garbage-collected out from
  under the scene — empty view or crash. pyqtgraph needs no equivalent because
  `GLMeshItem` owns its arrays.
* **Plain dicts work as QML models.** A Python dict becomes a `QVariantMap`, so
  `modelData.geom` reads off it directly; the `QObject` + `pyqtProperty`
  wrappers the first draft used were unnecessary ceremony.
* **`pyqtProperty` is in `PyQt6.QtCore`** and imports fine; PyCharm's stub
  resolution flags it as unresolved. That is inspector noise, not an error.
* **`QQuickWidget` composites through an offscreen texture.** It works from
  Qt 6.4, but if the panel comes up black, a `QQuickView` in
  `QWidget.createWindowContainer` is the more reliable embedding — `fp3dq.py`
  has this behind `--container`.
* **`--check` before debugging anything else.** The likely failure is not the
  Python bindings but the `QtQuick3D` / `QtQuick3D.Helpers` **QML plugin
  directories**, which stripped Qt builds can omit even when the module
  imports. Verified present in the standard PyQt6 wheel.

---

## 7. Known gaps

* No ceilings, roofs, or floor-to-floor structure; multi-level plans stack by
  `elevation_in` but nothing spans between them. **And `elevation_in` is always
  0.0 — see the ruling below, which makes this line true and empty.**
* ~~Furniture *elevation* is not honoured.~~ **Closed.** Each catalog entry
  carries `elevation_in`, the height of the item's underside above the level's
  floor, and `build_solid` builds a wall-hung item exactly like a
  floor-standing one, higher up — no second code path. Eight items are off
  the floor: the three upper cabinets at 54″, `large_tv` at 42″,
  `electric_panel` at 48″, `car_charger` at 42″, `battery_wall` at 24″, and
  the counter-mounted `kitchen_sink` at 26″, whose rim then lands at 36″.
* Room `holes` in the schema are ignored.
* Door leaves, swings and window frames are not drawn — an opening is a void.
* `fp3d.py --shot` grabs the framebuffer after three `processEvents` calls,
  which is adequate for a smoke check and not a reliable regression instrument.
* `fp3dq.py` has no view presets (the pyqtgraph viewer's T / F / S / I / R) and
  no `--xray`, `--edges`, `--obj` or `--dump`; it is a presentation view, not a
  replacement CLI.
* ~~Neither viewer has any test coverage.~~ **Partly closed.**
  `tests/test_viewer_model.py` (11 tests, marker `viewer`) pins the catalog's
  3D data and what `build_model` does with it: every entry carries a usable
  `height_in`/`elevation_in`/`form`/`material`; every material named resolves;
  an unknown form falls back to a box **in magenta and is reported**;
  `elevation_in` puts an item off the floor, with a floor-standing control so
  the assertion discriminates; a missing catalog is reported rather than
  raised; and — in a subprocess, because this session has already imported
  both — `build_model` pulls in neither Qt nor `floorplanner`. The module is
  loaded **by path**, the way running it as a script loads it; importing
  `floorplanner.viewer.fp3d` would drag in the whole editor and quietly test
  something else. **Still unpinned, and still the obvious next assertions:**
  outline degeneracy handling and `opening_span`'s three anchor cases.

---

## 8. `--stack` is REFUSED — ruled 2026-08-07

**Measured first.** `--list-levels` over every plan available — Patrick's
two-storey `farmplaceBIGmultifloor.json`, a three-floor plan built by the app,
and the six other v5 examples — reports `elevation_in 0.0` and `height_in 96.0`
on **every level of every file**. The full reading is
`docs/evidence/viewer-floors-levels.txt`.

That is not a data accident. `model.Floor` carries `name` and `reference` and no
elevation at all, and all three writers emit literals (`bridge.py:796`,
`bridge.py:976`, `importer.py:184`). A non-zero elevation placed in a file by
hand is **destroyed** by a load/save round trip: in `108.0 / 108.0`, out
`0.0 / 96.0`. That is register **D50**.

**So the viewer is correct and stays as it is.** `fp3d` stacks levels by
`elevation_in`; every value it is handed is 0.0; every level therefore renders at
the same height. The renderer is faithfully drawing what the document says. The
fault is upstream, in the editor's floor model.

### Why a `--stack` flag is refused rather than deferred

A flag that spaces levels by an assumed storey height would have the viewer
**invent a number the document does not contain**. Three things follow, and the
third is the one that settles it:

1. It is a decision about the **model** wearing a renderer's clothes. What a
   storey height *is* belongs in `Floor` and in the document, where every
   consumer can see it — not in one renderer's argument list.
2. It would make the picture **stop being evidence**. §4's whole argument for
   `--dump` is that the viewer reads the same documents the editor does and
   fails differently; a viewer that supplies its own geometry can no longer be a
   second opinion about the first one's.
3. **The moment elevations are real, the flag becomes a way to disagree with
   them.** A plan whose storeys are 108″ apart, rendered with `--stack 96`,
   would be wrong in a way that looks deliberate.

### `--explode` is not refused — it is waiting

Separating levels along z for inspection is a legitimate *view* of a real
geometry: it exaggerates a distance rather than inventing one. It has nothing to
exaggerate until D50 closes, so it waits. When it lands, its argument is a
multiplier on real elevations, never a substitute for absent ones.
