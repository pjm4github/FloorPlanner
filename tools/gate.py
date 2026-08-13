#!/usr/bin/env python3
"""Run the migration gate and EMIT ITS OWN CENSUS, as a commit trailer.

Why this exists, and it is not convenience. Three separate incidents in P3.5-P3.6
came from the same failure, and none of them was a typo:

  * a gate line transcribed into a commit message WITHOUT its ", 2 errors", so
    the message read green while the run was red (3cdf046);
  * "515 collected" quoted in a report written after two more tests had landed;
  * "516 collected" quoted the same way, with a reconciliation ASSERTED against
    it that was never performed -- 512 + 6 is 518.

A FOURTH, on 2026-08-07, with this tool and the commit hook both in place: the
gate was run as `python tools/gate.py | tail -3`, so only the DEEP line and the
verdict were ever seen, and the OFF and ON lines were typed into the commit
message from an earlier run (17.28s / 20.55s quoted; 17.14s / 19.79s recorded).
The verdict, counts and sums were right and the gate was genuinely green -- the
fabricated part was two wall-clock durations, which is the least consequential
thing in the block and exactly why it is the same failure. The hook cannot catch
it: the hook checks that a green gate EXISTS for this tree, not that the message
quotes it. `--trailer` closes it by removing the human from the copy.

The common cause is a human copying a number from one moment into a sentence
written at another. So the numbers stop being copied: this runs the gate,
computes the census, checks that every gate's outcomes SUM to what
`--collect-only` found, and prints a block meant to be pasted verbatim. A report
quotes the trailer; it does not restate it.

Exit status is the gate's: non-zero if any run is red OR any sum fails to
reconcile. An unreconciled sum is a defect (a test counted twice, as
`test_a_clipped_band_leaves_every_room_coherent` was under `deep`), not a
rounding difference, so it is treated as red.

    python tools/gate.py            # ruff + OFF + ON + DEEP
    python tools/gate.py --quick    # ruff + OFF only
    python tools/gate.py --deep     # ruff + DEEP only -- what CI's deep job runs
    python tools/gate.py --perf     # the timing lane, explicitly (P3.8)
    python tools/gate.py --docs     # the record lane: defect front matter,
                                    # the generated index, every defect
                                    # reference, and the GitHub dry run
    python tools/gate.py --trailer  # re-print the last full-mode trailer,
                                    # verbatim, for redirection into a commit
                                    # message file -- NEVER retype it

THE DOCS LANE IS ITS OWN LANE, like `--perf`, and deliberately NOT part of the
default block. The trailer above is pasted verbatim into commit messages, so its
SHAPE is load-bearing: adding a line to it partway through a branch would make
that branch's own trailers incomparable, which is the census-discrepancy class
this tool exists to prevent. `--docs` prints its own verdict, quoted beside the
full-mode trailer rather than inside it.

CI CALLS THIS TOOL RATHER THAN REIMPLEMENTING IT (defect 27, P3.8). The DEEP
job runs `--deep`, so the invariant set, the perf exclusion and the census
reconciliation are defined ONCE. Two implementations of a gate are two things
that can drift, and this project has already paid for that once (F2's disease,
P3.4 point 1).
"""
import re
import subprocess
import sys

# every outcome pytest reports that consumes a collected test
OUTCOMES = ("passed", "failed", "xfailed", "xpassed", "error", "errors",
            "skipped", "deselected")
RED = ("failed", "error", "errors")

# P3.8, THE FLAP-CLASS RULING: the timing lane is excluded from EVERY mode, not
# just DEEP. It used to run in OFF and ON, where a wall-clock ratio could turn
# the gate red on machine load alone -- and did, 1 of 8 and 2 of 8 in two
# sweeps. A gate whose red has two indistinguishable causes (a regression, or a
# busy machine) is separable only by reading which test failed, which is the
# manual step this tool exists to remove.
#
# It also makes the three runs' censuses reconcile against the SAME collected
# total, instead of DEEP alone reporting "7 deselected".
#
# The lane is not abandoned: `tools/gate.py --perf` runs it explicitly and
# prints its numbers, which is what P0.3b ruled it was for.
GATES = [
    ("OFF ", {}, ["-m", "not perf"]),
    ("ON  ", {"FP_VERIFY_DESIGN": "1"}, ["-m", "not perf"]),
    ("DEEP", {"FP_VERIFY_DESIGN": "deep"}, ["-m", "not perf"]),
]


def _run(args, env_extra=None):
    import os
    env = dict(os.environ)
    env.update(env_extra or {})
    p = subprocess.run([sys.executable, "-m", *args], capture_output=True,
                       text=True, env=env)
    return p.returncode, (p.stdout + p.stderr)


def _run_script(args, env_extra=None):
    """Run a SCRIPT by path. `_run` prepends `-m` and runs modules; the docs
    lane's three tools are scripts, and `python -m tools/foo.py` is not a
    thing."""
    import os
    env = dict(os.environ)
    env.update(env_extra or {})
    p = subprocess.run([sys.executable, *args], capture_output=True,
                       text=True, env=env, errors="replace")
    return p.returncode, (p.stdout + p.stderr)


def _summary(out: str) -> str:
    """pytest's final summary line, whatever the noise before it."""
    for line in reversed(out.strip().splitlines()):
        if re.search(r"\d+ (passed|failed|error|skipped|deselected)", line):
            return line.strip("= ").strip()
    return "<no summary line>"


def _counts(line: str) -> dict:
    got = {}
    for word in OUTCOMES:
        m = re.search(rf"(\d+) {word}\b", line)
        if m:
            got[word] = int(m.group(1))
    return got


def _perf() -> int:
    """Run the timing lane explicitly and print its numbers.

    P0.3b: the harness is "a local gate, invoked explicitly at P0.6 and P3.8 --
    the two moments its numbers decide something". This is that invocation, so
    it stops being a remembered incantation. It asserts only the catastrophic
    absolute bounds (P3.8's flap ruling); the ratios are printed to be READ."""
    rc, out = _run(["pytest", "-q", "-p", "no:randomly", "-m", "perf", "-s"])
    for line in out.splitlines():
        if line.startswith("[scaling]") or " passed" in line or " failed" in line:
            print(line)
    print(f"Perf-Verdict: {'RED' if rc else 'GREEN'} (absolute bounds only -- "
          f"the ratios above are RECORDED, not asserted)")
    return rc


# Assertions that cannot fail, in the ONE shape a machine can recognise.
# See the Working agreement's vacuity entry: of the three shapes, only
# vacuity BY TAUTOLOGY is detectable by grep -- vacuity by precondition and
# by basis need a human reading what the test established before it asserted.
# This catches the cheapest and most misleading one, because it reads as
# coverage in a diff.
_VACUOUS = (
    re.compile(r"\bassert\b.*\bor True\b"),
    re.compile(r"\bassert\b.*\bor 1\b"),
    re.compile(r"\bassert True\b"),
    re.compile(r"\bassert not False\b"),
)


def _vacuity() -> tuple:
    """Scan the suite for tautologically-unfailable assertions."""
    import pathlib
    hits = []
    for p in sorted(pathlib.Path("tests").rglob("test_*.py")):
        try:
            text = p.read_text(encoding="utf-8")
        except OSError:
            continue
        for n, line in enumerate(text.splitlines(), 1):
            code = line.split("#", 1)[0]
            if any(rx.search(code) for rx in _VACUOUS):
                hits.append(f"{p.as_posix()}:{n}: {line.strip()}")
    return len(hits), hits


# Coordinate assignment to a wall end. P3.1's split-on-write shim: `wall.p1 =
# ...` minted a fresh Vertex for that end and left every sharer behind, so the
# wall moved and the room outline did not. Four writers were retired across
# P4.5 and the shim itself deleted with them.
#
# THIS REPLACES `vertex.split_count()`, AND DELIBERATELY AT A DIFFERENT LAYER.
# The counter measured RUNTIME CHURN -- how many splits a run caused -- which
# is a fact about the code paths a test happened to execute. What is wanted
# permanently is that the MECHANISM CANNOT RETURN, and that is a question about
# the source text. So this is cheaper (a grep, not bookkeeping in a hot path),
# stricter (it catches a writer no test exercises), and it cannot go vacuous,
# because its subject is the file rather than a run. It is the pre-work census
# made permanent.
#
# WHAT IT DOES NOT COVER, stated here per the instrument-boundary rule: it sees
# the literal assignment shape only. `setattr(w, "p1", v)` and an alias
# (`end = w; end.p1 = ...`) both pass it, and it says nothing about identity
# being preserved by any other route. The tests are still where that is
# asserted; this only guarantees the retired spelling stays retired.
_END_ASSIGN = re.compile(r"\.p[12]\s*=(?!=)")


def _end_assignments() -> tuple:
    """Coordinate assignments to a wall end anywhere in `floorplanner/`."""
    import pathlib
    hits = []
    for p in sorted(pathlib.Path("floorplanner").rglob("*.py")):
        try:
            text = p.read_text(encoding="utf-8")
        except OSError:
            continue
        for n, line in enumerate(text.splitlines(), 1):
            code = line.split("#", 1)[0]
            if _END_ASSIGN.search(code):
                hits.append(f"{p.as_posix()}:{n}: {line.strip()}")
    return len(hits), hits


SNAPSHOT = "docs/SESSION_SNAPSHOT.md"
SNAPSHOT_MARK = re.compile(r"<!--\s*SNAPSHOT-HEAD:\s*([0-9a-f]{7,40})\s*-->")
SNAPSHOT_ROW = re.compile(r"^\|\s*\*\*`main`\*\*\s*\|(.*)$", re.M)


def _snapshot_head() -> int:
    """Does `docs/SESSION_SNAPSHOT.md` name the commit it was cut against?

    THIS IS THE ONE CONVENTION IN THIS REPOSITORY THAT HAS FAILED THREE TIMES,
    and it is now a condition rather than a note. The snapshot is the file a
    fresh session reads first; when it is stale it does not merely go unread, it
    actively misdirects. The last cut sat EIGHT COMMITS behind with a "where the
    work stands" table pinning a head that had moved and a "next task" naming a
    census already done and ruled.

    It had a warning about exactly that, in bold, at its own line 9. The warning
    did not maintain the file -- **a warning is a note to a reader; staleness is
    a property of the file.** The only two things that have ever fixed this
    class here are GENERATION (`defects/INDEX.md` and its `--check`) and A GATE
    THAT FAILS. This is the second.

    THE SEMANTICS, because they are not the obvious ones. The snapshot records
    the commit it was cut AGAINST -- the tip at gate time, which is the commit
    the pending work is built on, NOT the commit about to be made (which has no
    hash yet). So a commit that changes anything must re-point the marker at the
    current tip, and the file is "one behind" between the gate and the commit
    landing. That is the treadmill working: it caps drift at ONE commit, where
    it reached eight.

    TWO ASSERTIONS, not one. The marker must match the tip, AND the human-
    readable `main` row must carry the same hash -- otherwise the marker becomes
    a number that is bumped mechanically while the prose beside it goes on
    lying, which is the same convention failing in a smaller font.

    IT DOES NOT CHECK THAT THE CONTENT WAS RE-READ. Nothing can. It makes the
    file impossible to ignore, not impossible to update carelessly.
    """
    try:
        with open(SNAPSHOT, encoding="utf-8") as fh:
            text = fh.read()
    except OSError as e:
        print(f"Docs-Snapshot: RED -- cannot read {SNAPSHOT} ({e})")
        return 1
    tips = []
    for rev in ("HEAD", "HEAD~1"):
        try:
            p = subprocess.run(["git", "rev-parse", rev], capture_output=True,
                               text=True)
        except OSError:
            break
        if p.returncode == 0 and p.stdout.strip():
            tips.append(p.stdout.strip())
    rc, msg = snapshot_verdict(text, tips)
    print(msg)
    return rc


def snapshot_verdict(text: str, tips):
    """The check itself, as a PURE function of (file text, tips) -> (rc, msg).

    `tips` is [HEAD, HEAD~1] -- see ONE COMMIT OF SLACK below for why it is two.

    Split out from the IO so it can be tested, and it is: `tests/test_gate.py`
    drives every outcome. A staleness check nobody can demonstrate failing would
    be the same species as the convention it replaces -- something that looks
    like a guarantee and has never been asked to prove it.

    ONE COMMIT OF SLACK, AND IT IS NOT LENIENCY -- IT IS THE DIFFERENCE BETWEEN
    A GATE AND A NUISANCE. The first cut of this check accepted only HEAD, and
    it was wrong in a way worth recording: **the gate runs BEFORE a commit**, so
    the marker it approves names the tip at that moment; the instant the commit
    lands, the marker is one behind. Requiring an exact match would leave the
    repository RED AT REST -- red immediately after every correct commit, red
    for CI on every push (CI calls this tool with `--deep`, which runs this
    check), and red for the next session before it had done anything wrong.

    **A gate that is red in the resting state trains people to ignore it**,
    which would have rebuilt the very problem this closes, in a louder form.

    So the marker may name HEAD or its parent. Worst-case drift is TWO commits
    -- one of slack plus the pending one -- against the EIGHT it reached.
    """
    if not tips:
        return 1, ("Docs-Snapshot: RED -- cannot read HEAD (git unavailable). "
                   "A guard that cannot verify must not approve.")
    m = SNAPSHOT_MARK.search(text)
    if not m:
        return 1, (f"Docs-Snapshot: RED -- {SNAPSHOT} carries no "
                   f"`<!-- SNAPSHOT-HEAD: <sha> -->` marker.")
    recorded = m.group(1)
    if not any(t.startswith(recorded) for t in tips):
        return 1, (
            f"Docs-Snapshot: RED -- {SNAPSHOT} was cut against {recorded}, "
            f"which is neither HEAD ({tips[0][:len(recorded)]}) nor its "
            f"parent.\n"
            f"               Re-cut it (sections 0 and 1 at least) and "
            f"re-point the marker. The snapshot records the commit it was cut "
            f"AGAINST, which is the tip at gate time.")
    row = SNAPSHOT_ROW.search(text)
    if row is None or recorded not in row.group(1):
        return 1, (
            f"Docs-Snapshot: RED -- the marker says {recorded} but the `main` "
            f"row does not carry that hash.\n"
            f"               The marker and the prose must agree, or the "
            f"marker is a number nobody means.")
    where = "HEAD" if tips[0].startswith(recorded) else "HEAD~1 (one of slack)"
    return 0, f"Docs-Snapshot: cut against {recorded}, which is {where}"


def _docs() -> int:
    """The record lane: are the defect records well-formed and reachable?

    Three tools, each already the single definition of its own question, run in
    the order that makes a failure readable: the records themselves first (a
    malformed record makes everything downstream meaningless), then whether the
    repo's references still find them, then whether they would still migrate.

    Every check here is on DATA, not behaviour, so it costs no test run and can
    be invoked on its own while editing records.
    """
    checks = [
        ("Docs-Defects", ["tools/defects_index.py", "--validate"]),
        ("Docs-Index", ["tools/defects_index.py", "--check"]),
        ("Docs-Refs", ["tools/ref_audit.py", "--strict-ids"]),
        ("Docs-GitHub", ["tools/defects_to_github.py", "--dry-run"]),
    ]
    bad = bool(_snapshot_head())
    for label, cmd in checks:
        rc, out = _run_script(cmd)
        bad = bad or rc != 0
        keep = [ln for ln in out.splitlines()
                if ln.startswith(("Docs-", "Ref-")) or (rc and ln.strip())]
        # the GitHub dry run prints a whole script on success; only its verdict
        # is wanted here
        if label == "Docs-GitHub" and not rc:
            keep = [ln.lstrip("# ") for ln in out.splitlines()
                    if "DRY RUN" in ln]
        for ln in keep[:12 if rc else 4]:
            print(ln)
    note = "" if bad else (" (snapshot current, records valid, index current, "
                           "every defect reference resolves, migration dry run "
                           "clean)")
    print(f"Docs-Verdict: {'RED' if bad else 'GREEN'}{note}")
    return 1 if bad else 0


RESULT = ".gate-result.json"             # gitignored; see _write_result


def _write_result(bad, collected, ruff, n_vac, n_end, lines) -> None:
    """Leave the verdict ON DISK, for the commit hook to read.

    THE HOOK CHECKS THIS FILE, NEVER THE COMMIT MESSAGE, and that is the whole
    design. Three of the four incidents behind the hook were a CLAIM about a
    gate rather than a gate: a trailer transcribed without its ", 2 errors";
    "515 collected" quoted after two more tests had landed; a reconciliation
    asserted against a number that was never computed. A guard that read the
    message would have passed all three.

    Written on RED as well as GREEN. A missing file and a red file mean
    different things -- "you did not run it" and "you ran it and it failed" --
    and a guard that cannot tell them apart teaches people to delete the file.

    Only a FULL-MODE run writes it. `--quick` skips two of the three gates and
    `--deep` skips two others; letting either satisfy the hook would make the
    guard weaker than the thing it guards.
    """
    import json
    import time
    payload = {
        "verdict": "RED" if bad else "GREEN",
        "collected": collected,
        "ruff": ruff,
        "vacuous": n_vac,
        "end_assign": n_end,
        "timestamp": time.time(),
        "written_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "trailer": lines,
    }
    try:
        with open(RESULT, "w", encoding="utf-8") as fh:
            json.dump(payload, fh, indent=2)
            fh.write("\n")
    except OSError as e:                       # never fail a green gate on this
        print(f"Gate-Result: could not write {RESULT}: {e}")
        return
    print(f"Gate-Result: {RESULT} written ({payload['verdict']})")


def _trailer() -> int:
    """Print the LAST full-mode trailer, verbatim, from the result file.

    Added 2026-08-07 after the failure this whole tool exists to prevent
    happened anyway, one commit into the GREEN batch: the gate was run with
    `| tail -3`, so only the DEEP line and the verdict were ever seen, and the
    OFF and ON lines were typed into the commit message from an earlier run.
    Wall-clock times 17.28s / 20.55s were quoted; the run recorded 17.14s /
    19.79s. Outcomes, sums and verdict were correct -- the fabricated part was
    only the durations -- and that is exactly what makes it the same class as
    "515 collected": a number copied from one moment into a sentence written at
    another, in the one block that is supposed to be beyond retyping.

    Printing the trailer TO BE REDIRECTED INTO THE MESSAGE FILE closes it. The
    numbers stop passing through a human at all.

        python tools/gate.py                       # run it
        python tools/gate.py --trailer >> msg.txt  # quote it, verbatim
        git commit -F msg.txt

    Exits non-zero if there is no result file, so a missing trailer is loud
    rather than an empty append.
    """
    import json
    try:
        with open(RESULT, encoding="utf-8") as fh:
            data = json.load(fh)
    except (OSError, ValueError) as e:
        print(f"Gate-Trailer: no usable {RESULT} ({e}); run the gate first",
              file=sys.stderr)
        return 1
    print("\n".join(data.get("trailer") or []))
    return 0


def main() -> int:
    if "--perf" in sys.argv:
        return _perf()
    if "--docs" in sys.argv:
        return _docs()
    if "--trailer" in sys.argv:
        return _trailer()
    quick = "--quick" in sys.argv
    deep_only = "--deep" in sys.argv          # CI's DEEP job (defect 27)
    rc, out = _run(["ruff", "check", "."])
    ruff = "clean" if rc == 0 else f"{out.strip().splitlines()[-1]}"
    if rc:
        print(out)

    rc_c, out_c = _run(["pytest", "-q", "--collect-only"])
    collected = len([ln for ln in out_c.splitlines() if "::" in ln])

    n_vac, vac = _vacuity()
    n_end, ends = _end_assignments()
    # THE SNAPSHOT CHECK RUNS IN FULL MODE, NOT ONLY IN `--docs`, AND THE
    # DIFFERENCE IS THE WHOLE POINT. The commit hook reads `.gate-result.json`,
    # which only a full-mode run writes; `--docs` prints its own verdict and
    # writes nothing. A staleness check living only in the docs lane would be
    # one more thing nobody runs -- which is the exact failure it exists to
    # close. It costs one file read and one `git rev-parse`.
    n_snap = _snapshot_head()
    lines = [f"Gate-Census: collected={collected} ruff={ruff} "
             f"vacuous={n_vac} end_assign={n_end} snapshot="
             f"{'stale' if n_snap else 'current'}"]
    bad = rc != 0 or n_vac > 0 or n_end > 0 or n_snap > 0
    if vac:
        print("Unfailable assertions (vacuous by tautology):")
        for h in vac:
            print(f"    {h}")
    if ends:
        print("Coordinate assignment to a wall end (split-on-write is retired "
              "-- use set_end_vertex / relocated_to):")
        for h in ends:
            print(f"    {h}")
    modes = GATES[:1] if quick else (GATES[2:3] if deep_only else GATES)
    for label, env, extra in modes:
        grc, gout = _run(["pytest", "-q", "-p", "no:randomly", *extra], env)
        summary = _summary(gout)
        c = _counts(summary)
        total = sum(v for k, v in c.items() if k != "errors" or "error" not in c)
        red = [k for k in RED if c.get(k)]
        ok = (total == collected) and not red and grc == 0
        bad = bad or not ok
        note = "OK" if ok else (
            "RED:" + ",".join(red) if red
            else f"UNRECONCILED (sum {total} != collected {collected})")
        lines.append(f"Gate-{label.strip()}: {summary}  -> sum {total}  {note}")
    lines.append(f"Gate-Verdict: {'RED' if bad else 'GREEN'}"
                 f"{'' if bad else ' (every sum reconciles against --collect-only)'}")

    print("\n".join(lines))
    if not quick and not deep_only:      # full mode only -- see the docstring
        _write_result(bad, collected, ruff, n_vac, n_end, lines)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
