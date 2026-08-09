#!/usr/bin/env python3
"""D53 constraint 1: what does widening `RoomItem.shape()` change the hit target of?

    python docs/evidence/d53_hit_census.py > docs/evidence/d53-hit-census.txt

**Parsed, not grepped**, and the distinction is this repo's own rule: grep for
identifiers, parse for shapes. A hit target is decided by three things that are
each spelled many ways — the item's `shape()`, its z, and its flags — plus the
call sites that ASK. A grep for `shape` finds the word; `ast` finds the
overrides, the `setZValue` arguments wherever they occur (including in a helper
that never mentions the class), the `setFlag` calls with the enum they set, and
every `itemAt` / `items(` hit query with the function that contains it.

Qt picks the TOPMOST item whose `shape()` contains the point. `RoomItem.shape()`
returns only the label rect today; widening it to the outline makes every room
contain its whole interior, so for any point inside a room the answer changes
from "the item below" to "the room" **unless something above it also contains
the point**. That makes z-order the deciding term, which is why it is censused
beside the flags rather than assumed.

WHAT THIS CENSUS DOES NOT COVER, stated because an unstated boundary reads as
coverage: it enumerates the DECIDERS (shape / z / flags) and the ASKERS (hit
queries). It cannot tell you which gesture a user will actually make, and it
does not execute anything -- a runtime probe over a real plan is the
complement, not a substitute. Nor does it see hit decisions made by Qt
internally on the scene's own item list (rubber-band `items(rect)`,
`QGraphicsScene` press routing), which is why those are listed separately as
call sites rather than resolved here.
"""
import ast
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
PKG = ROOT / "floorplanner"

GRAPHICS_BASE_HINT = ("QGraphicsItem", "QGraphicsObject", "QGraphicsPathItem",
                      "QGraphicsRectItem", "QGraphicsPixmapItem",
                      "QGraphicsLineItem", "QGraphicsSimpleTextItem")
HIT_CALLS = {"itemAt", "items"}
MOUSE = ("mousePressEvent", "mouseMoveEvent", "mouseReleaseEvent",
         "mouseDoubleClickEvent", "dropEvent", "dragMoveEvent",
         "contextMenuEvent", "hoverMoveEvent")


def base_names(cls):
    out = []
    for b in cls.bases:
        out.append(ast.unparse(b))
    return out


def literal(node):
    try:
        return ast.unparse(node)
    except Exception:                                  # pragma: no cover
        return "?"


def enclosing(tree, node):
    """Name of the function/class that lexically contains `node`."""
    best = None
    for n in ast.walk(tree):
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            if (getattr(n, "lineno", 0) <= node.lineno
                    and node.lineno <= getattr(n, "end_lineno", 0)):
                if best is None or n.lineno > best.lineno:
                    best = n
    return best.name if best else "<module>"


def main():
    files = sorted(PKG.rglob("*.py"))
    items, zvals, flags, hits = {}, [], [], []

    for f in files:
        rel = f.relative_to(ROOT).as_posix()
        tree = ast.parse(f.read_text(encoding="utf-8"))

        for cls in [n for n in ast.walk(tree) if isinstance(n, ast.ClassDef)]:
            bases = base_names(cls)
            if not any(h in b for b in bases for h in GRAPHICS_BASE_HINT):
                continue
            meths = {m.name for m in cls.body
                     if isinstance(m, (ast.FunctionDef, ast.AsyncFunctionDef))}
            items[cls.name] = {
                "file": f"{rel}:{cls.lineno}",
                "bases": bases,
                "shape": "OVERRIDDEN" if "shape" in meths else "inherited",
                "boundingRect": "OVERRIDDEN" if "boundingRect" in meths else "inherited",
                "mouse": sorted(m for m in meths if m in MOUSE),
            }

        for call in [n for n in ast.walk(tree) if isinstance(n, ast.Call)]:
            fn = call.func
            name = fn.attr if isinstance(fn, ast.Attribute) else (
                fn.id if isinstance(fn, ast.Name) else None)
            if name == "setZValue" and call.args:
                zvals.append((rel, call.lineno, enclosing(tree, call),
                              ast.unparse(fn.value) if isinstance(fn, ast.Attribute) else "?",
                              literal(call.args[0])))
            elif name == "setFlag" and call.args:
                zvals_target = ast.unparse(fn.value) if isinstance(fn, ast.Attribute) else "?"
                flags.append((rel, call.lineno, enclosing(tree, call),
                              zvals_target, literal(call.args[0]),
                              literal(call.args[1]) if len(call.args) > 1 else "True"))
            elif name in HIT_CALLS and isinstance(fn, ast.Attribute):
                recv = ast.unparse(fn.value)
                if name == "items" and not call.args:
                    continue                      # a full scan, not a hit query
                hits.append((rel, call.lineno, enclosing(tree, call),
                             f"{recv}.{name}({', '.join(literal(a) for a in call.args)})"))

    w = sys.stdout.write
    w("D53 -- HIT-TARGET CENSUS, parsed from the AST of floorplanner/**.py\n")
    w(f"    {len(files)} files, {len(items)} QGraphicsItem subclasses\n")
    w("=" * 78 + "\n\n")

    w("1. THE ITEMS -- who can be hit, and who decides their own hit shape\n\n")
    w(f"   {'class':<22}{'shape()':<12}{'boundingRect()':<16}site\n")
    for k in sorted(items):
        v = items[k]
        w(f"   {k:<22}{v['shape']:<12}{v['boundingRect']:<16}{v['file']}\n")
        if v["mouse"]:
            w(f"   {'':<22}mouse: {', '.join(v['mouse'])}\n")
    w("\n")

    w("2. Z-ORDER -- every setZValue, with the value as written\n")
    w("   (Qt picks the TOPMOST item whose shape() contains the point, so this\n")
    w("    is the term that decides whether a widened room WINS the press.)\n\n")
    for rel, ln, encl, target, val in sorted(zvals):
        w(f"   {rel}:{ln:<5} {encl:<28} {target}.setZValue({val})\n")
    w("\n")

    w("3. ITEM FLAGS -- selectable / movable, which gate what a hit can DO\n\n")
    for rel, ln, encl, target, flag, val in sorted(flags):
        short = flag.split(".")[-1]
        w(f"   {rel}:{ln:<5} {encl:<28} {target}: {short} = {val}\n")
    w("\n")

    w("4. THE ASKERS -- every hit query. These are the call sites whose ANSWER\n")
    w("   changes when a room's shape widens.\n\n")
    for rel, ln, encl, expr in sorted(hits):
        w(f"   {rel}:{ln:<5} {encl:<28} {expr}\n")


if __name__ == "__main__":
    main()
