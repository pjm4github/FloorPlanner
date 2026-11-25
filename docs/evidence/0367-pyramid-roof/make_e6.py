"""0367 arc -- evidence E6: a HALF-GAZEBO (arc 180 in 3 sections).

Patrick's words: "split the gazebo into an arc ... an arc of 180 degrees and 3
sections then each roof section should be 60 degrees ... a pie shaped section
that truncates into the peak." So this is a three-facet half-gazebo: the facets
fan symmetrically about up, each spans 60 degrees, and the back half is left
open to the peak -- no vertical cut face, no gable wall. A 6x6 post stands under
each present eave corner and rises to the roof's underside; the posts on the
flat back sit on the open cut line.

Writes the plan JSON (validated against the packaged v6 schema, so the app can
open it) and renders a 3D shot offscreen. Run:
    python docs/evidence/0367-pyramid-roof/make_e6.py
"""
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from floorplanner.parametric import pyramid_geometry as pg  # noqa: E402

HERE = Path(__file__).parent
CENTRE = (240.0, 240.0)
INRADIUS = 72.0
SIDES = 3
ARC_DEG = 180.0


def build_doc():
    st = {"sides": SIDES, "arc_deg": ARC_DEG, "inradius_in": INRADIUS,
          "eaves_bind": "manual", "eaves_h_in": 96.0, "pitch_12": 10.0,
          "overhang_in": 12.0, "weld": "auto"}
    # the wall-line corners of the present facets (sides + 1 for an open arc)
    corners = [pg.to_plan(CENTRE, 0.0, v) for v in pg.wall_polygon(st)]
    verts = [{"id": f"v{i}", "level": "L1", "x": round(x, 3), "y": round(y, 3)}
             for i, (x, y) in enumerate(corners)]
    # a room on the fan footprint (apex + the eave corners), so the half-gazebo
    # has a deck under it
    fan = [pg.to_plan(CENTRE, 0.0, v) for v in pg.footprint(st)]
    fverts = [{"id": f"f{i}", "level": "L1", "x": round(x, 3), "y": round(y, 3)}
              for i, (x, y) in enumerate(fan)]
    room = {"id": "half_gazebo", "level": "L1", "name": "Half gazebo",
            "category": "exterior",
            "outline": [{"v": f"f{i}"} for i in range(len(fan))],
            "placement": {"state": "floating"}}
    posts = [{"id": f"post{i}", "level": "L1", "kind": "post",
              "pos": [round(x, 3), round(y, 3)], "rotation": 0.0}
             for i, (x, y) in enumerate(corners)]
    pyramid = {"id": "roof", "level": "L1", "kind": "pyramid_roof",
               "pos": [CENTRE[0], CENTRE[1]], "rotation": 0.0, "state": st}
    return {"format": "floorplanner-design", "version": 6, "units": "inches",
            "levels": [{"id": "L1", "name": "Main", "elevation_in": 0.0,
                        "height_in": 96.0}],
            "vertices": verts + fverts, "walls": [], "rooms": [room],
            "furnishings": posts + [pyramid]}


def main():
    doc = build_doc()
    try:
        import jsonschema
        schema = json.loads((ROOT / "floorplanner" / "design"
                             / "design-schema.v6.json").read_text(encoding="utf-8"))
        jsonschema.validate(doc, schema)
        print("schema: valid v6")
    except ImportError:
        print("schema: jsonschema not installed -- skipped")
    out = HERE / "E6-half-gazebo-arc.json"
    out.write_text(json.dumps(doc, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {out.name}")
    shot = HERE / "E6-half-gazebo-arc.png"
    r = subprocess.run(
        [sys.executable, str(ROOT / "floorplanner" / "viewer" / "fp3d.py"),
         str(out), "--shot", str(shot)],
        capture_output=True, text=True, cwd=ROOT)
    print((r.stdout or "").strip() or (r.stderr or "").strip()[:400])
    print(f"shot: {'ok ' + shot.name if shot.exists() else 'NOT rendered'}")


if __name__ == "__main__":
    main()
