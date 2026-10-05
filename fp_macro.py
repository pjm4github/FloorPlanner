#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Patrick Moran and Claude (Anthropic). See LICENSE.
"""
fp_macro.py -- headless driver for FloorPlanner (Part 2 of the macro tool).

This is the program an AI (or any script) runs to edit a floor plan without a
GUI: it boots FloorPlanner offscreen, loads an optional plan, feeds a macro to
the in-app MacroRunner hook, snapshots the canvas (SVG and/or PNG) so the
result can be "seen", saves the edited plan, and prints a JSON summary of the
resulting layout so the next step can reason about what changed.

Macro syntax lives with the hook (FloorPlanner.MacroRunner) and is documented
in docs/macro_language.md.  Positions are in scene inches (1 unit = 1 inch).

Examples
  # place a sofa, copy it to the mouse point, snapshot, save
  python fp_macro.py --out plan.json \
      --macro "PLACE sofa 120 96  MOVE 240 96  SELECT 120 96  ^C ^V  SHOT s.svg"

  # apply a macro file to an existing plan and render a PNG preview
  python fp_macro.py --in plan.json --file edits.fpm --png after.png --out plan.json

  # interactive line-by-line session (one macro line per stdin line)
  python fp_macro.py --in plan.json --repl

  # rewrite existing-format macro files as macro language v2 (keeps FILE.bak)
  python fp_macro.py --convert edits.fpm other.fpm
"""
import argparse
import json
import os
import sys


def _build_window(window: bool):
    """Create the offscreen (or visible) app + a prepared MainWindow."""
    if not window:
        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    from PyQt6.QtGui import QFont
    from PyQt6.QtWidgets import QApplication

    app = QApplication(sys.argv[:1])
    import FloorPlanner as FP

    if FP.FONT_DIR.is_dir():
        os.environ.setdefault("QT_QPA_FONTDIR", str(FP.FONT_DIR))
    app.setApplicationName(FP.APP_NAME)
    FP.load_fonts()
    app.setFont(QFont(FP.FONT_FAMILY, 10))

    win = FP.MainWindow()
    win.prepare_headless()
    return app, FP, win


def _gather_macro(args) -> str:
    parts = []
    if args.file:
        with open(args.file, "r", encoding="utf-8") as f:
            parts.append(f.read())
    if args.macro:
        parts.append(args.macro)
    return "\n".join(parts)


def _do_exports(win, args) -> list:
    exports = []
    for path in [*(args.svg or []), *(args.png or []), *(args.shot or [])]:
        ok = win.export_canvas(path)
        exports.append({"path": path, "ok": bool(ok)})
    return exports


def _convert_files(paths, quiet: bool) -> int:
    """Rewrite each existing-format macro file as macro language v2
    (docs/macro-spec/MACRO_SPEC.md sec11), the original kept beside it as
    FILE.bak. A file already in v2 is left alone, and so is one whose .bak
    exists -- that copy may be the only original. Anything with no v2 form
    is reported, and written into the new file as a `; NOT CONVERTED`
    comment where it stood; the exit code is then 1."""
    import shutil

    from floorplanner.macro2 import is_v2
    from floorplanner.macro2.convert import convert

    files, ok = [], True
    for path in paths:
        entry = {"path": path}
        files.append(entry)
        try:
            with open(path, "r", encoding="utf-8") as f:
                text = f.read()
            if is_v2(text):
                entry["status"] = "already v2"
                continue
            bak = path + ".bak"
            if os.path.exists(bak):
                raise FileExistsError(f"{bak} exists; not overwritten")
            conv = convert(text)
            shutil.copy2(path, bak)
            with open(path, "w", encoding="utf-8", newline="\n") as f:
                f.write(conv.text)
            entry.update(status="converted", backup=bak,
                         lines=len(conv.macro.lines),
                         not_converted=[str(p) for p in conv.problems],
                         notes=[str(n) for n in conv.notes])
            ok = ok and conv.ok
        except (OSError, UnicodeDecodeError) as ex:
            entry.update(status="error", error=f"{type(ex).__name__}: {ex}")
            ok = False
    if not quiet:
        print(json.dumps({"ok": ok, "files": files}, indent=2))
    return 0 if ok else 1


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(
        prog="fp_macro.py",
        description="Headless FloorPlanner macro driver.")
    ap.add_argument("-i", "--in", dest="infile",
                    help="plan JSON to load before running the macro")
    ap.add_argument("-o", "--out", dest="outfile",
                    help="plan JSON to write after the macro (also the "
                         "target of the ^S shortcut)")
    ap.add_argument("-m", "--macro", help="macro string to run")
    ap.add_argument("-f", "--file", help="file containing a macro to run")
    ap.add_argument("--svg", action="append", metavar="PATH",
                    help="write an SVG snapshot (repeatable)")
    ap.add_argument("--png", action="append", metavar="PATH",
                    help="write a PNG snapshot (repeatable)")
    ap.add_argument("--shot", action="append", metavar="PATH",
                    help="write a snapshot, format by extension (repeatable)")
    ap.add_argument("--repl", action="store_true",
                    help="read macro lines from stdin, one run per line")
    ap.add_argument("--convert", nargs="+", metavar="FILE",
                    help="rewrite existing-format macro files as macro "
                         "language v2, keeping FILE.bak; runs nothing")
    ap.add_argument("--window", action="store_true",
                    help="show a real window instead of rendering offscreen")
    ap.add_argument("--summary", choices=["counts", "full", "none"],
                    default="counts",
                    help="how much of the resulting layout to print as JSON")
    ap.add_argument("-q", "--quiet", action="store_true",
                    help="suppress the JSON result on stdout")
    args = ap.parse_args(argv)

    if args.convert:
        return _convert_files(args.convert, args.quiet)

    app, FP, win = _build_window(args.window)

    result = {"ok": True, "errors": [], "steps": 0,
              "loaded": None, "saved": None, "exports": []}
    try:
        if args.infile:
            win.load_path(args.infile)
            result["loaded"] = args.infile
        # ^S in a macro saves to the current file; point it at --out so a
        # fresh plan can be ^S-saved too.
        if args.outfile:
            win.current_path = args.outfile

        if args.repl:
            return _repl(win, args)

        macro = _gather_macro(args)
        if macro.strip():
            r = win.run_macro(macro)
            result["ok"] = r["ok"]
            result["errors"] = r["errors"]
            result["steps"] = r["steps"]

        result["exports"] = _do_exports(win, args)

        if args.outfile:
            win.save_path(args.outfile)
            result["saved"] = args.outfile
    except Exception as ex:                               # noqa: BLE001
        result["ok"] = False
        result["errors"].append(f"{type(ex).__name__}: {ex}")

    if args.summary == "counts":
        result["counts"] = win.scene_summary()["counts"]
    elif args.summary == "full":
        result["scene"] = win.scene_summary()

    if not args.quiet:
        print(json.dumps(result, indent=2))
    return 0 if result["ok"] else 1


def _repl(win, args) -> int:
    """One macro line per stdin line; print a compact JSON result for each.
    A line of 'QUIT'/'EXIT' (or EOF) ends the session."""
    sys.stderr.write("fp_macro REPL - one macro line per line; QUIT to end.\n")
    sys.stderr.flush()
    for line in sys.stdin:
        line = line.rstrip("\n")
        if line.strip().upper() in ("QUIT", "EXIT"):
            break
        r = win.run_macro(line)
        out = {"ok": r["ok"], "steps": r["steps"], "errors": r["errors"],
               "counts": r["counts"]}
        print(json.dumps(out))
        sys.stdout.flush()
    if args.outfile:
        win.save_path(args.outfile)
        sys.stderr.write(f"saved {args.outfile}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
