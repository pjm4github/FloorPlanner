#!/usr/bin/env python3
"""PHASE 6 READ-BACK CENSUS -- the material a ruling needs, measured.

    python docs/evidence/phase6_readback_census.py

Phase 6 is RED in the charter: "command undo -- the largest remaining task;
retires `snapshot()`". RED means A RULING IS MISSING, not that the work is
large. This census produces the material that ruling needs and implements
nothing.

THREE QUESTIONS, from the framing that got Phase 6 the go-ahead:

  Q1  WHAT ARE `snapshot()`'s CALLERS, ACTUALLY?  P6.2 retires snapshot undo,
      and the "tidy-up pass that outlives its mess" rule says every remaining
      caller then needs RE-JUSTIFYING rather than inheriting. So they have to
      be enumerated before anything is designed, split by what they use it FOR
      -- undo history, dirty tracking, or something else.
  Q2  WHAT MUST THE COMMAND INTERFACE COVER?  P6.1 names nine command classes.
      That list was written in Phase 0. The census is of the MUTATING ENTRY
      POINTS that exist now, so the gap between the two is visible.
  Q3  WHICH QUEUED ITEMS GENUINELY DIE WITH IT?  The claim that Phase 6
      subsumes queued work is worth exactly what it can be checked against.

-- HOW IT COUNTS, and this is the rule it is obeying --

**GREP FOR IDENTIFIERS, PARSE FOR SHAPES.** `snapshot` is a NAME, so a grep for
it is exact and is used. But "which methods MUTATE the document" is a SHAPE, and
a grep for it would find the spelling I happened to think of -- the error that
survived two censuses at P3.6 and P4.5(40). So the mutation census is an `ast`
walk: a method is a mutator if its body reaches `_commit_if_changed`,
`_touch`/dirty marking, or any known scene-mutating call.

**AND ITS OWN BOUNDARY IS STATED**: an AST walk finds what the SOURCE says.
A method that mutates only through a helper it calls indirectly is counted at
the helper, not at the caller, so the entry-point list is a lower bound on the
command surface and is labelled as one.
"""
import ast
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PKG = os.path.join(ROOT, "floorplanner")

# the marks that make a method a MUTATION as far as undo is concerned
DIRTY_MARKS = {"_commit_if_changed", "_mark_dirty", "_touch", "_schedule_dirty",
               "_dirty_timer"}
SCENE_MUTATORS = {"addItem", "removeItem", "setPos", "bind_wall", "unbind_wall",
                  "rebuild_all_walls", "normalize_walls", "merge_all",
                  "weld_scene", "delete_wall", "extract_room", "join_room",
                  "coalesce_outline_corners", "split_body_landings"}


def py_files():
    for dirpath, _dirs, files in os.walk(PKG):
        for f in sorted(files):
            if f.endswith(".py"):
                yield os.path.join(dirpath, f)


def rel(p):
    return os.path.relpath(p, ROOT).replace("\\", "/")


class _Walker(ast.NodeVisitor):
    """Records the wanted attribute accesses with their enclosing function."""

    def __init__(self, want, out, path, lines):
        self.want, self.out, self.path, self.lines = want, out, path, lines
        self.stack = []

    def visit_FunctionDef(self, node):
        self.stack.append(node.name)
        self.generic_visit(node)
        self.stack.pop()

    def visit_Attribute(self, node):
        if node.attr in self.want:
            self.out.append({
                "file": self.path, "line": node.lineno,
                "in_function": self.stack[-1] if self.stack else "<module>",
                "name": node.attr,
                "source": self.lines[node.lineno - 1].strip()[:110],
            })
        self.generic_visit(node)


# ------------------------------------------------------------------------ Q1
def snapshot_callers():
    """Every call to `snapshot()` / `_restore_state()` / the stacks, by NAME
    (exact -- these are identifiers) with the enclosing function, so each can
    be re-justified individually as P6.2 requires."""
    want = ("snapshot", "_restore_state", "_undo_stack", "_redo_stack",
            "_committed_state", "_saved_state")
    out = []
    for path in py_files():
        src = open(path, encoding="utf-8").read()
        try:
            tree = ast.parse(src)
        except SyntaxError:
            continue
        # the enclosing-function name is carried on the VISITOR INSTANCE, not
        # in a closure over a loop variable -- B023, the same late-binding trap
        # the viewer's fix records. This file is held to the shipped lint bar
        # (the P0.1 standing rule: CI does not distinguish `docs/` from code).
        _Walker(want, out, rel(path), src.split("\n")).visit(tree)
    return out


# ------------------------------------------------------------------------ Q2
def mutating_methods():
    """Methods whose body reaches a dirty mark or a known scene mutator.

    A SHAPE, so it is parsed. Reported with which signal matched, because
    "marks the document dirty" and "mutates the scene" are different claims and
    a command interface has to cover the union."""
    out = []
    for path in py_files():
        src = open(path, encoding="utf-8").read()
        try:
            tree = ast.parse(src)
        except SyntaxError:
            continue
        for node in ast.walk(tree):
            if not isinstance(node, ast.FunctionDef):
                continue
            names = {n.attr for n in ast.walk(node)
                     if isinstance(n, ast.Attribute)}
            names |= {n.id for n in ast.walk(node) if isinstance(n, ast.Name)}
            d = names & DIRTY_MARKS
            m = names & SCENE_MUTATORS
            if d or m:
                out.append({"file": rel(path), "line": node.lineno,
                            "method": node.name,
                            "dirty_marks": sorted(d), "scene_calls": sorted(m),
                            "public": not node.name.startswith("_")})
    return out


# ------------------------------------------------------------------------ Q3
def queued_items_claimed():
    """Records the plan/roadmap say Phase 6 absorbs -- read off DISK, with the
    line that says so, rather than from memory."""
    hits = []
    for name in ("V5_MIGRATION_PLAN.md", "ROADMAP.md"):
        p = os.path.join(ROOT, "docs", name)
        if not os.path.exists(p):
            continue
        for i, line in enumerate(open(p, encoding="utf-8").read().split("\n"), 1):
            if re.search(r"Phase 6|P6\.[123]", line):
                hits.append({"file": f"docs/{name}", "line": i,
                             "text": line.strip()[:200]})
    return hits


def main():
    callers = snapshot_callers()
    muts = mutating_methods()
    by_use = {}
    for c in callers:
        by_use.setdefault(c["name"], []).append(c)
    return {
        "Q1_snapshot_and_undo_call_sites": {
            "total": len(callers),
            "by_name": {k: len(v) for k, v in sorted(by_use.items())},
            "by_file": {f: sum(1 for c in callers if c["file"] == f)
                        for f in sorted({c["file"] for c in callers})},
            "sites": callers,
        },
        "Q2_mutating_methods": {
            "total": len(muts),
            "public": sum(1 for m in muts if m["public"]),
            "private": sum(1 for m in muts if not m["public"]),
            "by_file": {f: sum(1 for m in muts if m["file"] == f)
                        for f in sorted({m["file"] for m in muts})},
            "BOUNDARY": ("an AST walk finds what the SOURCE says. A method that "
                         "mutates only through a helper it calls indirectly is "
                         "counted at the helper, so this is a LOWER BOUND on "
                         "the command surface"),
            "methods": sorted(muts, key=lambda m: (m["file"], m["line"])),
        },
        "Q3_what_the_record_says_phase_6_absorbs": queued_items_claimed(),
    }


if __name__ == "__main__":
    json.dump(main(), sys.stdout, indent=1)
    sys.stdout.write(chr(10))
