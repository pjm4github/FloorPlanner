"""0367 stage 3 — the weld evidence (ruling §7).

E2  an octagon bay on an eave, mid-wall, under a plain gable roof.
E4  a square pyramid (sides 4) astride a ridge.
E5  E4 with `weld: off` — both drawn whole (the contrast).

E3 (the NOOK on a copy of wiscaway-c03-roofA-garage.json) is owed with that
file, which is not in the repository; see INDEX.md.

Each plan is validated against the packaged v6 schema and rendered offscreen.
Run:  python docs/evidence/0367-pyramid-roof/make_weld_evidence.py
"""
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).parent


def _rect(x0, y0, x1, y1):
    V = [("a", x0, y0), ("b", x1, y0), ("c", x1, y1), ("d", x0, y1)]
    verts = [{"id": i, "level": "L1", "x": x, "y": y} for i, x, y in V]
    walls = [{"id": f"w{k}", "level": "L1", "v1": a, "v2": b, "type": "exterior"}
             for k, (a, b) in enumerate([("a", "b"), ("b", "c"), ("c", "d"), ("d", "a")])]
    room = {"id": "r", "level": "L1", "name": "Room", "category": "interior",
            "outline": [{"v": i} for i, _, _ in V],
            "placement": {"state": "placed"}}
    return verts, walls, room


def _base(verts, walls, rooms, roofs, furn):
    return {"format": "floorplanner-design", "version": 6, "units": "inches",
            "levels": [{"id": "L1", "name": "Main", "elevation_in": 0.0,
                        "height_in": 96.0}],
            "vertices": verts, "walls": walls, "rooms": rooms,
            "roofs": roofs, "furnishings": furn}


def e2():
    # a plain gable over a rectangle; an octagon bay projecting from the middle
    # of the front (y=280) eave wall, its roof welding into the gable eave.
    verts, walls, room = _rect(80, 120, 320, 280)
    roof = {"id": "rf1", "level": "L1", "ridge": [[110, 200], [290, 200]],
            "eaves_h_in": 96.0, "ridge_h_in": 150.0, "span_in": [80, 80],
            "overhang_in": [14, 14], "gable": [True, True]}
    bay = {"id": "bay", "level": "L1", "kind": "pyramid_roof", "pos": [200, 280],
           "rotation": 0.0,
           "state": {"sides": 8, "inradius_in": 44.0, "eaves_bind": "manual",
                     "eaves_h_in": 104.0, "pitch_12": 9.0, "overhang_in": 10.0,
                     "weld": "auto"}}
    return _base(verts, walls, [room], [roof], [bay])


def e4(weld="auto"):
    verts, walls, room = _rect(80, 100, 320, 300)
    roof = {"id": "rf1", "level": "L1", "ridge": [[100, 200], [300, 200]],
            "eaves_h_in": 96.0, "ridge_h_in": 150.0, "span_in": [100, 100],
            "overhang_in": [12, 12], "gable": [True, True]}
    pyr = {"id": "pyr", "level": "L1", "kind": "pyramid_roof", "pos": [200, 200],
           "rotation": 0.0,
           "state": {"sides": 4, "inradius_in": 60.0, "eaves_bind": "manual",
                     "eaves_h_in": 110.0, "pitch_12": 12.0, "overhang_in": 10.0,
                     "weld": weld}}
    return _base(verts, walls, [room], [roof], [pyr])


def main():
    try:
        import jsonschema
        schema = json.loads((ROOT / "floorplanner" / "design"
                             / "design-schema.v6.json").read_text(encoding="utf-8"))
    except ImportError:
        schema = None
    cases = {"E2-octagon-bay-on-eave": e2(),
             "E4-square-astride-ridge": e4("auto"),
             "E5-weld-off-both-whole": e4("off")}
    for name, doc in cases.items():
        if schema is not None:
            import jsonschema
            jsonschema.validate(doc, schema)
        out = HERE / f"{name}.json"
        out.write_text(json.dumps(doc, indent=2) + "\n", encoding="utf-8")
        shot = HERE / f"{name}.png"
        subprocess.run([sys.executable, str(ROOT / "floorplanner" / "viewer" / "fp3d.py"),
                        str(out), "--shot", str(shot)], capture_output=True, text=True, cwd=ROOT)
        print(f"{name}: {'schema ok, ' if schema else ''}"
              f"{'shot ok' if shot.exists() else 'SHOT FAIL'}")


if __name__ == "__main__":
    main()
