"""Wall merging: overlapping same-type walls merge into one shared wall.

The shared-wall model replaces the old party-wall duplicates -- a merged
boundary wall borders every room it runs along.  Merging is gated by the
SETTINGS['auto_coalesce'] flag and must reach a fixed point (idempotent).

REWRITTEN AT P3.4 (iv). Old ops: `_coalesce_all_impl` / `_coalesce_wall_impl`,
deleted with the rest of the coalesce family. New ops: `merge_all` /
`merge_wall`, the gated entries onto `topology.plan_merge_collinear`. Why the
assertions did NOT move: they are the behaviour contract, not the
implementation -- "these two become one, those two do not, the flag is
honoured, the survivor borders both rooms" is as true of the new op as of the
old, and every line below still says exactly what it said before. Only the
call changed. (Where the new op does MORE than the old -- deduping openings on
merge, defect 9 -- that is pinned in test_topology_ops.py, not smuggled in
here.)"""
import pytest
from PyQt6.QtCore import QLineF, QPointF

from floorplanner.walls import merge_all, merge_wall

pytestmark = pytest.mark.walls


def _walls(scene, fp):
    return [w for w in scene.items()
            if isinstance(w, fp.WallItem) and not w.is_open]


def test_within_grid_parallel_walls_merge_to_one(fp, scene):
    # two parallel walls 6" apart (within the wall-snap grid), overlapping span
    scene.addItem(fp.WallItem(QPointF(0, 0), QPointF(120, 0), "interior"))
    scene.addItem(fp.WallItem(QPointF(60, 6), QPointF(180, 6), "interior"))
    merge_all(scene)
    assert len(_walls(scene, fp)) == 1


def test_far_parallel_walls_do_not_merge(fp, scene):
    # 18" apart (> 6" grid): must stay separate
    scene.addItem(fp.WallItem(QPointF(0, 0), QPointF(120, 0), "interior"))
    scene.addItem(fp.WallItem(QPointF(0, 18), QPointF(120, 18), "interior"))
    merge_all(scene)
    assert len(_walls(scene, fp)) == 2


def test_different_types_never_merge(fp, scene):
    scene.addItem(fp.WallItem(QPointF(0, 0), QPointF(120, 0), "interior"))
    scene.addItem(fp.WallItem(QPointF(0, 0), QPointF(120, 0), "exterior"))
    merge_all(scene)
    assert len(_walls(scene, fp)) == 2


def test_merge_is_idempotent(fp, scene):
    for i in range(5):                      # a chain of overlapping segments
        scene.addItem(fp.WallItem(QPointF(i * 30, 0),
                                  QPointF(i * 30 + 90, 0), "interior"))
    merge_all(scene)
    n = len(_walls(scene, fp))
    assert n == 1                           # all merge into one span
    merge_all(scene)                        # running again changes nothing
    assert len(_walls(scene, fp)) == n


def test_auto_coalesce_flag_disables_it(fp, scene):
    fp.SETTINGS["auto_coalesce"] = False
    try:
        a = fp.WallItem(QPointF(0, 0), QPointF(120, 0), "interior")
        scene.addItem(a)
        scene.addItem(fp.WallItem(QPointF(60, 0), QPointF(180, 0), "interior"))
        merge_wall(scene, a)                # gated entry -> no-op
        assert len(_walls(scene, fp)) == 2
        merge_all(scene)                    # gated sweep -> no-op
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
    survivor = merge_wall(scene, free)
    assert room in survivor.rooms
    assert survivor in room.walls
