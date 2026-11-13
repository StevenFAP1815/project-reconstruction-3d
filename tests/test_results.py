"""Tests de recon3d.results."""

import json

import pytest

from recon3d.results import write_meta

REQUIRED_FIELDS = {
    "object",
    "method",
    "created_at",
    "n_images",
    "n_registered",
    "registered_ratio",
    "runtime_s",
    "seed",
    "scale_factor",
    "environment",
    "extra",
}


def _write(run_dir, **overrides):
    kwargs = dict(
        object_name="vaso-vidrio",
        method="colmap",
        n_images=81,
        n_registered=72,
        runtime_s=123.456,
        seed=42,
    )
    kwargs.update(overrides)
    return write_meta(run_dir, **kwargs)


def test_write_meta_creates_file_with_required_fields(tmp_path):
    run_dir = tmp_path / "results" / "vaso-vidrio" / "colmap"

    meta_path = _write(run_dir, scale_factor=12.5, extra={"matcher": "exhaustive"})

    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    assert meta_path == run_dir / "meta.json"
    assert REQUIRED_FIELDS <= meta.keys()
    assert meta["registered_ratio"] == pytest.approx(72 / 81, abs=1e-4)
    assert meta["runtime_s"] == 123.46
    assert meta["scale_factor"] == 12.5
    assert meta["extra"] == {"matcher": "exhaustive"}
    assert "python" in meta["environment"]


@pytest.mark.parametrize(
    "overrides",
    [
        {"n_registered": 90},  # más registradas que imágenes
        {"n_registered": -1},
        {"runtime_s": -1},
        {"scale_factor": 0},
    ],
)
def test_write_meta_rejects_inconsistent_values(tmp_path, overrides):
    with pytest.raises(ValueError):
        _write(tmp_path, **overrides)


def test_write_meta_requires_keyword_arguments(tmp_path):
    with pytest.raises(TypeError):
        write_meta(tmp_path, "vaso-vidrio", "colmap", 81, 72, 1.0, 42)
