import json
import struct

import numpy as np
import pytest

from recon3d.dense import read_colmap_array
from recon3d.measurements import MEASUREMENTS, SCALE_BY
from recon3d.paths import OBJECTS
from recon3d.pointcloud import (
    clean_object_cloud,
    crop_mesh,
    dimensional_errors,
    fit_plane_ransac,
    largest_component,
    look_at_point,
    measure,
    object_frame,
    read_ply,
    write_glb,
    write_obj,
    write_ply,
)


def box_surface(size, n=6000, seed=0):
    """Puntos sobre la superficie de una caja de lados `size`, con la base en z = 0."""
    rng = np.random.default_rng(seed)
    points = rng.uniform(0, 1, (n, 3)) * size
    axis = rng.integers(0, 3, n)
    side = rng.integers(0, 2, n)
    points[np.arange(n), axis] = side * np.asarray(size)[axis]
    return points - [size[0] / 2, size[1] / 2, 0]


def orbit_cameras(radius=10.0, height=4.0, n=24):
    angles = np.linspace(0, 2 * np.pi, n, endpoint=False)
    centers = np.column_stack([radius * np.cos(angles), radius * np.sin(angles), np.full(n, height)])
    target = np.array([0.0, 0.0, 1.0])
    return centers, target - centers


def test_ply_roundtrip_with_faces(tmp_path):
    points = np.random.default_rng(1).normal(size=(50, 3))
    colors = np.random.default_rng(2).integers(0, 255, (50, 3)).astype(np.uint8)
    normals = points / np.linalg.norm(points, axis=1, keepdims=True)
    faces = np.array([[0, 1, 2], [2, 3, 4]])
    path = write_ply(tmp_path / "m.ply", points, colors=colors, normals=normals, faces=faces)
    data = read_ply(path)
    np.testing.assert_allclose(data["points"], points, atol=1e-6)
    np.testing.assert_allclose(data["normals"], normals, atol=1e-6)
    np.testing.assert_array_equal(data["colors"], colors)
    np.testing.assert_array_equal(data["faces"], faces)


def test_read_ascii_ply(tmp_path):
    path = tmp_path / "a.ply"
    path.write_text("ply\nformat ascii 1.0\nelement vertex 2\nproperty float x\n"
                    "property float y\nproperty float z\nend_header\n0 1 2\n3 4 5\n")
    np.testing.assert_allclose(read_ply(path)["points"], [[0, 1, 2], [3, 4, 5]])


def test_look_at_point_finds_orbit_target():
    centers, directions = orbit_cameras()
    np.testing.assert_allclose(look_at_point(centers, directions), [0, 0, 1], atol=1e-9)


def test_fit_plane_ransac_ignores_outliers():
    rng = np.random.default_rng(3)
    plane = np.column_stack([rng.uniform(-5, 5, (500, 2)), rng.normal(0, 0.01, 500)])
    noise = rng.uniform(-5, 5, (100, 3))
    normal, d, mask = fit_plane_ransac(np.vstack([plane, noise]), 0.05)
    assert abs(abs(normal[2]) - 1) < 1e-3
    assert abs(d) < 0.01
    assert mask[:500].mean() > 0.99


def test_largest_component_drops_far_islands():
    rng = np.random.default_rng(4)
    big = rng.uniform(0, 1, (800, 3))
    island = rng.uniform(0, 0.2, (50, 3)) + 5
    mask = largest_component(np.vstack([big, island]), voxel=0.1)
    assert mask[:800].all() and not mask[800:].any()


def test_clean_object_cloud_removes_table_and_background():
    rng = np.random.default_rng(5)
    obj = box_surface((1.0, 0.6, 2.0), n=4000)
    table = np.column_stack([rng.uniform(-3, 3, (4000, 2)), np.zeros(4000)])
    far = rng.uniform(-30, 30, (300, 3)) + [0, 40, 0]
    points = np.vstack([obj, table, far])
    centers, directions = orbit_cameras()
    mask, report = clean_object_cloud(points, centers, directions, up=[0, 0, 1])
    assert report["table_plane_found"]
    assert not mask[4000:].any()
    # Se pierden la base de la caja (1/6 de sus puntos), que toca la mesa, y una
    # franja de los laterales igual a la tolerancia del plano.
    assert mask[:4000].mean() > 0.75


def test_object_frame_and_measurements_on_box():
    size = (0.93, 0.58, 1.96)  # caja en unidades arbitrarias, de pie
    rotation = np.linalg.qr(np.random.default_rng(6).normal(size=(3, 3)))[0]
    if np.linalg.det(rotation) < 0:
        rotation[:, 0] *= -1
    points = box_surface(size, n=20000) @ rotation.T
    up = rotation @ np.array([0, 0, 1.0])
    coords, rotation_found, origin = object_frame(points, up)
    np.testing.assert_allclose((points - origin) @ rotation_found.T, coords)
    assert coords[:, 2].min() == pytest.approx(0, abs=0.02)
    assert measure(coords, {"kind": "height"}) == pytest.approx(1.96, rel=0.02)
    assert measure(coords, {"kind": "extent", "rank": 2}) == pytest.approx(0.58, rel=0.02)
    assert measure(coords, {"kind": "max_width"}) == pytest.approx(0.93, rel=0.02)

    scale, rows = dimensional_errors(coords, MEASUREMENTS["caja-carton-leche"], "alto")
    assert scale == pytest.approx(100, rel=0.02)
    assert all(abs(row["error_pct"]) < 2 for row in rows)
    assert [row["role"] for row in rows].count("escala") == 1


def test_slice_width_measures_a_cylinder_diameter():
    rng = np.random.default_rng(7)
    angle = rng.uniform(0, 2 * np.pi, 20000)
    z = rng.uniform(0, 3, 20000)
    radius = np.where(z < 1, 0.5, 1.0)  # base estrecha, parte alta ancha
    coords = np.column_stack([radius * np.cos(angle), radius * np.sin(angle), z])
    assert measure(coords, {"kind": "slice_width", "from": 0.0, "to": 0.3}) == pytest.approx(1.0, rel=0.03)
    assert measure(coords, {"kind": "slice_width", "from": 0.5, "to": 1.0}) == pytest.approx(2.0, rel=0.03)


def test_measurements_cover_every_object():
    assert set(MEASUREMENTS) == set(OBJECTS) == set(SCALE_BY)
    for name, items in MEASUREMENTS.items():
        assert SCALE_BY[name] in {m["name"] for m in items}
        assert len(items) >= 3


def test_crop_mesh_keeps_inside_triangles():
    vertices = np.array([[0, 0, 0], [1, 0, 0], [0, 1, 0], [5, 5, 5]], dtype=float)
    faces = np.array([[0, 1, 2], [1, 2, 3]])
    kept_vertices, kept_faces, used = crop_mesh(vertices, faces, low=[-1, -1, -1], high=[2, 2, 2])
    np.testing.assert_array_equal(kept_faces, [[0, 1, 2]])
    np.testing.assert_array_equal(used, [0, 1, 2])
    assert len(kept_vertices) == 3


def test_write_obj_and_glb(tmp_path):
    vertices = np.array([[0, 0, 0], [1, 0, 0], [0, 1, 0]], dtype=float)
    faces = np.array([[0, 1, 2]])
    colors = np.array([[255, 0, 0]] * 3, dtype=np.uint8)
    text = write_obj(tmp_path / "m.obj", vertices, faces, colors).read_text()
    assert "f 1 2 3" in text and text.count("\nv ") == 3

    raw = write_glb(tmp_path / "m.glb", vertices, faces, colors).read_bytes()
    magic, version, total = struct.unpack("<4sII", raw[:12])
    assert magic == b"glTF" and version == 2 and total == len(raw) and total % 4 == 0
    json_len = struct.unpack("<I", raw[12:16])[0]
    document = json.loads(raw[20:20 + json_len])
    assert document["accessors"][0]["count"] == 3
    assert document["meshes"][0]["primitives"][0]["attributes"] == {"POSITION": 0, "COLOR_0": 2}


def test_read_colmap_array(tmp_path):
    depth = np.arange(12, dtype=np.float32).reshape(3, 4)  # alto 3, ancho 4
    path = tmp_path / "d.bin"
    with open(path, "wb") as file:
        file.write(b"4&3&1&")
        np.transpose(depth[:, :, None], (1, 0, 2)).flatten(order="F").tofile(file)
    np.testing.assert_array_equal(read_colmap_array(path), depth)
