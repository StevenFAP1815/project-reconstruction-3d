"""Tests de las utilidades de SfM que no dependen de pycolmap."""

from types import SimpleNamespace

import pytest

pytest.importorskip("numpy")

from recon3d.sfm import set_options  # noqa: E402


def test_set_options_assigns_nested_values_and_reports_unknown():
    target = SimpleNamespace(
        guided_matching=False,
        mapper=SimpleNamespace(abs_pose_min_num_inliers=30),
    )

    ignored = set_options(
        target,
        {
            "guided_matching": True,
            "mapper.abs_pose_min_num_inliers": 15,
            "mapper.does_not_exist": 1,
            "missing.parent": 2,
        },
    )

    assert target.guided_matching is True
    assert target.mapper.abs_pose_min_num_inliers == 15
    assert not hasattr(target.mapper, "does_not_exist")  # no se crean atributos nuevos
    assert ignored == ["mapper.does_not_exist", "missing.parent"]


def test_set_options_accepts_none():
    assert set_options(SimpleNamespace(), None) == []
