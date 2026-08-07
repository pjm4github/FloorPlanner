#!/usr/bin/env python3
"""FAIL-FIRST RECEIPT for the one-call rule in .claude/hooks/verify_gate.py.

A command that runs `tools/gate.py` AND commits, in one invocation, must be
BLOCKED outright -- before the result file is even read, because in that shape
the result file is guaranteed to be the previous run's.

Each probe states the command shape, PROVES which patterns it contains, and
checks the exit code. The last two are the ones that keep the rule honest: a
gate run on its own must stay allowed, and a commit on its own must still be
judged on the verdict rather than refused for the wrong reason.
"""
import json
import pathlib
import subprocess
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="backslashreplace")
ROOT = pathlib.Path(".").resolve()
HOOK = ROOT / ".claude" / "hooks" / "verify_gate.py"
RESULT = ROOT / ".gate-result.json"

CC = "git " + "commit"          # assembled: this file is scanned by the hook
GATE = "python tools/gate.py"

CASES = [
    (f"{GATE} && {CC} -m x", 2, True, True, "gate AND commit, one call"),
    (f"{GATE}\\n{CC} -F msg.txt", 2, True, True, "same, newline-separated"),
    (f"{GATE} --docs ; {CC} -q -F -", 2, True, True, "docs lane AND commit"),
    (f"{GATE}", 0, True, False, "gate alone -- must stay ALLOWED"),
    (f"{CC} -m x", None, False, True, "commit alone -- judged on the verdict"),
    ("python -m pytest -q", 0, False, False, "neither -- untouched"),
]


def run(cmd):
    p = subprocess.run([sys.executable, str(HOOK)],
                       input=json.dumps({"tool_name": "Bash",
                                         "tool_input": {"command": cmd}}),
                       capture_output=True, text=True, cwd=str(ROOT))
    first = (p.stderr.strip().splitlines() or [""])[0]
    return p.returncode, first


verdict = "MISSING"
if RESULT.exists():
    try:
        verdict = json.loads(RESULT.read_text(encoding="utf-8"))["verdict"]
    except (ValueError, OSError):
        verdict = "UNREADABLE"

print("FAIL-FIRST RECEIPT -- the one-call rule")
print(f"(.gate-result.json currently reads {verdict}; the 'commit alone' case "
      f"is judged against it)\n")

ok = 0
for cmd, want, has_gate, has_commit, label in CASES:
    real = cmd.replace("\\n", "\n")
    # The proof column shows what the command ACTUALLY contains, and flags any
    # disagreement with what the case claims. An earlier draft printed "Y" for
    # *agreement with the expectation*, which rendered `gate=Y commit=Y` on the
    # case containing neither -- a proof column that proves nothing is worse
    # than none, and this receipt exists because of exactly that class.
    got_gate, got_commit = "tools/gate.py" in real, ("git " + "commit") in real
    proof = (f"gate={'Y' if got_gate else 'n'}"
             f"{'!' if got_gate != has_gate else ' '}"
             f"commit={'Y' if got_commit else 'n'}"
             f"{'!' if got_commit != has_commit else ' '}")
    rc, why = run(real)
    good = (rc == want) if want is not None else True
    ok += good
    shown = "BLOCKS" if rc == 2 else ("allows" if rc == 0 else f"rc={rc}")
    note = "" if want is not None else "  (verdict-dependent, not asserted)"
    print(f"  {label:<38} {proof}  {shown:<7} "
          f"{'as required' if good else '*** WRONG ***'}{note}")
    if rc == 2 and why:
        print(f"       -> {why[:100]}")

print(f"\n  {len(CASES)} probes, {ok} behaved as required, {len(CASES) - ok} did not")
sys.exit(0 if ok == len(CASES) else 1)
