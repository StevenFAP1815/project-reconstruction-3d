"""Tests de recon3d.paths."""

import pytest

from recon3d.paths import OBJECTS, REPO_ROOT, get_paths


def test_get_paths_outside_colab_uses_repo_root():
    assert get_paths().root == REPO_ROOT


def test_run_dir_follows_results_convention(tmp_path):
    paths = get_paths(tmp_path)

    run_dir = paths.run_dir("vaso-vidrio", "colmap")

    assert run_dir == tmp_path / "results" / "vaso-vidrio" / "colmap"
    assert not run_dir.exists()  # run_dir solo construye la ruta


@pytest.mark.parametrize("method", ["", "COLMAP", "../colmap", "col map", "-x"])
def test_run_dir_rejects_invalid_method(tmp_path, method):
    with pytest.raises(ValueError):
        get_paths(tmp_path).run_dir("vaso-vidrio", method)


def test_unknown_object_is_rejected(tmp_path):
    paths = get_paths(tmp_path)
    with pytest.raises(ValueError):
        paths.run_dir("vaso", "colmap")
    with pytest.raises(ValueError):
        paths.data_zip("vaso")


def test_data_zip_accepts_objects_and_calibration(tmp_path):
    paths = get_paths(tmp_path)
    assert paths.data_zip("audifonos") == tmp_path / "data" / "zips" / "audifonos.zip"
    assert paths.data_zip("calibration").name == "calibration.zip"


def test_create_builds_structure_and_is_idempotent(tmp_path):
    paths = get_paths(tmp_path)
    marker = paths.results / "audifonos" / "keep.txt"

    paths.create()
    marker.write_text("no borrar")
    paths.create()  # segunda ejecución: no debe fallar ni borrar nada

    for name in OBJECTS:
        assert (paths.results / name).is_dir()
    assert paths.zips.is_dir()
    assert paths.calibration.is_dir()
    assert paths.work.is_dir()
    assert paths.checkpoints.is_dir()
    assert marker.read_text() == "no borrar"
