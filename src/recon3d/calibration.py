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
# findChessboardCorners. EXHAUSTIVE amplía la búsqueda (más lento, más fiable).
_SB_FLAGS = cv2.CALIB_CB_NORMALIZE_IMAGE | cv2.CALIB_CB_EXHAUSTIVE | cv2.CALIB_CB_ACCURACY
_CLASSIC_FLAGS = cv2.CALIB_CB_ADAPTIVE_THRESH | cv2.CALIB_CB_NORMALIZE_IMAGE

# Lado máximo (px) de la imagen reducida en la que se busca el tablero primero.
# A 12 MP la cámara capta la rejilla de píxeles del monitor (moiré), que
# confunde al detector; en la imagen reducida ese patrón desaparece.
DETECTION_MAX_SIDE = 2000

_SUBPIX_CRITERIA = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 50, 0.01)

# Suavizado gaussiano (sigma en px) aplicado a la foto completa antes del
# refinamiento subpíxel, para atenuar el moiré sin desplazar las esquinas.
# Solo se aplica cuando la foto es mayor que DETECTION_MAX_SIDE.
REFINE_BLUR_SIGMA = 1.5


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


def _refine_corners(
    gray: np.ndarray,
    corners: np.ndarray,
    pattern_size: tuple[int, int],
    blur_sigma: float = 0.0,
) -> np.ndarray:
    """Ajusta las esquinas con precisión subpíxel sobre la imagen completa.

    La ventana de búsqueda se adapta al tamaño de los cuadros en la foto
    (~20 % del lado de un cuadro), para no "saltar" a una esquina vecina.
    Con `blur_sigma > 0` se suaviza antes la imagen: el suavizado gaussiano es
    simétrico, así que atenúa el moiré sin mover la posición de las esquinas.
    """
    if blur_sigma > 0:
        gray = cv2.GaussianBlur(gray, (0, 0), sigmaX=blur_sigma)
    cols, rows = pattern_size
    grid = corners.reshape(rows, cols, 2)
    spacing = float(np.median(np.linalg.norm(np.diff(grid, axis=1), axis=2)))
    half_window = int(np.clip(0.2 * spacing, 3, 30))
    refined = cv2.cornerSubPix(
        gray,
        corners.reshape(-1, 1, 2).astype(np.float32),
        (half_window, half_window),
        (-1, -1),
        _SUBPIX_CRITERIA,
    )
    return refined.reshape(-1, 2)


def find_corners(
    gray: np.ndarray,
    pattern_size: tuple[int, int] = DEFAULT_PATTERN,
    max_side: int = DETECTION_MAX_SIDE,
) -> tuple[np.ndarray | None, str | None]:
    """Busca el tablero con varios intentos, del más fiable al último recurso.

    1. Detector SB sobre la imagen reducida a `max_side`.
    2. Detector SB sobre la imagen completa.
    3. Detector clásico sobre la imagen reducida.

    Las esquinas encontradas se escalan a la resolución original y se refinan
    allí con precisión subpíxel.

    Returns:
        (esquinas (N, 2), nombre del intento que funcionó) o (None, None).
    """
    scale = min(1.0, max_side / max(gray.shape))
    small = gray
    if scale < 1:
        small = cv2.resize(gray, None, fx=scale, fy=scale, interpolation=cv2.INTER_AREA)

    attempts = [("sb_reduced", small, scale, "sb")]
    if scale < 1:
        attempts.append(("sb_full", gray, 1.0, "sb"))
    attempts.append(("classic_reduced", small, scale, "classic"))

    for label, image, image_scale, kind in attempts:
        if kind == "sb":
            found, corners = cv2.findChessboardCornersSB(image, pattern_size, flags=_SB_FLAGS)
        else:
            found, corners = cv2.findChessboardCorners(image, pattern_size, flags=_CLASSIC_FLAGS)
        if found:
            # Convención de cv2.resize: el centro del píxel x de la imagen
            # reducida corresponde a (x + 0.5) / escala - 0.5 en la original.
            corners = (corners.reshape(-1, 2) + 0.5) / image_scale - 0.5
            blur = REFINE_BLUR_SIGMA if scale < 1 else 0.0
            return _refine_corners(gray, corners, pattern_size, blur).astype(np.float32), label
    return None, None


@dataclass
class Detections:
    """Resultado de buscar el tablero en un conjunto de fotos."""

    image_size: tuple[int, int]  # (ancho, alto) en píxeles
    image_paths: list[Path] = field(default_factory=list)
    corners: list[np.ndarray] = field(default_factory=list)  # (N, 2) por foto
    methods: list[str] = field(default_factory=list)  # intento que funcionó, por foto
    rejected: list[Path] = field(default_factory=list)


def detect_corners(
    image_paths: list[Path],
    pattern_size: tuple[int, int] = DEFAULT_PATTERN,
    expected_size: tuple[int, int] | None = None,
    max_side: int = DETECTION_MAX_SIDE,
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

        corners, method = find_corners(gray, pattern_size, max_side=max_side)
        if corners is not None:
            detections.image_paths.append(Path(path))
            detections.corners.append(corners)
            detections.methods.append(method)
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
    excluded_views: dict[str, float] = field(default_factory=dict)  # nombre -> error (px)
    fix_k3: bool = False
    outlier_ratio: float | None = None

    def to_dict(self) -> dict:
        k = self.camera_matrix
        return {
            "image_size": list(self.image_size),
            "pattern_size": list(self.pattern_size),
            "square_mm": self.square_mm,
            "n_views": len(self.image_names),
            "fix_k3": self.fix_k3,
            "outlier_ratio": self.outlier_ratio,
            "excluded_views": {name: round(err, 4) for name, err in self.excluded_views.items()},
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


def _calibrate_once(board, corners_list, image_size, flags):
    """Una pasada de calibrateCamera más el error RMS de cada vista."""
    object_points = [board] * len(corners_list)
    rms, camera_matrix, dist_coeffs, rvecs, tvecs = cv2.calibrateCamera(
        object_points, corners_list, image_size, None, None, flags=flags
    )
    per_view = []
    for corners, rvec, tvec in zip(corners_list, rvecs, tvecs):
        projected, _ = cv2.projectPoints(board, rvec, tvec, camera_matrix, dist_coeffs)
        diff = projected.reshape(-1, 2) - corners
        per_view.append(float(np.sqrt(np.mean(np.sum(diff**2, axis=1)))))
    return float(rms), camera_matrix, dist_coeffs.ravel(), per_view


def calibrate(
    detections: Detections,
    square_mm: float,
    pattern_size: tuple[int, int] = DEFAULT_PATTERN,
    min_views: int = 15,
    fix_k3: bool = True,
    outlier_ratio: float | None = 2.0,
) -> CalibrationResult:
    """Calibra la cámara con las esquinas detectadas.

    Args:
        min_views: mínimo de vistas válidas; 15 es lo que exige la rúbrica.
        fix_k3: fija k3 = 0. Con poca cobertura de los bordes del encuadre,
            k1, k2 y k3 tienden a tomar valores grandes que se compensan entre
            sí (sobreajuste); un modelo con menos parámetros es más estable.
        outlier_ratio: si no es None, tras una primera calibración se excluyen
            las vistas cuyo error supera `outlier_ratio` × la mediana y se
            recalibra una vez (solo si siguen quedando `min_views` vistas).

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
    flags = cv2.CALIB_FIX_K3 if fix_k3 else 0
    names = [path.name for path in detections.image_paths]
    corners_list = list(detections.corners)

    rms, camera_matrix, dist_coeffs, per_view = _calibrate_once(
        board, corners_list, detections.image_size, flags
    )

    excluded = {}
    if outlier_ratio is not None:
        limit = outlier_ratio * float(np.median(per_view))
        keep = [i for i, err in enumerate(per_view) if err <= limit]
        if len(keep) < n_views and len(keep) >= min_views:
            excluded = {names[i]: per_view[i] for i in range(n_views) if i not in keep}
            names = [names[i] for i in keep]
            corners_list = [corners_list[i] for i in keep]
            rms, camera_matrix, dist_coeffs, per_view = _calibrate_once(
                board, corners_list, detections.image_size, flags
            )

    return CalibrationResult(
        camera_matrix=camera_matrix,
        dist_coeffs=dist_coeffs,
        rms_px=rms,
        per_view_errors_px=per_view,
        image_size=detections.image_size,
        pattern_size=tuple(pattern_size),
        square_mm=square_mm,
        image_names=names,
        excluded_views=excluded,
        fix_k3=fix_k3,
        outlier_ratio=outlier_ratio,
    )


def colmap_camera_from_calibration(path: str | Path) -> tuple[str, list[float]]:
    """Modelo y parámetros de cámara de COLMAP a partir de `calibration.json`.

    - Si k3 = 0 (calibración v2), el modelo `OPENCV` de COLMAP
      (fx, fy, cx, cy, k1, k2, p1, p2) coincide exactamente con OpenCV.
    - Si k3 ≠ 0, se usa `FULL_OPENCV`, que añade k3..k6 (k4..k6 = 0).
    """
    camera_matrix, dist, _ = load_calibration(path)
    fx, fy = camera_matrix[0, 0], camera_matrix[1, 1]
    cx, cy = camera_matrix[0, 2], camera_matrix[1, 2]
    k1, k2, p1, p2, k3 = (list(dist) + [0.0] * 5)[:5]
    params = [fx, fy, cx, cy, k1, k2, p1, p2]
    if k3 == 0:
        return "OPENCV", [float(v) for v in params]
    return "FULL_OPENCV", [float(v) for v in params + [k3, 0.0, 0.0, 0.0]]


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
