"""Tests de recon3d.preprocessing."""

import pytest

cv2 = pytest.importorskip("cv2")
np = pytest.importorskip("numpy")

from recon3d.preprocessing import enhance_contrast, flag_blurry, laplacian_variance  # noqa: E402


def test_enhance_contrast_brightens_dark_low_contrast_image(tmp_path):
    rng = np.random.default_rng(0)
    dark = np.clip(rng.normal(30, 6, (300, 400, 3)), 0, 255).astype(np.uint8)
    source = tmp_path / "dark.jpg"
    cv2.imwrite(str(source), dark)

    out = enhance_contrast(source, tmp_path / "out" / "dark.jpg")

    result = cv2.imread(str(out))
    assert result.shape == dark.shape
    assert result.std() > dark.std()  # más contraste


def _checkerboard(size=400, square=20):
    rows, cols = np.indices((size, size)) // square
    return ((rows + cols) % 2 * 255).astype(np.uint8)


def test_blurred_image_has_lower_laplacian_variance(tmp_path):
    sharp = _checkerboard()
    blurred = cv2.GaussianBlur(sharp, (0, 0), sigmaX=4)
    cv2.imwrite(str(tmp_path / "sharp.png"), sharp)
    cv2.imwrite(str(tmp_path / "blurred.png"), blurred)

    sharp_score = laplacian_variance(tmp_path / "sharp.png")
    blurred_score = laplacian_variance(tmp_path / "blurred.png")

    assert blurred_score < 0.2 * sharp_score


def test_laplacian_variance_unreadable_file_raises(tmp_path):
    bad = tmp_path / "bad.jpg"
    bad.write_bytes(b"no es una imagen")
    with pytest.raises(ValueError):
        laplacian_variance(bad)


def test_flag_blurry_uses_ratio_of_median():
    scores = {"a.jpg": 100.0, "b.jpg": 110.0, "c.jpg": 90.0, "d.jpg": 20.0, "e.jpg": 36.0}
    # mediana = 90 -> umbral 0.35 * 90 = 31.5
    assert flag_blurry(scores, ratio=0.35) == ["d.jpg"]
    assert flag_blurry({}) == []
    with pytest.raises(ValueError):
        flag_blurry(scores, ratio=1.5)
