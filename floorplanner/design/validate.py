"""Validate a v5 design document against the JSON Schema AND the referential
invariants JSON Schema cannot express.  The invariants are the contract that
makes this file a source of truth rather than a dump.

`check(doc) -> list[str]` is the importable invariant checker (pure Python, no
third-party imports, safe to call from the app's shadow-mode verification).
`schema_errors(doc) -> list[str]` validates against the packaged JSON Schema and
lazy-imports `jsonschema` (a dev/test dependency, never shipped).

Ported from tools/validate_design.py at P0.7; that script is now a thin CLI
over this module.
"""
import json
import math
import re
from pathlib import Path

STD_T = {"exterior": 6.0, "interior": 4.5, "partition": 3.5,
         "railing": 2.0, "fence": 2.0, "hedge": 18.0, "retaining": 8.0}
"""THE NORMATIVE wall thickness by type, in inches -- ONE TABLE (D73).

The schema calls this a contract: `wall.thickness_in` is documented as
*"Override; omitted = the standard for `type`"*, so **"the standard for `type`"
has to be somewhere**, and the model layer is where a contract the schema names
belongs.

**IT USED TO BE THREE TABLES.** `viewer/fp3d.py` carried its own `WALL_T` and the
scene carried a two-branch conditional over `EXTERIOR_T`/`INTERIOR_T` that knew
none of the landscape types -- and the two tables DISAGREED on `hedge`, 18.0 here
against 12.0 there, while this one was **never read by anything**. Both duplicates
are now readers of this dict rather than copies of it, because three tables that
are synced become three tables that disagree again.

**`hedge` is 18.0 BECAUSE IT IS THE MODEL'S VALUE, not because 18 is a better
number for a hedge.** Nothing was measured to depend on 12.0: the corpus holds
one hedge wall, no test asserts its thickness, and the only consumer was the
viewer's renderer. The visible effect is that one wall in `site_demo` renders
50% thicker.

**A Qt-free consumer must NOT `import floorplanner.design.validate` to read
this.** Measured: that import drags in the Qt bindings, because
`floorplanner/__init__.py` star-imports the editor -- so `viewer/fp3d.py`, which
runs headless in CI on numpy alone, loads this module BY PATH instead. This
module itself imports only `json`, `math` and `pathlib`, which is what makes
that safe.

(The name of those bindings is deliberately not written here: this file is
guarded by a SOURCE-TEXT check, `test_design_module_source_is_qt_free`, which
cannot tell code from prose -- the same boundary the gate's `end_assign` check
has. Tripping it with a comment would be a false positive in the one file whose
Qt-freeness is load-bearing.)"""

SCHEMA_PATH = Path(__file__).with_name("design-schema.v5.json")


def load_schema() -> dict:
    """The packaged v5 JSON Schema as a dict."""
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


def schema_errors(doc, schema=None) -> list:
    """JSON-Schema (Draft 2020-12) errors for `doc`, as 'path: message' strings.
    Lazy-imports jsonschema so importing this module never requires it."""
    import jsonschema           # dev/test dependency; not needed to import this
    if schema is None:
        schema = load_schema()
    errs = sorted(jsonschema.Draft202012Validator(schema).iter_errors(doc),
                  key=lambda e: list(e.path))
    return [f"{list(e.path)}: {e.message}" for e in errs]


def _area2(pts):
    n = len(pts)
    return sum(pts[i][0] * pts[(i + 1) % n][1] - pts[(i + 1) % n][0] * pts[i][1]
               for i in range(n))


def _pip(q, pts):
    x, y = q
    ins = False
    n = len(pts)
    for i in range(n):
        x1, y1 = pts[i]
        x2, y2 = pts[(i + 1) % n]
        if (y1 > y) != (y2 > y):
            if x < x1 + (y - y1) * (x2 - x1) / (y2 - y1):
                ins = not ins
    return ins


def _seg_cross(a, b, c, d, tol=1e-4):
    """Proper crossing test.  The cross product is divided by the segment length
    so `tol` is a real perpendicular distance in INCHES -- collinear edges that
    two rooms legitimately share must not read as a crossing, and at plan scale
    a raw 1e-9 epsilon on the cross product is far too tight to guarantee that."""
    def o(p, q, r):
        lv = math.hypot(q[0] - p[0], q[1] - p[1]) or 1.0
        return ((q[0] - p[0]) * (r[1] - p[1]) - (q[1] - p[1]) * (r[0] - p[0])) / lv

    def sgn(v):
        return 0 if abs(v) < tol else (1 if v > 0 else -1)
    return (sgn(o(a, b, c)) * sgn(o(a, b, d)) < 0
            and sgn(o(c, d, a)) * sgn(o(c, d, b)) < 0)


def check(d, deep=True, boundary=False):
    """Referential-invariant errors for a v5 design, as a list of strings ([] is
    valid). There are 15 named checks; three are O(n^2) and gated behind `deep`:

      deep-only (3): I5b room-outline self-intersection (O(edges^2) per room),
        I11 room-vs-room overlap (O(rooms^2)), I14 weld closure (O(walls^2) --
        ~6,700 pairs on an 82-wall plan). I11 and I14 are the two that caught the
        real M Bath / Hall corruption in planc1.json.
      always-on (12): I1 I2 I3 I4 I5 I6 I7 I8 I9 I10 I12 I13.

    Call sites drive the split: the cheap twelve run per mutation under P1.6's
    `--verify-design`, where an O(n^2) sweep after every edit would make the app
    unusable; the deep three run on save, load and import -- paid once, where the
    stakes are highest. `deep=True` (the default) runs all fifteen; pass
    `deep=False` for the per-command path."""
    E = []
    V = {v["id"]: v for v in d["vertices"]}
    W = {w["id"]: w for w in d["walls"]}
    R = {r["id"]: r for r in d["rooms"]}
    LV = {lv["id"] for lv in d["levels"]}

    def xy(v):
        return (V[v]["x"], V[v]["y"])

    def poly(r):
        return [xy(e["v"]) for e in r["outline"]]

    # I1 ids unique document-wide
    seen = set()
    for coll in ("levels", "vertices", "walls", "rooms", "furnishings", "groups"):
        for o in d.get(coll, []):
            if o["id"] in seen:
                E.append(f"I1  duplicate id {o['id']}")
            seen.add(o["id"])
    for w in d["walls"]:
        for op in w.get("openings", []):
            if op["id"] in seen:
                E.append(f"I1  duplicate id {op['id']}")
            seen.add(op["id"])

    # I2 references resolve, on the same level
    for v in d["vertices"]:
        if v["level"] not in LV:
            E.append(f"I2  vertex {v['id']} -> unknown level")
    for w in d["walls"]:
        for k in ("v1", "v2"):
            if w[k] not in V:
                E.append(f"I2  wall {w['id']}.{k} -> missing vertex")
            elif V[w[k]]["level"] != w["level"]:
                E.append(f"I2  wall {w['id']}.{k} on another level")
        # I3 non-degenerate
        if w["v1"] == w["v2"]:
            E.append(f"I3  wall {w['id']} degenerate")

    # I4 no two walls on the same vertex pair  <- coincident copies unrepresentable
    pairs = {}
    for w in d["walls"]:
        k = (w["level"], *sorted((w["v1"], w["v2"])))
        if k in pairs:
            E.append(f"I4  walls {pairs[k]} and {w['id']} share a vertex pair")
        pairs[k] = w["id"]

    # I5 outline is a closed loop of same-level vertices; every bound wall
    #    spans exactly that edge (direction is derived, never stored)
    for r in d["rooms"]:
        n = len(r["outline"])
        for i, e in enumerate(r["outline"]):
            if e["v"] not in V:
                E.append(f"I5  room {r['id']} -> missing vertex {e['v']}")
                continue
            if V[e["v"]]["level"] != r["level"]:
                E.append(f"I5  room {r['id']} corner {e['v']} on another level")
            nv = r["outline"][(i + 1) % n]["v"]
            if e["v"] == nv:
                E.append(f"I5  room {r['id']} repeats corner {e['v']}")
            if e.get("wall"):
                w = W.get(e["wall"])
                if w is None:
                    E.append(f"I5  room {r['id']} -> missing wall {e['wall']}")
                elif {w["v1"], w["v2"]} != {e["v"], nv}:
                    E.append(f"I5  room {r['id']} edge {i}: wall {w['id']} does "
                             f"not span {e['v']}->{nv}")
        # I5b simple polygon (non-self-intersecting) -- O(edges^2), deep only
        if deep:
            p = poly(r)
            for i in range(n):
                for j in range(i + 2, n):
                    if i == 0 and j == n - 1:
                        continue
                    if _seg_cross(p[i], p[(i + 1) % n], p[j], p[(j + 1) % n]):
                        E.append(f"I5b room {r['id']} ({r['name']}) outline "
                                 f"self-intersects at edges {i}/{j}")
                        break
                else:
                    continue
                break

    # I6 wall.left/right agree with the room outlines that name it
    used = {}
    for r in d["rooms"]:
        for e in r["outline"]:
            if e.get("wall"):
                used.setdefault(e["wall"], set()).add(r["id"])
    for w in d["walls"]:
        stored = {s for s in (w.get("left"), w.get("right")) if s}
        derived = used.get(w["id"], set())
        if stored != derived:
            E.append(f"I6  wall {w['id']} sides {sorted(stored)} != outline "
                     f"users {sorted(derived)}")
        for s in stored:
            if s not in R:
                E.append(f"I6  wall {w['id']} -> missing room {s}")

    # I7 openings fit their wall, do not overlap, and only on buildable types
    for w in d["walls"]:
        ops = w.get("openings") or []
        if not ops:
            continue
        if w["type"] in ("railing", "fence", "hedge", "retaining"):
            for op in ops:                     # only gates belong in landscape walls
                if op["kind"] != "gate":
                    E.append(f"I7  {w['type']} wall {w['id']} carries a "
                             f"{op['kind']} ({op['id']}); only gates are allowed")
        L = math.dist(xy(w["v1"]), xy(w["v2"]))
        spans = []
        for op in ops:
            c = op["code"]
            k = 2 if len(c) == 4 else 3
            ow = float(c[:k])
            off = op["anchor"]["offset_in"]
            fr = op["anchor"]["from"]
            s0 = off if fr == "v1" else (L - off - ow if fr == "v2"
                                         else L / 2 + off - ow / 2)
            if s0 < -1e-6 or s0 + ow > L + 1e-6:
                E.append(f"I7  opening {op['id']} runs off wall {w['id']} "
                         f"({s0:.1f}..{s0 + ow:.1f} of {L:.1f})")
            spans.append((s0, s0 + ow, op["id"]))
        spans.sort()
        for (_a0, a1, ai), (b0, _b1, bi) in zip(spans, spans[1:], strict=False):
            if b0 < a1 - 1e-6:
                E.append(f"I7  openings {ai}/{bi} overlap on {w['id']}")

    # I8 furnishing owner exists, same level
    for f in d.get("furnishings", []):
        if f.get("room"):
            if f["room"] not in R:
                E.append(f"I8  furnishing {f['id']} -> missing room {f['room']}")
            elif R[f["room"]]["level"] != f["level"]:
                E.append(f"I8  furnishing {f['id']} on another level than its room")

    # I9 groups: members exist, share the level, no nesting
    G = {g["id"] for g in d.get("groups", [])}
    for g in d.get("groups", []):
        for m in g["members"]:
            if m in G:
                E.append(f"I9  group {g['id']} nests group {m}")
            elif m not in seen:
                E.append(f"I9  group {g['id']} -> missing member {m}")

    # I10 no orphan vertices
    live = {v for w in d["walls"] for v in (w["v1"], w["v2"])}
    live |= {e["v"] for r in d["rooms"] for e in r["outline"]}
    for v in d["vertices"]:
        if v["id"] not in live:
            E.append(f"I10 orphan vertex {v['id']}")

    # I15 OUTLINE COMPLETENESS: no outline edge passes through a wall endpoint
    #     without naming it.  For every outline edge from one vertex to the
    #     next, no vertex that is a wall endpoint may lie strictly between them.
    #
    #     WHY IT EXISTS, and it is a gap NEITHER of its neighbours can close.
    #     I14 compares wall ends to WALLS -- a room outline is outside its
    #     subject entirely.  I5 cannot fail on a saved document, because
    #     `bridge._walk` emits one outline edge per wall BY CONSTRUCTION, so the
    #     violation is repaired in the act of asking: an instrument that repairs
    #     what it measures reports health it manufactured.  Stated here as a
    #     DIRECT PROPERTY OF THE STORED DOCUMENT, never as a difference between
    #     two representations, which is what makes it checkable on bytes nobody
    #     has loaded.
    #
    #     THE TOLERANCE IS NOT `vertex_weld_in`.  That is a COINCIDENCE radius
    #     -- do two points name one corner.  This is a point-on-SEGMENT
    #     question and needs a PERPENDICULAR distance, so the two must not share
    #     a number.  Exact on the lattice (three lattice points are collinear
    #     exactly when an integer cross product is zero, so no tolerance is
    #     consulted at all), declared tolerance off it -- the same shape as
    #     `rooms._corner_path`, deliberately, so there is one rule for "is this
    #     point on this run" rather than two.  0.05" was chosen off a measured
    #     plateau: the corpus reports the same 2 violations at 0.001, 0.01 and
    #     0.05, while 0.0 drops a genuine hit to float exactness and 0.25 pulls
    #     in a different question (`handoff/0006-readback-outline-invariants.md`).
    #
    #     ITS PLACE IN THE CHEAP LANE IS A FACT ABOUT THIS IMPLEMENTATION, NOT
    #     ABOUT THE INVARIANT, and that is why `_i15_probes` exists.  Measured:
    #     naive (every edge against every endpoint) costs 36 ms on the largest
    #     corpus plan against the whole deep set's 49 -- honestly DEEP.  Behind
    #     the grid index below it costs 0.917 ms against the cheap lane's 0.447
    #     -- honestly CHEAP.  A later refactor to something clearer and slower
    #     would silently move a 40x cost into the per-mutation path, so the work
    #     is COUNTED and pinned by a test rather than left to a wall-clock
    #     timing assertion, which flaps in CI and gets disabled.
    #
    #     IT IS A BOUNDARY CHECK, NOT A PER-MUTATION ONE, AND THAT WAS MEASURED
    #     RATHER THAN CHOSEN.  Landed first in the always-on lane, it turned the
    #     gate RED on exactly one test -- `test_acceptance_shuffle_drag_across_
    #     the_plan`, at "mid-drag step 1 (over the plan)".  A room being dragged
    #     across the plan TRANSIENTLY has outline edges running through wall
    #     endpoints it does not name, and that state is legitimate: it is the
    #     same class D49 was amended for, where a deform-to-follow drag may
    #     transiently overlap and a hard refusal would trap the user with
    #     unsaveable work.  So I15 runs only when asked (`boundary=True`), which
    #     is where a document is READ or WRITTEN -- never after every edit.
    if boundary:
        _i15(d, E, V, xy)
        # I16 SIMPLE RING: a room outline visits no vertex twice.  D41, ruled at
        #     R-A as a NEW invariant rather than a widening of I5b -- I5b tests
        #     PROPER CROSSING, and `_seg_cross` must not fire on the collinear edges
        #     two rooms legitimately share, so widening it would blur something that
        #     works.  A ring that visits a vertex twice is a DEGENERACY, not a
        #     crossing: the pinched loop the walk planarises, and the zero-width
        #     spur (out to a corner and straight back, contributing no area).
        #
        #     IT IS CHEAP AND ALWAYS-ON, unlike I15 beside it.  Measured across the
        #     whole corpus it costs 0.157 ms -- a set membership per outline slot --
        #     against I15's 4.2 ms indexed, so there is no case for gating it.
        #
        #     I5 ALREADY CATCHES THE ADJACENT CASE ("repeats corner"), which is a
        #     ring that stutters on one vertex.  This is the NON-ADJACENT case, and
        #     the two are different faults: the first is a duplicated slot, the
        #     second is an excursion that comes back.
        for r in d["rooms"]:
            seen_ring = set()
            for e in r["outline"]:
                if e["v"] in seen_ring:
                    E.append(f"I16 room {r['id']} ({r['name']}) outline visits "
                             f"vertex {e['v']} twice -- not a simple ring")
                    break
                seen_ring.add(e["v"])



    # I11 no two PLACED rooms of the same overlap class may overlap.
    # I11 no two PLACED rooms of the same overlap class may overlap.
    #     interior + exterior form one class (a porch may not overlap a bedroom);
    #     `site` is its own class (a lawn zone may run under a deck);
    #     `concept` is exempt -- that is what makes shuffle mode safe.
    #     This is the check that caught the M Bath / Hall corruption.
    def oclass(r):
        c = r.get("category", "interior")
        return "site" if c == "site" else ("concept" if c == "concept" else "building")

    if deep:                              # O(rooms^2), deep only
        rl = {}
        for r in d["rooms"]:
            if r["placement"]["state"] != "placed" or oclass(r) == "concept":
                continue
            rl.setdefault((r["level"], oclass(r)), []).append(r)
        for _key, rs in rl.items():
            for i in range(len(rs)):
                for j in range(i + 1, len(rs)):
                    a, b = rs[i], rs[j]
                    pa, pb = poly(a), poly(b)
                    ca = (sum(p[0] for p in pa) / len(pa), sum(p[1] for p in pa) / len(pa))
                    cb = (sum(p[0] for p in pb) / len(pb), sum(p[1] for p in pb) / len(pb))
                    cross = any(_seg_cross(pa[i], pa[(i+1)%len(pa)],
                                           pb[j], pb[(j+1)%len(pb)])
                                for i in range(len(pa)) for j in range(len(pb)))
                    if _pip(cb, pa) or _pip(ca, pb) or cross:
                        E.append(f"I11 rooms '{a['name']}' and '{b['name']}' overlap")

    # I12 a `floating` room really is independent
    for r in d["rooms"]:
        if r["placement"]["state"] != "floating":
            continue
        mine = {e["wall"] for e in r["outline"] if e.get("wall")}
        vs = {e["v"] for e in r["outline"]}
        for wid in mine:
            w = W[wid]
            if w.get("left") and w.get("right"):
                E.append(f"I12 floating room {r['id']} shares wall {wid}")
        for w in d["walls"]:
            if w["id"] in mine or w["level"] != r["level"]:
                continue
            if w["v1"] in vs or w["v2"] in vs:
                E.append(f"I12 floating room {r['id']} shares vertex with "
                         f"outside wall {w['id']}")
    # I14 the document is WELDED: no wall end sits within vertex_weld_in of
    #     another wall's body or end without being that same vertex.  This is
    #     what lets the app skip the weld pass when opening a v5 file -- only
    #     legacy v1-v4 imports weld, and only those open dirty.  The tolerance
    #     is the tight modelling one (0.6"), NOT the 9" gesture tolerance: a
    #     wall deliberately stopping short of another stays where the user put it.
    tol = float((d.get("settings") or {}).get("vertex_weld_in", 0.6))
    # P4.2: a FLOATING room legitimately sits anywhere -- within weld
    # tolerance of the plan, or exactly over its old berth. Its walls are
    # exempt from weld closure AGAINST the plan (and against other floating
    # rooms); closure WITHIN one floating room still holds. I12 is the
    # invariant that guards the floating boundary, and I14 must not re-demand
    # the very sharing I12 forbids. Same class of exemption I11 grants.
    floatw = {}
    for r in d["rooms"]:
        if (r.get("placement") or {}).get("state") == "floating":
            for e in r["outline"]:
                if e.get("wall"):
                    floatw[e["wall"]] = r["id"]
    if deep:                              # O(walls^2), deep only
        for w in d["walls"]:
            a, b = xy(w["v1"]), xy(w["v2"])
            for o in d["walls"]:
                if o["id"] == w["id"] or o["level"] != w["level"]:
                    continue
                if (floatw.get(w["id"]) != floatw.get(o["id"])
                        and (w["id"] in floatw or o["id"] in floatw)):
                    continue              # floating-vs-plan pair: exempt
                c, e2 = xy(o["v1"]), xy(o["v2"])
                L = math.dist(c, e2)
                if L < 1e-6:
                    continue
                ux, uy = (e2[0] - c[0]) / L, (e2[1] - c[1]) / L
                for vid, p in ((w["v1"], a), (w["v2"], b)):
                    if vid in (o["v1"], o["v2"]):
                        continue                 # already the shared vertex
                    dx, dy = p[0] - c[0], p[1] - c[1]
                    s_ = dx * ux + dy * uy
                    perp = abs(dy * ux - dx * uy)
                    if perp <= tol and tol < s_ < L - tol:
                        E.append(f"I14 wall {w['id']} end {vid} lies on wall "
                                 f"{o['id']} but is not a vertex of it (unwelded T)")
                    for q, qid in ((c, o["v1"]), (e2, o["v2"])):
                        if math.dist(p, q) <= tol and vid != qid:
                            lo, hi = sorted((vid, qid))     # one per pair
                            E.append(f"I14 vertices {lo} and {hi} are within "
                                     f"{tol}\" but are not the same vertex")

    for r in d["rooms"]:
        if r.get("category") == "concept" and r["placement"]["state"] != "floating":
            E.append(f"I13 concept room {r['id']} must be floating")
        lv = next((x for x in d["levels"] if x["id"] == r["level"]), None)
        if lv and lv.get("kind") == "site" and r.get("category") not in ("site", "concept"):
            E.append(f"I13 room {r['id']} ({r['name']}) is on site level "
                     f"'{lv['name']}' but category is {r.get('category')}")
    return list(dict.fromkeys(E))


def near_vertex_gaps(d, lo=None, hi=None):
    """DEFECT 34's listing half (P4.2): the document's near-vertex pairs in
    the (vertex_weld_in, join_tol_in) band -- real gaps in the FILE that
    nothing reports and nothing may silently close. At or below `lo` two
    points ARE one vertex (the walk welds them); at or beyond `hi` the wall
    is simply elsewhere. In between, a 1.5" gap is probably a mistake and a
    6" gap is probably a reveal, and nothing here can tell which -- so this
    only LISTS, with distances, for a human to close one pair at a time
    (`walls.close_gap`, the review op's apply half). Floating rooms'
    vertices are exempt: their distance to the plan is their position, not
    a gap.

    Returns [(level_id, (ax, ay), (bx, by), dist)], nearest first."""
    s = d.get("settings") or {}
    lo = float(s.get("vertex_weld_in", 0.6)) if lo is None else lo
    hi = float(s.get("join_tol_in", 9.0)) if hi is None else hi
    floatv, floatw = set(), set()
    for r in d["rooms"]:
        if (r.get("placement") or {}).get("state") == "floating":
            for e in r["outline"]:
                floatv.add(e["v"])
                if e.get("wall"):
                    floatw.add(e["wall"])
    for w in d["walls"]:
        if w["id"] in floatw:
            floatv.add(w["v1"])
            floatv.add(w["v2"])
    out = []
    V = d["vertices"]
    for i, a in enumerate(V):
        if a["id"] in floatv:
            continue
        for b in V[i + 1:]:
            if b["id"] in floatv or a.get("level") != b.get("level"):
                continue
            dd = math.dist((a["x"], a["y"]), (b["x"], b["y"]))
            if lo < dd < hi:
                out.append((a.get("level"), (a["x"], a["y"]),
                            (b["x"], b["y"]), dd))
    return sorted(out, key=lambda t: t[3])


def _i15(d, E, V, xy):
    """I15's body, lifted out of `check` so the invariant reads as one thing."""
    tol_perp = float((d.get("settings") or {}).get("outline_on_edge_in", 0.05))
    step = float((d.get("settings") or {}).get("wall_snap_in", 6.0)) or 6.0
    cell = max(step * 4.0, 24.0)
    grid, placed = {}, set()
    for w in d["walls"]:
        for k in ("v1", "v2"):
            vid = w[k]
            if vid in placed or vid not in V:
                continue
            placed.add(vid)                 # one entry per VERTEX, never per wall
            v = V[vid]
            grid.setdefault((v["level"], int(v["x"] // cell),
                             int(v["y"] // cell)), []).append(vid)
    for r in d["rooms"]:
        # a FLOATING room deliberately breaks its sharing with the plan (P4.2),
        # the same exemption I11 and I14 grant, and for the same reason
        if (r.get("placement") or {}).get("state") == "floating":
            continue
        ring = [e["v"] for e in r["outline"] if e["v"] in V]
        n = len(ring)
        if n < 3:
            continue
        for i in range(n):
            va, vb = ring[i], ring[(i + 1) % n]
            a, b = xy(va), xy(vb)
            lo_x, hi_x = min(a[0], b[0]) - tol_perp, max(a[0], b[0]) + tol_perp
            lo_y, hi_y = min(a[1], b[1]) - tol_perp, max(a[1], b[1]) + tol_perp
            for cx in range(int(lo_x // cell), int(hi_x // cell) + 1):
                for cy in range(int(lo_y // cell), int(hi_y // cell) + 1):
                    for vid in grid.get((r["level"], cx, cy), ()):
                        if vid == va or vid == vb:
                            continue
                        if _between(a, xy(vid), b, step, tol_perp):
                            E.append(f"I15 room {r['id']} edge {va}->{vb} "
                                     f"passes through wall endpoint {vid} "
                                     f"without naming it")


def _between(a, p, b, step, tol_perp):
    """Does `p` lie STRICTLY between `a` and `b`? I15's one predicate.

    EXACT WHEN EVERY COORDINATE IS ON THE LATTICE -- three lattice points are
    collinear exactly when an integer cross product is zero, so the test is a
    comparison rather than a tolerance question, and `tol_perp` is not consulted
    at all. Off the lattice it falls back to a perpendicular distance. Same
    shape as `rooms._corner_path`: one rule for "is this point on this run".

    EVERY CALL IS COUNTED (`_i15_probes`), because I15's place in the cheap lane
    is a property of the grid index above and not of the invariant -- see the
    note at I15 and `test_i15_stays_in_the_cheap_lane`.
    """
    global _i15_probes
    _i15_probes += 1
    if all(abs(c / step - round(c / step)) < 1e-9
           for c in (a[0], a[1], p[0], p[1], b[0], b[1])):
        ax, ay = round(a[0] / step), round(a[1] / step)
        bx, by = round(b[0] / step), round(b[1] / step)
        px, py = round(p[0] / step), round(p[1] / step)
        cross = (bx - ax) * (py - ay) - (by - ay) * (px - ax)
        dot = (px - ax) * (bx - ax) + (py - ay) * (by - ay)
        ll = (bx - ax) ** 2 + (by - ay) ** 2
        return cross == 0 and 0 < dot < ll
    L = math.dist(a, b)
    if L < 1e-9:
        return False
    ux, uy = (b[0] - a[0]) / L, (b[1] - a[1]) / L
    s = (p[0] - a[0]) * ux + (p[1] - a[1]) * uy
    perp = abs((p[0] - a[0]) * uy - (p[1] - a[1]) * ux)
    return perp <= tol_perp and 1e-6 < s < L - 1e-6


_i15_probes = 0
"""Point-on-segment comparisons I15 has performed since `reset_i15_probes()`.

A BOUNDED-WORK COUNTER, NOT A TIMER. I15 sits in the cheap twelve only because
the grid index keeps it near-linear; measured, the naive form costs 36 ms on the
largest corpus plan against the deep set's 49, and a refactor to something
clearer and slower would move a 40x cost into the per-mutation path with nothing
objecting. A wall-clock assertion would catch that and would also flap on a busy
CI runner, so it would be disabled inside a month. A comparison count is
DETERMINISTIC: it fails loudly on exactly the change that matters and never on
machine load."""


def reset_i15_probes():
    global _i15_probes
    _i15_probes = 0


def i15_probes():
    return _i15_probes


def report(d):
    V = {v["id"]: (v["x"], v["y"]) for v in d["vertices"]}
    rows = []
    for r in d["rooms"]:
        pts = [V[e["v"]] for e in r["outline"]]
        n = len(pts)
        per = sum(math.dist(pts[i], pts[(i + 1) % n]) for i in range(n))
        openn = sum(1 for e in r["outline"] if not e.get("wall"))
        acc = r.get("area_accounting") or {
            "interior": "conditioned", "exterior": "unconditioned",
            "site": "site", "concept": "excluded"}[r.get("category", "interior")]
        rows.append((r["name"], abs(_area2(pts)) / 2 / 144, per / 12,
                     len(r["outline"]), openn, r["placement"]["state"], acc))
    return rows


def wall_angle_deviation_deg(a, b):
    """Degrees off the nearest axis-aligned angle, in `[0, 45]` -- 0 is
    perfectly orthogonal, 45 is a perfect diagonal. Read the same whether the
    wall is a deliberate 45-degree bay or a join artifact that happens to
    land there: this measures WHAT the geometry is, not WHY it got that way
    (0055-ruling.md SS5 declines that question on purpose)."""
    dx, dy = b[0] - a[0], b[1] - a[1]
    if dx == 0.0 and dy == 0.0:
        return 0.0
    deg = math.degrees(math.atan2(dy, dx)) % 90.0
    return min(deg, 90.0 - deg)


def wall_orthogonality_displacement_in(deg: float, length_in: float) -> float:
    """0066-ruling.md sec1: the tolerance a REPAIR is bounded by is not the
    degree the report reads in -- a repair moves a vertex, and length is the
    other half of that product. `length_in * sin(radians(deg))` is exactly
    how far the free endpoint moves if the wall is straightened onto its
    nearest axis, keeping the other endpoint fixed (the perpendicular
    coordinate set equal, nothing else touched) -- verified against 0066's
    own four-row table (e.g. 0.9290deg over 185.02in -> 3.000in) to the
    thousandth of an inch. Degrees stay in the report, where they belong --
    "how the fault is found, not how the fix is bounded" (0066 sec1)."""
    return length_in * math.sin(math.radians(deg))


def wall_orthogonality(d):
    """Per-wall deviation from the nearest axis-aligned angle, AND the
    displacement (inches) that deviation implies if the wall were
    straightened -- 0055-ruling.md's item B, THE REPORT (the degrees),
    extended by 0066-ruling.md item C sec1's own finding that a REPAIR
    cannot be bounded in degrees (nearly the same angle can move a vertex
    by an inch or by three, across a single "under 1 degree" band -- 0066
    sec1's own measurement). Grid snap constrains new cursor input; it
    cannot see a wall an existing operation (move/join/weld/coalesce)
    already rotated off axis after the fact, and this measures exactly
    that population, worst first.

    Returns `[(wall_id, level, type, deg, displacement_in)]`. A wall with a
    missing or coincident vertex pair is already an I2/I3 violation and is
    skipped here -- this is a report about walls that are VALID but not
    quite straight, not a second copy of `check()`."""
    V = {v["id"]: (v["x"], v["y"]) for v in d["vertices"]}
    out = []
    for w in d["walls"]:
        a, b = V.get(w["v1"]), V.get(w["v2"])
        if a is None or b is None:
            continue
        deg = wall_angle_deviation_deg(a, b)
        length_in = math.hypot(b[0] - a[0], b[1] - a[1])
        out.append((w["id"], w["level"], w["type"], deg,
                     wall_orthogonality_displacement_in(deg, length_in)))
    return sorted(out, key=lambda t: -t[3])


ORTHOGONALITY_BANDS = (
    (5.0, math.inf, "> 5 deg"),
    (1.0, 5.0, "1-5 deg"),
    (0.1, 1.0, "0.1-1 deg"),
    (0.01, 0.1, "0.01-0.1 deg"),
    (0.0, 0.01, "0 < dev < 0.01 deg"),
    (None, None, "on axis"),
)
"""0059-ruling.md SS2's six deviation bands, in degrees, worst first. Each
band is `(lo, hi, label)` with `lo < deg <= hi`, except the last, `(None,
None, "on axis")`, which takes `deg == 0.0` exactly and is matched
separately rather than by range.

0055-ruling.md's original five bands merged "exactly on axis" into "< 0.01
deg", which let 791 of 948 corpus walls sit in one bucket mixing the two --
undercounting 0059's own headline (63 walls within 1 deg of orthogonal
without being on it) by the 12 that were exactly 0.0 and so never reached
the range check at all. Splitting the bucket is what lets a reader
reproduce that headline from the printed table (0059-ruling.md SS2: "print
every raw value so a different cut needs no re-run").

ASCII labels deliberately -- no degree sign -- SESSION_SNAPSHOT.md SS5: the
test console is cp1252, and a label that appears in an assertion diff must
not be able to crash the very failure message reporting it."""


def orthogonality_bands(rows):
    """Bucket `wall_orthogonality()`'s rows into `ORTHOGONALITY_BANDS`.

    Returns `{label: count}`, ZERO-FILLED for every band even when empty --
    an instrument that only prints the bands it found something in cannot be
    told apart from one that never ran (the positive-control family,
    `WORKING_AGREEMENT.md`)."""
    counts = {label: 0 for _lo, _hi, label in ORTHOGONALITY_BANDS}
    for _wid, _lvl, _typ, deg, _disp in rows:
        if deg == 0.0:
            counts["on axis"] += 1
            continue
        for lo, hi, label in ORTHOGONALITY_BANDS:
            if lo is not None and lo < deg <= hi:
                counts[label] += 1
                break
    return counts


# ---------------------------------------------------------------------------
# The orthogonality REPAIR -- 0066-ruling.md item C, unblocked by
# 0082-ruling.md's three amendments (its own sec6 tier table). Item B above
# is a report and stays one; nothing below is reachable except from the one
# menu item 0066 sec5 names ("Never automatic. Never on open, never on save,
# never on export.").
# ---------------------------------------------------------------------------

REPAIR_NEAR_AXIS_DEG = 1.0
"""The upper bound on the population `wall_orthogonality()` is even
considered from -- item 1's own census, "63 within 1 degree of an axis
without being on it" (0066-ruling.md sec1). This is what 0066 sec1's "safe
by construction" argument for the 45-degree bay rests on: a deliberate
diagonal's displacement (0.707 * length, tens of inches) is enormous, but
the argument only holds if the bay never enters this population at all.
`REPAIR_T_IN` (below) narrows it further, to the walls the repair actually
touches."""

REPAIR_T_IN = 1 / 16
"""0066-ruling.md sec3's own boxed ruling: **"below T, moving a vertex
cannot change any dimension a residential plan expresses; above it, the
correction is a real edit and the user must see it before it happens."**
`0084-ruling.md` sec1 corrected `0083-report.md`'s reading of this: the
0079-report.md read-back that measured conflicts "over all 63" was a
SUPERSET MEASUREMENT, never a candidacy decision -- 0066 sec3's own table
(32 auto-repairable under T, 31 reported-not-touched at or above it) is the
one that was actually ruled, and it is restored here. Below `T`: a
candidate for straightening, subject only to the conflict predicate. At or
above it: reported in `over_t`, never moved -- which is what makes `w24`
(0066 sec1's own 3.000" headline outlier) untouchable for the RIGHT reason,
size, not conflict."""


def wall_repair_conflict(d, wall_id, endpoint_attr):
    """True if straightening `wall_id` by moving its `endpoint_attr`
    ('v1' or 'v2') would tilt another wall sharing that vertex.

    Straightening a near-horizontal wall changes only the moved endpoint's
    y (set equal to the other endpoint's y); a near-vertical wall, only x.
    So the conflict is exact: does any OTHER wall at that same vertex
    already run EXACTLY along the axis about to move? Moving y tilts an
    exactly-horizontal neighbour; moving x tilts an exactly-vertical one --
    0066-ruling.md sec4's own words, as a predicate.

    Reads `d` FRESH on every call -- no snapshot is taken -- which is what
    makes 0082-ruling.md sec3's per-wall re-evaluation correct: called again
    after `repair_wall_orthogonality` has mutated earlier walls in the same
    batch, it sees THOSE walls' new, now-exact axis alignment."""
    V = {v["id"]: (v["x"], v["y"]) for v in d["vertices"]}
    w = next(x for x in d["walls"] if x["id"] == wall_id)
    a, b = V[w["v1"]], V[w["v2"]]
    dx, dy = b[0] - a[0], b[1] - a[1]
    moving_y = abs(dy) <= abs(dx)          # near-horizontal: y is the free coord
    vid = w[endpoint_attr]
    for other in d["walls"]:
        if other["id"] == wall_id or vid not in (other["v1"], other["v2"]):
            continue
        oa, ob = V[other["v1"]], V[other["v2"]]
        if moving_y and oa[1] == ob[1] and oa[0] != ob[0]:
            return True                     # an exactly-horizontal neighbour
        if not moving_y and oa[0] == ob[0] and oa[1] != ob[1]:
            return True                     # an exactly-vertical neighbour
    return False


def choose_repair_endpoint(d, wall_id):
    """'v1', 'v2', or None (both ends conflict -- the whole wall is
    refused). The endpoint with NO conflict; if both are free, either --
    for an isolated wall the displacement is identical either way (moving
    v1's y to match v2's, or v2's to match v1's, moves the SAME distance).
    The tie-break only has teeth once a vertex is shared by more than one
    near-axis wall in the same batch, which is item 3's graph-solve, not
    this first delivery -- stated now so it needs no re-deriving there."""
    free = [a for a in ("v1", "v2") if not wall_repair_conflict(d, wall_id, a)]
    if not free:
        return None
    return free[0]


def _invariant_key(message):
    """A `check()` message reduced to a STABLE key -- the invariant code
    plus every subject id, never the rendered geometry (0082-ruling.md
    sec4). `check()`'s messages embed measurements ("48.3..108.3 of 95.5",
    a wall length) that the repair itself changes for a WALL THAT WAS
    ALREADY FAILING, by moving a vertex that wall's own neighbours share --
    comparing on the full string would read that as a brand-new violation
    and roll back a repair for a fault that predates it.

    Invariant codes are `I` + digits (+ an optional letter, e.g. `I5b`);
    document ids are a lowercase letter (or letters) + digits (`w17`,
    `v92`, `o26`). The two alphabets never collide, so one regex separates
    them. I11's own message names rooms by NAME, not id ("rooms 'Kitchen'
    and 'Hall' overlap") -- quoted substrings are pulled in too, so that
    check keys on the same room pair rather than collapsing every overlap
    into one key."""
    code = message.split(None, 1)[0]
    ids = sorted(set(re.findall(r"\b[a-z]+\d+\b", message))
                 | set(re.findall(r"'([^']+)'", message)))
    return (code, tuple(ids))


def _worsened_wall(work, orig_deg, tol=1e-6):
    """0084-ruling.md sec2: has ANY wall gotten WORSE than its degree before
    the repair ran? Returns that wall's id, or `None`. `tol` absorbs float
    noise from a relocation that does not touch this wall's own coordinates
    at all.

    NO WALL IS EXEMPTED, INCLUDING A CANDIDATE STILL WAITING ITS OWN TURN --
    measured, not assumed: an earlier draft exempted still-pending
    candidates on the theory that they get a chance to fix themselves. A
    real corpus wall (`wiscaway2026-08-09R`'s `w57`) disproved it: tilted
    off axis by an EARLIER neighbour's move while still pending, it then
    reached its OWN turn already worse than it started, was refused there
    for an unrelated conflict, and was never re-checked against its
    original degree again -- the guarantee silently broke. Checking every
    wall, unconditionally, costs some coverage (a move gets undone even
    when the wall it disturbs would have straightened itself moments
    later) but is the only form of this check that is actually correct."""
    for wid, _lvl, _typ, deg, _disp in wall_orthogonality(work):
        if deg > orig_deg.get(wid, 0.0) + tol:
            return wid
    return None


def repair_wall_orthogonality(d, deep=True, t_in=REPAIR_T_IN):
    """0066-ruling.md item C, as amended by 0082-ruling.md secs 2-4 and
    0084-ruling.md secs 1-2. Straightens every near-axis wall whose
    displacement is UNDER `t_in` (`REPAIR_T_IN` by default -- 0084 sec1
    restores 0066 sec3's own candidacy filter, which `0083-report.md` had
    dropped) by moving exactly one endpoint onto the OTHER endpoint's
    axis-aligned coordinate, worst deviation first. A candidate is REFUSED,
    left exactly where it was, for either of two reasons:

      "conflict"      -- every candidate endpoint is shared with a wall
                          already exactly on axis (`choose_repair_endpoint`
                          returns `None`)
      "would worsen X" -- moving it leaves some OTHER wall, X, MORE off
                          axis than X was before the repair ran (0084
                          sec2's own post-condition, below)

    Near-axis walls AT OR ABOVE `t_in` are never candidates at all --
    returned in `over_t`, reported, untouched. This is what makes `w24`
    (0066 sec1's own 3.000" headline outlier) untouchable for the RIGHT
    reason: size, not conflict (0084 sec1).

    THE INTERLOCK (0082 sec2, withdrawing 0066 sec5's refuse-to-start
    clause): runs on any document, even one that already fails `check()` --
    refusing protects nothing, since the plans this repair exists for are
    exactly the ones with the most pre-existing drift. `check()` runs
    before and after, compared on `_invariant_key` (0082 sec4), and the
    WHOLE repair is discarded -- returning `d` byte-for-byte, via a deep
    copy that is never mutated in place -- if and only if it introduces a
    key that was not already failing.

    THE CONFLICT PREDICATE IS RE-EVALUATED PER WALL (0082 sec3): each call
    to `choose_repair_endpoint` reads the document as mutated by every wall
    already processed in this same batch, not a snapshot taken up front --
    a wall straightened earlier can make a later wall's shared vertex newly
    conflicted, and only a live re-check catches it (measured on a real
    six-wall chain, `wiscaway2026-08-09R`'s `w53`..`w59`).

    THE ORTHOGONALITY POST-CONDITION (0084 sec2): `0082`'s interlock guarded
    `check()`'s invariants and never the quantity this repair exists to
    improve. Measured: a wall this repair REFUSES can still be tilted worse
    by a NEIGHBOUR's successful move, through a vertex they share -- `check()`
    saw nothing wrong (no invariant reads "is this wall still as straight as
    it was"). So after each successful move, EVERY wall is re-measured; if
    any of them is now worse than before the whole repair started, THIS move
    alone is undone (the vertex reverts to its saved position) and the
    candidate is refused instead. NOT EVEN A STILL-PENDING CANDIDATE IS
    EXEMPTED -- an earlier draft exempted them on the theory that they get a
    chance to straighten themselves later in the same batch, and a real
    corpus wall (`wiscaway2026-08-09R`'s `w57`) disproved it: tilted by an
    earlier move while pending, it then reached its own turn already worse,
    was refused there for an unrelated conflict, and the guarantee silently
    broke (`_worsened_wall`'s own docstring carries the full account). This
    costs some coverage -- a move can be undone even when the wall it
    disturbs would have fixed itself moments later -- but is the only form
    of this check that is actually correct. `0084` sec2's own accounting:
    restoring `t_in` already caps the damage (a `T`-sized move on a typical
    wall tilts a neighbour by at most `asin(T/L)`, a fraction of a degree);
    this closes the remainder.

    Returns a dict:
      doc          -- the repaired document (a deep copy; `d` itself is
                       never mutated), or `d` unchanged if `rolled_back`
      moved        -- [(wall_id, level, type, displacement_in)], worst first
      refused      -- [(wall_id, level, type, displacement_in, reason)]
      over_t       -- [(wall_id, level, type, displacement_in)], near-axis
                       but never a candidate -- size, not conflict
      relocations  -- [(level, (old_x, old_y), (new_x, new_y))], one entry
                       per VERTEX actually relocated (a shared vertex moved
                       by more than one wall in this batch appears once, at
                       its final position) -- the scene applier's input,
                       matching `walls.close_gap`'s own (level, a, b) shape
                       so the same coordinate-relocate-and-reweld path
                       serves both
      rolled_back  -- True if the repair introduced a new violation
      newly_failing -- the `_invariant_key`s that would have been new,
                       populated only when `rolled_back`

    NEVER CLAIMS ZERO OFF-AXIS WALLS REMAIN (0066 sec4): a rectilinear loop
    whose runs do not sum to zero has a residual, and a refused (or
    over-`t_in`) wall is where it lands. For every wall in `moved`, the
    displacement this function leaves behind is exactly 0 -- the moved
    coordinate is SET EQUAL to the other endpoint's, not merely brought
    within a tolerance."""
    import copy
    before_keys = {_invariant_key(m) for m in check(d, deep=deep)}
    orig_xy = {v["id"]: (v["x"], v["y"]) for v in d["vertices"]}

    work = copy.deepcopy(d)
    V = {v["id"]: v for v in work["vertices"]}
    W = {w["id"]: w for w in work["walls"]}
    all_rows = wall_orthogonality(work)
    orig_deg = {wid: deg for wid, _lvl, _typ, deg, _disp in all_rows}
    near_axis = [row for row in all_rows if 0 < row[3] <= REPAIR_NEAR_AXIS_DEG]
    candidates = [row for row in near_axis if row[4] < t_in]
    over_t = [(wid, lvl, typ, disp) for wid, lvl, typ, _deg, disp in near_axis
              if disp >= t_in]

    moved, refused = [], []
    relocated_ids = set()
    for wall_id, level, wtype, _deg, disp in candidates:
        ep = choose_repair_endpoint(work, wall_id)
        if ep is None:
            refused.append((wall_id, level, wtype, disp, "conflict"))
            continue
        w = W[wall_id]
        other_id = w["v2"] if ep == "v1" else w["v1"]
        a, b = V[w["v1"]], V[w["v2"]]
        moving_y = abs(b["y"] - a["y"]) <= abs(b["x"] - a["x"])
        moved_v, other_v = V[w[ep]], V[other_id]
        saved = (moved_v["x"], moved_v["y"])
        if moving_y:
            moved_v["y"] = other_v["y"]
        else:
            moved_v["x"] = other_v["x"]

        worsened = _worsened_wall(work, orig_deg)
        if worsened is not None:
            moved_v["x"], moved_v["y"] = saved
            refused.append((wall_id, level, wtype, disp,
                            f"would worsen {worsened}"))
            continue

        moved.append((wall_id, level, wtype, disp))
        relocated_ids.add(w[ep])

    after_keys = {_invariant_key(m) for m in check(work, deep=deep)}
    newly_failing = after_keys - before_keys
    if newly_failing:
        return {"doc": d, "moved": [], "refused": [], "over_t": [],
                "relocations": [], "rolled_back": True,
                "newly_failing": newly_failing}
    relocations = [(V[vid]["level"], orig_xy[vid], (V[vid]["x"], V[vid]["y"]))
                   for vid in sorted(relocated_ids)
                   if orig_xy[vid] != (V[vid]["x"], V[vid]["y"])]
    return {"doc": work, "moved": moved, "refused": refused,
            "over_t": over_t, "relocations": relocations,
            "rolled_back": False, "newly_failing": set()}


# ---------------------------------------------------------------------------
# "Snap to Grid Orthogonal" -- 0110-ruling.md SS2, amended by 0109-ruling.md
# SS3. A per-wall, manual action (0108-ruling.md), NOT a use of
# `repair_wall_orthogonality`: it makes the CLICKED endpoint's wall exactly
# axis-aligned AND both ends land on the alignment grid, in one move,
# anchored at the vertex the user clicked -- so "which endpoint moves"
# (0079-report.md SS2(c)'s open question for item C) is answered by where
# they click, not guessed.
# ---------------------------------------------------------------------------

SNAP_ORTHO_NEAR_45_DEG = 5.0
"""0110-ruling.md SS2's "REFUSE when the wall is too near 45 -- there is no
orthogonal value to share, and guessing one would rotate the wall 45
degrees" names the HAZARD but not a number. This is a judgement call, not a
ruled value: refuse when the wall's deviation from axis
(`wall_angle_deviation_deg`, 0 = on axis, 45 = exact diagonal) is within
this many degrees of 45, i.e. `deg > 45.0 - SNAP_ORTHO_NEAR_45_DEG`. Chosen
by the same reasoning `REPAIR_NEAR_AXIS_DEG` used at the other end of the
scale (a round, named band, not a tuned constant) -- flagged here for a
future ruling to tighten or loosen if 5 degrees turns out wrong in
practice."""


def vertex_grid_error_in(x: float, y: float, step: float) -> float:
    """Distance from `(x, y)` to the nearest grid intersection at `step` --
    how far a corner sits off the alignment grid, in inches. `0` exactly on
    grid on both axes."""
    gx, gy = round(x / step) * step, round(y / step) * step
    return math.hypot(x - gx, y - gy)


def wall_grid_error_in(d, step: float) -> dict:
    """`{wall_id: error_in}` -- each wall's WORSE of its two endpoints'
    `vertex_grid_error_in`, for every wall with two resolvable vertices.
    Companion measurement to `wall_orthogonality`'s per-wall degree, for the
    same "did this wall get worse" comparison, applied to grid alignment
    rather than axis alignment."""
    V = {v["id"]: (v["x"], v["y"]) for v in d["vertices"]}
    out = {}
    for w in d["walls"]:
        a, b = V.get(w["v1"]), V.get(w["v2"])
        if a is None or b is None:
            continue
        out[w["id"]] = max(vertex_grid_error_in(*a, step),
                           vertex_grid_error_in(*b, step))
    return out


def snap_wall_to_grid_orthogonal(d, wall_id, endpoint_attr, step):
    """0110-ruling.md SS2, amended by 0109-ruling.md SS3.

    The CLICKED vertex (`wall_id`'s `endpoint_attr`, `'v1'` or `'v2'`) snaps
    to the nearest grid point on BOTH coordinates. The OTHER vertex takes
    the clicked vertex's SHARED-AXIS coordinate -- the one that must match
    for the wall to land exactly on axis, chosen by the wall's LARGER
    original delta, the same test `wall_repair_conflict` uses -- and its own
    free coordinate independently snaps to grid. Result: exactly
    axis-aligned AND both ends on grid, in one move.

    Moving a shared `Vertex` moves every other wall (and room outline) that
    holds it, by construction (P3.1) -- correct, and not something this
    function works around.

    REFUSES, `d` returned byte-identical (nothing applied):
      "near-45"           -- see `SNAP_ORTHO_NEAR_45_DEG`
      "degenerate"        -- both ends would round to the same grid point
      "would introduce X" -- `check()`'s invariant differential
                              (0082-ruling.md SS4's stable key), the SAME
                              interlock `repair_wall_orthogonality` uses --
                              an opening running off its wall (I7) is caught
                              HERE, not by a special case, and so is a
                              degenerate NEIGHBOUR this function did not
                              directly touch

    REPORTS, does not refuse (0109-ruling.md SS3's amendment to
    0108-ruling.md SS3's fourth refusal): every OTHER wall whose angle
    deviation OR grid error gets worse. Named, not prevented -- "he is
    cleaning a whole plan one wall at a time... a neighbour left temporarily
    crooked is the next wall he selects, not a defect."

    Returns a dict:
      doc         -- the result (a deep copy of `d`, mutated), or `d` itself
                     if refused
      refused     -- `None`, or one of the reason strings above
      relocations -- `[(level, (old_x, old_y), (new_x, new_y))]`, one entry
                     per vertex that actually moved (0, 1 or 2) -- the same
                     shape `repair_wall_orthogonality` returns, so the same
                     scene applier (`close_gap`) serves both
      worsened    -- sorted `[wall_id, ...]`, the OTHER walls the report
                     names, empty when nothing got worse
    """
    import copy
    work = copy.deepcopy(d)
    before_keys = {_invariant_key(m) for m in check(d, deep=True)}
    V = {v["id"]: v for v in work["vertices"]}
    w = next(x for x in work["walls"] if x["id"] == wall_id)
    other_attr = "v2" if endpoint_attr == "v1" else "v1"
    clicked, other = V[w[endpoint_attr]], V[w[other_attr]]
    ax, ay = clicked["x"], clicked["y"]
    bx, by = other["x"], other["y"]

    deg = wall_angle_deviation_deg((ax, ay), (bx, by))
    if deg > 45.0 - SNAP_ORTHO_NEAR_45_DEG:
        return {"doc": d, "refused": "near-45", "relocations": [], "worsened": []}

    dx, dy = bx - ax, by - ay
    moving_y = abs(dy) <= abs(dx)          # near-horizontal: shared coord is y
    new_ax, new_ay = round(ax / step) * step, round(ay / step) * step
    if moving_y:
        new_bx, new_by = round(bx / step) * step, new_ay
    else:
        new_bx, new_by = new_ax, round(by / step) * step

    if (new_ax, new_ay) == (new_bx, new_by):
        return {"doc": d, "refused": "degenerate", "relocations": [],
                "worsened": []}

    orig_deg = {wid: dg for wid, _lvl, _typ, dg, _disp in wall_orthogonality(work)}
    orig_grid = wall_grid_error_in(work, step)
    orig_clicked_xy, orig_other_xy = (ax, ay), (bx, by)

    clicked["x"], clicked["y"] = new_ax, new_ay
    other["x"], other["y"] = new_bx, new_by

    after_keys = {_invariant_key(m) for m in check(work, deep=True)}
    newly = after_keys - before_keys
    if newly:
        return {"doc": d, "refused": f"would introduce {sorted(newly)[0][0]}",
                "relocations": [], "worsened": []}

    new_deg = {wid: dg for wid, _lvl, _typ, dg, _disp in wall_orthogonality(work)}
    new_grid = wall_grid_error_in(work, step)
    worsened = sorted({
        wid for wid in new_deg
        if new_deg[wid] > orig_deg.get(wid, 0.0) + 1e-6
        or new_grid.get(wid, 0.0) > orig_grid.get(wid, 0.0) + 1e-6})

    relocations = []
    if (clicked["x"], clicked["y"]) != orig_clicked_xy:
        relocations.append((clicked["level"], orig_clicked_xy,
                            (clicked["x"], clicked["y"])))
    if (other["x"], other["y"]) != orig_other_xy:
        relocations.append((other["level"], orig_other_xy,
                            (other["x"], other["y"])))

    return {"doc": work, "refused": None, "relocations": relocations,
            "worsened": worsened}


# ---------------------------------------------------------------------------
# "Snap to Grid" (plain) -- 0108-ruling.md, amended by 0109-ruling.md SS3.
# Simpler than the orthogonal variant: no anchor, no shared axis, no
# near-45 hazard -- both endpoints round to the grid INDEPENDENTLY, so the
# wall's angle is whatever it is afterward, not forced onto axis. 0108 SS1:
# "two ends that round to the same row make the wall axis-aligned as a side
# effect, not as the goal."
# ---------------------------------------------------------------------------

def snap_wall_to_grid(d, wall_id, step):
    """0108-ruling.md, amended by 0109-ruling.md SS3. Each of `wall_id`'s two
    endpoints independently snaps to the nearest grid point at `step` --
    NOT `repair_wall_orthogonality` (a wall can be axis-aligned and off-grid,
    or the reverse, 0108 SS1) and not `snap_wall_to_grid_orthogonal` (no
    anchor: both ends move, neither is privileged, so "which endpoint moves"
    does not arise here either, just for a different reason -- both do).

    REFUSES, `d` returned byte-identical (nothing applied):
      "degenerate"        -- both ends would round to the same grid point
      "would introduce X" -- `check()`'s invariant differential
                              (0082-ruling.md SS4's stable key) -- an
                              opening running off its wall (I7) is caught
                              here, not by a special case, exactly as
                              `snap_wall_to_grid_orthogonal` does it

    REPORTS, does not refuse (0109-ruling.md SS3's amendment): every OTHER
    wall whose angle deviation or grid error gets worse.

    Returns the same shape `snap_wall_to_grid_orthogonal` does:
      doc, refused, relocations (0, 1 or 2 entries), worsened
    """
    import copy
    work = copy.deepcopy(d)
    before_keys = {_invariant_key(m) for m in check(d, deep=True)}
    V = {v["id"]: v for v in work["vertices"]}
    w = next(x for x in work["walls"] if x["id"] == wall_id)
    v1, v2 = V[w["v1"]], V[w["v2"]]
    orig1_xy, orig2_xy = (v1["x"], v1["y"]), (v2["x"], v2["y"])
    new1 = (round(v1["x"] / step) * step, round(v1["y"] / step) * step)
    new2 = (round(v2["x"] / step) * step, round(v2["y"] / step) * step)

    if new1 == new2:
        return {"doc": d, "refused": "degenerate", "relocations": [],
                "worsened": []}

    orig_deg = {wid: dg for wid, _lvl, _typ, dg, _disp in wall_orthogonality(work)}
    orig_grid = wall_grid_error_in(work, step)

    v1["x"], v1["y"] = new1
    v2["x"], v2["y"] = new2

    after_keys = {_invariant_key(m) for m in check(work, deep=True)}
    newly = after_keys - before_keys
    if newly:
        return {"doc": d, "refused": f"would introduce {sorted(newly)[0][0]}",
                "relocations": [], "worsened": []}

    new_deg = {wid: dg for wid, _lvl, _typ, dg, _disp in wall_orthogonality(work)}
    new_grid = wall_grid_error_in(work, step)
    worsened = sorted({
        wid for wid in new_deg
        if new_deg[wid] > orig_deg.get(wid, 0.0) + 1e-6
        or new_grid.get(wid, 0.0) > orig_grid.get(wid, 0.0) + 1e-6})

    relocations = []
    if (v1["x"], v1["y"]) != orig1_xy:
        relocations.append((v1["level"], orig1_xy, (v1["x"], v1["y"])))
    if (v2["x"], v2["y"]) != orig2_xy:
        relocations.append((v2["level"], orig2_xy, (v2["x"], v2["y"])))

    return {"doc": work, "refused": None, "relocations": relocations,
            "worsened": worsened}
