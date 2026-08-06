#!/usr/bin/env python3
"""Turn `docs/defects/*.md` into GitHub issues -- or, on a dry run, into the
exact `gh` commands that would do it.

WHY THIS EXISTS NOW AND NOT LATER. The record format was designed to map onto
GitHub Issues, and a format declared "GitHub-ready" without a dry run that emits
valid commands is an unmeasured claim -- the same class as a census quoted from
memory. So the emitter is written with the format, `--dry-run` runs in the gate,
and the claim is checked every time the gate runs rather than the day someone
finally tries to migrate.

    python tools/defects_to_github.py --dry-run     # prints commands, creates
                                                    # nothing on GitHub
    python tools/defects_to_github.py --execute     # creates issues, writes
                                                    # github_issue: back

THE D-NUMBER IS THE PERMANENT KEY AND THE ISSUE NUMBER IS NOT. GitHub numbers
issues and pull requests from one sequence, and this repo already has ten PRs,
so D23 will not be issue #23. Every issue body therefore opens by naming its
D-number, `--execute` writes the issue number back into the record as
`github_issue:`, and the mapping lives in the repo instead of in a memory.

WHAT A DRY RUN CREATES: nothing on GitHub, and one local body file per record in
a temporary directory, so that the commands it prints are literally runnable
rather than illustrative. Pass `--body-dir` to put them somewhere you choose.

LABELS AND MILESTONES ARE EMITTED FIRST, and that is not padding: `gh issue
create --label X` FAILS if label X does not exist in the repo, and the same goes
for `--milestone`. A script that emitted only the issue creates would die on its
first line.
"""
import argparse
import pathlib
import re
import subprocess
import sys
import tempfile

# The emitted script is meant to be redirected or pasted into a shell, and the
# corpus is not ASCII -- titles carry arrows, primes and en dashes. So stdout is
# real UTF-8 rather than the console's cp1252, and rather than the
# backslash-transliteration `ref_audit.py` uses: that is right for a REPORT a
# human reads and wrong for a COMMAND a shell runs.
sys.stdout.reconfigure(encoding="utf-8")

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from defects_index import ROOT, load, phases, validate  # noqa: E402

# `gh` is not on PATH in this project's usual environment (CLAUDE.md), so the
# Windows install location is tried before giving up.
GH_FALLBACK = r"C:\Program Files\GitHub CLI\gh.exe"


def gh_path(explicit=None):
    if explicit:
        return explicit
    for cand in ("gh", GH_FALLBACK):
        try:
            subprocess.run([cand, "--version"], capture_output=True, check=True)
            return cand
        except (OSError, subprocess.CalledProcessError):
            continue
    return "gh"


def shq(s):
    """POSIX-ish quoting for display. The printed script is meant to be read
    and pasted into a shell, so it quotes rather than assuming a bare word."""
    return s if re.fullmatch(r"[A-Za-z0-9_./:-]+", s) else "'" + s.replace(
        "'", "'\\''") + "'"


def body_of(path, d, body):
    """The issue body: the record, with its permanent key stated first."""
    rel = path.relative_to(ROOT).as_posix()
    head = (f"> **Defect `D{d['id']}`** — the permanent key for this record, "
            f"independent of this issue's number.\n"
            f"> Source of truth: [`{rel}`]"
            f"(https://github.com/pjm4github/FloorPlanner/blob/main/{rel})\n")
    meta = [f"`rank: {d['rank']}`"]
    if d.get("milestone"):
        meta.append(f"`milestone: {d['milestone']}`")
    for k in ("opened", "closed", "closed_by", "state_source"):
        if d.get(k):
            meta.append(f"`{k}: {d[k]}`")
    if d.get("related"):
        meta.append("related: " + ", ".join(f"D{x}" for x in d["related"]))
    head += ">\n> " + " · ".join(meta) + "\n"
    # strip the record's own H1 -- the issue title carries it
    text = re.sub(r"\A\s*#\s.*\n", "", body).strip()
    return head + "\n" + text + "\n"


def commands(recs, gh, body_dir):
    """Every command needed, in the order they must run."""
    labels, milestones, out = set(), set(), []
    for _, d, _ in recs:
        labels.update(d.get("labels") or [])
        if d.get("milestone"):
            milestones.add(d["milestone"])

    out.append("# 1. labels must exist before an issue can carry one")
    for lb in sorted(labels):
        kind = lb.split(":", 1)[0]
        colour = {"type": "d73a4a", "area": "0075ca",
                  "status": "fbca04"}.get(kind, "cccccc")
        out.append(f"{shq(gh)} label create {shq(lb)} --color {colour} "
                   f"--description {shq(kind + ' label, fixed taxonomy')} "
                   f"--force")

    out.append("")
    out.append("# 2. milestones must exist too")
    for ms in sorted(milestones):
        out.append(f"{shq(gh)} api repos/:owner/:repo/milestones -f "
                   f"title={shq(ms)} || true   # already exists -> non-zero")

    out.append("")
    out.append(f"# 3. one issue per record ({len(recs)}), body from file")
    for _path, d, _ in recs:
        bf = (body_dir / f"D{d['id']}.md").as_posix()
        cmd = [shq(gh), "issue", "create",
               "--title", shq(f"D{d['id']}: {d['title']}"),
               "--body-file", shq(bf)]
        for lb in d.get("labels") or []:
            cmd += ["--label", shq(lb)]
        if d.get("milestone"):
            cmd += ["--milestone", shq(d["milestone"])]
        out.append(" ".join(cmd))
        if d["state"] == "closed":
            reason = ("completed" if d["state_reason"] == "completed"
                      else "not planned")
            out.append(f"#   then: {shq(gh)} issue close <number> --reason "
                       f"{shq(reason)}   # {d['state_reason']}")
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--dry-run", action="store_true")
    g.add_argument("--execute", action="store_true")
    ap.add_argument("--gh", help="path to the gh executable")
    ap.add_argument("--body-dir", help="where body files are written")
    ap.add_argument("--force", action="store_true",
                    help="re-create issues for records that already have one")
    ap.add_argument("--yes", action="store_true",
                    help="required with --execute; confirms creating issues")
    a = ap.parse_args()

    # --execute REACHES GITHUB, and creating fifty issues is not undoable by
    # any command here -- issues can be closed but not deleted. It is therefore
    # made hard to do by accident, because it already was done by accident once:
    # `--execute` was run while testing the idempotence guard and got as far as
    # the API before failing on a missing label. Nothing was created that time.
    # A flag is cheap; fifty stray issues in someone's tracker are not.
    if a.execute and not a.yes:
        print("Docs-GitHub: --execute creates issues on GitHub and cannot be "
              "undone from here.\n"
              "             Re-run with --yes if that is what you want, or "
              "use --dry-run to see\n"
              "             exactly what it would do.")
        return 2

    try:
        recs = load()
    except ValueError as e:
        print(f"Docs-GitHub: MALFORMED -- {e}")
        return 1
    errs = validate(recs, phases())
    if errs:
        print(f"Docs-GitHub: {len(errs)} record problem(s); refusing to emit")
        for e in errs:
            print(f"    {e}")
        return 1

    done = [d for _, d, _ in recs if d.get("github_issue")]
    if done and not a.force:
        if a.execute:
            print(f"Docs-GitHub: {len(done)} record(s) already carry "
                  f"github_issue; refusing (use --force)")
            return 1

    gh = gh_path(a.gh)
    body_dir = pathlib.Path(a.body_dir) if a.body_dir else pathlib.Path(
        tempfile.mkdtemp(prefix="fp-defect-bodies-"))
    body_dir.mkdir(parents=True, exist_ok=True)
    for path, d, body in recs:
        (body_dir / f"D{d['id']}.md").write_text(
            body_of(path, d, body), encoding="utf-8", newline="\n")

    cmds = commands(recs, gh, body_dir)

    if a.dry_run:
        print("\n".join(cmds))
        n_iss = sum(1 for ln in cmds if " issue create " in ln)
        print(f"\n# Docs-GitHub: DRY RUN -- {len(recs)} records, {n_iss} issue "
              f"create commands, nothing created on GitHub.")
        print(f"# Bodies written to {body_dir}")
        if n_iss != len(recs):
            print(f"# MISMATCH: {n_iss} commands for {len(recs)} records")
            return 1
        return 0

    # --execute
    created = 0
    for path, d, _ in recs:
        if d.get("github_issue") and not a.force:
            continue
        cmd = [gh, "issue", "create",
               "--title", f"D{d['id']}: {d['title']}",
               "--body-file", str(body_dir / f"D{d['id']}.md")]
        for lb in d.get("labels") or []:
            cmd += ["--label", lb]
        if d.get("milestone"):
            cmd += ["--milestone", d["milestone"]]
        p = subprocess.run(cmd, capture_output=True, text=True, cwd=ROOT)
        if p.returncode:
            print(f"Docs-GitHub: FAILED on D{d['id']}: "
                  f"{p.stderr.strip()[:300]}")
            return 1
        m = re.search(r"/issues/(\d+)", p.stdout)
        if not m:
            print(f"Docs-GitHub: D{d['id']} created but no number in output: "
                  f"{p.stdout.strip()[:200]}")
            return 1
        num = m.group(1)
        text = path.read_text(encoding="utf-8")
        text = re.sub(r"^github_issue:.*$", f"github_issue: {num}", text,
                      count=1, flags=re.M)
        path.write_text(text, encoding="utf-8", newline="\n")
        created += 1
        if d["state"] == "closed":
            reason = ("completed" if d["state_reason"] == "completed"
                      else "not planned")
            subprocess.run([gh, "issue", "close", num, "--reason", reason],
                           capture_output=True, cwd=ROOT)
    print(f"Docs-GitHub: created {created} issue(s); github_issue written back")
    return 0


if __name__ == "__main__":
    sys.exit(main())
