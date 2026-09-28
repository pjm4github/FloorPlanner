"""0197-ruling.md sec5, the second measurement: "does any roof path read the
level's elevation today? Every roof height is measured from the level-base
datum. When the level base stops being zero, say whether the dialog's
seeded heights -- R3b's governing ceiling -- are still right, measured on
his fixture, not reasoned about."

His fixture, `fixtures/wiscaway-2level-stacked-floor.json`, has L2 at
100in. This probe reads, for every roof on both levels: its stored heights
(level-relative) and the absolute heights they compose at; what the
room-top binding measures (`bound_eaves_height`); what the End-On dialog
seeds its three fields and its wall-top reference with; what the Dormer
tool would seed on it (`dormer_defaults`); and how many walls of each level
the R3b dash marks. Then the same L2 readings again with L2's elevation set
to 0 and to 250 -- a reading that moves with the elevation READS it (directly,
or through the composed territory, which has depended on the elevation since
R6.b); one that does not is level-relative. Each reading is compared on its
own, so a change names itself.

A measurement; nothing is changed. Output kept as
`roof-elevation-readers-probe.txt`.

    python docs/evidence/roof_elevation_readers_probe.py
"""
import os
import sys

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, ROOT)

from PyQt6.QtCore import QPointF                   # noqa: E402
from PyQt6.QtWidgets import QApplication           # noqa: E402

_app = QApplication.instance() or QApplication([])

import FloorPlanner as fp                           # noqa: E402
from floorplanner.dialogs import RoofEndOnDialog    # noqa: E402
from floorplanner.roofs import (                    # noqa: E402
    RoofItem, bound_eaves_height, dormer_defaults, roof_clip_spans,
    roof_clip_trace,
)

PLAN = os.path.join(ROOT, "fixtures", "wiscaway-2level-stacked-floor.json")


def roofs_of(win):
    return sorted((it for it in win.scene.items() if isinstance(it, RoofItem)),
                  key=lambda r: (r.floor, r.p1.x(), r.p1.y()))


def readings(win):
    """Everything a roof path says about heights, per roof, as one row."""
    rows = []
    for rf in roofs_of(win):
        elev = fp.floor_elevation(rf.floor)
        b = bound_eaves_height(win.scene, rf)
        dlg = RoofEndOnDialog(rf, win)
        mid = QPointF((rf.p1.x() + rf.p2.x()) / 2.0, (rf.p1.y() + rf.p2.y()) / 2.0)
        _, _, nx, ny = rf._axis()
        on_slope = QPointF(mid.x() + nx * rf.span_in[0] * 0.6,
                           mid.y() + ny * rf.span_in[0] * 0.6)
        d_eaves, d_slope = dormer_defaults(win.scene, rf, on_slope)
        rows.append({
            "floor": rf.floor, "elev": elev,
            "ridge": (round(rf.p1.x()), round(rf.p1.y())),
            "stored": (rf.eaves_h_in, rf.ridge_h_in),
            "absolute": (rf.eaves_h_in + elev, rf.ridge_h_in + elev),
            "bound_eaves": (b.eaves_h_in, b.fallback, len(b.rooms)),
            "dialog": (dlg.sp_eaves.value(), dlg.sp_ridge.value(),
                       round(dlg.sp_pitch.value(), 1), dlg.canvas.wall_top_in),
            "dormer_default": (d_eaves, round(d_slope, 4)),
            "region": None if rf._clip_region is None else round(rf._clip_region.area()),
            "trace_len": round(sum(((q.x() - p.x()) ** 2 + (q.y() - p.y()) ** 2) ** 0.5
                                   for p, q in roof_clip_trace(win.scene, rf))),
        })
        dlg.deleteLater()
    return rows


def dashed_walls(win):
    out = {}
    for w in win.scene.items():
        if isinstance(w, fp.WallItem):
            n = out.setdefault(w.floor, [0, 0])
            n[1] += 1
            if roof_clip_spans(win.scene, w):
                n[0] += 1
    return {k: f"{a} of {b}" for k, (a, b) in sorted(out.items())}


def show(rows):
    for r in rows:
        print(f"   {r['floor']:8s} +{r['elev']:5.0f}  ridge@{r['ridge']}  "
              f"stored eaves/ridge {r['stored'][0]:6.1f}/{r['stored'][1]:6.1f}  "
              f"absolute {r['absolute'][0]:6.1f}/{r['absolute'][1]:6.1f}")
        print(f"            room-top binding measures eaves {r['bound_eaves'][0]:.1f} "
              f"({r['bound_eaves'][2]} room(s), fallback={r['bound_eaves'][1]}); "
              f"dialog seeds eaves {r['dialog'][0]:.1f} ridge {r['dialog'][1]:.1f} "
              f"pitch {r['dialog'][2]} wall-top line {r['dialog'][3]:.1f}; "
              f"dormer default eaves {r['dormer_default'][0]:.1f} slope {r['dormer_default'][1]}")
        print(f"            composed region {r['region']} in2, clip trace {r['trace_len']} in")


def main():
    win = fp.MainWindow()
    win.prepare_headless()
    win.load_path(PLAN)
    print("floors:", [(f.name, f.elevation_in, f.height_in) for f in win.floors])
    print("room ceilings by floor:",
          {fl: sorted({it.properties["ceiling_height_in"] for it in win.scene.items()
                       if isinstance(it, fp.RoomItem) and it.floor == fl})
           for fl in ("default", "upper")})
    print("\n== as drawn: L2 at 100 ==")
    base = readings(win)
    show(base)
    print("   walls the R3b dash marks, by floor:", dashed_walls(win))
    base_dash = dashed_walls(win)

    # each reading on its own, so a change names itself
    READINGS = (("stored heights", lambda r: r["stored"]),
                ("room-top binding", lambda r: r["bound_eaves"]),
                ("dialog seeds (eaves, ridge, pitch, wall-top line)", lambda r: r["dialog"]),
                ("dormer default", lambda r: r["dormer_default"]),
                ("clip trace length", lambda r: r["trace_len"]),
                ("composed region", lambda r: r["region"]))

    for elev in (0.0, 250.0):
        win.set_floor_levels("upper", elev, win._floor("upper").height_in)
        rows = readings(win)
        dash = dashed_walls(win)
        print(f"
== L2 moved to {elev:.0f} ==")
        for label, get in READINGS:
            diff = [(r["floor"], r["ridge"]) for r, b in zip(rows, base, strict=True)
                    if get(r) != get(b)]
            print(f"   {label:52s} "
                  f"{'identical on all six roofs' if not diff else f'CHANGED on {len(diff)}: {diff}'}")
        print(f"   {'walls the R3b dash marks':52s} {dash} -- "
              f"{'identical' if dash == base_dash else 'CHANGED'}")
        print("   composed regions:",
              {f"{r['floor']}@{r['ridge'][0]}": r["region"] for r in rows})
    win.close()


if __name__ == "__main__":
    main()
