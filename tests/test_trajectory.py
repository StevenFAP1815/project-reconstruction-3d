import numpy as np

from recon3d.geometry import overlap_from_step, viewing_angle_steps


def test_viewing_angle_steps_on_orbit():
    angles = np.radians(np.arange(0, 360, 10))
    directions = -np.column_stack([np.cos(angles), np.sin(angles), np.zeros_like(angles)])
    steps = viewing_angle_steps(directions)
    np.testing.assert_allclose(steps, 10.0, atol=1e-9)


def test_overlap_from_step():
    assert overlap_from_step(10.0, 50.0) == 0.8
    np.testing.assert_allclose(overlap_from_step([0.0, 60.0], 50.0), [1.0, 0.0])
