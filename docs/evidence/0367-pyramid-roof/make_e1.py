"""0367 stage 2 -- evidence E1 (ruling §7): a FREE-STANDING HEXAGON.

"an exterior room 12 ft across flats, six posts, sides 6." A gazebo: a regular
hexagonal deck 144 in (12 ft) across the flats, a 6x6 post at each corner, and a
six-sided pyramid roof over it whose wall line sits on those corners. The posts
rise to the roof's underside; the roof is drawn whole (no weld at stage 2).

Writes the plan JSON (validated against the packaged v6 schema, so the app can
open it) and renders a 3D shot offscreen. Run:
    python docs/evidence/0367-pyramid-roof/make_e1.py
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
INRADIUS = 72.0                      # 144 in across flats = 2 * inradius
SIDES = 6


def build_doc():
    st = {"sides": SIDES, "inradius_in": INRADIUS, "eaves_bind": "manual",
          "eaves_h_in": 96.0, "pitch_12": 10.0, "overhang_in": 12.0, "weld": "auto"}
    corners = [pg.to_plan(CENTRE, 0.0, v) for v in pg.wall_polygon(st)]
    verts = [{"id": f"v{i}", "level": "L1", "x": round(x, 3), "y": round(y, 3)}
             for i, (x, y) in enumerate(corners)]
    room = {"id": "gazebo", "level": "L1", "name": "Gazebo", "category": "exterior",
            "outline": [{"v": f"v{i}"} for i in range(SIDES)],
            "placement": {"state": "floating"}}
    posts = [{"id": f"post{i}", "level": "L1", "kind": "post",
              "pos": [round(x, 3), round(y, 3)], "rotation": 0.0}
             for i, (x, y) in enumerate(corners)]
    pyramid = {"id": "roof", "level": "L1", "kind": "pyramid_roof",
               "pos": [CENTRE[0], CENTRE[1]], "rotation": 0.0, "state": st}
    return {"format": "floorplanner-design", "version": 6, "units": "inches",
            "levels": [{"id": "L1", "name": "Main", "elevation_in": 0.0,
                        "height_in": 96.0}],
            "vertices": verts, "walls": [], "rooms": [room],
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
    out = HERE / "E1-free-standing-hexagon.json"
    out.write_text(json.dumps(doc, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {out.name}")
    shot = HERE / "E1-free-standing-hexagon.png"
    r = subprocess.run(
        [sys.executable, str(ROOT / "floorplanner" / "viewer" / "fp3d.py"),
         str(out), "--shot", str(shot)],
        capture_output=True, text=True, cwd=ROOT)
    print((r.stdout or "").strip() or (r.stderr or "").strip()[:400])
    print(f"shot: {'ok ' + shot.name if shot.exists() else 'NOT rendered'}")


if __name__ == "__main__":
    main()
