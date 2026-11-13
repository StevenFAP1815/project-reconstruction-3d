"""Tests de recon3d.dataset.

`tmp_path` es una carpeta temporal que pytest crea (y limpia) para cada test,
así los tests no dependen de las fotos reales de data/.
"""

import zipfile

import pytest

from recon3d.dataset import extract_object_zip, list_images


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


def _make_zip(zip_path, members):
    with zipfile.ZipFile(zip_path, "w") as archive:
        for name, content in members.items():
            archive.writestr(name, content)


def test_extract_object_zip_flattens_and_keeps_only_images(tmp_path):
    zip_path = tmp_path / "vaso-vidrio.zip"
    _make_zip(
        zip_path,
        {
            "vaso-vidrio/b.jpg": b"b",
            "a.JPG": b"a",
            "notes.txt": b"x",
            "../../evil.jpg": b"e",  # no debe escribirse fuera del destino
        },
    )
    dest = tmp_path / "out"

    result = extract_object_zip(zip_path, dest)

    assert [path.name for path in result] == ["a.JPG", "b.jpg", "evil.jpg"]
    assert all(path.parent == dest for path in result)
    assert (dest / "b.jpg").read_bytes() == b"b"
    assert not (tmp_path.parent / "evil.jpg").exists()


def test_extract_object_zip_rejects_duplicate_names(tmp_path):
    zip_path = tmp_path / "dup.zip"
    _make_zip(zip_path, {"x/a.jpg": b"1", "y/a.jpg": b"2"})

    with pytest.raises(ValueError):
        extract_object_zip(zip_path, tmp_path / "out")


def test_extract_object_zip_missing_file_raises(tmp_path):
    with pytest.raises(FileNotFoundError):
        extract_object_zip(tmp_path / "missing.zip", tmp_path / "out")
