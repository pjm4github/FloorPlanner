"""0367 stage 2 -- C3 differential receipt.

Condition C3 (0367-ruling.md): "Every fixture with no pyramid builds the same
before and after. Triangle count and bounds, per file, every difference named."

Here "before" is the branch base (stage 1, 24601ac -- fp3d had NO pyramid code),
"after" is the working tree. Both build the SAME no-pyramid documents, each one
chosen to exercise a path the stage-2 wall-climb touched (`_wall_under_roofs`'s
surface-height, its `_cut_lines` split, and the gable climb). For every mesh we
compare the triangle count and the rounded (x, y, z) bounds; any difference is
named. A no-pyramid build must be byte-for-byte in these terms, because the only
new code runs when a pyramid is present (`pyramid_terr` is empty otherwise and
the dispatchers take the ridge-roof branch).

Run:  python docs/evidence/0367-pyramid-roof/c3_differential.py
It writes C3-differential.json next to itself and exits non-zero on any diff.
"""
import importlib.util
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
BASE = "24601ac"                         # stage 1: fp3d without any pyramid code


def _load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def _docs():
    """No-pyramid documents, each touching the wall-climb paths stage 2 edited."""
    meet_y = 100.0 + (150.0 - 136.0) / 0.54
    gable = {"id": "g", "level": "L1", "ridge": [[0, 100], [400, 100]],
             "eaves_h_in": 96.0, "ridge_h_in": 150.0, "overhang_in": [12, 12],
             "span_in": [100, 100], "gable": [True, True]}
    dormer = {"id": "d", "level": "L1", "ridge": [[200, 190], [200, meet_y]],
              "eaves_h_in": 116.0, "ridge_h_in": 136.0, "overhang_in": [0, 0],
              "span_in": [30, 30], "gable": [True, True], "host": "g"}
    cross = {"id": "x", "level": "L1", "ridge": [[200, 0], [200, 200]],
             "eaves_h_in": 96.0, "ridge_h_in": 140.0, "overhang_in": [12, 12],
             "span_in": [80, 80], "gable": [True, True]}
    verts = [{"id": "a", "x": 40, "y": 170}, {"id": "b", "x": 360, "y": 170},
             {"id": "c", "x": 360, "y": 30}, {"id": "d", "x": 40, "y": 30}]
    walls = [{"id": "w1", "level": "L1", "v1": "a", "v2": "b", "type": "exterior"},
             {"id": "w2", "level": "L1", "v1": "b", "v2": "c", "type": "exterior"},
             {"id": "w3", "level": "L1", "v1": "c", "v2": "d", "type": "exterior"},
             {"id": "w4", "level": "L1", "v1": "d", "v2": "a", "type": "exterior"}]
    room = {"id": "r", "level": "L1", "category": "interior", "ceiling_in": 96.0,
            "outline": [{"v": v["id"]} for v in verts]}
    lv = [{"id": "L1", "elevation_in": 0.0, "height_in": 96.0}]
    base = {"levels": lv, "vertices": verts, "walls": walls, "rooms": [room]}
    return {
        "gable+walls": {**base, "furnishings": [], "roofs": [gable]},
        "gable+dormer+walls": {**base, "furnishings": [], "roofs": [gable, dormer]},
        "cross-gable+walls": {**base, "furnishings": [],
                              "roofs": [gable, cross]},
        "walls-no-roof": {**base, "furnishings": [], "roofs": []},
    }


def _sig(model):
    out = []
    for m in model.meshes:
        v = m.verts
        bounds = ([round(float(v[:, i].min()), 6) for i in range(3)]
                  + [round(float(v[:, i].max()), 6) for i in range(3)]) if len(v) else []
        out.append([m.name, int(len(m.faces)), bounds])
    out.sort()
    return out


def main():
    tmp = Path(tempfile.gettempdir()) / "fp3d_stage1_c3.py"
    tmp.write_text(subprocess.check_output(
        ["git", "show", f"{BASE}:floorplanner/viewer/fp3d.py"],
        cwd=ROOT, text=True), encoding="utf-8")
    cur = _load(ROOT / "floorplanner" / "viewer" / "fp3d.py", "_fp3d_cur")
    old = _load(tmp, "_fp3d_old")
    # the old module sits in a temp dir, so its BY-PATH lookups for roofclip and
    # dormer_geometry fail there; inject the current ones (unchanged on this
    # branch -- only fp3d was touched) so the before/after differ ONLY by fp3d.
    old.ROOFCLIP = cur.ROOFCLIP
    old.DORMERGEO = cur.DORMERGEO
    cat = cur.load_catalog()                 # found from the repo; handed to both

    report, ok = {}, True
    for name, doc in _docs().items():
        a = _sig(old.build_model(doc, catalog=cat, floors=False, furnishings=False))
        b = _sig(cur.build_model(doc, catalog=cat, floors=False, furnishings=False))
        same = a == b
        ok = ok and same
        diffs = []
        if not same:
            for x, y in zip(a, b, strict=False):
                if x != y:
                    diffs.append({"before": x, "after": y})
        report[name] = {"identical": same, "meshes": len(b), "diffs": diffs}

    result = {"base": BASE, "metric": "per-mesh triangle count + rounded bounds",
              "verdict": "PASS -- every no-pyramid build is identical" if ok
              else "FAIL -- differences named below", "files": report}
    (Path(__file__).with_name("C3-differential.json")).write_text(
        json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(result["verdict"])
    for n, r in report.items():
        print(f"  {n}: {'same' if r['identical'] else 'DIFF'} ({r['meshes']} meshes)")
    os.remove(tmp)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
