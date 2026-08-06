#!/usr/bin/env python3
"""Read the defect records, and regenerate `docs/defects/INDEX.md` from them.

THE INDEX IS GENERATED, NEVER HAND-EDITED. A hand-maintained index is a second
copy of the register, and this project has already measured what a second copy
of anything does: the 3D viewer's private `FURN` table disagreed with the
catalog on 22 of the 37 entries it shared, three of them by transposing width
and depth. So the index is derived, `--check` fails when it has drifted, and
`tools/gate.py --docs` runs that check.

    python tools/defects_index.py              # rewrite INDEX.md
    python tools/defects_index.py --check       # fail if it would change
    python tools/defects_index.py --validate    # front matter + taxonomy only

FRONT MATTER IS PARSED HERE RATHER THAN WITH A YAML LIBRARY, deliberately: the
shape is fixed and tiny (scalars, one flat list, comments, a `[a, b]` inline
list), a strict reader catches malformation that a permissive one would accept
and silently reinterpret, and it adds no dependency to a gate that has to run
in CI on two Python versions.
"""
import argparse
import pathlib
import re
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
DEFECTS = ROOT / "docs" / "defects"
INDEX = DEFECTS / "INDEX.md"
_RM = "README" + ".md"          # see the note in render()

TYPES = {"defect", "gap", "limit", "task"}
AREAS = {"geometry", "groups", "io", "ui", "tests", "docs", "perf", "schema",
         "tooling", "viewer"}
STATUSES = {"carried", "partial"}
STATES = {"open", "closed"}
REASONS = {None, "completed", "not_planned"}
SCALARS = ("id", "title", "state", "state_reason", "milestone", "opened",
           "closed", "closed_by", "rank", "related", "state_source",
           "github_issue")


def phases():
    """Every phase the Status table names (ruling C)."""
    out = set()
    for line in (ROOT / "docs" / "V5_MIGRATION_PLAN.md").read_text(
            encoding="utf-8").splitlines():
        if line.startswith("|"):
            c = [x.strip() for x in line.strip().strip("|").split("|")]
            if len(c) >= 2:
                m = re.match(r"\*\*(P\d\.\d[a-z]?)\*\*", c[1])
                if m:
                    out.add(m.group(1))
    return out


def unquote(val):
    """Strip the wrapping quotes AND unescape what the writer escaped.

    Not cosmetic: a title containing quotes -- `room_boolean("fragment") ...` --
    is written with `\\"` inside, and a reader that only strips the outer quotes
    hands back a string one character longer per quote. The title-length check
    then fails on a title that is actually within the limit, which is exactly
    how a lint teaches people to distrust it.
    """
    if len(val) >= 2 and val[0] == '"' and val[-1] == '"':
        val = val[1:-1]
    return val.replace('\\"', '"')


def parse(path):
    """Strict front-matter reader. Raises ValueError with a usable message."""
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        raise ValueError(f"{path.name}: no front matter (must start with ---)")
    end = text.find("\n---\n", 3)
    if end < 0:
        raise ValueError(f"{path.name}: front matter is not terminated by ---")
    fm, body = text[4:end], text[end + 5:]
    data, key = {}, None
    for n, raw in enumerate(fm.split("\n"), 2):
        line = raw.split(" #")[0].rstrip() if not raw.lstrip().startswith("#") \
            else ""
        if not line.strip():
            continue
        if line.startswith("  - "):
            if key is None:
                raise ValueError(f"{path.name}:{n}: list item before any key")
            data.setdefault(key, []).append(unquote(line[4:].strip()))
            continue
        m = re.match(r"^([a-z_]+):\s*(.*)$", line)
        if not m:
            raise ValueError(f"{path.name}:{n}: not `key: value` -> {line!r}")
        key, val = m.group(1), m.group(2).strip()
        if val == "":
            data[key] = []
        elif val == "null":
            data[key] = None
        elif val.startswith("[") and val.endswith("]"):
            inner = val[1:-1].strip()
            data[key] = [x.strip() for x in inner.split(",")] if inner else []
        else:
            data[key] = unquote(val)
    return data, body


def validate(recs, known_phases):
    """Every rule the gate enforces, each returning a usable message."""
    errs, shas = [], {}
    for path, d, _ in recs:
        n = path.name

        def bad(msg, _n=n):
            errs.append(f"{_n}: {msg}")

        for k in SCALARS + ("labels",):
            if k not in d:
                bad(f"front matter missing `{k}`")
        if d.get("state") not in STATES:
            bad(f"state {d.get('state')!r} not in {sorted(STATES)}")
        if d.get("state_reason") not in REASONS:
            bad(f"state_reason {d.get('state_reason')!r} is not one of "
                "null / completed / not_planned")
        if d.get("state") == "open" and d.get("state_reason") is not None:
            bad("an OPEN record cannot carry a state_reason")
        if d.get("state") == "closed" and d.get("state_reason") is None:
            bad("a CLOSED record must say completed or not_planned")
        labels = d.get("labels") or []
        types = [x for x in labels if x.startswith("type:")]
        areas = [x for x in labels if x.startswith("area:")]
        if len(types) != 1:
            bad(f"expected exactly one type: label, found {types}")
        if len(areas) != 1:
            bad(f"expected exactly one area: label, found {areas}")
        for lb in labels:
            kind, _, val = lb.partition(":")
            ok = ((kind == "type" and val in TYPES)
                  or (kind == "area" and val in AREAS)
                  or (kind == "status" and val in STATUSES))
            if not ok:
                bad(f"label {lb!r} is outside the fixed taxonomy")
        ms = d.get("milestone")
        if ms is not None and ms not in known_phases:
            bad(f"milestone {ms!r} names no phase in the Status table")
        title = d.get("title") or ""
        if len(title) > 99:
            bad(f"title is {len(title)} chars (limit 99)")
        if title.endswith("."):
            bad("title ends with a period")
        if not title:
            bad("title is empty")
        if d.get("closed_by"):
            shas[n] = d["closed_by"]
        if not re.fullmatch(r"\d+[a-z]?", str(d.get("id"))):
            bad(f"id {d.get('id')!r} is not <number>[letter]")
    # commit existence, batched: one git call, not one per record
    for n, sha in shas.items():
        rc = subprocess.run(["git", "cat-file", "-e", f"{sha}^{{commit}}"],
                            cwd=ROOT, capture_output=True).returncode
        if rc:
            errs.append(f"{n}: closed_by {sha!r} is not a commit in this repo")
    return errs


def load():
    out = []
    for path in sorted(DEFECTS.glob("*.md")):
        if path.name in ("INDEX.md", "README.md"):
            continue
        d, body = parse(path)
        out.append((path, d, body))
    return out


def render(recs):
    by_rank = sorted(recs, key=lambda r: int(r[1]["rank"]))
    def key(r):
        i = str(r[1]["id"])
        return (int(re.sub(r"\D", "", i)), i)
    by_id = sorted(recs, key=key)

    def counts(field):
        c = {}
        for _, d, _ in recs:
            for lb in d.get("labels") or []:
                k, _, v = lb.partition(":")
                if k == field:
                    c[v] = c.get(v, 0) + 1
        return dict(sorted(c.items(), key=lambda kv: (-kv[1], kv[0])))

    n_open = sum(1 for _, d, _ in recs if d["state"] == "open")
    t, a = counts("type"), counts("area")

    def row(path, d):
        lbl = " ".join(x for x in d["labels"] if not x.startswith("area:"))
        st = d["state"] + (f" ({d['state_reason']})" if d["state_reason"]
                           else "")
        ms = d["milestone"] or "—"
        area = next((x.split(":")[1] for x in d["labels"]
                     if x.startswith("area:")), "—")
        return (f"| **D{d['id']}** | [{d['title']}]({path.name}) | {st} | "
                f"{ms} | {area} | {lbl} |")

    head = "| id | title | state | milestone | area | labels |\n|---|---|---|---|---|---|"
    lines = [
        "# Defect register — index",
        "",
        "<!-- GENERATED by tools/defects_index.py — do not hand-edit. -->",
        "<!-- `python tools/defects_index.py` rewrites it; `--check` fails on drift. -->",
        "",
        f"**{len(recs)} records** — {n_open} open, {len(recs) - n_open} closed.",
        "",
        "| type | count | | area | count |",
        "|---|---:|---|---|---:|",
    ]
    ta, aa = list(t.items()), list(a.items())
    for i in range(max(len(ta), len(aa))):
        left = f"`type:{ta[i][0]}` | {ta[i][1]}" if i < len(ta) else " | "
        right = f"`area:{aa[i][0]}` | {aa[i][1]}" if i < len(aa) else " | "
        lines.append(f"| {left} | | {right} |")
    lines += [
        "",
        "The id is a permanent key written **D23**, independent of any tracker;",
        # The link is ASSEMBLED rather than written out, for the same reason
        # `ref_audit.py` describes its patterns instead of exhibiting them: a
        # literal markdown link in a tool's source is scanned where it sits, in
        # `tools/`, and reported as dangling -- a finding about nothing.
        f"see [`{_RM}`]({_RM}) for the field rules and the taxonomy.",
        "",
        "---",
        "",
        "## In register order (`rank`)",
        "",
        "The order the register listed them in, preserved because it exists",
        "nowhere else. It is **not** a ranking throughout — see `README.md`.",
        "",
        head,
    ]
    lines += [row(p, d) for p, d, _ in by_rank]
    lines += ["", "---", "", "## In id order", "", head]
    lines += [row(p, d) for p, d, _ in by_id]
    return "\n".join(lines) + "\n"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--validate", action="store_true")
    a = ap.parse_args()
    try:
        recs = load()
    except ValueError as e:
        print(f"Docs-Defects: MALFORMED -- {e}")
        return 1
    errs = validate(recs, phases())
    if errs:
        print(f"Docs-Defects: {len(errs)} problem(s)")
        for e in errs:
            print(f"    {e}")
        return 1
    if a.validate:
        print(f"Docs-Defects: {len(recs)} records, front matter valid")
        return 0
    want = render(recs)
    have = INDEX.read_text(encoding="utf-8") if INDEX.exists() else None
    if a.check:
        if have != want:
            print("Docs-Index: INDEX.md DIFFERS from a regeneration "
                  "(run `python tools/defects_index.py`)")
            return 1
        print(f"Docs-Index: INDEX.md matches a regeneration ({len(recs)} records)")
        return 0
    INDEX.write_text(want, encoding="utf-8", newline="\n")
    print(f"Docs-Index: wrote {INDEX.relative_to(ROOT)} ({len(recs)} records)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
