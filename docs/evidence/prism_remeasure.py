"""PRISM'S RECEIPT: after it lands, how many of the 28 still fall back, and which.

    python docs/evidence/prism_remeasure.py            # the numbers
    python docs/evidence/prism_remeasure.py --look     # + the picture

Patrick's ruling, 2026-08-13:

  > Prism's receipt is a RE-MEASUREMENT, not a claim: after it lands, how many
  > of the 28 box-fallback items still fall back, and which. That number is what
  > decides whether any further generator gets written, and "a third of the
  > catalog renders as a box" is the sentence it either falsifies or does not.

MEASURED THROUGH `build_model` ITSELF -- the production path -- so the answer is
what the viewer will actually draw, not what a separate instrument predicts. The
model reports `prism_kinds` and `box_fallback_kinds` in its stats for exactly
this reason: a claim about the viewer that does not come from the viewer is the
shape of error this repository has paid for repeatedly.

The document built here holds ONE OF EVERY CATALOG KIND, so the answer covers
the whole catalog rather than whatever a sample plan happens to contain.

`--look` additionally draws what each symbol contributes, against the footprint
a box would have filled. **That half is not decoration.** The count says 27 of
28 extruded; only the picture says whether an extrusion is a body or a handful
of fragments, and the read-back predicted two items where it would be fragments.
D74's lesson, one feature earlier: every assertion was true and the drawing was
still wrong.
"""
import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
FURN = ROOT / "assets" / "furnishings"


def load_fp3d():
    """The viewer, by path -- it is Qt-free and importing the package would
    drag in the bindings (D73)."""
    spec = importlib.util.spec_from_file_location(
        "fp3d_receipt", ROOT / "floorplanner" / "viewer" / "fp3d.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


def whole_catalog_doc(manifest):
    return {
        "format": "floorplanner-design", "version": 5,
        "levels": [{"id": "L0", "name": "default", "elevation_in": 0.0,
                    "height_in": 96.0}],
        "vertices": [], "walls": [], "rooms": [],
        "furnishings": [{"id": f"f{i}", "level": "L0", "kind": it["id"],
                         "pos": [i * 200.0, 0.0], "rotation": 0.0}
                        for i, it in enumerate(manifest)],
    }


def look(fp3d, specs, kinds, out):
    """Draw each symbol's extruded rings over the footprint a box would fill."""
    import os
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    from PyQt6.QtCore import QPointF, QRectF
    from PyQt6.QtGui import QBrush, QColor, QImage, QPainter, QPen, QPolygonF
    from PyQt6.QtWidgets import QApplication

    app = QApplication.instance() or QApplication([])   # noqa: F841
    cell, pad, cols = 300, 24, 4
    rows = (len(kinds) + cols - 1) // cols
    img = QImage(cols * (cell + pad) + pad, rows * (cell + pad) + pad,
                 QImage.Format.Format_ARGB32)
    img.fill(QColor(255, 255, 255))
    p = QPainter(img)
    p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    for n, kind in enumerate(kinds):
        ox = pad + (n % cols) * (cell + pad)
        oy = pad + (n // cols) * (cell + pad)
        rings, (vw, vh) = fp3d.svg_outlines(str(FURN / specs[kind]["file"]))
        if vw <= 0:
            continue
        s = min(cell / vw, cell / vh)
        fx, fy = ox + (cell - vw * s) / 2, oy + (cell - vh * s) / 2
        p.setPen(QPen(QColor(200, 60, 60), 0))          # what a BOX fills
        p.setBrush(QBrush(QColor(240, 200, 200, 90)))
        p.drawRect(QRectF(fx, fy, vw * s, vh * s))
        p.setPen(QPen(QColor(20, 60, 130), 0))          # what PRISM extrudes
        p.setBrush(QBrush(QColor(70, 110, 200, 190)))
        for r in rings:
            p.drawPolygon(QPolygonF([QPointF(fx + x * s, fy + y * s)
                                     for x, y in r]))
    p.end()
    img.save(str(out))
    print(f"wrote {out}  (order: {', '.join(kinds)})")


def main():
    fp3d = load_fp3d()
    manifest = json.loads((FURN / "manifest.json").read_text("utf-8"))
    specs = {it["id"]: it for it in manifest}
    model = fp3d.build_model(whole_catalog_doc(manifest))

    prism = model.stats["prism_kinds"]
    box = model.stats["box_fallback_kinds"]
    pending = {it["id"] for it in manifest
               if (it.get("form") or "box") not in ("box", "slab")}

    print(f"catalog                  {len(manifest)} items")
    print(f"was falling back to box  {len(pending)}")
    print(f"EXTRUDED (prism)         {len(prism)}")
    print(f"STILL A BOX              {len(box)}  {box}")
    assert set(prism) | set(box) == pending, "the two lists must partition"

    per = {}
    for k in prism:
        per.setdefault(specs[k]["form"], []).append(k)
    print("\nextruded by form:")
    for f in sorted(per):
        total = sum(1 for it in manifest if (it.get("form") or "box") == f)
        print(f"  {f:10s} {len(per[f]):2d} of {total:2d}")

    print("\nfrom the model's own report:")
    for line in model.info:
        print(f"  {line}")
    for line in model.notes:
        print(f"  NOTE: {line}")
    print(f"\ntriangles {model.stats['triangles']}  "
          f"furnishings {model.stats['furnishings']}")

    if "--look" in sys.argv:
        look(fp3d, specs,
             ["sofa", "lawnmower", "motorcycle", "snowblower",
              "bicycle", "boat_trailer", "glass_shower", "car"],
             Path(__file__).resolve().parent / "prism-extrusion-look.png")


if __name__ == "__main__":
    main()
