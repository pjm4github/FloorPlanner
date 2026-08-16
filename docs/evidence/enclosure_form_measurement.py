"""THE OWED MEASUREMENT (handoff 0016 §5): for `walk_in_shower`, `sauna` and
`whirlpool`, does each item's internal region come out as a RAISED SOLID or an
OPENED CAP (a "well")?

    python docs/evidence/enclosure_form_measurement.py [--look]

MEASUREMENT ONLY. This does not decide whether `form="enclosure"` needs
splitting into two forms; it answers the one question the ruling asked, so that
decision can be made on a confirmed premise rather than an inferred one.

THE INSTRUMENT IS BLACK-BOX BY DESIGN: it calls only `build_model` — the
production entry point, unmodified — and inspects the MESH IT BUILT, rather
than re-deriving `build_prism`'s classification logic in a second copy that
could drift from it. The question "did this region open the body's cap" has
one clean, direct signal: **is there a horizontal face at the body's full
height, directly over the region's centre?** A raised region never touches the
cap at all, so the cap stays whole there; a well by construction cuts a hole in
the cap where the well sits. No face there = the cap is open = a well.

This is the same technique `test_a_tub_is_HOLLOW` in `tests/test_viewer_model.py`
already uses and already proved discriminates a hollow structure from a solid
one wearing the same z-values (that test's own first cut was vacuous for
exactly the reason a naive z-value check would be here too).

CONTROLLED ON BOTH SIDES (added at handoff 0018, correcting the first cut):
`bathtub` must read WELL and `sofa`'s back must read RAISED, or the result
below is not trusted. The first cut ran only the WELL side, which every case
under test also happened to expect -- see `two_sided_control`'s own docstring
for why that made the first run's "3 of 3" not yet a measurement.
"""
import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
FURN = ROOT / "assets" / "furnishings"
ITEMS = ["walk_in_shower", "sauna", "whirlpool"]


def load_fp3d():
    spec = importlib.util.spec_from_file_location(
        "fp3d_enclosure_measurement", ROOT / "floorplanner" / "viewer" / "fp3d.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


def one_item_doc(kind):
    return {
        "format": "floorplanner-design", "version": 5,
        "levels": [{"id": "L0", "name": "default", "elevation_in": 0.0,
                    "height_in": 96.0}],
        "vertices": [], "walls": [], "rooms": [],
        "furnishings": [{"id": "f0", "level": "L0", "kind": kind,
                         "pos": [0.0, 0.0], "rotation": 0.0}],
    }


def roof_over(model, x, y, z, tol=1e-6):
    """Is there a horizontal face at height `z` covering world point (x, y)?"""
    def inside(p, a, b, c):
        def side(u, v):
            return (v[0] - u[0]) * (p[1] - u[1]) - (v[1] - u[1]) * (p[0] - u[0])
        d1, d2, d3 = side(a, b), side(b, c), side(c, a)
        return not ((d1 < 0 or d2 < 0 or d3 < 0) and (d1 > 0 or d2 > 0 or d3 > 0))

    for m in model.meshes:
        if not m.name.startswith("furnishings:"):
            continue
        for tri in m.faces:
            vs = [m.verts[i] for i in tri]
            if all(abs(v[2] - z) < tol for v in vs) and inside((x, y), *vs):
                return True
    return False


def region_world_centroid(fp3d, ring, vw, vh, w, d):
    """The SAME mapping `build_prism.to_world` uses, for an item placed at
    (0, 0) with rotation 0 -- where `place(lx, ly) == (lx, ly)`."""
    cx = sum(p[0] for p in ring) / len(ring)
    cy = sum(p[1] for p in ring) / len(ring)
    sx, sy = w / vw, d / vh
    return (cx - vw / 2.0) * sx, (vh / 2.0 - cy) * sy


def measure(fp3d, manifest, kind, region_filter=None):
    """(results, outer, model) for one catalog kind.

    `body_h` is derived exactly as `build_prism` derives it -- **the body's own
    annotation if it carries one, else the catalog's `height_in`** -- not
    hardcoded to `height_in`. A first draft of this function hardcoded it, which
    would have silently mis-measured any item whose BODY states its own height
    (`sofa`'s body is 17″, not its catalog 32″); it happened to be harmless for
    the three enclosure items only because none of them annotates its body.
    Caught before it shipped by needing `sofa` for the negative control below,
    which would have failed with the wrong `body_h`.

    `region_filter` narrows which nested regions are measured (used by the
    negative control to isolate a RAISED region on an item that also has
    regions this probe is not asking about)."""
    spec = next(i for i in manifest if i["id"] == kind)
    parts, (vw, vh) = fp3d.svg_outlines(str(FURN / spec["file"]))
    parts = sorted(parts, key=lambda p: fp3d._ring_area(p.ring), reverse=True)
    outer = parts[0]
    body_h = outer.h if outer.h is not None else float(spec["height_in"])
    regions = [p for p in parts[1:] if p.nested and p.h is not None]
    if region_filter is not None:
        regions = [p for p in regions if region_filter(p)]

    model = fp3d.build_model(one_item_doc(kind))
    results = []
    for p in regions:
        wx, wy = region_world_centroid(fp3d, p.ring, vw, vh,
                                       spec["width_in"], spec["depth_in"])
        cap_open = not roof_over(model, wx, wy, body_h)
        results.append({
            "kind": kind, "region_h": p.h, "body_h": body_h,
            "cap_open_at_body_h": cap_open,
            "outcome": "WELL (cap opened)" if cap_open else "RAISED (cap intact)",
        })
    return results, outer, model


def look(manifest, out_dir):
    """Writes the CHECK PLAN only. The render itself is one more command,
    printed rather than shelled out to from here: `--shot`'s framebuffer grab
    (`main()`'s `body.view.grabFramebuffer().save(...)`) proved FLAKY when
    invoked as a subprocess-of-a-subprocess under `QT_QPA_PLATFORM=offscreen`
    -- it reported success and wrote nothing, reproducibly, only in that
    nesting. Run standalone (once, directly, not from inside another script)
    it works every time, so that is what this prints rather than automates."""
    doc = {
        "format": "floorplanner-design", "version": 5,
        "levels": [{"id": "L0", "name": "default", "elevation_in": 0.0,
                    "height_in": 96.0}],
        "vertices": [], "walls": [], "rooms": [],
        "furnishings": [
            {"id": f"f{i}", "level": "L0", "kind": k,
             "pos": [i * 200.0, 0.0], "rotation": 0.0}
            for i, k in enumerate(ITEMS)],
    }
    path = ROOT / "fixtures" / "enclosure-form-check.json"
    path.write_text(json.dumps(doc, indent=1), encoding="utf-8")
    out = out_dir / "enclosure-form-measurement.png"
    print(f"wrote {path}  (order: {', '.join(ITEMS)})")
    print("now run, standalone (not piped through this script):")
    print(f"  python floorplanner/viewer/fp3d.py {path.relative_to(ROOT)} "
         f"--shot {out.relative_to(ROOT)}")


def two_sided_control(fp3d, manifest):
    """BOTH of the instrument's two possible answers, each demonstrated on a
    KNOWN case, before either is trusted on the three items under test.

    THE FIRST CUT OF THIS PROBE RAN ONLY ONE SIDE (handoff 0018 §2): `bathtub`
    reading WELL, and every one of the three items under test ALSO reading
    WELL. **A control that shares its expected answer with every case under
    test tests the one direction that cannot fail** -- a `roof_over()` that
    always returned `False` (a mis-mapped centroid, a viewBox transform off by
    a factor, a bug in the face lookup) would have produced that exact output,
    control included. `bathtub` showed the instrument CAN say WELL; nothing
    showed it can say anything else, so *"3 of 3 produced a WELL"* was a
    sentence about a function that had only ever emitted one string.

    This is a THIRD member of a family this project already keeps: the plain
    positive control catches an instrument reporting NOTHING; the
    identical-cases rule catches one reporting a PLAUSIBLE SOMETHING; this one
    catches an instrument that can only report ONE OF ITS TWO ANSWERS. **A
    control must be chosen for the answer you are NOT expecting.**

    So: `bathtub`'s well (unchanged) PLUS `sofa`'s back, a region already
    proven RAISED by PR #29's own tests -- if this probe cannot reproduce that,
    it cannot be trusted to prove the fix either, since the fix's own receipt
    is *"the sauna's heater now reads RAISED"*, measured by this same probe."""
    well, _outer, _model = measure(fp3d, manifest, "bathtub")
    assert well and well[0]["cap_open_at_body_h"], (
        "CONTROL FAILED (well side): bathtub -- a known, ruled-correct well "
        "-- did not read as one. The measurement below cannot be trusted.")

    raised, _outer, _model = measure(
        fp3d, manifest, "sofa", region_filter=lambda p: p.h == 32.0)
    assert raised and not raised[0]["cap_open_at_body_h"], (
        "CONTROL FAILED (raised side): sofa's back -- a known-raised region "
        "-- did not read as one. The instrument may be unable to report "
        "RAISED at all, which would make every WELL result below meaningless "
        "rather than merely wrong.")

    print("control: bathtub -> WELL, sofa's back -> RAISED -- both sides of "
         "the instrument shown working; proceeding\n")


def main():
    fp3d = load_fp3d()
    manifest = json.loads((FURN / "manifest.json").read_text("utf-8"))
    two_sided_control(fp3d, manifest)

    print(f"{'item':16s} {'region h':>9s} {'body h':>7s}  outcome")
    print("-" * 60)
    all_results = []
    for kind in ITEMS:
        results, outer, _model = measure(fp3d, manifest, kind)
        assert results, f"{kind}: no nested annotated region found -- census stale?"
        for r in results:
            print(f"{r['kind']:16s} {r['region_h']:9.1f} {r['body_h']:7.1f}  "
                  f"{r['outcome']}")
            all_results.append(r)

    wells = [r for r in all_results if r["cap_open_at_body_h"]]
    print(f"\nTHE THREE LINES: {len(wells)} of {len(all_results)} tall "
          f"enclosures produced a WELL (cap opened into the top face) for "
          f"their internal feature.")
    if wells:
        print("Confirmed: " + ", ".join(f"{r['kind']} ({r['region_h']:.0f}in "
                                        f"< {r['body_h']:.0f}in body)"
                                        for r in wells))

    if "--look" in sys.argv:
        look(manifest, Path(__file__).resolve().parent)


if __name__ == "__main__":
    main()
