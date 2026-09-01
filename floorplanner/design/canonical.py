"""Canonical form for a v5 design document (P1.5, made total at P2.2).

**One plan has one representation, whatever built it.** Two documents that
describe the same geometry must be byte-equal, so that equality can be used for
the dirty flag, the undo comparison and every round-trip test -- without those
comparisons being sensitive to the order some producer happened to emit things.

Two normalisations, and BOTH are needed; ids alone leave the form partial:

  * **ids**, renumbered in geometric order. Without this they encode emission
    order. `design_from_scene` visits the scene's walls; the importer visits the
    file's; `apply_design_to_scene` turns each split segment into its own wall
    and so reorders the next walk. Same plan, three different id assignments.
  * **outline rotation**, restarted at each room's lexicographically-least
    (x, y) corner, orientation untouched. A cycle has no natural first element,
    so two producers can emit the same loop from different starting corners --
    identical polygon, unequal document. This is what made `symmetricP1.json`'s
    Garage outline differ between the stored-corners fallback and the traced
    face at P1.3b.

Orientation is deliberately NOT normalised: winding carries meaning (an inner
face is wound so the interior is on each edge's `left`), so reversing a loop
would silently swap every wall's sides.

Pure data, stdlib only -- no Qt and no scene layer, so the Qt-free importer can
canonicalize its output just as the scene walk does.
"""


def _rotated(outline, vpos):
    """`outline` restarted at its lexicographically-least (x, y) corner.

    Rotating a cyclic list preserves every element's successor, so each entry
    keeps the wall that spans it to the next corner -- the pairing survives."""
    if len(outline) < 2:
        return outline
    k = min(range(len(outline)),
            key=lambda i: (vpos[outline[i]["v"]], i))
    return outline[k:] + outline[:k]


def canonicalize(doc):
    """Normalise `doc` in place and return it. Safe to call more than once --
    canonical form is a fixed point."""
    levels = doc.get("levels") or []
    vertices = doc.get("vertices") or []
    walls = doc.get("walls") or []
    rooms = doc.get("rooms") or []
    furnishings = doc.get("furnishings") or []
    groups = doc.get("groups") or []

    lorder = {lv["id"]: i for i, lv in enumerate(levels)}
    vpos = {v["id"]: (v["x"], v["y"]) for v in vertices}

    for r in rooms:                         # rotation first: the id assignment
        r["outline"] = _rotated(r["outline"], vpos)   # below must see final loops

    vertices.sort(key=lambda v: (lorder[v["level"]], v["x"], v["y"]))
    vid = {v["id"]: f"v{i}" for i, v in enumerate(vertices, 1)}

    walls.sort(key=lambda w: (lorder[w["level"]], vpos[w["v1"]], vpos[w["v2"]],
                              w["type"]))
    wid = {w["id"]: f"w{i}" for i, w in enumerate(walls, 1)}

    def centroid(outline):
        pts = [vpos[e["v"]] for e in outline]
        return (sum(p[0] for p in pts) / len(pts),
                sum(p[1] for p in pts) / len(pts))

    rooms.sort(key=lambda r: (lorder[r["level"]], r["name"],
                              *centroid(r["outline"])))
    rid = {r["id"]: f"r{i}" for i, r in enumerate(rooms, 1)}

    furnishings.sort(key=lambda f: (lorder[f["level"]], f["pos"][0],
                                    f["pos"][1], f["kind"],
                                    f.get("rotation", 0.0)))

    for v in vertices:
        v["id"] = vid[v["id"]]
    n_op = 0
    for w in walls:
        w["id"] = wid[w["id"]]
        w["v1"], w["v2"] = vid[w["v1"]], vid[w["v2"]]
        w["left"] = rid[w["left"]] if w.get("left") else None
        w["right"] = rid[w["right"]] if w.get("right") else None
        for op in w.get("openings") or []:   # already in along-the-wall order
            n_op += 1
            op["id"] = f"o{n_op}"
    for r in rooms:
        r["id"] = rid[r["id"]]
        for e in r["outline"]:
            e["v"] = vid[e["v"]]
            e["wall"] = wid[e["wall"]] if e.get("wall") else None
    fid = {f["id"]: f"f{i}" for i, f in enumerate(furnishings, 1)}
    for f in furnishings:
        f["id"] = fid[f["id"]]
        f["room"] = rid[f["room"]] if f.get("room") else None
    # GROUPS (P4.5): a group is a set of MEMBER IDS, so it has to be renumbered
    # with everything it points at -- otherwise canonicalising a document
    # silently dangles every membership (I9). Members are sorted so the set is
    # compared as a set, and the groups themselves are ordered by level and
    # membership so the form is stable and idempotent.
    ren = {**wid, **rid, **fid}
    for g in groups:
        g["members"] = sorted(ren.get(m, m) for m in g.get("members") or [])
    groups.sort(key=lambda g: (lorder.get(g.get("level"), 0), g["members"]))
    for i, g in enumerate(groups, 1):
        g["id"] = f"g{i}"

    # ROOFS (0139-ruling.md R1): a ridge's two literal points ARE its
    # identity, same as a furnishing's `pos` -- no vertex table to remap,
    # since a roof does not need welding (`_roofs_of`'s own docstring).
    roofs = doc.get("roofs") or []
    roofs.sort(key=lambda rf: (lorder[rf["level"]], rf["ridge"][0][0],
                               rf["ridge"][0][1]))
    for i, rf in enumerate(roofs, 1):
        rf["id"] = f"rf{i}"
    return doc
