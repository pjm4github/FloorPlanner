#!/usr/bin/env python3
"""Run the migration gate and EMIT ITS OWN CENSUS, as a commit trailer.

Why this exists, and it is not convenience. Three separate incidents in P3.5-P3.6
came from the same failure, and none of them was a typo:

  * a gate line transcribed into a commit message WITHOUT its ", 2 errors", so
    the message read green while the run was red (3cdf046);
  * "515 collected" quoted in a report written after two more tests had landed;
  * "516 collected" quoted the same way, with a reconciliation ASSERTED against
    it that was never performed -- 512 + 6 is 518.

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


def main() -> int:
    if "--perf" in sys.argv:
        return _perf()
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
    lines = [f"Gate-Census: collected={collected} ruff={ruff} "
             f"vacuous={n_vac} end_assign={n_end}"]
    bad = rc != 0 or n_vac > 0 or n_end > 0
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
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
