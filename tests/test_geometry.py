"""Tests de recon3d.geometry con escenas sintéticas."""

import pytest

np = pytest.importorskip("numpy")

from recon3d.geometry import epipolar_distances, trajectory_frame  # noqa: E402


def _skew(v):
    return np.array([[0, -v[2], v[1]], [v[2], 0, -v[0]], [-v[1], v[0], 0]])


def _rotation(axis, angle):
    axis = np.asarray(axis, float) / np.linalg.norm(axis)
    k = _skew(axis)
    return np.eye(3) + np.sin(angle) * k + (1 - np.cos(angle)) * k @ k


def _project(K, R, t, points):
    cam = points @ R.T + t
    pix = cam @ K.T
    return pix[:, :2] / pix[:, 2:3]


def test_epipolar_distances_zero_for_true_matches():
    rng = np.random.default_rng(0)
    K = np.array([[800.0, 0, 320], [0, 800.0, 240], [0, 0, 1]])
    R = _rotation([0, 1, 0], np.deg2rad(10))
    t = np.array([-0.5, 0.0, 0.05])
    points = rng.uniform([-1, -1, 4], [1, 1, 6], size=(30, 3))

    x1 = _project(K, np.eye(3), np.zeros(3), points)
    x2 = _project(K, R, t, points)
    K_inv = np.linalg.inv(K)
    F = K_inv.T @ _skew(t) @ R @ K_inv  # F = K^-T [t]x R K^-1

    assert np.all(epipolar_distances(x1, x2, F) < 1e-6)

    shifted = x2 + np.array([0.0, 5.0])  # desplazar 5 px rompe la restricción
    assert np.mean(epipolar_distances(x1, shifted, F)) > 1.0


def test_trajectory_frame_recovers_vertical_axis():
    # Dos órbitas horizontales (alturas 0 y 0.3) giradas arbitrariamente.
    angles = np.linspace(0, 2 * np.pi, 40, endpoint=False)
    orbit = np.column_stack([np.cos(angles), np.sin(angles), np.zeros_like(angles)])
    centers = np.vstack([orbit, orbit + [0, 0, 0.3]])
    R = _rotation([1, 2, 3], 0.7)
    rotated = centers @ R.T + [5, -2, 1]

    coords, axes = trajectory_frame(rotated)

    true_up = R @ np.array([0, 0, 1.0])
    assert abs(axes[2] @ true_up) == pytest.approx(1.0, abs=1e-6)
    heights = np.abs(coords[:, 2])
    assert heights.max() == pytest.approx(0.15, abs=1e-6)
    assert np.linalg.det(axes) == pytest.approx(1.0)


def test_trajectory_frame_rejects_bad_input():
    with pytest.raises(ValueError):
        trajectory_frame(np.zeros((2, 3)))
