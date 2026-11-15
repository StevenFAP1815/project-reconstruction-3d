import numpy as np
import pytest

from recon3d.meshing import (
    estimate_normals,
    nearest_colors,
    orient_normals,
    sample_surface,
    voxel_downsample,
)


def sphere(n=4000, seed=0):
    rng = np.random.default_rng(seed)
    points = rng.normal(size=(n, 3))
    return points / np.linalg.norm(points, axis=1, keepdims=True)


def test_voxel_downsample_averages_points_and_colors():
    points = np.array([[0.1, 0.1, 0.1], [0.3, 0.3, 0.3], [5.0, 5.0, 5.0]])
    colors = np.array([[0, 0, 0], [100, 100, 100], [255, 0, 0]], dtype=np.uint8)
    reduced, reduced_colors = voxel_downsample(points, 1.0, colors)
    assert len(reduced) == 2
    order = np.argsort(reduced[:, 0])
    np.testing.assert_allclose(reduced[order[0]], [0.2, 0.2, 0.2])
    np.testing.assert_array_equal(reduced_colors[order[0]], [50, 50, 50])


def test_normals_on_a_sphere_are_radial_and_point_outwards():
    points = sphere()
    normals = orient_normals(points, estimate_normals(points, k=15))
    # En una esfera la normal es el propio radio; orientadas hacia fuera, el
    # producto escalar con la posición es positivo en (casi) todos los puntos.
    alignment = np.einsum("ij,ij->i", normals, points)
    assert np.mean(alignment > 0.9) > 0.98


def test_orientation_is_consistent_even_if_pca_signs_are_random():
    points = sphere(seed=1)
    normals = estimate_normals(points, k=15)
    flips = np.random.default_rng(2).choice([-1.0, 1.0], size=len(points))
    oriented = orient_normals(points, normals * flips[:, None])
    assert np.mean(np.einsum("ij,ij->i", oriented, points) > 0) > 0.98


def test_sample_surface_follows_triangle_area():
    vertices = np.array([[0, 0, 0], [1, 0, 0], [0, 1, 0], [10, 0, 0], [13, 0, 0], [10, 3, 0]], float)
    faces = np.array([[0, 1, 2], [3, 4, 5]])                # áreas 0,5 y 4,5
    samples = sample_surface(vertices, faces, 20000, seed=0)
    assert np.mean(samples[:, 0] >= 10) == pytest.approx(0.9, abs=0.02)
    assert np.all(samples[:, 2] == 0)


def test_nearest_colors_picks_the_closest_point():
    points = np.array([[0.0, 0, 0], [10.0, 0, 0]])
    colors = np.array([[255, 0, 0], [0, 0, 255]], dtype=np.uint8)
    np.testing.assert_array_equal(nearest_colors(np.array([[9.0, 0, 0]]), points, colors), [[0, 0, 255]])
