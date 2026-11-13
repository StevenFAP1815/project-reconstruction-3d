"""Tests de recon3d.calibration con imágenes sintéticas.

Se fabrica un tablero, se "fotografía" con una cámara virtual de K conocida
(proyección por homografía) y se comprueba que la calibración recupera esa K.
Así el test no depende de fotos reales.
"""

import pytest

cv2 = pytest.importorskip("cv2")
np = pytest.importorskip("numpy")

from recon3d.calibration import (  # noqa: E402
    board_object_points,
    calibrate,
    detect_corners,
    focal_px_from_35mm,
    load_calibration,
    save_calibration,
)

PATTERN = (9, 6)
SQUARE_MM = 25.0
IMAGE_SIZE = (640, 480)
K_TRUE = np.array([[500.0, 0, 320.0], [0, 500.0, 240.0], [0, 0, 1]])


def _board_texture(square_px=20, margin=1):
    """Tablero de 10 x 7 cuadros con un cuadro de margen blanco."""
    cols, rows = PATTERN[0] + 1, PATTERN[1] + 1
    height, width = (rows + 2 * margin) * square_px, (cols + 2 * margin) * square_px
    texture = np.full((height, width), 255, np.uint8)
    for r in range(rows):
        for c in range(cols):
            if (r + c) % 2 == 0:
                y0, x0 = (margin + r) * square_px, (margin + c) * square_px
                texture[y0 : y0 + square_px, x0 : x0 + square_px] = 0
    # Primera esquina interna, en coordenadas continuas de la textura.
    origin = (margin + 1) * square_px - 0.5
    return texture, square_px / SQUARE_MM, origin


def _render_views(folder, n_views, seed=0):
    texture, px_per_mm, origin = _board_texture()
    # Textura (px) -> plano del tablero (mm), con origen en la primera esquina.
    to_board = np.array(
        [[1 / px_per_mm, 0, -origin / px_per_mm], [0, 1 / px_per_mm, -origin / px_per_mm], [0, 0, 1]]
    )
    center = np.array([(PATTERN[0] - 1) * SQUARE_MM / 2, (PATTERN[1] - 1) * SQUARE_MM / 2, 0])
    rng = np.random.default_rng(seed)
    paths = []
    for i in range(n_views):
        rvec = np.deg2rad(rng.uniform(-30, 30, 3) * np.array([1, 1, 0.3]))
        rotation, _ = cv2.Rodrigues(rvec)
        offset = np.array([rng.uniform(-60, 60), rng.uniform(-40, 40), rng.uniform(550, 700)])
        translation = -rotation @ center + offset
        homography = K_TRUE @ np.column_stack([rotation[:, 0], rotation[:, 1], translation]) @ to_board
        image = cv2.warpPerspective(texture, homography, IMAGE_SIZE, flags=cv2.INTER_LINEAR, borderValue=128)
        path = folder / f"view_{i:02d}.png"
        cv2.imwrite(str(path), image)
        paths.append(path)
    return paths


def test_board_object_points_grid():
    points = board_object_points(SQUARE_MM, PATTERN)
    assert points.shape == (54, 3)
    assert points[1].tolist() == [25.0, 0.0, 0.0]  # avanza primero en columnas
    assert points[9].tolist() == [0.0, 25.0, 0.0]
    with pytest.raises(ValueError):
        board_object_points(0, PATTERN)


def test_focal_px_from_35mm_matches_phone_exif():
    # 24 mm equivalentes en una foto de 3000 x 4000 px -> ~2773 px.
    assert focal_px_from_35mm(24, (3000, 4000)) == pytest.approx(2773.4, abs=0.5)


def test_calibration_recovers_known_camera(tmp_path):
    paths = _render_views(tmp_path, n_views=12)
    blank = tmp_path / "blank.png"
    cv2.imwrite(str(blank), np.full((IMAGE_SIZE[1], IMAGE_SIZE[0]), 200, np.uint8))

    detections = detect_corners([*paths, blank], PATTERN, expected_size=IMAGE_SIZE)

    assert blank in detections.rejected
    assert len(detections.corners) >= 10

    result = calibrate(detections, SQUARE_MM, PATTERN, min_views=10)

    assert result.rms_px < 0.3
    assert result.camera_matrix[0, 0] == pytest.approx(500, rel=0.02)
    assert result.camera_matrix[1, 1] == pytest.approx(500, rel=0.02)
    assert result.camera_matrix[0, 2] == pytest.approx(320, abs=10)
    assert result.camera_matrix[1, 2] == pytest.approx(240, abs=10)
    assert len(result.per_view_errors_px) == len(detections.corners)

    saved = save_calibration(result, tmp_path / "calib" / "calibration.json")
    k, dist, size = load_calibration(saved)
    assert np.allclose(k, result.camera_matrix)
    assert np.allclose(dist, result.dist_coeffs)
    assert size == IMAGE_SIZE


def test_calibrate_requires_min_views(tmp_path):
    detections = detect_corners(_render_views(tmp_path, n_views=3), PATTERN)
    with pytest.raises(ValueError):
        calibrate(detections, SQUARE_MM, PATTERN, min_views=15)


def test_detect_corners_rejects_unexpected_size(tmp_path):
    path = tmp_path / "landscape.png"
    cv2.imwrite(str(path), np.full((300, 400), 255, np.uint8))
    with pytest.raises(ValueError, match="horizontal"):
        detect_corners([path], PATTERN, expected_size=(300, 400))
