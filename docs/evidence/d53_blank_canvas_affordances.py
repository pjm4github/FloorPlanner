#!/usr/bin/env python3
"""What AFFORDANCES hang off the blank-canvas path?

    python docs/evidence/d53_blank_canvas_affordances.py > docs/evidence/d53-blank-canvas-affordances.txt

Ordered before implementing anything, and the reason is D53's own history: the
room-naming route turned out to be parasitic on the hit-testing defect -- a
right-click on a room's region returned None, the view called it blank canvas,
and a menu intended for empty space appeared over the room. If ONE affordance
was resting there, others may be.

So this enumerates, by parse, every branch gated on the blank-canvas question
and every user-facing action inside it. The gate is spelled two ways across the
tree's history -- `itemAt(...) is None` before D53, `self.blank(...)` after --
so both are matched, and any OTHER predicate standing in the same position is
reported as UNCLASSIFIED rather than silently skipped.

WHAT THIS DOES NOT COVER: whether an affordance is REACHABLE over a room. That
is the runtime question -- existence is a parse question, reachability is a run
question -- and it is measured by the probe beside this one. Stated because an
unstated boundary reads as coverage, which is the mistake that produced the
census this file is correcting for.
"""
import ast
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
PKG = ROOT / "floorplanner"

BLANK_SPELLINGS = ("itemAt", "blank", "on_blank_canvas", "_menu_target_is_canvas")


def is_blank_test(node):
    """Does this expression ask the blank-canvas question, however spelled?"""
    for n in ast.walk(node):
        if isinstance(n, ast.Call):
            f = n.func
            name = f.attr if isinstance(f, ast.Attribute) else getattr(f, "id", None)
            if name in BLANK_SPELLINGS:
                return name
    return None


def enclosing_fn(tree, node):
    best = None
    for n in ast.walk(tree):
        if isinstance(n, ast.FunctionDef) and n.lineno <= node.lineno <= n.end_lineno:
            if best is None or n.lineno > best.lineno:
                best = n
    return best.name if best else "<module>"


def affordances(node):
    """User-facing actions created inside a branch."""
    out = []
    for n in ast.walk(node):
        if not isinstance(n, ast.Call):
            continue
        f = n.func
        name = f.attr if isinstance(f, ast.Attribute) else getattr(f, "id", None)
        if name == "addAction" and n.args:
            try:
                lit = ast.literal_eval(n.args[0])
                out.append(f'menu item "{lit}"')
            except (ValueError, TypeError):
                out.append("menu item <computed>")
        elif name in ("select_floor_popup", "show_3d_view", "paste_room",
                      "new_concept_room", "setCursor"):
            out.append(f"calls {name}()")
        elif name == "clearSelection":
            out.append("CLEARS THE SELECTION")
    return out


def main():
    w = sys.stdout.write
    w("BLANK-CANVAS AFFORDANCES -- parsed from floorplanner/**.py\n")
    w("Every branch gated on 'is there nothing under the cursor?', and what a\n")
    w("user can reach inside it.\n")
    w("=" * 78 + "\n\n")
    found = 0
    for f in sorted(PKG.rglob("*.py")):
        rel = f.relative_to(ROOT).as_posix()
        tree = ast.parse(f.read_text(encoding="utf-8"))
        for n in ast.walk(tree):
            if not isinstance(n, ast.If):
                continue
            spelling = is_blank_test(n.test)
            if spelling is None:
                continue
            found += 1
            acts = affordances(n) or ["(no user-facing action)"]
            w(f"{rel}:{n.lineno}  in {enclosing_fn(tree, n)}()\n")
            w(f"    gate: {ast.unparse(n.test)[:70]}\n")
            w(f"    spelled via: {spelling}\n")
            for a in dict.fromkeys(acts):
                w(f"      - {a}\n")
            w("\n")
    w(f"{found} blank-canvas-gated branch(es).\n")


if __name__ == "__main__":
    main()
