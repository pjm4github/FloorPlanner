#!/usr/bin/env python3
"""Inventory every cross-reference in the repo, from a FROZEN pattern set.

Why this is code and not a grep. The docs refactor moves the defect register
out of one table into one file per record, and the acceptance condition is that
no reference is lost in translation: the count taken before the move must match
the count taken after, or every difference must be itemised. A grep retyped at
the end cannot establish that -- it is the same failure `tools/gate.py` was
written for, a number produced at one moment and compared against a number
produced by a different incantation at another. So the pattern set lives here,
in one place, and both the before and the after run THIS module.

Three consumers, one definition:

  * step 0 of the refactor takes the baseline inventory;
  * `tools/gate.py --docs` resolves every reference and fails on a dangling one;
  * step 9 re-runs it and compares against the baseline.

WHAT IT LOOKS FOR, and the shape is deliberately narrow -- a pattern that also
matched prose would make the totals noise:

  defect N / defects N   the long form, the one the corpus actually uses
  row N / rows N         the register's own idiom, from when it was a table
  DN                     the permanent-key form, the going-forward spelling
  defectN-x / defectN_x  an evidence artifact named for the record it belongs to
  a markdown link to another document, in the usual bracket-paren spelling

THIS FILE'S OWN PROSE IS DELIBERATELY WRITTEN NOT TO MATCH. The tool scans every
tracked text file including itself, so a docstring that spelled out a sample
reference would count as one -- and a sample link would count as a DANGLING one,
which is a fabricated finding. The patterns above are described rather than
exhibited for exactly that reason, and the regex literals below do not match
themselves either (the separator between the word and its digits is regex
syntax, not whitespace). Keep it that way when editing.

WHAT IT DOES NOT LOOK FOR, stated so the boundary is on the record rather than
discovered later: bare `#N` (indistinguishable from a hex colour, a heading and
an ordinary count -- 1,002 hits, almost none of them references), phase ids
(`P4.5`), and commit shas. None of those are defect references and counting
them would drown the ones that are.

RESOLUTION has two sources and prefers the newer, so the same code works on
both sides of the move: `docs/defects/*.md` front matter if that directory
exists, otherwise the register table in `docs/CODE_REVIEW_v2.md`. A markdown
link resolves against the linking file's own directory.

RESOLUTION VIA PARENT, and it exists because the corpus needs it. A lettered id
whose own record does not exist resolves to its numeric parent -- `11a` to `11`.
That is not laxity: 11a is a HALF of one record, named in the register's prose
and never given a row of its own, and the ruling on this refactor is that such a
half stays in its parent's body rather than being split out (splitting it would
rewrite prose while moving it). The audit therefore reports it as resolved and
says by what route, so the count is honest in both directions -- the reference
is real, the record it names is real, and the file it lands in is the parent's.
A lettered id whose parent does not exist either still dangles.

    python tools/ref_audit.py                     # human report
    python tools/ref_audit.py --json out.json     # write the inventory
    python tools/ref_audit.py --compare base.json # itemise every difference
    python tools/ref_audit.py --strict            # exit 1 if anything dangles
"""
import argparse
import json
import pathlib
import re
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent

# Text files only, and tracked files only: an untracked scratch file is not part
# of the record and must not move the totals.
TEXT_SUFFIXES = {".py", ".md", ".yml", ".yaml", ".ini", ".toml", ".txt",
                 ".json", ".csv", ".qml", ".cfg"}

# THE AUDIT MUST NOT COUNT ITSELF. Its own inventories quote the context line of
# every reference they record, so scanning one would roughly double the total
# and make the baseline a moving target -- the count would depend on how many
# times the audit had been run. Excluded by name, not by directory, so ordinary
# evidence files beside them are still scanned.
SELF_ARTIFACTS = re.compile(r"docs/evidence/ref-audit-[\w.-]+\.json$")

# THE FROZEN SET. Changing it invalidates every baseline taken before the
# change, so a change must be accompanied by a fresh baseline and said so.
PATTERNS = (
    ("defect", re.compile(r"\bdefects?\s+(\d+[a-z]?)\b", re.I)),
    ("row", re.compile(r"\brows?\s+(\d+[a-z]?)\b", re.I)),
    ("dnum", re.compile(r"\bD(\d+[a-z]?)\b")),
    ("artifact", re.compile(r"\bdefect(\d+[a-z]?)[-_]")),
    ("mdlink", re.compile(r"\]\(([^)\s]*\.md)(?:#[^)\s]*)?\)")),
)

ID_KINDS = ("defect", "row", "dnum", "artifact")


def tracked_text_files():
    out = subprocess.run(["git", "ls-files"], cwd=ROOT,
                         capture_output=True, text=True).stdout
    files = []
    for rel in out.splitlines():
        if not rel:
            continue
        if SELF_ARTIFACTS.search(rel):
            continue
        p = ROOT / rel
        if p.suffix.lower() in TEXT_SUFFIXES and p.is_file():
            files.append(rel)
    return sorted(files)


def known_ids():
    """The set of record ids, from whichever source exists.

    `docs/defects/` wins when it is there, because after the split it IS the
    register; before the split the table is the only source there is.
    """
    ddir = ROOT / "docs" / "defects"
    ids, source = set(), None
    if ddir.is_dir():
        for f in sorted(ddir.glob("*.md")):
            m = re.search(r"^id:\s*['\"]?([0-9]+[a-z]?)['\"]?\s*$",
                          f.read_text(encoding="utf-8"), re.M)
            if m:
                ids.add(m.group(1).lower())
        if ids:
            source = "docs/defects/*.md"
    if not ids:
        reg = ROOT / "docs" / "CODE_REVIEW_v2.md"
        if reg.is_file():
            for line in reg.read_text(encoding="utf-8").splitlines():
                if not line.startswith("|"):
                    continue
                first = line.strip().strip("|").split("|")[0].strip()
                if re.fullmatch(r"\d+[a-z]?", first):
                    ids.add(first.lower())
            source = "docs/CODE_REVIEW_v2.md (register table)"
    return ids, source


def collect():
    ids, id_source = known_ids()
    refs = []
    for rel in tracked_text_files():
        path = ROOT / rel
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        for n, line in enumerate(text.splitlines(), 1):
            for kind, rx in PATTERNS:
                for m in rx.finditer(line):
                    target, via = m.group(1), "direct"
                    if kind in ID_KINDS:
                        target = target.lower()
                        ok = target in ids
                        if not ok and target[-1].isalpha() \
                                and target[:-1] in ids:
                            ok, via = True, "parent"
                    else:
                        base = (path.parent / target).resolve()
                        ok = base.is_file()
                    refs.append({
                        "file": rel, "line": n, "kind": kind,
                        "target": target, "resolves": ok, "via": via,
                        "context": line.strip()[:160],
                    })
    return refs, ids, id_source


def inventory():
    refs, ids, id_source = collect()
    by_kind, by_file, tokens = {}, {}, {}
    for r in refs:
        by_kind[r["kind"]] = by_kind.get(r["kind"], 0) + 1
        by_file[r["file"]] = by_file.get(r["file"], 0) + 1
        key = f'{r["kind"]}:{r["target"]}'
        tokens[key] = tokens.get(key, 0) + 1
    rev = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT,
                         capture_output=True, text=True).stdout.strip()
    return {
        "schema": 1,
        "rev": rev,
        "id_source": id_source,
        "known_ids": sorted(ids, key=lambda s: (int(re.sub(r"\D", "", s)), s)),
        "files_scanned": len(tracked_text_files()),
        "files_with_refs": len(by_file),
        "total": len(refs),
        "by_kind": dict(sorted(by_kind.items())),
        "by_file": dict(sorted(by_file.items())),
        "tokens": dict(sorted(tokens.items())),
        "unresolved": [r for r in refs if not r["resolves"]],
        "via_parent": [r for r in refs if r["via"] == "parent"],
        "refs": refs,
    }


def _ascii(s):
    """Echoed document text, made safe for the console.

    The suite's console is cp1252 and the corpus is not -- the register alone
    uses non-breaking hyphens, en dashes and arrows. A report that dies while
    printing a finding is worse than no report, so quoted text is transliterated
    on the way OUT only; the inventory JSON keeps it verbatim.
    """
    return s.encode("ascii", "backslashreplace").decode("ascii")


def report(inv, verbose=False):
    print(f"Ref-Audit: rev={inv['rev'][:9]} files={inv['files_scanned']} "
          f"with-refs={inv['files_with_refs']} total={inv['total']} "
          f"unresolved={len(inv['unresolved'])}")
    print(f"Ref-Ids:   {len(inv['known_ids'])} known, from {inv['id_source']}")
    print("Ref-Kinds: " + "  ".join(f"{k}={v}" for k, v in inv["by_kind"].items()))
    if inv["via_parent"]:
        print(f"Ref-Parent: {len(inv['via_parent'])} lettered reference(s) "
              f"resolved to a parent record (a half named in its body)")
        for r in inv["via_parent"]:
            print(f"    {r['file']}:{r['line']}: {r['target']} -> "
                  f"{r['target'][:-1]}")
    if inv["unresolved"]:
        print("\nUNRESOLVED -- these resolve to nothing today:")
        for r in inv["unresolved"]:
            print(f"    {r['file']}:{r['line']}: {r['kind']} -> "
                  f"{r['target']!r}\n        {_ascii(r['context'])}")
    if verbose:
        print("\nBy file:")
        for f, n in sorted(inv["by_file"].items(), key=lambda kv: -kv[1]):
            print(f"    {n:>5}  {f}")


def compare(inv, baseline_path):
    """Itemise every difference against a baseline. Nothing may be lost."""
    base = json.loads(pathlib.Path(baseline_path).read_text(encoding="utf-8"))
    print(f"Ref-Compare: baseline rev={base['rev'][:9]} total={base['total']}"
          f"  ->  now rev={inv['rev'][:9]} total={inv['total']}"
          f"  delta={inv['total'] - base['total']:+d}")
    bt, nt = base["tokens"], inv["tokens"]
    lost = {k: bt[k] for k in bt if k not in nt}
    gained = {k: nt[k] for k in nt if k not in bt}
    changed = {k: (bt[k], nt[k]) for k in bt if k in nt and bt[k] != nt[k]}
    print(f"Ref-Tokens: baseline={len(bt)} now={len(nt)} "
          f"lost={len(lost)} gained={len(gained)} recount={len(changed)}")
    if lost:
        print("\nLOST -- a reference target that no longer appears anywhere:")
        for k, n in sorted(lost.items()):
            print(f"    {k}  (was cited {n}x)")
    if gained:
        print("\nGAINED -- a reference target that did not appear before:")
        for k, n in sorted(gained.items()):
            print(f"    {k}  (now cited {n}x)")
    if changed:
        print("\nRECOUNTED -- same target, different number of citations:")
        for k, (a, b) in sorted(changed.items()):
            print(f"    {k}  {a} -> {b}  ({b - a:+d})")
    bu, nu = len(base["unresolved"]), len(inv["unresolved"])
    print(f"\nRef-Unresolved: baseline={bu} now={nu} delta={nu - bu:+d}")
    return 1 if lost else 0


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--json", metavar="PATH", help="write the inventory")
    ap.add_argument("--compare", metavar="PATH", help="itemise vs a baseline")
    ap.add_argument("--strict", action="store_true",
                    help="exit 1 if ANY reference resolves to nothing")
    ap.add_argument("--strict-ids", action="store_true",
                    help="exit 1 only if a DEFECT reference resolves to nothing")
    ap.add_argument("-v", "--verbose", action="store_true")
    args = ap.parse_args()

    inv = inventory()
    report(inv, args.verbose)
    rc = 0
    if args.json:
        pathlib.Path(args.json).write_text(
            json.dumps(inv, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8")
        print(f"\nWrote {args.json}")
    if args.compare:
        rc |= compare(inv, args.compare)
    if args.strict and inv["unresolved"]:
        rc |= 1
    # THE GATE FAILS ON A DANGLING DEFECT REFERENCE, NOT ON A DANGLING LINK, and
    # the difference is deliberate. A record reference that resolves to no file
    # is a broken key -- the register has lost a row. A markdown link can be
    # dangling and CORRECT: `superseded/CANVAS_ITEM_REFACTOR_PLAN.md` links
    # relative to the directory it was written in, and repairing it would mean
    # editing history to satisfy a lint. Links are counted and reported so the
    # number is visible; only keys are enforced.
    if args.strict_ids:
        broken = [r for r in inv["unresolved"] if r["kind"] in ID_KINDS]
        if broken:
            print(f"\nRef-Strict: {len(broken)} DEFECT reference(s) resolve to "
                  f"no record")
            rc |= 1
        else:
            n_link = len(inv["unresolved"])
            tail = (f" ({n_link} markdown link(s) dangling, reported not "
                    f"enforced)") if n_link else ""
            print(f"Ref-Strict: every defect reference resolves{tail}")
    return rc


if __name__ == "__main__":
    sys.exit(main())
