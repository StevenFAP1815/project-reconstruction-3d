"""Tests de recon3d.dataset.

`tmp_path` es una carpeta temporal que pytest crea (y limpia) para cada test,
así los tests no dependen de las fotos reales de data/.
"""

import pytest

from recon3d.dataset import list_images


def test_list_images_returns_only_images_sorted(tmp_path):
    for name in ["b.jpg", "a.JPG", "c.png", "notes.txt"]:
        (tmp_path / name).write_bytes(b"")
    (tmp_path / "subfolder.jpg").mkdir()  # carpeta con nombre engañoso

    result = list_images(tmp_path)

    assert [path.name for path in result] == ["a.JPG", "b.jpg", "c.png"]


def test_list_images_empty_folder_returns_empty_list(tmp_path):
    assert list_images(tmp_path) == []


def test_list_images_missing_folder_raises(tmp_path):
    with pytest.raises(FileNotFoundError):
        list_images(tmp_path / "does-not-exist")
