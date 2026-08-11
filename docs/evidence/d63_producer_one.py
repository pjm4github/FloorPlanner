#!/usr/bin/env python3
"""D63 PRODUCER 1: WHY THE SAVE PUTS BACK THE CORNERS THE COALESCE REMOVED

    python docs/evidence/d63_producer_one.py <plan.json> [more.json ...]

THE CANDIDATE MECHANISM, and it is written down in the code that does it.
`bridge._walk` (`design/bridge.py:348`):

    "A room edge whose span was split at a T-junction is several walls, not
     one; each hop becomes its own outline edge so that every outline edge
     maps to exactly one wall (invariant I5)."

So if the outline coalesce removes a corner where a wall still ENDS -- a
T-junction the room edge must cross -- the save cannot represent that edge as
one edge. It walks the chain and emits one outline edge per wall, putting the
corner straight back. **That would make producer 1 not a save-side bug at all,
but the coalesce removing a corner the document model requires.**

THE TEST: for every corner the save re-inserts, ask what is at that point in the
COALESCED scene, before the save.

  a wall END there            -> I5 requires the hop; the coalesce was wrong
  nothing there at all        -> the save is inventing it; the save is wrong

CONTROLS
  POSITIVE  the same question asked of corners the coalesce removed and the
            save did NOT put back. If those also have a wall end at them, the
            predicate below does not discriminate and proves nothing.
  the re-inserted set is obtained by DIFFING the saved document against the
  scene that produced it -- not by re-deriving it from a rule.
"""
import json
import math
import os
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from d61_normalize_outline_arrow import (                        # noqa: E402
    open_plan, _rooms_of, _walls_of,
)

import floorplanner.rooms as R                                   # noqa: E402
import floorplanner.walls as W                                   # noqa: E402

TOL = 0.05


def outline_pts(win):
    out = {}
    for r in _rooms_of(win):
        out.setdefault(r.name, []).extend(
            (round(e.p.x(), 3), round(e.p.y(), 3)) for e in r.outline)
    return out


def file_pts(path):
    d = json.loads(open(path, encoding="utf-8").read())
    V = {v["id"]: (round(v["x"], 3), round(v["y"], 3))
         for v in d.get("vertices", ())}
    out = {}
    for r in d.get("rooms", ()):
        out.setdefault(r["name"], []).extend(
            V[e["v"]] for e in r.get("outline", ()) if e.get("v") in V)
    return out


def bag_diff(a, b):
    rest, gone = list(b), []
    for p in a:
        hit = next((q for q in rest if math.dist(p, q) <= TOL), None)
        if hit is None:
            gone.append(p)
        else:
            rest.remove(hit)
    return gone


def probe_point(win, pt):
    """What is AT this point in the scene: wall ends, and bodies crossing it."""
    ends = 0
    bodies = 0
    for w in _walls_of(win):
        for q in (w.p1, w.p2):
            if math.dist((q.x(), q.y()), pt) <= TOL:
                ends += 1
        # does the point lie strictly INSIDE this wall's span?
        ax, ay, bx, by = w.p1.x(), w.p1.y(), w.p2.x(), w.p2.y()
        L = math.hypot(bx - ax, by - ay)
        if L < 1e-6:
            continue
        ux, uy = (bx - ax) / L, (by - ay) / L
        s = (pt[0] - ax) * ux + (pt[1] - ay) * uy
        if 0.5 < s < L - 0.5:
            perp = abs((pt[0] - ax) * uy - (pt[1] - ay) * ux)
            if perp <= TOL:
                bodies += 1
    return {"wall_ends_here": ends, "wall_bodies_crossing": bodies}


def run(path):
    name = os.path.basename(path)
    win = open_plan(path)
    W.normalize_walls(win.scene)
    before = outline_pts(win)
    R.coalesce_outline_corners(win.scene, dry_run=False)
    after = outline_pts(win)
    tmp = os.path.join(tempfile.gettempdir(), f"p1-{name}")
    win.save_path(tmp)
    infile = file_pts(tmp)

    removed, reinserted = [], []
    for room in sorted(set(before) | set(infile)):
        for p in bag_diff(before.get(room, []), after.get(room, [])):
            removed.append((room, p))
        for p in bag_diff(infile.get(room, []), after.get(room, [])):
            reinserted.append((room, p))

    rein_pts = [p for _, p in reinserted]
    stayed = [(rm, p) for rm, p in removed
              if not any(math.dist(p, q) <= TOL for q in rein_pts)]

    def survey(items):
        return [{"room": rm, "at": list(p), **probe_point(win, p)}
                for rm, p in items]

    rein = survey(reinserted)
    kept = survey(stayed)
    win.close()

    n_end_rein = sum(1 for r in rein if r["wall_ends_here"])
    n_end_kept = sum(1 for r in kept if r["wall_ends_here"])
    return {
        "plan": name,
        "removed_by_the_coalesce": len(removed),
        "REINSERTED_by_the_save": len(rein),
        "stayed_removed": len(kept),
        "of_the_REINSERTED_how_many_have_a_wall_END_there": n_end_rein,
        "of_those_that_STAYED_how_many_have_a_wall_END_there": n_end_kept,
        "POSITIVE_CONTROL_the_predicate_discriminates": {
            "claim": ("if a wall end explains re-insertion, the corners that "
                      "STAYED removed must mostly NOT have one -- otherwise "
                      "the predicate is true of everything and explains "
                      "nothing"),
            "reinserted_with_a_wall_end": f"{n_end_rein}/{len(rein)}",
            "stayed_with_a_wall_end": f"{n_end_kept}/{len(kept)}",
            "verdict": ("PASS" if (rein and n_end_rein == len(rein)
                                   and n_end_kept == 0) else
                        "PARTIAL" if rein and n_end_rein > n_end_kept else
                        "no re-insertions on this plan" if not rein else
                        "FAIL -- the predicate does not discriminate"),
        },
        "reinserted_detail": rein,
        "stayed_detail": kept[:8],
        "VERDICT": (
            "no rebound on this plan"
            if not rein else
            "I5 REQUIRES THE HOP -- the coalesce removed a corner a wall ends "
            "at, and the save must split the edge there"
            if n_end_rein == len(rein) else
            "MIXED -- some re-inserted corners have no wall end at them"),
    }


if __name__ == "__main__":
    json.dump({
        "question": ("is producer 1 the save inventing corners, or the "
                     "coalesce removing corners invariant I5 requires?"),
        "plans": [run(os.path.abspath(p)) for p in sys.argv[1:]],
    }, sys.stdout, indent=1)
    sys.stdout.write(chr(10))
