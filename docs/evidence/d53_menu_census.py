#!/usr/bin/env python3
"""D53 / A1b: EVERY way a right-click reaches a menu in this application.

    python docs/evidence/d53_menu_census.py > docs/evidence/d53-menu-census.txt

**Parsed, not grepped, and deliberately NOT scoped by a predicate.** The earlier
hit census asked "which sites read `itemAt(...) is None` as blank canvas?" and
answered it completely -- which is exactly why it missed a menu reached by any
other route. A census inherits the blindness of the predicate that scopes it,
so this one is scoped by the QUESTION ("what shows a menu on a right-click?")
and enumerates every mechanism Qt offers for it:

  1. `contextMenuEvent` overrides            -- the item/widget route
  2. `QMenu(...)` construction               -- who builds one, and where
  3. `.exec(...)` on a menu                  -- who actually SHOWS one
  4. `setContextMenuPolicy` / `customContextMenuRequested` -- the signal route
  5. `addAction` on a menu built elsewhere   -- shared menu builders

Each is reported with its enclosing class and function, so "which item type
answers a right-click" is readable off the output rather than inferred.

WHAT IT DOES NOT COVER: whether a given menu is REACHABLE at runtime. A
handler that exists can still be shadowed by a widget above it accepting the
event first -- which is the whole question this census was built to inform, and
it needs a runtime probe, not a parse. Stated here because an unstated boundary
reads as coverage, and that is the mistake this file exists to correct.
"""
import ast
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
PKG = ROOT / "floorplanner"


def enclosing(tree, node):
    cls = fn = None
    for n in ast.walk(tree):
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            if n.lineno <= node.lineno <= getattr(n, "end_lineno", 0):
                if isinstance(n, ast.ClassDef):
                    if cls is None or n.lineno > cls.lineno:
                        cls = n
                elif fn is None or n.lineno > fn.lineno:
                    fn = n
    return (cls.name if cls else "-"), (fn.name if fn else "<module>")


def call_name(node):
    f = node.func
    if isinstance(f, ast.Attribute):
        return f.attr
    if isinstance(f, ast.Name):
        return f.id
    return None


def main():
    overrides, builds, execs, policies, adders = [], [], [], [], []
    for f in sorted(PKG.rglob("*.py")):
        rel = f.relative_to(ROOT).as_posix()
        tree = ast.parse(f.read_text(encoding="utf-8"))

        for n in ast.walk(tree):
            if isinstance(n, ast.FunctionDef) and n.name == "contextMenuEvent":
                cls, _ = enclosing(tree, n)
                body = [x for x in ast.walk(n) if isinstance(x, ast.Call)]
                shows = any(call_name(c) == "exec" for c in body)
                overrides.append((rel, n.lineno, cls, shows, n.end_lineno - n.lineno + 1))
            elif isinstance(n, ast.Call):
                name = call_name(n)
                cls, fn = enclosing(tree, n)
                if name == "QMenu":
                    builds.append((rel, n.lineno, cls, fn))
                elif name == "exec" and isinstance(n.func, ast.Attribute):
                    recv = ast.unparse(n.func.value)
                    if "menu" in recv.lower():
                        execs.append((rel, n.lineno, cls, fn, recv))
                elif name in ("setContextMenuPolicy",):
                    policies.append((rel, n.lineno, cls, fn, ast.unparse(n)))
                elif name == "connect" and isinstance(n.func, ast.Attribute):
                    recv = ast.unparse(n.func.value)
                    if "customContextMenuRequested" in recv:
                        policies.append((rel, n.lineno, cls, fn, ast.unparse(n)))
                elif name == "addAction" and isinstance(n.func, ast.Attribute):
                    recv = ast.unparse(n.func.value)
                    if "menu" in recv.lower():
                        adders.append((rel, n.lineno, cls, fn, recv))

    w = sys.stdout.write
    w("D53 / A1b -- CONTEXT-MENU CENSUS, parsed from the AST of floorplanner/**.py\n")
    w("Scoped by the QUESTION, not by a predicate. See the module docstring.\n")
    w("=" * 78 + "\n\n")

    w("1. `contextMenuEvent` OVERRIDES -- the item/widget route\n")
    w("   This is the set the earlier census could not see, because it asked\n")
    w("   about `itemAt(...) is None` sites instead.\n\n")
    w(f"   {'class':<22}{'shows a menu?':<16}{'lines':<8}site\n")
    for rel, ln, cls, shows, n in sorted(overrides, key=lambda t: t[2]):
        w(f"   {cls:<22}{'YES' if shows else 'no exec':<16}{n:<8}{rel}:{ln}\n")
    w("\n")

    w("2. `QMenu(...)` CONSTRUCTION -- who builds one\n\n")
    for rel, ln, cls, fn in sorted(builds):
        w(f"   {rel}:{ln:<5} {cls}.{fn}\n")
    w("\n")

    w("3. MENU `.exec(...)` -- who actually SHOWS one\n\n")
    for rel, ln, cls, fn, recv in sorted(execs):
        w(f"   {rel}:{ln:<5} {cls}.{fn}  ->  {recv}.exec(...)\n")
    w("\n")

    w("4. THE SIGNAL ROUTE -- setContextMenuPolicy / customContextMenuRequested\n\n")
    if policies:
        for rel, ln, cls, fn, src in sorted(policies):
            w(f"   {rel}:{ln:<5} {cls}.{fn}  {src[:70]}\n")
    else:
        w("   (none -- this application does not use the signal route at all)\n")
    w("\n")

    w("5. SHARED MENU BUILDERS -- addAction on a menu passed in\n\n")
    seen = set()
    for rel, ln, cls, fn, _recv in sorted(adders):
        if (cls, fn) in seen:
            continue
        seen.add((cls, fn))
        w(f"   {rel}:{ln:<5} {cls}.{fn}\n")


if __name__ == "__main__":
    main()
