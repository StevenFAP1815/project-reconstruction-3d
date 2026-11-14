import numpy as np

from recon3d.pointcloud import angular_coverage
from recon3d.vggt_tools import (
    camera_rays,
    confidence_mask,
    content_box,
    expected_focal,
    select_frames,
    unproject_depth,
)


def look_at_extrinsic(center, target):
    """Extrínseco (3, 4) de OpenCV de una cámara en `center` que mira a `target`."""
    z = np.asarray(target, float) - center
    z /= np.linalg.norm(z)
    x = np.cross(z, [0, 0, 1.0])
    x /= np.linalg.norm(x)
    y = np.cross(z, x)
    rotation = np.vstack([x, y, z])
    return np.hstack([rotation, (-rotation @ center)[:, None]])


def test_select_frames_spreads_and_keeps_ends():
    items = list(range(100))
    chosen = select_frames(items, 5)
    assert chosen == [0, 25, 50, 74, 99] or chosen == [0, 25, 50, 75, 99]
    assert select_frames(items[:3], 10) == [0, 1, 2]


def test_camera_rays_recover_center_and_direction():
    center = np.array([3.0, -2.0, 1.5])
    extrinsic = look_at_extrinsic(center, [0, 0, 0])
    centers, directions = camera_rays(extrinsic[None])
    np.testing.assert_allclose(centers[0], center, atol=1e-12)
    np.testing.assert_allclose(directions[0], -center / np.linalg.norm(center), atol=1e-12)


def test_unproject_depth_hits_known_plane():
    # Cámara en (0, 0, 5) mirando al origen: el plano z = 0 está a profundidad 5.
    extrinsic = look_at_extrinsic(np.array([0, 0.001, 5.0]), [0, 0, 0])
    intrinsic = np.array([[100.0, 0, 32], [0, 100.0, 24], [0, 0, 1]])
    height, width = 48, 64
    u, v = np.meshgrid(np.arange(width), np.arange(height))
    rays = np.stack([(u - 32) / 100, (v - 24) / 100, np.ones_like(u, dtype=float)], -1)
    world_dirs = rays @ extrinsic[:, :3]  # Rᵀ · rayo
    depth = (5.0 / -world_dirs[..., 2])  # escala del rayo hasta z = 0 (rayo con z_cam = 1)
    points = unproject_depth(depth[None], extrinsic[None], intrinsic[None])
    np.testing.assert_allclose(points[0, ..., 2], 0, atol=1e-9)


def test_confidence_mask_keeps_upper_half():
    confidence = np.arange(100.0).reshape(10, 10)
    assert confidence_mask(confidence, 50).sum() == 50


def test_content_box_and_focal_for_portrait_photo():
    assert content_box((3000, 4000)) == (63, 0, 392, 518)
    fx, fy = expected_focal((2852.0, 2852.0), (3000, 4000))
    assert abs(fx - 2852 * 392 / 3000) < 1e-9 and abs(fy - 2852 * 518 / 4000) < 1e-9


def test_angular_coverage_full_and_half():
    angle = np.linspace(-np.pi, np.pi, 3600, endpoint=False)
    ring = np.column_stack([np.cos(angle), np.sin(angle), np.zeros_like(angle)])
    assert angular_coverage(ring) == 100.0
    half = ring[ring[:, 1] > 0]
    assert angular_coverage(half, center=(0, 0)) == 50.0
