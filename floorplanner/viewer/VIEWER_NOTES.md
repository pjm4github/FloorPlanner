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
* **Colour comes from three tables** near the top of `fp3d.py` — `WALL_C` by
  wall type, `FLOOR_C` by room category, `FAMILY_C` by furnishing material
  family. But see the palette caveat in §5: **these values are tuned for
  `fp3d`'s baked flat shading and read much darker under Qt Quick 3D's PBR
  lighting.** The palette is renderer-dependent; that is a finding, not a bug.
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
   alongside its 2D symbol; `FURN`'s box dimensions become the fallback and the
   placement bounds. This is the largest remaining item and it is an asset
   problem more than a code one.
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

An **offline render** path (export glTF, render headless in Blender/Cycles for
presentation images) remains open and would share `build_model` too. That is the
reason to keep that function Qt-free and renderer-agnostic no matter what
happens above it.

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
  `elevation_in` but nothing spans between them.
* Furniture rotation is honoured; furniture *elevation* is not (everything sits
  on the level's floor — no wall-mounted or counter-top items).
* Room `holes` in the schema are ignored.
* Door leaves, swings and window frames are not drawn — an opening is a void.
* `fp3d.py --shot` grabs the framebuffer after three `processEvents` calls,
  which is adequate for a smoke check and not a reliable regression instrument.
* `fp3dq.py` has no view presets (the pyqtgraph viewer's T / F / S / I / R) and
  no `--xray`, `--edges`, `--obj` or `--dump`; it is a presentation view, not a
  replacement CLI.
* Neither viewer has any test coverage. `build_model` is pure and headless and
  would be straightforward to pin — outline degeneracy handling and
  `opening_span`'s three anchor cases are the obvious first assertions.
