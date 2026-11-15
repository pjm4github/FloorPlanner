"""The first-person camera pose transform (`fp3dq.plan_to_qml_pose`).

A plan camera is (x, y-DOWN inches) + an aim `rot` (0 = +x), the same frame
`CameraItem` carries. The 3D view is Qt Quick 3D (y-up), and its meshes are the
fp3d world (x, -y, z) recentred by `- ctr` then rotated z-up -> y-up as
(x, y, z) -> (x, z, -y). The camera eye and aim must ride the SAME y-flip and
`-ctr` recentre or the camera will not sit in the room / will look the wrong
way. These hold that, so a future edit to the transform cannot get it wrong
silently (the real 3D view needs a display; this is the part that does not).
"""
import math

import numpy as np
import pytest

from floorplanner.viewer.fp3dq import plan_to_qml_pose

pytestmark = pytest.mark.geometry


def test_at_zero_centre_the_eye_is_a_plain_yflip():
    # ctr = 0: eye_world (px, -py, wz) -> QML (x, z, -y) = (px, wz, py)
    ex, ey, ez, yaw, pitch = plan_to_qml_pose(100.0, 200.0, 65.0, 0.0, np.zeros(3))
    assert (ex, ey, ez) == (100.0, 65.0, 200.0)
    assert pitch == 0.0


def test_the_eye_rides_the_same_recenter_as_the_meshes():
    # ctr is the world-frame bbox centre (x, -y_plan, z). A camera standing at
    # the plan centre, at the centre height, lands at the QML origin in x,z.
    ctr = np.array([50.0, -300.0, 40.0])        # plan centre (50, 300), z 40
    ex, ey, ez, _yaw, _p = plan_to_qml_pose(50.0, 300.0, 65.0, 0.0, ctr)
    assert ex == pytest.approx(0.0)
    assert ez == pytest.approx(0.0)
    assert ey == pytest.approx(25.0)            # 65 - 40


def test_yaw_is_minus_rot_minus_90():
    for rot in (0.0, 30.0, 90.0, 180.0, 270.0, -45.0):
        _ex, _ey, _ez, yaw, _p = plan_to_qml_pose(0.0, 0.0, 0.0, rot, np.zeros(3))
        assert yaw == pytest.approx(-rot - 90.0)


@pytest.mark.parametrize("rot", [0.0, 30.0, 45.0, 90.0, 135.0, 200.0, -60.0])
def test_the_yaw_aims_the_camera_along_the_plan_direction(rot):
    # A Qt Quick 3D camera at eulerRotation.y = yaw looks along the forward
    # (-sin yaw, 0, -cos yaw). The plan aim `rot` (0=+x, y-down) maps into QML
    # as (cos rot, 0, sin rot). The transform's yaw must make the two agree.
    _ex, _ey, _ez, yaw, _p = plan_to_qml_pose(0.0, 0.0, 0.0, rot, np.zeros(3))
    yr = math.radians(yaw)
    forward = (-math.sin(yr), 0.0, -math.cos(yr))
    rr = math.radians(rot)
    want = (math.cos(rr), 0.0, math.sin(rr))
    for a, b in zip(forward, want, strict=True):
        assert a == pytest.approx(b, abs=1e-9)
