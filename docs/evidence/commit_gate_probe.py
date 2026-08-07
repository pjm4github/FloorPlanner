#!/usr/bin/env python3
"""FAIL-FIRST RECEIPT for .claude/hooks/verify_gate.py.

Four probes. Each sets up a state, PROVES that state is on disk, invokes the
hook exactly as the harness does (payload on stdin), and checks the exit code.
Probe 4 is the one that matters: if touching a source file does not produce a
block, the freshness check is not wired and the hook reads as coverage.
"""
import json
import os
import pathlib
import subprocess
import sys
import time

sys.stdout.reconfigure(encoding="utf-8", errors="backslashreplace")
ROOT = pathlib.Path(".").resolve()
RESULT = ROOT / ".gate-result.json"
HOOK = ROOT / ".claude" / "hooks" / "verify_gate.py"
VICTIM = ROOT / "floorplanner" / "config.py"      # a real tracked source file

PAYLOAD = json.dumps({"tool_name": "Bash",
                      "tool_input": {"command": "git commit -m 'x'"}})


def run_hook():
    p = subprocess.run([sys.executable, str(HOOK)], input=PAYLOAD,
                       capture_output=True, text=True, cwd=str(ROOT))
    first = (p.stderr.strip().splitlines() or [""])[0]
    return p.returncode, first


def show(n, name, proof, rc, want, why):
    ok = (rc == want)
    verdict = "BLOCKS" if rc == 2 else ("PASSES" if rc == 0 else f"rc={rc}")
    print(f"  {n}  {name:<34} proof={proof:<22} {verdict:<7} "
          f"{'as required' if ok else '*** WRONG ***'}")
    if why:
        print(f"       -> {why[:104]}")
    return ok


print("FAIL-FIRST RECEIPT -- .claude/hooks/verify_gate.py")
print("Each probe proves its state is ON DISK before the hook's answer is "
      "believed.\n")

backup = RESULT.read_bytes() if RESULT.exists() else None
results = []

# 1. no result file at all
if RESULT.exists():
    RESULT.unlink()
proof = "absent" if not RESULT.exists() else "STILL THERE"
rc, why = run_hook()
results.append(show(1, "no .gate-result.json", proof, rc, 2, why))

# 2. a RED verdict
RESULT.write_text(json.dumps({
    "verdict": "RED", "collected": 633,
    "trailer": ["Gate-OFF: 1 failed, 624 passed  -> sum 633  RED:failed",
                "Gate-Verdict: RED"]}), encoding="utf-8")
proof = "verdict=" + json.loads(RESULT.read_text(encoding="utf-8"))["verdict"]
rc, why = run_hook()
results.append(show(2, "verdict RED", proof, rc, 2, why))

# 3. a real, current green gate -- run the actual tool, no hand-written file
print("\n     running the REAL gate for probe 3 (full mode, ~80s)...")
g = subprocess.run([sys.executable, "tools/gate.py"], capture_output=True,
                   text=True, cwd=str(ROOT))
verdict = json.loads(RESULT.read_text(encoding="utf-8"))["verdict"] \
    if RESULT.exists() else "MISSING"
proof = f"gate wrote {verdict}"
rc, why = run_hook()
results.append(show(3, "real green gate", proof, rc, 0, why))
if verdict != "GREEN":
    print("       (gate was not green -- probe 3 cannot demonstrate the pass)")

# 4. STALENESS: touch a tracked source file, retry
time.sleep(1.1)                                    # beat filesystem granularity
os.utime(VICTIM, None)
fresher = os.path.getmtime(VICTIM) > os.path.getmtime(RESULT)
proof = f"config.py newer={fresher}"
rc, why = run_hook()
results.append(show(4, "touch a source file, retry", proof, rc, 2, why))

if backup is not None:
    RESULT.write_bytes(backup)
elif RESULT.exists():
    RESULT.unlink()

print(f"\n  4 probes, {sum(results)} behaved as required, "
      f"{4 - sum(results)} did not")
print("  NOTE: the tree is deliberately left stale by probe 4 -- re-run "
      "`python tools/gate.py` before committing.")
sys.exit(0 if all(results) else 1)
