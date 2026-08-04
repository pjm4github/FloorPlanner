"""One-room template documents (P4.4) — §4's *Duplicate a room*, and the
File ▸ Save / Load template room pair.

**Three workflows, ONE mechanism.** A room becomes a one-room v5 document
(`room_subdocument`), and a one-room document folds back into a design as a
floating room (`merge_room_document`). Copy/Paste puts a clipboard between
the two halves, Save/Load template puts a FILE between them, and Duplicate
calls them back to back. So there is no fourth definition of "what a room is
made of": both halves are document operations over what `design_from_scene`
already emits, which is why `_copy_spec`/`_perimeter_span` — the clipboard's
own third definition (a `bounding_walls` proximity query trimmed against the
corners) — die at this task rather than being ported.

**Why a template room must be FLOATING, and it is not UI polish.** The level
walk gives every floating room its OWN vertex namespace and its own walls
(I12, P4.2), so the subset *{this room, the walls its outline names, their
vertices, its furnishings}* is **closed** — nothing in it is shared with the
plan around it. Templating a *placed* room would cut through party walls and
shared corners, and there would be no honest answer to "whose wall is this".
That is what makes the ruled "Save template room… only when a room is
floated" a structural rule and not a menu convenience.

Qt-free by construction: dict in, dict out.
"""

FORMAT = "floorplanner-design"
VERSION = 5


def _room_entry(doc, name):
    rooms = [r for r in doc.get("rooms") or [] if r.get("name") == name]
    if not rooms:
        raise ValueError(f"no room named {name!r} in the document")
    if len(rooms) > 1:
        raise ValueError(f"{len(rooms)} rooms named {name!r}; names are "
                         f"unique in a scene, so this document is malformed")
    return rooms[0]


def room_subdocument(doc, name):
    """The one-room v5 document for the room called `name` — the room, the
    walls its OUTLINE names (the one definition of a room's walls, P3.5 and
    register row 36), the vertices those use, and the furnishings owned by
    it, on a single level.

    The room must be `floating`: only then is the subset closed (see the
    module note). Settings ride along from the source document so a template
    opened on its own validates and renders like the design it came from."""
    room = _room_entry(doc, name)
    if (room.get("placement") or {}).get("state") != "floating":
        raise ValueError(f"room {name!r} is not floating: a template is cut "
                         f"from a room that owns its walls outright (I12)")
    lid = room["level"]
    wanted = {e["wall"] for e in room["outline"] if e.get("wall")}
    walls = [w for w in doc.get("walls") or [] if w["id"] in wanted]
    used = {e["v"] for e in room["outline"]}
    used |= {v for w in walls for v in (w["v1"], w["v2"])}
    vertices = [v for v in doc.get("vertices") or [] if v["id"] in used]
    furnishings = [f for f in doc.get("furnishings") or []
                   if f.get("room") == room["id"]]
    level = next((lv for lv in doc.get("levels") or [] if lv["id"] == lid),
                 {"id": lid, "name": "default"})
    settings = dict(doc.get("settings") or {})
    settings.pop("active_floor", None)          # view state, never a template's
    return {
        "format": FORMAT, "version": VERSION, "units": "inches",
        "settings": settings,
        "levels": [dict(level)],
        "vertices": [dict(v) for v in vertices],
        "walls": [dict(w) for w in walls],
        "rooms": [dict(room)],
        "furnishings": [dict(f) for f in furnishings],
    }


def _fresh_prefix(base):
    """A short id prefix that collides with nothing in `base`. Ids match
    `^[A-Za-z][A-Za-z0-9_-]*$`, so a letter-led prefix is always legal; the
    canonicaliser renumbers everything on the next save anyway."""
    taken = set()
    for coll in ("levels", "vertices", "walls", "rooms", "furnishings",
                 "groups"):
        for row in base.get(coll) or []:
            taken.add(row.get("id"))
            for op in row.get("openings") or []:
                taken.add(op.get("id"))
    n = 1
    while any(str(i).startswith(f"t{n}_") for i in taken if i):
        n += 1
    return f"t{n}_"


def merge_room_document(base, tmpl, level_id=None, dx=0.0, dy=0.0,
                        name=None):
    """Fold the one-room document `tmpl` into `base` as a **floating** room,
    offset by (`dx`, `dy`) and landed on `level_id` (the base's first level
    when omitted). `base` is not mutated; the merged document is returned.

    Ids are re-minted under a prefix that collides with nothing in `base`, so
    a template can be inserted repeatedly — the canonicaliser renumbers them
    on the next save. The room arrives **floating** whatever the template
    said, because an inserted room has joined nothing yet: it is the user's
    to place, which is the same contract Extract gives and what makes
    shuffle-mode insertion behave."""
    out = {k: v for k, v in base.items()}
    for coll in ("levels", "vertices", "walls", "rooms", "furnishings"):
        out[coll] = [dict(row) for row in base.get(coll) or []]
    levels = out["levels"]
    if not levels:
        raise ValueError("the target design has no level to insert into")
    lid = level_id or levels[0]["id"]
    if not any(lv["id"] == lid for lv in levels):
        raise ValueError(f"no level {lid!r} in the target design")

    pre = _fresh_prefix(base)

    def rid(old):
        return f"{pre}{old}"

    for v in tmpl.get("vertices") or []:
        out["vertices"].append({**v, "id": rid(v["id"]), "level": lid,
                                "x": float(v["x"]) + dx,
                                "y": float(v["y"]) + dy})
    for w in tmpl.get("walls") or []:
        wall = {**w, "id": rid(w["id"]), "level": lid,
                "v1": rid(w["v1"]), "v2": rid(w["v2"])}
        # a template's wall sides name ROOMS; only its own room comes with it,
        # so a side pointing anywhere else would dangle (I2)
        keep = {r["id"] for r in tmpl.get("rooms") or []}
        for side in ("left", "right"):
            if wall.get(side) is not None:
                wall[side] = (rid(wall[side]) if wall[side] in keep else None)
        if w.get("openings"):
            wall["openings"] = [{**op, "id": rid(op["id"])}
                                for op in w["openings"]]
        out["walls"].append(wall)
    for r in tmpl.get("rooms") or []:
        room = {**r, "id": rid(r["id"]), "level": lid,
                "outline": [{**e, "v": rid(e["v"]),
                             "wall": rid(e["wall"]) if e.get("wall") else None}
                            for e in r["outline"]],
                # INSERTED MEANS FLOATING: the room has joined nothing yet.
                # `extracted_from` is cleared with it -- it was never lifted
                # out of THIS design, and pointing at a level it never sat on
                # would be a lie the document cannot check.
                "placement": {**(r.get("placement") or {}),
                              "state": "floating", "extracted_from": None}}
        if name:
            room["name"] = name
        out["rooms"].append(room)
    for f in tmpl.get("furnishings") or []:
        pos = f.get("pos") or [0.0, 0.0]
        out["furnishings"].append({
            **f, "id": rid(f["id"]), "level": lid,
            "room": rid(f["room"]) if f.get("room") else None,
            "pos": [float(pos[0]) + dx, float(pos[1]) + dy]})
    return out


def template_room_name(tmpl):
    """The name of the room a one-room template carries (for status lines and
    for naming the inserted copy). Raises if the document is not one room."""
    rooms = tmpl.get("rooms") or []
    if len(rooms) != 1:
        raise ValueError(f"a room template holds exactly one room, "
                         f"not {len(rooms)}")
    return rooms[0].get("name") or "Room"


def template_offset_to(tmpl, x, y):
    """The (dx, dy) that lands the template room's outline centroid on
    (`x`, `y`) — what a paste/insert at a clicked point wants."""
    room = (tmpl.get("rooms") or [{}])[0]
    pos = {v["id"]: (float(v["x"]), float(v["y"]))
           for v in tmpl.get("vertices") or []}
    pts = [pos[e["v"]] for e in room.get("outline") or [] if e["v"] in pos]
    if not pts:
        return 0.0, 0.0
    cx = sum(p[0] for p in pts) / len(pts)
    cy = sum(p[1] for p in pts) / len(pts)
    return x - cx, y - cy
