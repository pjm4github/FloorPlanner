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

    lines = [f"Gate-Census: collected={collected} ruff={ruff}"]
    bad = rc != 0
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
