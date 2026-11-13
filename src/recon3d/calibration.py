"""Calibración de la cámara con un tablero de ajedrez (OpenCV).

Modelo pinhole: un punto 3D (X, Y, Z) en coordenadas de la cámara se proyecta
en el píxel (u, v) mediante la matriz de intrínsecos K:

        | fx  0  cx |
    K = |  0 fy  cy |      u = fx · X/Z + cx,   v = fy · Y/Z + cy
        |  0  0   1 |

fx, fy son la focal expresada en píxeles y (cx, cy) el centro óptico. La lente
real además curva la imagen; esa distorsión se modela con los coeficientes
(k1, k2, p1, p2, k3).

La calibración fotografía un tablero cuyas esquinas tienen posiciones 3D
conocidas (en mm, sobre un plano) y busca K y la distorsión que mejor explican
dónde aparecen esas esquinas en cada foto.
"""

import json
from dataclasses import dataclass, field
from pathlib import Path

import cv2
import numpy as np

# Esquinas internas del tablero (columnas, filas): 10 x 7 cuadros -> 9 x 6.
DEFAULT_PATTERN = (9, 6)

# Diagonal del fotograma de 35 mm (36 x 24 mm), usada para convertir la
# "focal equivalente" del EXIF a píxeles.
_FULL_FRAME_DIAGONAL_MM = float(np.hypot(36.0, 24.0))

# Detector "SB" (sector-based): más robusto y preciso que el clásico
# findChessboardCorners, y ya devuelve las esquinas con precisión subpíxel.
_SB_FLAGS = cv2.CALIB_CB_NORMALIZE_IMAGE | cv2.CALIB_CB_ACCURACY


def board_object_points(
    square_mm: float, pattern_size: tuple[int, int] = DEFAULT_PATTERN
) -> np.ndarray:
    """Coordenadas 3D (mm) de las esquinas internas, en el plano Z = 0.

    El orden coincide con el de OpenCV: fila a fila, columna más rápida.
    """
    if square_mm <= 0:
        raise ValueError(f"square_mm debe ser positivo: {square_mm}")
    cols, rows = pattern_size
    points = np.zeros((cols * rows, 3), np.float32)
    points[:, :2] = np.mgrid[0:cols, 0:rows].T.reshape(-1, 2) * square_mm
    return points


def focal_px_from_35mm(focal_35mm: float, image_size: tuple[int, int]) -> float:
    """Focal aproximada en píxeles a partir de la focal equivalente del EXIF.

    Sirve como comprobación de orden de magnitud del fx calibrado.
    """
    width, height = image_size
    return focal_35mm * float(np.hypot(width, height)) / _FULL_FRAME_DIAGONAL_MM


@dataclass
class Detections:
    """Resultado de buscar el tablero en un conjunto de fotos."""

    image_size: tuple[int, int]  # (ancho, alto) en píxeles
    image_paths: list[Path] = field(default_factory=list)
    corners: list[np.ndarray] = field(default_factory=list)  # (N, 2) por foto
    rejected: list[Path] = field(default_factory=list)


def detect_corners(
    image_paths: list[Path],
    pattern_size: tuple[int, int] = DEFAULT_PATTERN,
    expected_size: tuple[int, int] | None = None,
) -> Detections:
    """Busca las esquinas del tablero en cada foto.

    Las fotos donde no se encuentra el tablero completo se guardan en
    `rejected` (no es un error: es normal descartar algunas).

    Raises:
        ValueError: si una foto no se puede leer o si las fotos no tienen
            todas el mismo tamaño (o no coinciden con `expected_size`).
    """
    detections = None
    for path in image_paths:
        gray = cv2.imread(str(path), cv2.IMREAD_GRAYSCALE)
        if gray is None:
            raise ValueError(f"No se pudo leer la imagen: {path}")

        size = (gray.shape[1], gray.shape[0])
        if expected_size is not None and size != tuple(expected_size):
            raise ValueError(
                f"{Path(path).name} mide {size[0]}x{size[1]} px y se esperaba "
                f"{expected_size[0]}x{expected_size[1]}. ¿Foto en horizontal?"
            )
        if detections is None:
            detections = Detections(image_size=size)
        elif size != detections.image_size:
            raise ValueError(
                f"{Path(path).name} mide {size[0]}x{size[1]} px, distinto del resto"
            )

        found, corners = cv2.findChessboardCornersSB(gray, pattern_size, flags=_SB_FLAGS)
        if found:
            detections.image_paths.append(Path(path))
            detections.corners.append(corners.reshape(-1, 2).astype(np.float32))
        else:
            detections.rejected.append(Path(path))

    if detections is None:
        raise ValueError("No se recibió ninguna imagen")
    return detections


@dataclass
class CalibrationResult:
    camera_matrix: np.ndarray  # K, 3x3
    dist_coeffs: np.ndarray  # (k1, k2, p1, p2, k3)
    rms_px: float  # error de reproyección global (RMS)
    per_view_errors_px: list[float]  # error RMS de cada foto
    image_size: tuple[int, int]
    pattern_size: tuple[int, int]
    square_mm: float
    image_names: list[str]

    def to_dict(self) -> dict:
        k = self.camera_matrix
        return {
            "image_size": list(self.image_size),
            "pattern_size": list(self.pattern_size),
            "square_mm": self.square_mm,
            "n_views": len(self.image_names),
            "rms_px": round(self.rms_px, 4),
            "fx": float(k[0, 0]),
            "fy": float(k[1, 1]),
            "cx": float(k[0, 2]),
            "cy": float(k[1, 2]),
            "camera_matrix": k.tolist(),
            "dist_coeffs": self.dist_coeffs.ravel().tolist(),
            "per_view_errors_px": {
                name: round(err, 4)
                for name, err in zip(self.image_names, self.per_view_errors_px)
            },
        }


def calibrate(
    detections: Detections,
    square_mm: float,
    pattern_size: tuple[int, int] = DEFAULT_PATTERN,
    min_views: int = 15,
) -> CalibrationResult:
    """Calibra la cámara con las esquinas detectadas.

    `min_views=15` es el mínimo que exige la rúbrica.

    Raises:
        ValueError: si hay menos vistas válidas que `min_views`.
    """
    n_views = len(detections.corners)
    if n_views < min_views:
        raise ValueError(
            f"Solo hay {n_views} fotos con el tablero detectado; se necesitan "
            f"al menos {min_views}."
        )

    board = board_object_points(square_mm, pattern_size)
    object_points = [board] * n_views
    rms, camera_matrix, dist_coeffs, rvecs, tvecs = cv2.calibrateCamera(
        object_points, detections.corners, detections.image_size, None, None
    )

    per_view = []
    for corners, rvec, tvec in zip(detections.corners, rvecs, tvecs):
        projected, _ = cv2.projectPoints(board, rvec, tvec, camera_matrix, dist_coeffs)
        diff = projected.reshape(-1, 2) - corners
        per_view.append(float(np.sqrt(np.mean(np.sum(diff**2, axis=1)))))

    return CalibrationResult(
        camera_matrix=camera_matrix,
        dist_coeffs=dist_coeffs.ravel(),
        rms_px=float(rms),
        per_view_errors_px=per_view,
        image_size=detections.image_size,
        pattern_size=tuple(pattern_size),
        square_mm=square_mm,
        image_names=[path.name for path in detections.image_paths],
    )


def save_calibration(result: CalibrationResult, path: str | Path) -> Path:
    """Guarda la calibración como JSON legible y devuelve su ruta."""
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        json.dumps(result.to_dict(), indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return target


def load_calibration(path: str | Path) -> tuple[np.ndarray, np.ndarray, tuple[int, int]]:
    """Lee un JSON de `save_calibration`: devuelve (K, distorsión, tamaño)."""
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    return (
        np.array(data["camera_matrix"], dtype=np.float64),
        np.array(data["dist_coeffs"], dtype=np.float64),
        tuple(data["image_size"]),
    )
