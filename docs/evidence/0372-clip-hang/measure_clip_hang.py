"""0372 item C — measure the compute_roof_clips hang (loop vs blow-up).

Loads a repro document, instruments the path-loaded ROOFCLIP module's hot
functions with counters + a wall-clock deadline, runs the real build_model,
and reports: rounds, per-round piece counts, _adjacent calls, _reach calls and
total frontier visits. No module is edited; measurement is by monkeypatch.
"""
import argparse
import json
import os
import sys
import time

# repo root (…/FloorPlanner), so `import FloorPlanner` resolves when this is
# run by path from the repo root: python docs/evidence/0372-clip-hang/…
sys.path.insert(0, os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..")))
os.environ["QT_QPA_PLATFORM"] = "offscreen"
from PyQt6.QtWidgets import QApplication  # noqa: E402
_app = QApplication.instance() or QApplication([])

import FloorPlanner  # noqa: E402,F401
from floorplanner.viewer import fp3d  # noqa: E402

RC = fp3d.ROOFCLIP

ap = argparse.ArgumentParser()
ap.add_argument("plan")
ap.add_argument("--deadline", type=float, default=25.0, help="wall-clock seconds")
ap.add_argument("--round-cap", type=int, default=400)
ap.add_argument("--keep", default="", help="comma roof ids to keep (else all)")
args = ap.parse_args()

with open(args.plan, "r", encoding="utf-8") as fh:
    doc = json.load(fh)

if args.keep:
    keep = set(args.keep.split(","))
    doc["roofs"] = [r for r in doc.get("roofs", []) if r.get("id") in keep]

n_roofs = len(doc.get("roofs", []))
print(f"roofs in doc: {n_roofs}  ids={[r.get('id') for r in doc.get('roofs', [])]}")


class Measured(Exception):
    pass


stats = {
    "adjacent": 0,
    "reach_calls": 0,
    "reach_visits": 0,
    "neighbour_builds": 0,
    "rounds": [],          # (piece_count, adjacent_so_far, t_since_start)
    "tripped": None,
}
t0 = time.perf_counter()

_orig_adjacent = RC._adjacent
_orig_reach = RC._reach
_orig_neighbours = RC._neighbours
_last_pieces = [None]


def adjacent(a, b, tol=1e-5):
    stats["adjacent"] += 1
    if stats["adjacent"] % 20000 == 0:
        if time.perf_counter() - t0 > args.deadline:
            stats["tripped"] = "deadline"
            raise Measured
    return _orig_adjacent(a, b, tol)


def neighbours(pieces, tol=1e-5):
    # a rebuild (new pieces identity) marks a new envelope round
    if pieces is not _last_pieces[0]:
        _last_pieces[0] = pieces
        stats["neighbour_builds"] += 1
        stats["rounds"].append(
            (len(pieces), stats["adjacent"], round(time.perf_counter() - t0, 2)))
        if len(stats["rounds"]) > args.round_cap:
            stats["tripped"] = "round-cap"
            raise Measured
    return _orig_neighbours(pieces, tol)


def reach(start, pieces, allowed, blocked, no_step=None):
    stats["reach_calls"] += 1
    res = _orig_reach(start, pieces, allowed, blocked, no_step)
    stats["reach_visits"] += len(res)
    return res


RC._adjacent = adjacent
RC._neighbours = neighbours
RC._reach = reach

print(f"running build_model (deadline {args.deadline}s, round-cap {args.round_cap}) ...")
err = None
try:
    fp3d.build_model(doc)
    print("build_model RETURNED (no hang on this input)")
except Measured:
    pass
except Exception as e:  # noqa: BLE001
    err = e
elapsed = time.perf_counter() - t0

r = stats["rounds"]
print(f"\n=== RESULT  (tripped: {stats['tripped']}, elapsed {elapsed:.1f}s) ===")
print(f"envelope rounds observed : {len(r)}")
print(f"_adjacent calls          : {stats['adjacent']:,}")
print(f"_reach calls             : {stats['reach_calls']:,}")
print(f"_reach total visits      : {stats['reach_visits']:,}")
if r:
    pcs = [p for p, _, _ in r]
    print(f"piece count per round    : first={pcs[0]} min={min(pcs)} max={max(pcs)} last={pcs[-1]}")
    print("round / pieces / adj_cumulative / t:")
    for i, row in enumerate(r):
        if i < 6 or i >= len(r) - 6 or len(r) <= 16:
            print(f"  {i:4d}  pieces={row[0]:5d}  adj={row[1]:>12,}  t={row[2]}")
        elif i == 6:
            print("   ...")
if err is not None:
    print(f"\n(build raised before trip: {type(err).__name__}: {err})")
