#!/usr/bin/env python3
"""PreToolUse hook: refuse `git commit`/`git push` unless a FRESH GREEN gate
result of the right STRENGTH is on disk.

THE ENFORCEMENT HALF OF "a green signal is only evidence about what it
measures". The gate has always measured the right thing. Nothing has ever made
running it unskippable, and there are four incidents behind that gap:

  * a gate line transcribed into a commit message WITHOUT its ", 2 errors", so
    the message read green while the run was red (3cdf046);
  * "515 collected" quoted in a report written after two more tests landed;
  * "516 collected" quoted the same way, with a reconciliation ASSERTED against
    it that was never performed -- 512 + 6 is 518;
  * a commit whose trailer was correct for an earlier state of the tree.

THREE OF THOSE FOUR WERE A CLAIM ABOUT A GATE RATHER THAN A GATE. So this hook
reads THE RESULT FILE and never the commit message. A message can say anything;
`.gate-result.json` is written by `tools/gate.py` itself, at the end of a
full-mode run, from the numbers it just computed.

Five conditions, the fourth from 0043/0047-ruling.md SS4 and the fifth from
0107-ruling.md SS3:

  1. `.gate-result.json` EXISTS          -- you ran the gate at all
  2. its verdict is GREEN                -- and it passed
  3. it is NEWER THAN EVERY TRACKED FILE -- and it passed on THIS tree
  4. its MODE IS STRONG ENOUGH FOR THE EVENT -- see the split below
  5. AT PUSH, `tools/gate.py --docs` IS RUN LIVE AND MUST BE GREEN -- see
     the docs-lane note below; unlike (1)-(4) this one is not read from a
     result file, because `--docs` writes none

Without (3) the hook is theatre: a green result from an hour and six edits ago
would wave through exactly the fourth incident. It is also the condition most
likely to be silently broken, which is why the fail-first receipt for this hook
tests it explicitly by touching a source file and retrying.

THE COMMIT/PUSH SPLIT. `python tools/gate.py --quick` (ruff + OFF only, ~25s)
now writes `.gate-result.json` too, tagged `"mode": "quick"` -- see that
script's own docstring. A `git commit` accepts either mode, GREEN and fresh; a
`git push` accepts `mode == "full"` only, PLUS the live `--docs` run at (5)
below. **Full mode itself is OFF+ON locally, OFF+ON+DEEP under CI**
(0107-ruling.md SS4 -- `gate.py`'s own docstring carries the full reasoning;
measured first, 0106-report.md, that DEEP has never once diverged from ON in
this project's recorded CI history). The bar moved from every commit to every
push, not down, and DEEP did not vanish -- it moved from the developer's own
push to the one run (CI, from a clean checkout) that cannot be bypassed by
`--no-verify` on the machine being checked. What changes for a session
splitting a change into private, never-pushed intermediate commits is that
none of them pay any of this tax; the one commit that actually leaves the
machine still pays it in full. `WORKING_AGREEMENT.md` (amended 2026-08-10)
already said gating every commit was wrong for exactly this shape -- a series
split for legibility, where the intermediate trees never existed as anything
a reviewer or CI would see -- and the hook had not caught up to the amendment
until now.

Exit codes: 0 lets the command through, 2 blocks it and shows stderr to the
model. Any other failure mode here (unreadable JSON, no git) also blocks, on the
principle that a guard which cannot verify must not approve.

WHAT THIS CANNOT SEE, stated here because an unstated boundary reads as
coverage -- and this one was found by testing the hook rather than by reasoning
about it:

  * A COMMAND THAT EDITS TRACKED FILES AND THEN COMMITS OR PUSHES, IN ONE
    INVOCATION, is not covered by the freshness check. `PreToolUse` fires
    BEFORE the command runs, so the tree the hook inspects is the tree as it
    was at approval time. A single Bash call that touches a source file and
    then commits will be approved against the pre-edit state -- measured, by
    exactly that command landing an empty commit while the guard watched.
    Splitting edit and commit into separate calls (the normal working shape)
    is fully covered.

    THE MOST COMMON SHAPE OF THIS IS NOW BLOCKED OUTRIGHT: a command containing
    BOTH a gate invocation and a commit or push. See `GATE_RUN_RE` below. It
    does not close the general case -- nothing at PreToolUse can -- but it
    closes the one that actually happens, which was writing this very
    boundary note and then walking into it within the hour.
  * `xargs`-fed commits, shell aliases, and any commit or push made outside
    these tools.
  * WHETHER THE COMMIT MESSAGE DESCRIBES THE RUN. This hook closes exactly one
    question -- *did the gate run, green, on this tree* -- and it never reads
    the message. A message can quote a trailer that is wrong, or invented, or
    from an earlier run, and this will approve it. That second question is
    closed by `python tools/gate.py --trailer`, which reprints the stored block
    for redirection into the message file so the numbers never pass through a
    human. It went unclosed until 2026-08-07, behind two instruments that were
    both working correctly.

It raises the floor. It is not a sandbox, and treating it as one is the failure
mode it exists to prevent.
"""
import json
import os
import re
import subprocess
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
RESULT = os.path.join(ROOT, ".gate-result.json")
GATE_CMD = "python tools/gate.py"

# `git commit` / `git push` in a COMMAND POSITION: at the start of a line, or
# after a shell separator, optionally behind one prefix token (`sudo git
# commit`). MULTILINE so a heredoc-bearing command still anchors per line. See
# the note at the call site for what this deliberately misses.
COMMIT_RE = re.compile(r"(?:^|[;&|])\s*(?:\S+\s+)?git\s+commit\b", re.M)
PUSH_RE = re.compile(r"(?:^|[;&|])\s*(?:\S+\s+)?git\s+push\b", re.M)

# A RUN OF THE GATE, in the same command line as a commit or push.
#
# Why this is enforced rather than left to discipline: `PreToolUse` fires BEFORE
# the command runs, so when one call does `gate.py` and then commits or pushes,
# the hook judges the tree AS IT WAS BEFORE THE GATE EVEN RAN. The verdict it
# reads is the PREVIOUS run's. On 2026-08-07 that let a commit through on a RED
# gate -- in the same session, and within the hour, as the note above
# documenting the hole was written. Three times that session a rule was
# written and then broken by its author; the answer to that is a check, not
# more resolve.
#
# Deliberately matches the TOOL, not the word "gate": `tools/gate.py` in any
# spelling (`python tools/gate.py`, `py -m ...`, a bare path), which is the only
# thing that writes the result file the commit/push is about to be judged
# against.
#
# `--trailer` IS EXEMPT, and the exemption is the rule working rather than a
# hole in it. That mode runs nothing and writes nothing -- it reprints the
# stored trailer so a message file can quote it verbatim -- so it cannot
# invalidate the verdict this hook just read. It is also exactly the command
# that BELONGS beside a commit: build the message, append the trailer, commit.
# The first draft matched it and blocked the intended workflow within minutes
# of shipping, which is the same "too broad by one case" the command-position
# fix already corrected once.
GATE_RUN_RE = re.compile(r"tools[/\\]gate\.py(?!\s+--trailer)")

# A new mailbox file, `docs/handoff/NNNN-*.md` -- never `archive/`, never
# `README.md` (no `[^/]` boundary trips on either). 0084-ruling.md SS4: the
# pair for THIS repair sat on `wall-orthogonality-repair`, unreadable from
# `main`, for the sixth time -- a rule restated five times and not followed
# is a rule that is wrong about how Code works, so it becomes a gate.
HANDOFF_RE = re.compile(r"^docs/handoff/\d{4}-[^/]+\.md$")

# The two-writer-one-suffix shape (README.md "THE CHANNEL CONTRACT"): Code
# writes `NNNN-report.md`, the reviewer writes `NNNN-ruling.md`, and each side
# only ever creates -- never edits the other's. That split is what makes a
# same-number collision impossible IF both sides check the directory first.
# Four have landed anyway (0036, 0043, 0050, 0101 -- 0103-ruling.md SS4)
# because nothing enforced it. `_staged_new_handoff_files` above already finds
# every add; this pattern picks the number and suffix off a standard name so
# the add can be checked against its counterpart already on disk.
PAIR_RE = re.compile(r"^docs/handoff/(\d{4})-(report|ruling)\.md$")


def _current_branch(cwd):
    r = subprocess.run(["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd=cwd,
                       capture_output=True, text=True)
    return r.stdout.strip() if r.returncode == 0 else None


def _staged_new_handoff_files(cwd, cmd):
    """Handoff files about to be ADDED by this commit -- staged via `git add`
    (`git diff --cached --diff-filter=A`) UNION any explicit path argument on
    the command line itself (`git commit docs/handoff/0086-ruling.md -F -`,
    this project's own documented pattern for committing alongside other
    staged files -- CLAUDE.md's "use git commit <paths> when anything else is
    staged"), checked with `git status --porcelain` for that one path so a
    MODIFY of an existing file is never mistaken for an add."""
    found = set()
    r = subprocess.run(["git", "diff", "--cached", "--name-status",
                        "--diff-filter=A", "--", "docs/handoff"],
                       cwd=cwd, capture_output=True, text=True)
    if r.returncode == 0:
        for line in r.stdout.splitlines():
            parts = line.split("\t", 1)
            if len(parts) == 2 and HANDOFF_RE.match(parts[1]):
                found.add(parts[1])

    for tok in cmd.split():
        path = tok.strip("'\"")
        if not HANDOFF_RE.match(path.replace(os.sep, "/")):
            continue
        st = subprocess.run(["git", "status", "--porcelain", "--", path],
                            cwd=cwd, capture_output=True, text=True)
        if st.returncode == 0 and st.stdout[:2] in ("??", "A ", "AM"):
            found.add(path)
    return found


def _collision(cwd, new_path):
    """If `new_path` is a standard `NNNN-report.md`/`NNNN-ruling.md` add and its
    counterpart (same number, other suffix) already exists on disk -- checked
    in `docs/handoff/` AND `docs/handoff/archive/`, since the numbering is
    shared across both (README.md SS"protocol" item 3) -- return that
    counterpart's path. `None` if the name doesn't fit the pattern (an older,
    pre-channel-contract file) or nothing collides."""
    m = PAIR_RE.match(new_path)
    if not m:
        return None
    number, suffix = m.groups()
    other = "ruling" if suffix == "report" else "report"
    name = f"{number}-{other}.md"
    for d in ("docs/handoff", "docs/handoff/archive"):
        candidate = os.path.join(cwd, d, name)
        if os.path.exists(candidate):
            return f"{d}/{name}"
    return None


def block(msg):
    sys.stderr.write(f"BLOCKED: {msg}\n")
    sys.exit(2)


def main():
    try:
        payload = json.load(sys.stdin)
    except (ValueError, OSError):
        sys.exit(0)                    # not a hook invocation we understand

    cmd = ""
    ti = payload.get("tool_input") or {}
    if isinstance(ti, dict):
        cmd = str(ti.get("command") or "")

    # Only commits and pushes are gated, and only ACTUAL INVOCATIONS of one.
    #
    # The first draft matched the substring anywhere in the command line and
    # blocked the very command that was validating it -- an `echo` whose
    # argument merely CONTAINED the words. `grep "git commit" docs/` would have
    # been blocked too, and this repo's documents are full of the phrase. So the
    # match is anchored to a command position. That still catches every form
    # used here -- `git add -A && git commit ...`, `git commit <paths> -F -` fed
    # by a heredoc, `cd x; git commit`, `git push origin main` -- while a
    # mention inside a quoted argument is not an invocation and is not treated
    # as one.
    #
    # `--amend` is a commit and is not exempt. Deliberately NOT handled:
    # `xargs git commit`, shell aliases, and a commit or push made outside
    # these tools. This hook raises the floor; it is not a sandbox, and saying
    # so is the point -- an unstated boundary reads as coverage.
    is_commit = bool(COMMIT_RE.search(cmd))
    is_push = bool(PUSH_RE.search(cmd))
    if not is_commit and not is_push:
        sys.exit(0)

    # A COMMAND NAMING BOTH ("git commit ... && git push") IS GATED AS A PUSH.
    # Push is the stricter requirement (full mode only), so judging the whole
    # line by it is correct either way: if only the commit half were meant to
    # run today, split the call.
    event = "push" if is_push else "commit"
    event_verb = "pushes" if is_push else "commits"       # "commit" -> "commits"

    # THE MAILBOX ONLY LANDS ON `main` (0084-ruling.md SS4). A COMMIT (not a
    # push -- this is about where the file is created, not where it ships)
    # that ADDS a `docs/handoff/NNNN-*.md` on any other branch is refused,
    # UNLESS it is a merge commit (`main` coming IN, which legitimately
    # carries mailbox files that already exist there).
    if event == "commit":
        branch = _current_branch(ROOT)
        merging = subprocess.run(
            ["git", "rev-parse", "--git-path", "MERGE_HEAD"], cwd=ROOT,
            capture_output=True, text=True)
        is_merge = (merging.returncode == 0
                   and os.path.exists(os.path.join(ROOT, merging.stdout.strip())))
        new_handoff = _staged_new_handoff_files(ROOT, cmd) if not is_merge else set()
        if branch and branch != "main" and not is_merge:
            if new_handoff:
                shown = ", ".join(sorted(new_handoff))
                block(f"this commit adds {shown} on branch '{branch}', not "
                      "`main`.\n"
                      "         The mailbox only lands on `main` -- write "
                      "the report or ruling, commit it there,\n"
                      "         then branch for the code that answers it "
                      "(0084-ruling.md SS4).")

        # THE FOURTH COLLISION (0036, 0043, 0050, 0101) IS A RACE: two writers,
        # one sequence, no lock. This closes Code's half of it -- a number
        # whose other suffix is already on disk is refused here instead of
        # landing as a collision that then has to be flagged and carried
        # forward per 0044-ruling.md (0103-ruling.md SS4).
        for path in sorted(new_handoff):
            counterpart = _collision(ROOT, path)
            if counterpart:
                number = PAIR_RE.match(path).group(1)
                block(f"{path} collides with {counterpart} -- number "
                      f"{number} is already taken.\n"
                      "         Next free number = highest in "
                      "`docs/handoff/` (archive included) plus one\n"
                      "         (README.md \"protocol\" item 3). Pick that "
                      "number and retry.")

    # ONE CALL CANNOT BOTH RUN THE GATE AND COMMIT/PUSH. Checked before the
    # result file is even read, because in this shape the result file is
    # guaranteed to be the WRONG one: this hook runs before the command, so it
    # would be judging the previous run's verdict against the pre-command
    # tree, and whatever the gate is about to say would never be consulted at
    # all.
    if GATE_RUN_RE.search(cmd):
        block(f"this command runs the gate AND {event_verb}.\n"
              "         PreToolUse fires BEFORE the command, so the verdict "
              "checked here is the\n"
              "         PREVIOUS run's -- the gate you are about to run cannot "
              "affect it. On\n"
              "         2026-08-07 exactly this let a commit through on a RED "
              "gate.\n"
              f"         Run the gate and {event} in SEPARATE calls: read the "
              f"verdict, then {event}.")

    if not os.path.exists(RESULT):
        need = GATE_CMD if event == "push" else f"{GATE_CMD} (or --quick)"
        block(f"no {os.path.basename(RESULT)} -- the gate has not been run.\n"
              f"         Run `{need}` and {event} after it reports GREEN.")

    try:
        with open(RESULT, encoding="utf-8") as fh:
            data = json.load(fh)
    except (ValueError, OSError) as e:
        block(f"{os.path.basename(RESULT)} is unreadable ({e}).\n"
              f"         Re-run `{GATE_CMD}`.")

    verdict = str(data.get("verdict", "")).upper()
    if verdict != "GREEN":
        trailer = [ln for ln in (data.get("trailer") or [])
                   if "RED" in ln or "UNRECONCILED" in ln]
        detail = ("\n         " + "\n         ".join(trailer)) if trailer else ""
        block(f"the last gate result was {verdict or 'not GREEN'}."
              f"{detail}\n         Fix it, re-run `{GATE_CMD}`, then {event}.")

    # (4) STRENGTH. A `git commit` accepts either mode; a `git push` needs the
    # full 3x-suite run specifically -- 0043/0047-ruling.md SS4. This is a
    # THIRD, DISTINCT message from both "no result" and "RED": a quick result
    # is a real, GREEN result, just not a strong enough one for this event.
    mode = str(data.get("mode", "full")).lower()
    if event == "push" and mode != "full":
        block("the last gate result is `--quick` (ruff + OFF only), GREEN, "
              "but a push needs FULL MODE.\n"
              "         `--quick` unlocks a commit; only `python tools/gate.py` "
              "(no flag) unlocks a push.\n"
              "         Run the full gate, then push.")

    # (3) FRESHNESS. The result must post-date every tracked file, or it is a
    # verdict about a tree that no longer exists.
    try:
        listing = subprocess.run(["git", "ls-files", "-z"], cwd=ROOT,
                                 capture_output=True, check=True).stdout
    except (OSError, subprocess.CalledProcessError) as e:
        block(f"cannot list tracked files to check gate freshness ({e}).")

    stamp = os.path.getmtime(RESULT)
    newer = []
    for rel in listing.decode("utf-8", "replace").split("\0"):
        if not rel:
            continue
        try:
            if os.path.getmtime(os.path.join(ROOT, rel)) > stamp:
                newer.append(rel)
        except OSError:
            continue                   # deleted-but-tracked: not a staleness signal

    if newer:
        age = (time.time() - stamp) / 60
        shown = ", ".join(sorted(newer)[:5])
        more = f" (+{len(newer) - 5} more)" if len(newer) > 5 else ""
        block(f"the gate result is STALE -- {len(newer)} tracked file(s) have "
              f"changed since it was written {age:.1f} min ago:\n"
              f"         {shown}{more}\n"
              f"         A green gate for an earlier tree is not a green gate "
              f"for this one.\n         Re-run `{GATE_CMD}`, then {event}.")

    # (5) THE DOCS LANE, AT PUSH ONLY -- 0107-ruling.md SS3. `0105-ruling.md`
    # cut CI's `records (gate --docs)` job on the claim "the commit hook
    # enforces it" -- IT DOES NOT: `--docs` is an early, mutually exclusive
    # return in `gate.py`'s `main()` (`if "--docs" in sys.argv: return
    # _docs()`), never reached by a bare, `--quick` or full-mode run, and it
    # writes no result file for this hook to have read. That gap cost seven
    # real catches (0106-report.md SS1: `Docs-Refs` unresolved cross-references
    # fired in 7 of the 47 CI failures measured, the one class the rest of the
    # gate never runs).
    #
    # THE FIX IS TO RUN IT, not to teach it to write `.gate-result.json` -- a
    # second result file the hook could read is a second source of truth, the
    # exact shape this hook's own docstring exists to prevent. So this is the
    # one place in this file that executes a check live rather than reading
    # one that already ran, and only at PUSH: the record is what lands there
    # (0047-ruling.md's strict bar already sits at push, not commit), and the
    # docs lane is cheap enough (`ci.yml`'s own former comment: "finishes in
    # seconds") that paying it once per push is not the tax full-mode pytest
    # would be.
    if event == "push":
        result = subprocess.run(
            [sys.executable, "tools/gate.py", "--docs"], cwd=ROOT,
            capture_output=True, text=True)
        if result.returncode != 0:
            lines = [ln for ln in result.stdout.splitlines()
                     if ln.startswith(("Docs-", "Ref-")) or ln.strip()]
            detail = ("\n         " + "\n         ".join(lines[-12:])) \
                if lines else ""
            block(f"`python tools/gate.py --docs` is RED.{detail}\n"
                  "         Fix it, then push -- this runs fresh on every "
                  "push attempt, no result file to re-check.")

    sys.exit(0)


if __name__ == "__main__":
    main()
