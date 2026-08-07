#!/usr/bin/env python3
"""Count the suite's NEGATIVE assertions, and how many establish a precondition.

D43. The rule it follows from is in the Working agreement: *absence and
prevention are indistinguishable in the result*. A test asserting "X did not
happen" passes identically whether X was prevented or was never attempted, so
negative assertions are where vacuity concentrates -- and `tools/gate.py`'s
vacuity check cannot see it, because that one detects TAUTOLOGY only.

THIS IS THE COUNT, AND ONLY THE COUNT. The record is explicit that a remediation
plan written before the number would be sized by intuition, which is the thing
this project keeps finding wrong. So: enumerate the shapes, report how many
exist, report how many establish a precondition, publish the hit rate. Nothing
here proposes a fix and nothing here fails a gate.

    python tools/negative_assertions.py            # the report
    python tools/negative_assertions.py --json P   # the inventory
    python tools/negative_assertions.py -v         # every site, with context

THE SHAPES are the ones the record names, plus `!=` and empty-container equality
which are the same claim in different clothes:

    assert not X                     assert X is None
    assert X == 0                    assert X not in Y
    assert X == []  / {} / () / ""   assert X != Y
    assert X == <a captured "before" value>

WHAT "ESTABLISHES A PRECONDITION" MEANS HERE, AND ITS BOUNDARY -- read this
before quoting the hit rate. The intent is: *the test proved the mechanism could
have fired before asserting that it did not.* That is not decidable by a script.
What IS decidable is a proxy: **does a POSITIVE assertion appear earlier in the
same test function?** A test that first asserts `len(walls) == 4` and then
asserts `not stranded` has at least established that there was something to
strand; one whose only assertions are negative has established nothing.

The proxy can err in both directions, and the two were SPOT-CHECKED rather than
assumed -- they behave differently and the difference matters:

  * OVERCOUNT (an earlier positive assertion about something unrelated) is real
    in principle and was NOT OBSERVED. Three "established" rows were sampled and
    all three asserted positively about the same subject as the negative claim
    (the catalog write, the concept room, the template). A sample of three
    proves nothing about 157, but it is what was looked at, and reporting a
    weakness nobody found would be as dishonest as hiding one.
  * UNDERCOUNT is real and WAS observed. `test_ungrouped_walls_survive_gc`
    asserts only `counts(sc) == before`, yet its precondition is thoroughly
    established BY CONSTRUCTION -- it builds a room, groups, moves, bakes,
    ungroups and collects. Nothing about that is an assert, so the proxy calls
    it bare. Preconditions established by construction are invisible here.

So the number is not "how many are sound". The bare list is **a superset of the
suspect ones**: everything genuinely vacuous is in it, along with tests that are
fine and merely quiet. That is the right error direction for sizing a human
read, and the list is short enough to read.
"""
import argparse
import ast
import json
import pathlib
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="backslashreplace")
ROOT = pathlib.Path(__file__).resolve().parent.parent
TESTS = ROOT / "tests"

# Names that mark a value captured BEFORE the operation, so `x == before` is a
# "nothing changed" claim rather than an ordinary equality.
BEFORE = ("before", "orig", "prev", "baseline", "pre_", "_pre", "start",
          "initial", "was")

# `== 0` IS TWO DIFFERENT CLAIMS AND ONLY ONE OF THEM IS NEGATIVE. "this count
# is zero" is an absence claim; "this process exited 0" is a SUCCESS claim, as
# positive as they come. Found by spot-checking the first draft's output:
# `test_model_imports_zero_qt` was flagged for `assert r.returncode == 0`, when
# its real negative assertion (`assert not qt`) lives inside a string run in a
# subprocess and is invisible to any AST pass over this file. Counting the
# success check as the negative one would have been wrong twice over.
SUCCESS = ("returncode", "retcode", "exitcode", "exit_code", "rc", "status")


def _is_success_probe(node):
    """`x.returncode == 0` and friends -- success, not absence."""
    name = None
    if isinstance(node, ast.Attribute):
        name = node.attr
    elif isinstance(node, ast.Name):
        name = node.id
    elif isinstance(node, ast.Subscript) and isinstance(node.value, ast.Name):
        name = node.value.id
    return bool(name) and name.lower() in SUCCESS


def _is_before_name(node):
    if isinstance(node, ast.Name):
        return any(k in node.id.lower() for k in BEFORE)
    if isinstance(node, ast.Attribute):
        return any(k in node.attr.lower() for k in BEFORE)
    return False


def shape_of(test):
    """The negative shape of an assert's expression, or None if it is positive.

    A BoolOp (`assert a and b`) is negative if ANY conjunct is -- the assertion
    as a whole then carries a negative claim.
    """
    if isinstance(test, ast.BoolOp):
        for v in test.values:
            s = shape_of(v)
            if s:
                return s
        return None
    if isinstance(test, ast.UnaryOp) and isinstance(test.op, ast.Not):
        return "not X"
    if isinstance(test, ast.Compare) and len(test.ops) == 1:
        op, right, left = test.ops[0], test.comparators[0], test.left
        if isinstance(op, ast.NotIn):
            return "not in"
        if isinstance(op, ast.Is) and isinstance(right, ast.Constant) \
                and right.value is None:
            return "is None"
        if isinstance(op, ast.NotEq):
            return "!="
        if isinstance(op, ast.Eq):
            if _is_success_probe(left) or _is_success_probe(right):
                return None                       # a success check, not absence
            for side in (right, left):
                if isinstance(side, ast.Constant) and side.value == 0 \
                        and not isinstance(side.value, bool):
                    return "== 0"
                if isinstance(side, (ast.List, ast.Dict, ast.Tuple, ast.Set)) \
                        and not getattr(side, "elts", getattr(side, "keys", 1)):
                    return "== empty"
                if isinstance(side, ast.Constant) and side.value in ("", None):
                    return "== empty"
            if _is_before_name(right) or _is_before_name(left):
                return "== before"
    return None


def scan():
    rows, files = [], sorted(TESTS.rglob("test_*.py"))
    for path in files:
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"), str(path))
        except (OSError, SyntaxError):
            continue
        src = path.read_text(encoding="utf-8").splitlines()
        for fn in ast.walk(tree):
            if not isinstance(fn, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            if not fn.name.startswith("test_"):
                continue
            asserts = [n for n in ast.walk(fn) if isinstance(n, ast.Assert)]
            asserts.sort(key=lambda n: n.lineno)
            marked = [(n, shape_of(n.test)) for n in asserts]
            for i, (node, shape) in enumerate(marked):
                if not shape:
                    continue
                has_pos = any(s is None for _, s in marked[:i])
                rows.append({
                    "file": path.relative_to(ROOT).as_posix(),
                    "test": fn.name,
                    "line": node.lineno,
                    "shape": shape,
                    "positive_before": has_pos,
                    "n_asserts_in_test": len(marked),
                    "src": src[node.lineno - 1].strip()[:150]
                    if node.lineno <= len(src) else "",
                })
    return rows, files


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--json", metavar="PATH")
    ap.add_argument("-v", "--verbose", action="store_true")
    a = ap.parse_args()

    rows, files = scan()
    total_asserts = 0
    for path in files:
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"), str(path))
        except (OSError, SyntaxError):
            continue
        total_asserts += sum(1 for n in ast.walk(tree)
                             if isinstance(n, ast.Assert))

    neg = len(rows)
    established = sum(1 for r in rows if r["positive_before"])
    bare = [r for r in rows if not r["positive_before"]]
    bare_tests = sorted({(r["file"], r["test"]) for r in bare})

    by_shape, by_file = {}, {}
    for r in rows:
        by_shape[r["shape"]] = by_shape.get(r["shape"], 0) + 1
        by_file[r["file"]] = by_file.get(r["file"], 0) + 1

    print(f"Neg-Census: files={len(files)} asserts={total_asserts} "
          f"negative={neg} ({neg * 100 // max(total_asserts, 1)}% of asserts)")
    print(f"Neg-Precondition: {established}/{neg} have a positive assertion "
          f"earlier in the same test -- hit rate "
          f"{established * 100 // max(neg, 1)}%")
    print(f"Neg-Bare: {len(bare)} negative assertion(s) in "
          f"{len(bare_tests)} test(s) with NO positive assertion at all")
    print("Neg-Shapes: " + "  ".join(f"{k}={v}" for k, v in
                                     sorted(by_shape.items(),
                                            key=lambda kv: -kv[1])))
    print("\nTests whose assertions are ALL negative -- the read-first list:")
    for f, t in bare_tests:
        n = sum(1 for r in bare if r["file"] == f and r["test"] == t)
        print(f"    {f}::{t}  ({n})")
    if a.verbose:
        print("\nEvery negative assertion:")
        for r in rows:
            flag = " " if r["positive_before"] else "!"
            print(f"  {flag} {r['file']}:{r['line']}  [{r['shape']}]  "
                  f"{r['src']}")
    if a.json:
        pathlib.Path(a.json).write_text(json.dumps({
            "files": len(files), "asserts": total_asserts,
            "negative": neg, "established": established,
            "hit_rate_pct": established * 100 // max(neg, 1),
            "bare": len(bare), "bare_tests": [f"{f}::{t}" for f, t in bare_tests],
            "by_shape": dict(sorted(by_shape.items())),
            "by_file": dict(sorted(by_file.items())),
            "rows": rows,
        }, indent=2) + "\n", encoding="utf-8")
        print(f"\nWrote {a.json}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
