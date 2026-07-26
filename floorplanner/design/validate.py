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
from pathlib import Path

STD_T = {"exterior": 6.0, "interior": 4.5, "partition": 3.5,
         "railing": 2.0, "fence": 2.0, "hedge": 18.0, "retaining": 8.0}

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


def check(d):
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
        # I5b simple polygon (non-self-intersecting)
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

    # I11 no two PLACED rooms of the same overlap class may overlap.
    #     interior + exterior form one class (a porch may not overlap a bedroom);
    #     `site` is its own class (a lawn zone may run under a deck);
    #     `concept` is exempt -- that is what makes shuffle mode safe.
    #     This is the check that caught the M Bath / Hall corruption.
    def oclass(r):
        c = r.get("category", "interior")
        return "site" if c == "site" else ("concept" if c == "concept" else "building")

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
    for w in d["walls"]:
        a, b = xy(w["v1"]), xy(w["v2"])
        for o in d["walls"]:
            if o["id"] == w["id"] or o["level"] != w["level"]:
                continue
            c, e2 = xy(o["v1"]), xy(o["v2"])
            L = math.dist(c, e2)
            if L < 1e-6:
                continue
            ux, uy = (e2[0] - c[0]) / L, (e2[1] - c[1]) / L
            for vid, p in ((w["v1"], a), (w["v2"], b)):
                if vid in (o["v1"], o["v2"]):
                    continue                     # already the shared vertex
                dx, dy = p[0] - c[0], p[1] - c[1]
                s_ = dx * ux + dy * uy
                perp = abs(dy * ux - dx * uy)
                if perp <= tol and tol < s_ < L - tol:
                    E.append(f"I14 wall {w['id']} end {vid} lies on wall "
                             f"{o['id']} but is not a vertex of it (unwelded T)")
                for q, qid in ((c, o["v1"]), (e2, o["v2"])):
                    if math.dist(p, q) <= tol and vid != qid:
                        lo, hi = sorted((vid, qid))     # one message per pair
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
