"""Wall coalescing: overlapping same-type walls merge into one shared wall.

The shared-wall model replaces the old party-wall duplicates -- a coalesced
boundary wall borders every room it runs along.  Coalescing is gated by the
SETTINGS['auto_coalesce'] flag and must reach a fixed point (idempotent)."""
import pytest
from PyQt6.QtCore import QLineF, QPointF

pytestmark = pytest.mark.walls


def _walls(scene, fp):
    return [w for w in scene.items()
            if isinstance(w, fp.WallItem) and not w.is_open]


def test_within_grid_parallel_walls_merge_to_one(fp, scene):
    # two parallel walls 6" apart (within the wall-snap grid), overlapping span
    scene.addItem(fp.WallItem(QPointF(0, 0), QPointF(120, 0), "interior"))
    scene.addItem(fp.WallItem(QPointF(60, 6), QPointF(180, 6), "interior"))
    fp._coalesce_all_impl(scene)
    assert len(_walls(scene, fp)) == 1


def test_far_parallel_walls_do_not_merge(fp, scene):
    # 18" apart (> 6" grid): must stay separate
    scene.addItem(fp.WallItem(QPointF(0, 0), QPointF(120, 0), "interior"))
    scene.addItem(fp.WallItem(QPointF(0, 18), QPointF(120, 18), "interior"))
    fp._coalesce_all_impl(scene)
    assert len(_walls(scene, fp)) == 2


def test_different_types_never_merge(fp, scene):
    scene.addItem(fp.WallItem(QPointF(0, 0), QPointF(120, 0), "interior"))
    scene.addItem(fp.WallItem(QPointF(0, 0), QPointF(120, 0), "exterior"))
    fp._coalesce_all_impl(scene)
    assert len(_walls(scene, fp)) == 2


def test_coalesce_is_idempotent(fp, scene):
    for i in range(5):                      # a chain of overlapping segments
        scene.addItem(fp.WallItem(QPointF(i * 30, 0),
                                  QPointF(i * 30 + 90, 0), "interior"))
    fp._coalesce_all_impl(scene)
    n = len(_walls(scene, fp))
    assert n == 1                           # all merge into one span
    fp._coalesce_all_impl(scene)            # running again changes nothing
    assert len(_walls(scene, fp)) == n


def test_auto_coalesce_flag_disables_it(fp, scene):
    fp.SETTINGS["auto_coalesce"] = False
    try:
        a = fp.WallItem(QPointF(0, 0), QPointF(120, 0), "interior")
        scene.addItem(a)
        scene.addItem(fp.WallItem(QPointF(60, 0), QPointF(180, 0), "interior"))
        fp.coalesce_wall(scene, a)          # gated entry -> no-op
        assert len(_walls(scene, fp)) == 2
        fp.coalesce_all(scene)              # gated sweep -> no-op
        assert len(_walls(scene, fp)) == 2
    finally:
        fp.SETTINGS["auto_coalesce"] = True


def test_merged_wall_unions_its_rooms(fp, scene, make_room):
    # a free wall coincident with two rooms' shared edge merges, bordering both
    room = make_room(scene, 0, 0, 120, 120, "Den")
    edge = next(w for w in room.walls
                if QLineF(w.p1, w.p2).length() > 1)
    free = fp.WallItem(QPointF(edge.p1), QPointF(edge.p2), edge.wall_type)
    scene.addItem(free)
    survivor = fp._coalesce_wall_impl(scene, free)
    assert room in survivor.rooms
    assert survivor in room.walls
