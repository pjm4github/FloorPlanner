"""0316: a session label (the W/O/V/R/F number a user sees) survives a
save/open cycle, so a Find by that number lands on the same item next session.

The number is a session LABEL, adopted on load from the file's `id`; but
`canonicalize` renumbers every id by geometry at each save, so the label would
drift across a save/open cycle unless it is persisted. These pin the fix: a
`uid` the canonical id cannot recover is written, carried and re-adopted --
while a plan whose labels already match its ids stays bare, so the byte-for-byte
reproduction guarantee (test_load_path) is undisturbed, and a label is stored on
at most one record even when several would claim it.
"""
import json
from pathlib import Path

import pytest

pytestmark = pytest.mark.io

EXAMPLES = Path(__file__).resolve().parent.parent / "examples"


def _load(name):
    return json.loads((EXAMPLES / name).read_text(encoding="utf-8"))


def _wall_labels(fp, win):
    return {w.uid for w in win.scene.items() if isinstance(w, fp.WallItem)}


def test_a_wall_label_survives_save_open_when_its_id_differs(fp, win):
    doc = _load("symmetricP1.json")
    doc["walls"][0]["uid"] = "W777"          # a number its canonical id can't give back
    win.open_document(doc, interactive=False)
    assert "W777" in _wall_labels(fp, win), "the stored label was not adopted on load"

    again = win.design_document()             # the SAVE path carries labels
    assert any(w.get("uid") == "W777" for w in again["walls"]), \
        "the label was not written to the file"

    win.open_document(again, interactive=False)
    assert "W777" in _wall_labels(fp, win), "the label did not survive the round trip"


def test_a_clean_canonical_plan_stores_no_labels(fp, win):
    # symmetricP1 is already canonical: every item's label matches its id, so
    # nothing needs storing and the file reproduces byte-for-byte (the
    # companion guarantee in test_load_path::..._reproduces_it_exactly).
    win.open_document(_load("symmetricP1.json"), interactive=False)
    doc = win.design_document()
    for key in ("vertices", "walls", "rooms", "furnishings"):
        assert all("uid" not in rec for rec in doc.get(key, [])), \
            f"a clean plan stored a redundant uid on a {key[:-1]}"
    assert all("uid" not in o for w in doc["walls"] for o in w.get("openings", [])), \
        "a clean plan stored a redundant uid on an opening"


def test_an_opening_label_survives_a_round_trip(fp, win):
    doc = _load("symmetricP1.json")
    w = next(w for w in doc["walls"] if w.get("openings"))
    w["openings"][0]["uid"] = "O555"
    win.open_document(doc, interactive=False)
    labels = {op.uid for wi in win.scene.items() if isinstance(wi, fp.WallItem)
              for op in wi.openings}
    assert "O555" in labels, "the opening label was not adopted on load"
    again = win.design_document()
    ops = [o for wl in again["walls"] for o in wl.get("openings", [])]
    assert any(o.get("uid") == "O555" for o in ops), "the opening label was not saved"


def test_a_room_label_survives_a_round_trip(fp, win):
    doc = _load("symmetricP1.json")
    doc["rooms"][0]["uid"] = "R321"
    win.open_document(doc, interactive=False)
    assert "R321" in {r.uid for r in win.scene.items() if isinstance(r, fp.RoomItem)}
    again = win.design_document()
    assert any(r.get("uid") == "R321" for r in again["rooms"]), "the room label was not saved"


def test_the_undo_dirty_snapshot_is_label_free(fp, win):
    # labels ride the FILE (design_document), never the snapshot that defines
    # undo and the dirty flag -- so a re-minted label never reads as an edit and
    # the snapshot stays granularity-invariant (one wall == its split segments).
    doc = _load("symmetricP1.json")
    doc["walls"][0]["uid"] = "W777"
    win.open_document(doc, interactive=False)
    snap = win.snapshot()
    assert all("uid" not in w for w in snap.get("walls", []))
    assert all("uid" not in v for v in snap.get("vertices", []))
    assert all("uid" not in r for r in snap.get("rooms", []))


def test_a_label_is_stored_on_at_most_one_record(fp, win):
    # a label is unique in a document. Force every wall to claim "W1"; the save
    # must keep it on exactly one record (`_persist_labels` drops the rest), or a
    # reload would give several walls the same number and a Find could not choose.
    doc = _load("symmetricP1.json")
    for w in doc["walls"]:
        w["uid"] = "W1"
    win.open_document(doc, interactive=False)
    again = win.design_document()
    stored = [w["uid"] for w in again["walls"] if "uid" in w]
    assert len(stored) == len(set(stored)), "a label was stored on more than one record"
    assert stored.count("W1") <= 1
