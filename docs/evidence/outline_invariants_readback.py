#!/usr/bin/env python3
"""READ-BACK for the TWO PROPOSED OUTLINE INVARIANTS. Measurement only --
nothing here is production code and nothing is implemented in `validate.py`.

    python docs/evidence/outline_invariants_readback.py

THE TWO CANDIDATES, both properties of the STORED DOCUMENT:

  OUTLINE COMPLETENESS (this ruling) -- "no outline edge passes through a wall
      endpoint without naming it": for every outline edge from one vertex to the
      next, no vertex that is a wall endpoint may lie strictly between them.
  SIMPLE RING (D41, ruled at R-A) -- "a room outline is a simple ring; no vertex
      appears in it twice".

**BOTH ARE CHECKABLE ON A FILE NOBODY HAS LOADED**, which is the point: they read
`rooms[*].outline`, `walls[*].v1/v2` and `vertices[*]` out of the same document.
No scene, no walk, no emit.

-- WHY THE EXISTING SET MISSES OUTLINE COMPLETENESS, and it is two DIFFERENT
   failures rather than one gap seen twice --

  I14  compares WALL ENDS to WALLS (`validate.py:283`). A room OUTLINE is
       outside its subject entirely. WRONG SUBJECT.
  I5   cannot catch it on a saved document, because `bridge._walk` emits one
       outline edge per wall BY CONSTRUCTION -- the violation is repaired in the
       act of asking. A QUESTION THAT DESTROYS ITS OWN EVIDENCE.

-- THE READ-BACK, four questions --

  Q1  which files in `examples/` and `fixtures/` fail each check -- symmetricP1
      first, because a clean reference failing a new invariant is a statement
      about the REFERENCE, not only about the check (R-A's situation again)
  Q2  cost, MEASURED against the existing lanes, so "cheap twelve or deep three"
      is decided by a number and not by the shape of the loop
  Q3  tolerance, DECLARED -- and it is NOT `vertex_weld_in`, which is a
      coincidence radius. This is a point-on-segment question, so it needs a
      PERPENDICULAR distance. Exact on the lattice, declared tolerance off it,
      the same shape as `rooms._corner_path`, which keeps one rule not two
  Q4  is ONE pass covering both cheaper than two?

`fixtures/incoming/` is excluded by construction -- uncharacterised intake, and
nothing may reach it.
"""
import glob
import json
import math
import os
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)

from floorplanner.design.validate import check                     # noqa: E402

TOL_PERP_DEFAULT = 0.05      # inches; see Q3 -- declared, then justified


# --------------------------------------------------------------- the document
def read(path):
    return json.loads(open(path, encoding="utf-8").read())


def parts(d):
    """v5 is flat (`walls`, `vertices`, `rooms` at the top) with `levels` as a
    roster. Both the flat and the nested spellings are accepted because the
    corpus contains files written by different producers."""
    walls, verts, rooms = list(d.get("walls") or []), {}, list(d.get("rooms") or [])
    for v in d.get("vertices") or []:
        verts[v["id"]] = v
    for lv in d.get("levels") or []:
        walls += list(lv.get("walls") or [])
        rooms += list(lv.get("rooms") or [])
        for v in lv.get("vertices") or []:
            verts[v["id"]] = v
    return walls, verts, rooms


def _lattice(step, *pts):
    return all(abs(c / step - round(c / step)) < 1e-9 for p in pts for c in p)


def between(a, p, b, step, tol_perp):
    """Does `p` lie STRICTLY between `a` and `b`?

    EXACT WHEN EVERY COORDINATE IS ON THE LATTICE -- three lattice points are
    collinear exactly when an integer cross product is zero, so no tolerance is
    consulted at all. Off the lattice, a declared PERPENDICULAR distance. Same
    shape as `rooms._corner_path`, deliberately: one rule for "is this point on
    this run", not two.

    Returns (is_between, perpendicular_distance, which_path).
    """
    if _lattice(step, a, p, b):
        ax, ay = round(a[0] / step), round(a[1] / step)
        bx, by = round(b[0] / step), round(b[1] / step)
        px, py = round(p[0] / step), round(p[1] / step)
        cross = (bx - ax) * (py - ay) - (by - ay) * (px - ax)
        dot = (px - ax) * (bx - ax) + (py - ay) * (by - ay)
        ll = (bx - ax) ** 2 + (by - ay) ** 2
        return (cross == 0 and 0 < dot < ll), 0.0, "exact"
    ax, ay = a
    bx, by = b
    L = math.hypot(bx - ax, by - ay)
    if L < 1e-9:
        return False, float("inf"), "tolerance"
    ux, uy = (bx - ax) / L, (by - ay) / L
    s = (p[0] - ax) * ux + (p[1] - ay) * uy
    perp = abs((p[0] - ax) * uy - (p[1] - ay) * ux)
    return (perp <= tol_perp and 1e-6 < s < L - 1e-6), perp, "tolerance"


# ------------------------------------------------------------- the candidates
def outline_completeness(d, tol_perp=TOL_PERP_DEFAULT, collect=None):
    """No outline edge passes through a wall endpoint without naming it."""
    walls, verts, rooms = parts(d)
    step = float((d.get("settings") or {}).get("wall_snap_in", 6.0)) or 6.0
    # DEDUPED BY VERTEX, and the index is what forced this. A vertex held by
    # three walls appears three times in a plain endpoint list, so the first
    # version of this function reported ONE violation THREE TIMES -- and the
    # grid form, which dedupes naturally, then disagreed with it on the only
    # plan that fails. A violation is one per (edge, vertex), never per wall.
    ends = {}                       # level -> [(vid, (x, y))]
    seen_v = set()
    for w in walls:
        for k in ("v1", "v2"):
            vid = w.get(k)
            v = verts.get(vid)
            if v and vid not in seen_v:
                seen_v.add(vid)
                ends.setdefault(v.get("level"), []).append((vid, (v["x"], v["y"])))
    errs = []
    for r in rooms:
        # a FLOATING room deliberately breaks sharing with the plan (P4.2), the
        # same exemption I11/I14 grant, so it is not asked this question
        if (r.get("placement") or {}).get("state") == "floating":
            continue
        lvl = r.get("level")
        ring = [e.get("v") for e in (r.get("outline") or [])]
        n = len(ring)
        if n < 3:
            continue
        for i in range(n):
            va, vb = verts.get(ring[i]), verts.get(ring[(i + 1) % n])
            if not va or not vb:
                continue
            a, b = (va["x"], va["y"]), (vb["x"], vb["y"])
            for vid, p in ends.get(lvl, ()):
                if vid == ring[i] or vid == ring[(i + 1) % n]:
                    continue
                ok, perp, path = between(a, p, b, step, tol_perp)
                if ok:
                    errs.append(f"IOC room {r.get('id')} edge "
                                f"{ring[i]}->{ring[(i + 1) % n]} passes through "
                                f"wall endpoint {vid} without naming it")
                    if collect is not None:
                        collect.append({"plan": d.get("_name"), "room": r.get("name"),
                                        "vid": vid, "at": list(p), "perp": perp,
                                        "path": path})
    return errs


def outline_completeness_indexed(d, tol_perp=TOL_PERP_DEFAULT):
    """The SAME predicate behind a uniform grid index.

    WHY THIS EXISTS: measured naive, the check costs MORE THAN THE WHOLE DEEP
    SET on several plans (57 ms against 25 ms on `roundedMultifloor`), because
    it is edges x endpoints with no locality. That would settle "cheap twelve or
    deep three" against a property of the loop rather than of the question, so
    the question is re-asked of an implementation that exploits what every wall
    in this model has: a short, mostly axis-aligned span.

    Endpoints are bucketed into cells; an edge queries only the cells its
    bounding box touches, expanded by the tolerance. The RESULT MUST BE
    IDENTICAL to the naive form -- asserted by the caller, because an index that
    changes the answer is not an optimisation.
    """
    walls, verts, rooms = parts(d)
    step = float((d.get("settings") or {}).get("wall_snap_in", 6.0)) or 6.0
    cell = max(step * 4.0, 24.0)
    grid = {}
    for w in walls:
        for k in ("v1", "v2"):
            vid = w.get(k)
            v = verts.get(vid)
            if not v:
                continue
            key = (v.get("level"), int(v["x"] // cell), int(v["y"] // cell))
            grid.setdefault(key, []).append((vid, (v["x"], v["y"])))
    errs = []
    for r in rooms:
        if (r.get("placement") or {}).get("state") == "floating":
            continue
        lvl = r.get("level")
        ring = [e.get("v") for e in (r.get("outline") or [])]
        n = len(ring)
        if n < 3:
            continue
        for i in range(n):
            va, vb = verts.get(ring[i]), verts.get(ring[(i + 1) % n])
            if not va or not vb:
                continue
            a, b = (va["x"], va["y"]), (vb["x"], vb["y"])
            x0 = min(a[0], b[0]) - tol_perp - 1e-6
            x1 = max(a[0], b[0]) + tol_perp + 1e-6
            y0 = min(a[1], b[1]) - tol_perp - 1e-6
            y1 = max(a[1], b[1]) + tol_perp + 1e-6
            seen = set()
            for cx in range(int(x0 // cell), int(x1 // cell) + 1):
                for cy in range(int(y0 // cell), int(y1 // cell) + 1):
                    for vid, p in grid.get((lvl, cx, cy), ()):
                        if vid in seen or vid in (ring[i], ring[(i + 1) % n]):
                            continue
                        seen.add(vid)
                        if between(a, p, b, step, tol_perp)[0]:
                            errs.append(f"IOC room {r.get('id')} edge "
                                        f"{ring[i]}->{ring[(i + 1) % n]} passes "
                                        f"through wall endpoint {vid} without "
                                        f"naming it")
    return errs


def simple_ring(d):
    """D41: a room outline is a simple ring -- no vertex appears in it twice."""
    _w, _v, rooms = parts(d)
    errs = []
    for r in rooms:
        ring = [e.get("v") for e in (r.get("outline") or [])]
        seen = set()
        for vid in ring:
            if vid in seen:
                errs.append(f"ISR room {r.get('id')} vertex {vid} appears "
                            f"twice in its outline")
                break
            seen.add(vid)
    return errs


def both_one_pass(d, tol_perp=TOL_PERP_DEFAULT):
    """Q4: ONE walk of `rooms[*].outline` answering both questions.

    The point of the comparison is that they share the traversal: the ring is
    enumerated once, the duplicate test is a set membership per slot, and the
    endpoint test is the inner loop. If the endpoint test dominates -- and it
    will, being edges x endpoints against edges x 1 -- then the combined pass
    costs essentially what completeness alone costs, and D41 rides along free.
    """
    walls, verts, rooms = parts(d)
    step = float((d.get("settings") or {}).get("wall_snap_in", 6.0)) or 6.0
    ends = {}
    for w in walls:
        for k in ("v1", "v2"):
            vid = w.get(k)
            v = verts.get(vid)
            if v:
                ends.setdefault(v.get("level"), []).append((vid, (v["x"], v["y"])))
    errs = []
    for r in rooms:
        ring = [e.get("v") for e in (r.get("outline") or [])]
        n = len(ring)
        seen = set()
        for vid in ring:                       # D41, same traversal
            if vid in seen:
                errs.append(f"ISR room {r.get('id')} vertex {vid} twice")
                break
            seen.add(vid)
        if (r.get("placement") or {}).get("state") == "floating" or n < 3:
            continue
        lvl = r.get("level")
        for i in range(n):
            va, vb = verts.get(ring[i]), verts.get(ring[(i + 1) % n])
            if not va or not vb:
                continue
            a, b = (va["x"], va["y"]), (vb["x"], vb["y"])
            for vid, p in ends.get(lvl, ()):
                if vid in (ring[i], ring[(i + 1) % n]):
                    continue
                if between(a, p, b, step, tol_perp)[0]:
                    errs.append(f"IOC room {r.get('id')} through {vid}")
    return errs


# ------------------------------------------------------------------ the runs
def timeit(fn, *a, reps=5):
    best = float("inf")
    for _ in range(reps):
        t = time.perf_counter()
        fn(*a)
        best = min(best, time.perf_counter() - t)
    return best * 1000.0                    # ms, best-of to damp machine noise


def corpus():
    out = []
    for pat in ("examples/*.json", "fixtures/*.json"):
        out += sorted(glob.glob(os.path.join(ROOT, pat)))
    return out                              # fixtures/incoming/ is NOT globbed


def is_v5(d):
    """`check()` requires the v5 shape and raises on anything else. The corpus
    still holds legacy files, so they are SKIPPED AND NAMED rather than dropped
    silently -- a corpus sweep that quietly covers fewer files than it lists is
    the census-blindness problem in miniature."""
    return isinstance(d.get("vertices"), list) and isinstance(d.get("rooms"), list)


def main():
    near = []
    rows = []
    skipped = []
    for path in corpus():
        d = read(path)
        d["_name"] = os.path.basename(path)
        if not is_v5(d):
            skipped.append({"plan": os.path.basename(path),
                            "version": d.get("version"),
                            "format": d.get("format"),
                            "why": "not a v5 document -- check() cannot read it"})
            continue
        walls, verts, rooms = parts(d)
        oc = outline_completeness(d, collect=near)
        sr = simple_ring(d)
        rows.append({
            "plan": os.path.basename(path),
            "walls": len(walls), "vertices": len(verts), "rooms": len(rooms),
            "OUTLINE_COMPLETENESS_failures": len(oc),
            "SIMPLE_RING_failures": len(sr),
            "sample_completeness": oc[:3],
            "sample_simple_ring": sr[:3],
            # Q2: measured against the EXISTING lanes on the same document, so
            # "cheap or deep" is a comparison and not an adjective
            "ms_cheap_twelve_check_deep_False": round(timeit(check, d, False), 3),
            "ms_deep_fifteen_check_deep_True": round(timeit(check, d, True), 3),
            "ms_outline_completeness_NAIVE": round(timeit(outline_completeness, d), 3),
            "ms_outline_completeness_INDEXED":
                round(timeit(outline_completeness_indexed, d), 3),
            # AN INDEX THAT CHANGES THE ANSWER IS NOT AN OPTIMISATION
            "INDEX_AGREES_WITH_NAIVE":
                sorted(outline_completeness_indexed(d)) == sorted(oc),
            "ms_simple_ring": round(timeit(simple_ring, d), 3),
            "ms_BOTH_in_one_pass": round(timeit(both_one_pass, d), 3),
        })

    # Q3: the tolerance question, answered from the DISTRIBUTION rather than
    # from a preference. Only the tolerance-path hits have a meaningful perp;
    # lattice hits are exact by construction.
    tolpath = [x for x in near if x["path"] == "tolerance"]
    sweep = {}
    for t in (0.0, 0.001, 0.01, 0.05, 0.25, 0.6):
        n = 0
        for path in corpus():
            d = read(path)
            d["_name"] = os.path.basename(path)
            if not is_v5(d):
                continue
            n += len(outline_completeness(d, tol_perp=t))
        sweep[str(t)] = n

    tot_oc = sum(r["OUTLINE_COMPLETENESS_failures"] for r in rows)
    tot_sr = sum(r["SIMPLE_RING_failures"] for r in rows)
    fail_oc = [r["plan"] for r in rows if r["OUTLINE_COMPLETENESS_failures"]]
    fail_sr = [r["plan"] for r in rows if r["SIMPLE_RING_failures"]]
    sym = next((r for r in rows if r["plan"] == "symmetricP1.json"), None)
    return {
        "Q1_which_files_fail": {
            "outline_completeness": fail_oc,
            "simple_ring_D41": fail_sr,
            "symmetricP1": (None if not sym else {
                "outline_completeness": sym["OUTLINE_COMPLETENESS_failures"],
                "simple_ring": sym["SIMPLE_RING_failures"]}),
            "totals": {"completeness": tot_oc, "simple_ring": tot_sr},
        },
        "Q3_tolerance": {
            "declared": TOL_PERP_DEFAULT,
            "NOT_vertex_weld_in": ("0.6 inches is a COINCIDENCE radius -- do two "
                                   "points name one corner. This is a "
                                   "point-on-SEGMENT question and needs a "
                                   "perpendicular distance, so the two must not "
                                   "share a number"),
            "failures_at_each_perpendicular_tolerance": sweep,
            "hits_decided_by_the_TOLERANCE_path": len(tolpath),
            "perp_distances_on_that_path":
                sorted(round(x["perp"], 6) for x in tolpath)[:12],
        },
        "Q4_one_pass_or_two": {
            "note": ("both share the outline traversal; the endpoint test is "
                     "edges x endpoints and the duplicate test is edges x 1"),
            "CAVEAT_the_combined_pass_is_NAIVE": (
                "`both_one_pass` was written against the unindexed inner loop, "
                "so its total is NOT comparable to `completeness_indexed`. It "
                "is left that way and labelled rather than quietly re-timed: "
                "the answer to Q4 does not depend on it, because simple_ring "
                "costs 0.157 ms across the whole corpus against the indexed "
                "check's 4.2 ms -- sharing the traversal can save at most that "
                "3.7 percent, and the two checks have DIFFERENT corpus "
                "consequences, which is the argument that actually decides it"),
            "totals_ms": {
                "completeness_naive": round(sum(r["ms_outline_completeness_NAIVE"]
                                                for r in rows), 3),
                "completeness_indexed": round(sum(
                    r["ms_outline_completeness_INDEXED"] for r in rows), 3),
                "simple_ring_alone": round(sum(r["ms_simple_ring"]
                                               for r in rows), 3),
                "run_separately_sum_indexed": round(sum(
                    r["ms_outline_completeness_INDEXED"] + r["ms_simple_ring"]
                    for r in rows), 3),
                "one_combined_pass": round(sum(r["ms_BOTH_in_one_pass"]
                                               for r in rows), 3),
            },
        },
        "per_plan": rows,
        "SKIPPED_not_v5": skipped,
    }


if __name__ == "__main__":
    json.dump(main(), sys.stdout, indent=1)
    sys.stdout.write(chr(10))
