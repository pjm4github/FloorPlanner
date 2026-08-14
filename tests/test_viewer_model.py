"""The 3D viewers' geometry core -- the first tests it has ever had.

WHAT THIS PINS, and why here rather than through the app: `build_model` is
Qt-free and imports no `floorplanner`, so it needs neither a QApplication nor
the editor.  The module is therefore loaded BY PATH, exactly as running
`python floorplanner/viewer/fp3d.py` loads it -- importing
`floorplanner.viewer.fp3d` would drag in the whole editor through the
package's star-imports and quietly test something else (VIEWER_NOTES.md s1).

The acceptance is that the CATALOG IS THE ONE SOURCE.  fp3d used to carry its
own table of footprints, heights and colours; these tests exist so it cannot
grow one back without something going red.
"""
import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest

pytestmark = pytest.mark.viewer

ROOT = Path(__file__).resolve().parents[1]
FURN_DIR = ROOT / "assets" / "furnishings"


def _load_fp3d():
    """fp3d.py loaded by path, the way running it as a script loads it."""
    path = ROOT / "floorplanner" / "viewer" / "fp3d.py"
    spec = importlib.util.spec_from_file_location("fp3d_under_test", path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod          # @dataclass looks its module up
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture(scope="module")
def fp3d():
    return _load_fp3d()


@pytest.fixture(scope="module")
def manifest():
    return json.loads((FURN_DIR / "manifest.json").read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def materials():
    return json.loads((FURN_DIR / "materials.json").read_text(encoding="utf-8"))


def _doc(kind, level_z=0.0, rotation=0.0):
    """A document holding exactly one furnishing, so what is measured is that
    furnishing and nothing else."""
    return {"levels": [{"id": "L1", "elevation_in": level_z,
                        "height_in": 96.0}],
            "vertices": [], "walls": [], "rooms": [],
            "furnishings": [{"id": "f1", "level": "L1", "kind": kind,
                             "pos": [0.0, 0.0], "rotation": rotation}]}


def _furn_mesh(model):
    return next(m for m in model.meshes if m.name.startswith("furnishings"))


# --------------------------------------------------------------------------
# the catalog is complete, and it is what the viewer can read
# --------------------------------------------------------------------------

def test_every_catalog_entry_carries_a_solid(manifest):
    """height_in, elevation_in, form and material on all 95 -- height_in most
    of all, because it is the one field with no safe default."""
    assert len(manifest) == 95, "catalog size changed; check this on purpose"
    missing = {}
    for e in manifest:
        absent = [f for f in ("height_in", "elevation_in", "form", "material")
                  if f not in e]
        if absent:
            missing[e["id"]] = absent
    assert not missing, f"catalog entries with no 3D data: {missing}"

    bad = {e["id"]: e["height_in"] for e in manifest
           if not isinstance(e["height_in"], (int, float))
           or e["height_in"] <= 0}
    assert not bad, f"height_in must be a positive number: {bad}"

    bad = {e["id"]: e["elevation_in"] for e in manifest
           if not isinstance(e["elevation_in"], (int, float))
           or e["elevation_in"] < 0}
    assert not bad, f"elevation_in must be >= 0: {bad}"


def test_every_material_named_resolves(manifest, materials):
    """A name is only a single source if it resolves.  Also checks the
    properties are the shape the renderers read, not merely present."""
    named = sorted({e["material"] for e in manifest})
    assert named, "precondition: the catalog names at least one material"
    unresolved = [m for m in named if m not in materials]
    assert not unresolved, f"materials named but not defined: {unresolved}"

    for name in named:
        m = materials[name]
        col = m["colour"]
        assert len(col) == 4 and all(0.0 <= float(c) <= 1.0 for c in col), \
            f"{name}: colour must be four channels in 0..1, got {col}"
        assert 0.0 <= float(m["roughness"]) <= 1.0
        assert 0.0 <= float(m["metalness"]) <= 1.0

    assert "unknown" in materials, \
        "the loud fallback must exist even though no entry names it"


def test_every_catalog_form_is_one_the_viewer_knows(manifest, fp3d):
    """The shipped catalog must never trip the viewer's own unknown-form
    path -- that path is for a catalog from the future, not for this one."""
    unknown = sorted({e["form"] for e in manifest
                      if e["form"] not in fp3d.KNOWN_FORMS})
    assert not unknown, f"catalog names form(s) the viewer cannot build: " \
                        f"{unknown}"


def test_the_viewer_finds_the_catalog_the_app_ships(fp3d, manifest):
    """`load_catalog()` walks up from the module, so it must resolve however
    the file is run.  A broken walk returns empty and reports -- which is the
    honest failure, and exactly what this asserts is NOT happening."""
    specs, materials, problems = fp3d.load_catalog()
    assert problems == [], f"the catalog did not load cleanly: {problems}"
    assert len(specs) == len(manifest)
    assert specs["wall_cab_30"]["height_in"] == 30
    assert materials["wood"]["colour"][0] == pytest.approx(0.52)


# --------------------------------------------------------------------------
# what the viewer does with it
# --------------------------------------------------------------------------

def test_elevation_places_an_item_off_the_floor(fp3d, manifest):
    """A wall-hung item must not sit on the floor -- with a floor-standing
    control in the same run, so "off the floor" is discriminating rather than
    a property every item happens to have."""
    spec = {e["id"]: e for e in manifest}
    hung, standing = spec["wall_cab_30"], spec["base_cab_36"]
    assert hung["elevation_in"] > 0, "precondition: wall_cab_30 is elevated"
    assert standing["elevation_in"] == 0, \
        "precondition: base_cab_36 stands on the floor"

    LEVEL_Z = 120.0                      # an upper storey, so 0 cannot pass
    for entry, name in ((hung, "wall_cab_30"), (standing, "base_cab_36")):
        model = fp3d.build_model(_doc(name, level_z=LEVEL_Z), floors=False)
        v = _furn_mesh(model).verts
        assert v[:, 2].min() == pytest.approx(LEVEL_Z + entry["elevation_in"])
        assert v[:, 2].max() == pytest.approx(
            LEVEL_Z + entry["elevation_in"] + entry["height_in"])

    # and the two really do differ, which is the whole claim
    hung_z = fp3d.build_model(_doc("wall_cab_30", level_z=LEVEL_Z),
                              floors=False)
    stand_z = fp3d.build_model(_doc("base_cab_36", level_z=LEVEL_Z),
                               floors=False)
    assert (_furn_mesh(hung_z).verts[:, 2].min()
            > _furn_mesh(stand_z).verts[:, 2].min())


def test_an_unknown_form_falls_back_visibly_and_is_reported(fp3d):
    """Box shape, MAGENTA colour, and a note naming the form.  A fallback
    nobody can see is a silent guess, which is what this whole change
    removed."""
    FORM = "hovercraft"
    assert FORM not in fp3d.KNOWN_FORMS, "precondition: the form is unknown"
    catalog = (
        {"oddity": {"width_in": 40.0, "depth_in": 20.0, "height_in": 30.0,
                    "elevation_in": 0.0, "form": FORM, "material": "wood"}},
        {"wood": {"colour": [0.52, 0.37, 0.23, 1.0], "roughness": 0.85,
                  "metalness": 0.0},
         "unknown": {"colour": [0.85, 0.35, 0.55, 1.0], "roughness": 0.6,
                     "metalness": 0.0}},
        [])
    model = fp3d.build_model(_doc("oddity"), catalog=catalog, floors=False)
    mesh = _furn_mesh(model)

    assert mesh.color == pytest.approx(catalog[1]["unknown"]["colour"]), \
        "an unknown form must not be drawn in its plausible material"
    assert len(mesh.faces) == 12, "fell back to something other than a box"
    v = mesh.verts
    assert v[:, 0].max() - v[:, 0].min() == pytest.approx(40.0)
    assert v[:, 1].max() - v[:, 1].min() == pytest.approx(20.0)
    assert any(FORM in n for n in model.notes), \
        f"the form was not named in the report: {model.notes}"


def test_a_form_awaiting_its_generator_is_info_not_a_fault(fp3d):
    """The severity split of VIEWER_NOTES s4, applied to forms: a RECOGNISED
    form whose generator is a later pass is routine, and reporting it as a
    fault would cry wolf.  Boundary marker for the first pass -- it expires
    when the last generator lands, and then this test is deleted with it."""
    pending = [f for f in fp3d.KNOWN_FORMS if f not in fp3d.BUILT_FORMS]
    assert pending, "precondition: some form is still awaiting its generator"
    form = pending[0]
    catalog = (
        {"waiting": {"width_in": 30.0, "depth_in": 30.0, "height_in": 30.0,
                     "elevation_in": 0.0, "form": form, "material": "wood"}},
        {"wood": {"colour": [0.52, 0.37, 0.23, 1.0], "roughness": 0.85,
                  "metalness": 0.0}},
        [])
    model = fp3d.build_model(_doc("waiting"), catalog=catalog, floors=False)

    assert not any(form in n for n in model.notes), \
        "a form awaiting its generator is not a fault"
    assert any(form in n for n in model.info), \
        f"...but it must still be said: {model.info}"
    assert _furn_mesh(model).color == pytest.approx([0.52, 0.37, 0.23, 1.0]), \
        "it is a known form, so it keeps its real material"


def test_slab_is_a_top_on_legs(fp3d, manifest):
    """Not just "the box got more triangles": there is SPACE under a table."""
    spec = {e["id"]: e for e in manifest}["desk"]
    assert spec["form"] == "slab", "precondition: desk is a slab"
    model = fp3d.build_model(_doc("desk"), floors=False)
    mesh = _furn_mesh(model)
    assert len(mesh.faces) > 12, "still a single box"

    # every part is a 8-vertex prism; find the ones spanning mid-height and
    # check none of them covers the centre of the footprint
    v, mid = mesh.verts, spec["height_in"] / 2.0
    covering = []
    for i in range(0, len(v), 8):
        part = v[i:i + 8]
        if part[:, 2].min() <= mid <= part[:, 2].max():
            if (part[:, 0].min() <= 0 <= part[:, 0].max()
                    and part[:, 1].min() <= 0 <= part[:, 1].max()):
                covering.append(i)
    assert not covering, \
        "something solid sits at the centre of the desk at half height"


def test_a_missing_catalog_is_reported_not_silent(fp3d):
    """The fallback exists so a viewer without assets still draws.  It must
    say so: an unannounced default box is indistinguishable from a measured
    one, which is the failure mode the catalog move exists to end."""
    problem = "furnishing catalog: cannot read manifest.json (test)"
    model = fp3d.build_model(_doc("sofa"), catalog=({}, {}, [problem]),
                             floors=False)
    assert problem in model.notes, "the missing catalog was not reported"

    v = _furn_mesh(model).verts
    assert len(_furn_mesh(model).faces) == 12
    assert v[:, 0].max() - v[:, 0].min() == pytest.approx(
        fp3d.CATALOG_DEFAULT["width_in"])
    assert v[:, 2].max() - v[:, 2].min() == pytest.approx(
        fp3d.CATALOG_DEFAULT["height_in"])
    assert _furn_mesh(model).color == pytest.approx(fp3d.UNKNOWN_C)


def test_load_catalog_reports_rather_than_raises_when_assets_are_absent(
        fp3d, tmp_path):
    """Pointed at a directory with no manifest, load_catalog returns empty
    and SAYS WHY -- it does not raise into whatever called it."""
    empty = tmp_path / "furnishings"
    empty.mkdir()
    specs, materials, problems = fp3d.load_catalog(str(empty))
    assert specs == {} and materials == {}
    assert len(problems) == 2, problems
    assert any("manifest.json" in p for p in problems)
    assert any("materials.json" in p for p in problems)


def test_build_model_imports_neither_qt_nor_floorplanner():
    """VIEWER_NOTES s1's isolation claim, asserted rather than asserted-about.

    Run in a SUBPROCESS on purpose: the test session has already imported both
    PyQt6 and floorplanner, so checking this process's sys.modules would pass
    no matter what fp3d did."""
    probe = (
        "import importlib.util, sys, json\n"
        f"spec = importlib.util.spec_from_file_location('m', r'"
        f"{ROOT / 'floorplanner' / 'viewer' / 'fp3d.py'}')\n"
        "m = importlib.util.module_from_spec(spec)\n"
        "sys.modules['m'] = m\n"
        "spec.loader.exec_module(m)\n"
        "doc = {'levels': [{'id': 'L1', 'elevation_in': 0, 'height_in': 96}],"
        " 'vertices': [], 'walls': [], 'rooms': [],"
        " 'furnishings': [{'id': 'f', 'level': 'L1', 'kind': 'sofa',"
        " 'pos': [0, 0], 'rotation': 0}]}\n"
        "model = m.build_model(doc)\n"
        "assert model.meshes, 'built nothing, so the check is vacuous'\n"
        "leaked = sorted(k for k in sys.modules\n"
        "                if k.split('.')[0] in ('PyQt6', 'floorplanner',\n"
        "                                       'FloorPlanner'))\n"
        "print(json.dumps(leaked))\n")
    out = subprocess.run([sys.executable, "-c", probe], capture_output=True,
                         text=True, cwd=str(ROOT))
    assert out.returncode == 0, out.stderr
    assert json.loads(out.stdout.strip()) == [], \
        f"build_model pulled in {out.stdout.strip()}"


# --------------------------------------------------------------------------
# `prism` -- the plan symbol, extruded (handoff 0012's ruling)
# --------------------------------------------------------------------------
def _furn_verts(fp3d, model):
    """Every furnishing vertex in a model, as a list of (x, y, z)."""
    return [tuple(v) for m in model.meshes if m.name.startswith("furnishings:")
            for v in m.verts]


def test_prism_is_used_where_a_symbol_has_an_outline(fp3d):
    """The ruling: a form whose own generator is not written yet is drawn from
    its PLAN SYMBOL rather than as a rectangle. `sofa` is form `seat`, which
    has no generator, and its symbol is one filled body."""
    model = fp3d.build_model(_doc("sofa"))
    assert "sofa" in model.stats["prism_kinds"], model.stats
    assert "sofa" not in model.stats["box_fallback_kinds"]


def test_a_prism_is_not_a_box(fp3d, manifest):
    """The point of the feature, and it needs a case where the two DIFFER.

    `lawnmower` is a deck plus a handle drawn in strokes: the extruded solid
    must cover materially less than the footprint, or prism is doing nothing
    that the box was not already doing."""
    spec = next(i for i in manifest if i["id"] == "lawnmower")
    model = fp3d.build_model(_doc("lawnmower"))
    assert "lawnmower" in model.stats["prism_kinds"]
    vs = _furn_verts(fp3d, model)
    ys = [v[1] for v in vs]
    span = max(ys) - min(ys)
    assert span < spec["depth_in"] * 0.75, (
        f"the extruded solid spans {span:.1f}\" of a {spec['depth_in']}\" "
        f"footprint -- that is a box, not the symbol")


def test_a_prism_never_exceeds_the_items_footprint(fp3d, manifest):
    """The under-approximation is deliberate: curves contribute their anchor
    points, so a rounded outline extrudes as its inscribed polygon. A solid
    LARGER than the symbol drawn would be an object poking through a wall."""
    for kind in ("sofa", "car", "bathtub", "bed_king"):
        spec = next(i for i in manifest if i["id"] == kind)
        vs = _furn_verts(fp3d, fp3d.build_model(_doc(kind)))
        assert vs, f"{kind} built nothing"
        w = max(v[0] for v in vs) - min(v[0] for v in vs)
        d = max(v[1] for v in vs) - min(v[1] for v in vs)
        assert w <= spec["width_in"] + 1e-6, f"{kind} wider than its footprint"
        assert d <= spec["depth_in"] + 1e-6, f"{kind} deeper than its footprint"


def test_a_prism_is_not_MIRRORED_along_the_depth_axis(fp3d):
    """THE Y FLIP, asserted on an asymmetric item.

    The editor's scene has y growing DOWN and this viewer's world has it
    growing up, so local y is `H/2 - sy`, not `sy - H/2`. A sign error here
    renders every asymmetric item mirrored -- and mirrored is exactly the class
    of fault the deleted furniture table shipped for months.

    `lawnmower` has its deck at the TOP of the symbol (small svg y), so in the
    viewer's world the solid must sit on the POSITIVE y side of the item's
    centre. With the sign flipped this assertion reverses cleanly."""
    vs = _furn_verts(fp3d, fp3d.build_model(_doc("lawnmower")))
    ys = [v[1] for v in vs]
    assert sum(ys) / len(ys) > 0.0, (
        "the mower's deck must land on the +y side; it is mirrored")


def test_a_line_art_symbol_FALLS_BACK_and_is_NAMED(fp3d):
    """`glass_shower` is drawn entirely in strokes -- there is nothing to
    extrude, and a prism would have to invent a boundary. It must fall back to
    the box AND be named in the report, because "a third of the catalog renders
    as a box" is a claim that only stays checkable if the survivors are listed
    rather than totalled."""
    model = fp3d.build_model(_doc("glass_shower"))
    assert model.stats["box_fallback_kinds"] == ["glass_shower"]
    assert "glass_shower" not in model.stats["prism_kinds"]
    assert any("STILL DRAWN AS A BOX" in line and "glass_shower" in line
               for line in model.info), model.info


def test_the_fallback_still_draws_the_item(fp3d, manifest):
    """A fallback that drew NOTHING would satisfy the test above and lose the
    furnishing. The box must still be there, at the catalog's size."""
    spec = next(i for i in manifest if i["id"] == "glass_shower")
    vs = _furn_verts(fp3d, fp3d.build_model(_doc("glass_shower")))
    assert vs, "the fallback drew nothing at all"
    w = max(v[0] for v in vs) - min(v[0] for v in vs)
    assert abs(w - spec["width_in"]) < 1e-6, "the box is not the catalog's size"


def test_rotation_carries_through_the_prism(fp3d, manifest):
    """`place` carries rotation for every generator; a prism that built in
    world coordinates would ignore it. Asserted on a long thin item so the
    swap is unmissable."""
    spec = next(i for i in manifest if i["id"] == "car")
    at0 = _furn_verts(fp3d, fp3d.build_model(_doc("car", rotation=0.0)))
    at90 = _furn_verts(fp3d, fp3d.build_model(_doc("car", rotation=90.0)))
    span0 = max(v[0] for v in at0) - min(v[0] for v in at0)
    span90 = max(v[0] for v in at90) - min(v[0] for v in at90)
    w, d = spec["width_in"], spec["depth_in"]
    assert d > w * 1.5, "PRECONDITION: a car must be longer than it is wide"
    # NOT an exact match with the catalog size, deliberately: the car's body is
    # inset from its viewBox and curves contribute anchor points only, so the
    # solid is a little smaller than the footprint by design. The claim is that
    # the extent SWAPS, which is what rotation means.
    assert abs(span0 - w) < abs(span0 - d), "unrotated, x should track WIDTH"
    assert abs(span90 - d) < abs(span90 - w), \
        "rotating 90 degrees must swap the item's extent, and did not"


def test_every_catalog_symbol_either_extrudes_or_is_reported(fp3d, manifest):
    """THE WHOLE CATALOG, not a sample -- and the assertion is that the two
    lists PARTITION the fallback set. An item that quietly vanished from both
    would be one nothing reports, which is the failure this file exists for."""
    doc = _doc("sofa")
    doc["furnishings"] = [
        {"id": f"f{i}", "level": "L1", "kind": it["id"],
         "pos": [i * 200.0, 0.0], "rotation": 0.0}
        for i, it in enumerate(manifest)]
    model = fp3d.build_model(doc)
    pending = {i["id"] for i in manifest
               if (i.get("form") or "box") not in ("box", "slab")}
    got = set(model.stats["prism_kinds"]) | set(model.stats["box_fallback_kinds"])
    assert got == pending, f"unaccounted: {pending ^ got}"
    assert model.stats["furnishings"] == len(manifest)


# --------------------------------------------------------------------------
# region extrusion -- a region's height is annotated, its position is not
# --------------------------------------------------------------------------
def _zs(fp3d, model):
    return sorted({round(v[2], 3) for v in _furn_verts(fp3d, model)})


def test_a_pillow_RISES_ABOVE_the_mattress(fp3d, manifest):
    """A raised region sits ON the body. The bed's own height is the mattress;
    the pillows state 30, and the solid must reach it."""
    spec = next(i for i in manifest if i["id"] == "bed_king")
    zs = _zs(fp3d, fp3d.build_model(_doc("bed_king")))
    assert spec["height_in"] in zs, "the mattress top must still be there"
    assert max(zs) > spec["height_in"], \
        f"nothing rises above the mattress: {zs}"
    assert max(zs) == 30.0, f"the pillows' annotated height, not another: {zs}"


def _roof_over(model, x, y, z):
    """Is there a horizontal face at height `z` covering the point (x, y)?"""
    def inside(p, a, b, c):
        def s(u, v):
            return ((v[0] - u[0]) * (p[1] - u[1])
                    - (v[1] - u[1]) * (p[0] - u[0]))
        d1, d2, d3 = s(a, b), s(b, c), s(c, a)
        return not ((d1 < 0 or d2 < 0 or d3 < 0)
                    and (d1 > 0 or d2 > 0 or d3 > 0))

    for m in model.meshes:
        if not m.name.startswith("furnishings:"):
            continue
        for tri in m.faces:
            vs = [m.verts[i] for i in tri]
            if all(abs(v[2] - z) < 1e-6 for v in vs) and inside((x, y), *vs):
                return True
    return False


def test_a_tub_is_HOLLOW(fp3d, manifest):
    """A region BELOW the body is a WELL, and a well is only a well if the body
    is OPENED for it.

    THE FIRST CUT OF THIS TEST WAS VACUOUS and is recorded rather than quietly
    replaced. It asserted that the well's height appears among the solid's z
    values and that there are more than twelve triangles -- both of which are
    ALSO true of a body left solid with a block sitting inside it, which is
    exactly what the broken version produced. It passed against code with the
    well branch disabled.

    So the assertion is now the thing the eye checks: IS THERE A ROOF OVER THE
    WELL? A hollow tub has no horizontal face at rim height above its centre; a
    solid one does. That cannot be satisfied by a block."""
    spec = next(i for i in manifest if i["id"] == "bathtub")
    rim = float(spec["height_in"])
    model = fp3d.build_model(_doc("bathtub"))
    zs = _zs(fp3d, model)
    assert rim in zs, "the rim must be at the catalog height"
    assert 4.0 in zs, f"the well floor must be at its annotated 4in: {zs}"

    assert not _roof_over(model, 0.0, 0.0, rim), \
        "there is a face at rim height over the tub's centre -- it is not hollow"
    # the precondition: the rim itself must still be there, or "no roof" is
    # satisfied by an item that built nothing at all
    edge_y = spec["depth_in"] / 2 - 1.0
    assert _roof_over(model, 0.0, edge_y, rim), \
        "the rim vanished -- the tub has no top at all"


def test_a_sofa_is_a_SEAT_WITH_A_BACK_not_a_slab(fp3d, manifest):
    """THE CHECK, as far as a test can carry it.

    `height_in` for a sofa is 32 -- the BACK height -- so a body that used it
    extruded the whole footprint to 32 and rendered as a slab. The body now
    states its own 17, and the back rises to 32.

    THE PRECONDITION IS THE HALF THAT MATTERS: without asserting that most of
    the footprint stops at the seat, "something reaches 32" is satisfied by the
    slab this replaces."""
    spec = next(i for i in manifest if i["id"] == "sofa")
    assert spec["height_in"] == 32, "PRECONDITION: the catalog states the back"
    model = fp3d.build_model(_doc("sofa"))
    zs = _zs(fp3d, model)
    assert 17.0 in zs, f"the seat must stop at its own height: {zs}"
    assert 32.0 in zs, f"the back must still reach the overall height: {zs}"
    assert 24.0 in zs, f"the arms must be between the two: {zs}"

    # and the 32 must be a BACK, not the whole item: the vertices at full
    # height must span far less depth than those at seat height
    vs = _furn_verts(fp3d, model)
    at_seat = [v for v in vs if abs(v[2] - 17.0) < 1e-6]
    at_back = [v for v in vs if abs(v[2] - 32.0) < 1e-6]
    depth_seat = max(v[1] for v in at_seat) - min(v[1] for v in at_seat)
    depth_back = max(v[1] for v in at_back) - min(v[1] for v in at_back)
    assert depth_back < depth_seat / 2, (
        f"the full-height part is {depth_back:.1f}in deep against the seat's "
        f"{depth_seat:.1f}in -- that is a slab, not a back")


def test_an_unannotated_nested_shape_is_still_DROPPED(fp3d):
    """Decoration that states no height would extrude to the body's own height
    and z-fight the face it sits on. `shower`'s inner shapes are unfilled and
    unannotated, so the solid stays a plain enclosure."""
    model = fp3d.build_model(_doc("shower"))
    tris = sum(len(m.faces) for m in model.meshes
               if m.name.startswith("furnishings:"))
    assert tris == 12, f"expected a plain prism, got {tris} triangles"


def test_the_annotation_carries_A_HEIGHT_AND_NOTHING_ELSE(manifest):
    """THE BOUNDARY, asserted on the artwork rather than trusted.

    Ruled: the region's POSITION comes from the artwork; only its HEIGHT is
    annotated. The moment the annotation could also say WHERE, there are two
    sources of truth about where a pillow is and they will disagree -- the same
    discipline as the one thickness table.

    So: every `data-` attribute in the asset tree is `data-h`, and every value
    is a single number."""
    import re
    bad_attr, bad_value = [], []
    for it in manifest:
        text = (FURN_DIR / it["file"]).read_text(encoding="utf-8")
        for name, value in re.findall(r'(data-[a-z-]+)="([^"]*)"', text):
            if name != "data-h":
                bad_attr.append(f"{it['id']}: {name}")
            elif not re.fullmatch(r"-?\d+(\.\d+)?", value):
                bad_value.append(f"{it['id']}: data-h={value!r}")
    assert not bad_attr, f"annotations beyond a height: {bad_attr}"
    assert not bad_value, f"a height that is not one number: {bad_value}"


def test_every_annotated_region_reaches_its_stated_height(fp3d, manifest):
    """THE WHOLE ANNOTATED SET, not a sample. Every `data-h` in the catalog
    must appear as a real z in the built solid -- an annotation the extruder
    silently ignored would be invisible in every other test here.

    `elevation_in` IS ADDED, and the first cut of this test forgot it and went
    red on `kitchen_sink`. That was the test being wrong and the extruder being
    right, and the distinction is worth keeping: **`data-h` is measured from the
    ITEM'S BASE, the same datum as `height_in`** -- so a counter-mounted sink's
    `data-h="2"` is 2in above the counter, not 2in above the floor. An
    annotation measured from the floor would have to know where the counter is,
    which is a coordinate, which is the boundary this must not cross."""
    import re
    checked = 0
    for it in manifest:
        text = (FURN_DIR / it["file"]).read_text(encoding="utf-8")
        wanted = {float(v) for v in re.findall(r'data-h="([^"]+)"', text)}
        if not wanted:
            continue
        base = float(it.get("elevation_in", 0) or 0)
        zs = set(_zs(fp3d, fp3d.build_model(_doc(it["id"]))))
        missing = {h for h in wanted if (h + base) not in zs}
        assert not missing, f"{it['id']}: annotated {missing}, built {sorted(zs)}"
        checked += 1
    assert checked >= 10, f"only {checked} annotated items -- did they vanish?"
