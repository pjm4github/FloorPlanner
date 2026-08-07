#!/usr/bin/env python3
"""Snap a plan's walls and vertices to a grid, and write the result.

    plan-snap.py < inputplan.json > outputplan.json
    python plan-snap.py -s12 -i inputplan.json -o outputplan.json

`-s` is the grid in inches; the default is 6. Everything else in the document
is passed through untouched -- furnishings, room names and properties,
settings, provenance, groups.

STDOUT IS THE DOCUMENT AND STDERR IS THE REPORT. That split is what makes the
redirect form work: `> outputplan.json` must receive JSON and nothing else, so
every count, warning and finding goes to stderr. Redirect stderr away and you
still get a valid plan; read it and you find out what the snap actually did.

PURE STDLIB, and deliberately: it imports nothing from `floorplanner`. Importing
even `floorplanner.design.validate` pulls the whole editor in behind it (the
package star-imports in dependency order), which would drag Qt into a text
filter. This runs anywhere Python does.

BOTH FORMATS, because the corpus has both:

  * **v5** (`floorplanner-design`) keeps coordinates in ONE place -- the
    `vertices` table -- and walls and room outlines reference them by id. So
    snapping the vertices moves the walls AND the room outlines that share those
    corners, with no chance of the two disagreeing.
  * **legacy** (`floorplanner-json`, v1-v4) has no vertex table: each wall
    carries its own `p1`/`p2`. Those are snapped in place. Legacy rooms have no
    stored geometry -- they are re-detected from the walls on load -- so there is
    nothing else to move.

WHAT SNAPPING NECESSARILY DOES, and why this tool does not stop at rounding:

  1. **Two corners can land on the same point.** In v5 that would leave two
     distinct `Vertex` records at one coordinate -- geometric coincidence
     without identity, which is exactly the fault D48 exists to detect and which
     `check()` cannot see once the document is welded. So coincident vertices
     are MERGED and every reference is rewired. Rounding without merging would
     produce a file that looks snapped and is quietly broken.
  2. **A short wall can collapse.** If both ends land on the same point the wall
     has zero length; it is dropped (with `--keep-degenerate` to retain it) and
     any group membership referring to it is dropped with it.
  3. **An opening can stop fitting.** A wall that shortens may no longer have
     room for its door or window. Those are REPORTED, never moved or deleted:
     where an opening should go on a shorter wall is a design decision, and a
     tool that guessed would be making it silently.

ROOM ANCHORS AND FURNISHINGS ARE LEFT ALONE. An anchor is a seed point for
detection, not geometry; nudging it to the grid can push it through a wall into
the neighbouring room. Furnishings are placed against walls by eye and are not
what "snap the walls" asks for.

Rounding is HALF-UP (`floor(x/s + 0.5) * s`), not Python's banker's rounding, so
3 inches on a 6-inch grid always goes to 6 and never sometimes to 0.
"""
import argparse
import json
import math
import sys
from collections import defaultdict

V5 = "floorplanner-design"


def snap(value, grid):
    """Nearest multiple of `grid`, halves away from zero-ish (see module note)."""
    return math.floor(value / grid + 0.5) * grid


def _fmt(x):
    """A clean float: 12.0 rather than 12.000000000000002."""
    return float(f"{x:.6f}") + 0.0


# --------------------------------------------------------------------- v5
def snap_v5(doc, grid, keep_degenerate, log):
    verts = doc.get("vertices") or []
    walls = doc.get("walls") or []
    rooms = doc.get("rooms") or []

    # Which rings ALREADY pinch, before this tool touches anything. Without
    # this the report blames the snap for faults it inherited -- `symmetricP1`
    # ships with a zero-width spur in WIC, which is a known finding of its own.
    was_pinched = {(r.get("name") or r.get("id")) for r in rooms
                   if len({e.get("v") for e in (r.get("outline") or [])})
                   != len(r.get("outline") or [])}

    moved = 0
    max_move = 0.0
    for v in verts:
        ox, oy = float(v.get("x", 0.0)), float(v.get("y", 0.0))
        nx, ny = _fmt(snap(ox, grid)), _fmt(snap(oy, grid))
        d = math.hypot(nx - ox, ny - oy)
        if d > 0:
            moved += 1
            max_move = max(max_move, d)
        v["x"], v["y"] = nx, ny

    # MERGE what landed together. Keyed by level as well as position: a vertex
    # carries exactly one level (I2), and two floors' corners at the same x/y
    # are different corners.
    first = {}
    remap = {}
    kept = []
    for v in verts:
        key = (v.get("level"), v["x"], v["y"])
        if key in first:
            remap[v["id"]] = first[key]
        else:
            first[key] = v["id"]
            kept.append(v)
    merged = len(verts) - len(kept)

    def rid(i):
        return remap.get(i, i)

    for w in walls:
        w["v1"], w["v2"] = rid(w.get("v1")), rid(w.get("v2"))
    collapsed_edges = 0
    pinched = []
    for r in rooms:
        out = r.get("outline") or []
        for e in out:
            e["v"] = rid(e.get("v"))
        # A merge can leave a ring visiting the same corner TWICE IN A ROW --
        # a zero-length outline edge, which trips I5 and is not geometry. Drop
        # the repeat, keeping the first entry's wall binding.
        if len(out) > 1:
            kept_e = [e for i, e in enumerate(out)
                      if e.get("v") != out[i - 1].get("v")]
            collapsed_edges += len(out) - len(kept_e)
            r["outline"] = kept_e
            out = kept_e
        # A NON-ADJACENT repeat is a different animal: the ring now touches
        # itself, which is a real pinch. Reported, never "fixed" -- which of the
        # two lobes the room keeps is a design decision.
        seen = [e.get("v") for e in out]
        if len(set(seen)) != len(seen):
            pinched.append(r.get("name") or r.get("id"))

    # COLLAPSED WALLS. A wall whose two ends are now one vertex has no length
    # and cannot be drawn, bound or opened.
    n_walls_before = len(walls)
    dead = {w["id"] for w in walls if w.get("v1") == w.get("v2")}
    if dead and not keep_degenerate:
        walls = [w for w in walls if w["id"] not in dead]
        doc["walls"] = walls
        for r in rooms:
            for e in r.get("outline") or []:
                if e.get("wall") in dead:
                    e["wall"] = None
        for g in doc.get("groups") or []:
            if isinstance(g.get("members"), list):
                g["members"] = [m for m in g["members"] if m not in dead]

    # RECONCILE THE WALL SIDES. Dropping a collapsed wall, or a zero-length
    # outline edge, can leave a surviving wall still naming a room whose
    # outline no longer names it back -- I6, and a fault this tool CAUSED. It
    # is repaired here rather than reported, because the repair is mechanical
    # and has no choice in it: a side that nobody claims becomes None. (The
    # faults this tool does NOT cause -- pinched rings, openings that stop
    # fitting -- are reported instead, because those do have a choice in them.)
    users = defaultdict(set)
    for r in rooms:
        for e in r.get("outline") or []:
            if e.get("wall"):
                users[e["wall"]].add(r["id"])
    unclaimed = 0
    for w in doc.get("walls") or []:
        for side in ("left", "right"):
            rid_ = w.get(side)
            if rid_ and rid_ not in users.get(w["id"], ()):
                w[side] = None
                unclaimed += 1
    if unclaimed:
        log(f"  wall sides {unclaimed} side reference(s) cleared -- the room's "
            f"outline no longer names that wall")

    # Collapsing a wall can strand the vertices only it used. Dropping them
    # keeps I10 (no orphan vertex) satisfied.
    live = {w.get(k) for w in doc.get("walls") or [] for k in ("v1", "v2")}
    live |= {e.get("v") for r in rooms for e in (r.get("outline") or [])}
    before_v = len(kept)
    kept = [v for v in kept if v["id"] in live]
    doc["vertices"] = kept

    log(f"  vertices   {len(verts)} -> {len(kept)}"
        f"   ({merged} merged onto a neighbour"
        f"{f', {before_v - len(kept)} orphaned and dropped' if before_v != len(kept) else ''})")
    log(f"  moved      {moved} of {len(verts)}   max move {max_move:.2f}\"")
    if collapsed_edges:
        log(f"  outlines   {collapsed_edges} zero-length outline edge(s) "
            f"collapsed after the merge")
    for name in pinched:
        if name in was_pinched:
            log(f"  ~ room {name}: its outline visited a corner twice BEFORE "
                f"the snap too -- pre-existing, not caused here")
        else:
            log(f"  ! room {name}: the snap made its outline visit a corner "
                f"twice -- the ring PINCHES. Reported, not repaired")
    log(f"  walls      {n_walls_before} -> {len(doc.get('walls') or [])}"
        f"   ({len(dead)} collapsed to zero length"
        f"{' -- KEPT (--keep-degenerate)' if keep_degenerate and dead else ', dropped' if dead else ''})")

    # OPENINGS that no longer fit. Reported, never moved -- see the module note.
    pos = {v["id"]: (v["x"], v["y"]) for v in kept}
    bad = []
    for w in doc.get("walls") or []:
        a, b = pos.get(w.get("v1")), pos.get(w.get("v2"))
        if not a or not b:
            continue
        span = math.dist(a, b)
        for op in w.get("openings") or []:
            width = _opening_width(op)
            if width is None:
                continue
            got = _opening_span(op, width, span)
            if got is None:
                continue
            off, end = got
            # BOTH ends, which is what I7 asks. The first draft tested only the
            # far end and missed an opening starting at -3.0" -- it ran off the
            # near end of a wall that had shortened behind it, and `check()`
            # reported what this did not.
            if off < -1e-6 or end > span + 1e-6:
                bad.append((w["id"], op.get("id") or op.get("code"), off, end, span))
    for wid, oid, off, end, span in bad:
        log(f"  ! opening {oid} on {wid}: spans {off:.1f}\"..{end:.1f}\" "
            f"of a wall that is now {span:.1f}\" long")
    if bad:
        log(f"  openings   {len(bad)} no longer fit -- REPORTED, not moved")
    return doc


def _opening_width(op):
    """Opening width in inches, or None if it cannot be determined.

    A KNOWING DUPLICATE of `floorplanner.geometry.parse_wwhh`, and the only one
    in this file. It cannot be imported: `floorplanner/__init__.py` star-imports
    in dependency order, so reaching any submodule pulls Qt in behind it, and a
    text filter should not need a GUI toolkit. Mirrored exactly rather than
    approximated -- the first draft read `4848` as 4'8" and would have reported
    fitting openings as broken.

        4 digits  WWHH    3280 = 32" x 80"
        5 digits  WWWHH   10884 = 108" x 84"
        6 digits  WWWHHH

    Anything else returns None, which SUPPRESSES the fit check for that opening.
    Declining to judge is right here: a width this cannot read is not evidence
    of a fault.
    """
    code = str(op.get("code") or "").strip()
    if code.isdigit() and len(code) in (4, 5, 6):
        return float(int(code[:2 if len(code) == 4 else 3]))
    w = op.get("width_in")
    return float(w) if isinstance(w, (int, float)) else None


def _opening_span(op, width, length):
    """Where the opening sits along the wall, as (start, end) measured from v1.

    Mirrors `floorplanner.viewer.fp3d.opening_span`, for the same reason
    `_opening_width` mirrors `parse_wwhh`: it cannot be imported without
    dragging the editor in. An opening is dimensioned from a NAMED END, never
    as an absolute distance from `p1` -- which is exactly what makes it survive
    the wall being stretched, and exactly what a naive reading gets wrong. The
    first draft here read every offset as "from v1" and reported an opening's
    position as 7.0"..51.0" when the document meant -3.0"..41.0".

        from=v1   offset is v1 -> the opening's near edge
        from=v2   offset is v2 -> the opening's near edge
        center    offset is the wall midpoint -> the opening's centre
    """
    a = op.get("anchor")
    if isinstance(a, dict) and isinstance(a.get("offset_in"), (int, float)):
        frm, off = a.get("from", "v1"), float(a["offset_in"])
        if frm == "v1":
            s0 = off
        elif frm == "v2":
            s0 = length - off - width
        else:
            s0 = length / 2.0 + off - width / 2.0
        return s0, s0 + width
    s = op.get("s")                      # legacy: a centre distance from p1
    if isinstance(s, (int, float)):
        return float(s) - width / 2.0, float(s) + width / 2.0
    return None


# ----------------------------------------------------------------- legacy
def snap_legacy(doc, grid, keep_degenerate, log):
    walls = doc.get("walls") or []
    moved = 0
    max_move = 0.0
    for w in walls:
        for key in ("p1", "p2"):
            p = w.get(key)
            if not (isinstance(p, list) and len(p) >= 2):
                continue
            ox, oy = float(p[0]), float(p[1])
            nx, ny = _fmt(snap(ox, grid)), _fmt(snap(oy, grid))
            d = math.hypot(nx - ox, ny - oy)
            if d > 0:
                moved += 1
                max_move = max(max_move, d)
            p[0], p[1] = nx, ny

    dead = [w for w in walls if w.get("p1") == w.get("p2")]
    if dead and not keep_degenerate:
        doc["walls"] = [w for w in walls if w.get("p1") != w.get("p2")]

    # In legacy there is no vertex table, so "merged" has no id to rewire --
    # but coincident ENDS are still worth naming, because that is what the
    # loader will weld into one corner.
    ends = defaultdict(int)
    for w in doc.get("walls") or []:
        for key in ("p1", "p2"):
            p = w.get(key)
            if isinstance(p, list) and len(p) >= 2:
                ends[(p[0], p[1])] += 1
    shared = sum(1 for n in ends.values() if n > 1)

    log(f"  wall ends  {moved} of {2 * len(walls)} moved   max move {max_move:.2f}\"")
    log(f"  walls      {len(walls)} -> {len(doc.get('walls') or [])}"
        f"   ({len(dead)} collapsed to zero length"
        f"{' -- KEPT (--keep-degenerate)' if keep_degenerate and dead else ', dropped' if dead else ''})")
    log(f"  corners    {len(ends)} distinct points, {shared} shared by 2+ walls")
    log("  note       legacy rooms are re-detected from the walls on load, so "
        "they follow")
    return doc


# ------------------------------------------------------------------- main
def main(argv=None):
    ap = argparse.ArgumentParser(
        prog="plan-snap.py",
        description="Snap a plan's walls and vertices to a grid.",
        epilog="stdout is the document; the report goes to stderr.")
    ap.add_argument("-s", "--snap", type=float, default=6.0, metavar="INCHES",
                    help="grid in inches (default: 6)")
    ap.add_argument("-i", "--input", metavar="FILE",
                    help="input plan (default: stdin)")
    ap.add_argument("-o", "--output", metavar="FILE",
                    help="output plan (default: stdout)")
    ap.add_argument("--indent", type=int, default=1,
                    help="JSON indent (default: 1, matching the corpus)")
    ap.add_argument("--keep-degenerate", action="store_true",
                    help="keep walls that collapse to zero length")
    ap.add_argument("-q", "--quiet", action="store_true",
                    help="suppress the stderr report")
    a = ap.parse_args(argv)

    if a.snap <= 0:
        ap.error(f"--snap must be positive, got {a.snap}")

    def log(msg):
        if not a.quiet:
            print(msg, file=sys.stderr)

    try:
        if a.input:
            with open(a.input, encoding="utf-8") as fh:
                doc = json.load(fh)
        else:
            doc = json.load(sys.stdin)
    except (OSError, ValueError) as e:
        print(f"plan-snap: cannot read the plan: {e}", file=sys.stderr)
        return 2

    fmt = doc.get("format")
    where = a.input or "<stdin>"
    log(f"plan-snap: {where}   grid {a.snap:g}\"   format {fmt or 'unknown'}")

    if fmt == V5:
        doc = snap_v5(doc, a.snap, a.keep_degenerate, log)
    elif isinstance(doc.get("walls"), list):
        if fmt != "floorplanner-json":
            log(f"  ! unrecognised format {fmt!r} -- treating it as legacy "
                f"because it has a walls[] list with p1/p2")
        doc = snap_legacy(doc, a.snap, a.keep_degenerate, log)
    else:
        print("plan-snap: this file has no walls[] -- is it a plan?",
              file=sys.stderr)
        return 2

    text = json.dumps(doc, indent=a.indent, ensure_ascii=False) + "\n"
    try:
        if a.output:
            with open(a.output, "w", encoding="utf-8", newline="\n") as fh:
                fh.write(text)
            log(f"  wrote      {a.output}")
        else:
            sys.stdout.write(text)
    except OSError as e:
        print(f"plan-snap: cannot write the plan: {e}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
