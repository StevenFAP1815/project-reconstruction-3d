"""Utilidades geométricas: geometría epipolar y trayectoria de la cámara."""

import numpy as np


def epipolar_distances(points1: np.ndarray, points2: np.ndarray, fundamental: np.ndarray) -> np.ndarray:
    """Distancia (px) de cada punto de la imagen 2 a su línea epipolar.

    La restricción epipolar dice que si x1 y x2 son el mismo punto 3D visto en
    dos fotos, entonces x2ᵀ F x1 = 0: x2 está sobre la recta l2 = F x1. Esta
    función mide cuánto se aleja x2 de esa recta; en un par bien estimado los
    inliers quedan a menos de 1-2 px.
    """
    ones = np.ones((len(points1), 1))
    x1 = np.hstack([points1, ones])
    x2 = np.hstack([points2, ones])
    lines = x1 @ fundamental.T  # cada fila: (a, b, c) de la recta a·u + b·v + c = 0
    numerator = np.abs(np.sum(lines * x2, axis=1))
    return numerator / np.hypot(lines[:, 0], lines[:, 1])


def viewing_angle_steps(directions: np.ndarray) -> np.ndarray:
    """Ángulo (grados) entre las direcciones de mirada de fotos consecutivas."""
    d = np.asarray(directions, dtype=float)
    d = d / np.linalg.norm(d, axis=1, keepdims=True)
    cosines = np.clip(np.sum(d[1:] * d[:-1], axis=1), -1.0, 1.0)
    return np.degrees(np.arccos(cosines))


def overlap_from_step(step_deg: np.ndarray | float, fov_deg: float) -> np.ndarray | float:
    """Solapamiento aproximado entre dos fotos que giran `step_deg` grados.

    Al girar alrededor del objeto mirando a su centro, la parte compartida del
    campo de visión es aproximadamente 1 - giro / campo de visión. Es una
    estimación geométrica sencilla (ignora la distancia y la forma del objeto).
    """
    return np.clip(1.0 - np.asarray(step_deg, dtype=float) / fov_deg, 0.0, 1.0)


def trajectory_frame(centers: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Expresa los centros de cámara en un sistema "horizontal + vertical".

    SfM devuelve la escena con una orientación arbitraria. Como la captura se
    hizo en órbitas aproximadamente horizontales, la dirección en la que los
    centros de cámara varían **menos** es la vertical. El análisis de
    componentes principales (PCA) encuentra esas direcciones.

    Returns:
        coords: (N, 3) centros centrados; columnas 0 y 1 = plano de las órbitas
            (vista desde arriba), columna 2 = altura.
        axes: (3, 3) ejes usados, uno por fila, en coordenadas de SfM.
    """
    centers = np.asarray(centers, dtype=float)
    if centers.ndim != 2 or centers.shape[1] != 3 or len(centers) < 3:
        raise ValueError("Se necesitan al menos 3 centros de cámara con forma (N, 3)")
    centered = centers - centers.mean(axis=0)
    # Filas de vt ordenadas de mayor a menor varianza: la última es la vertical.
    _, _, vt = np.linalg.svd(centered, full_matrices=False)
    axes = vt.copy()
    if np.linalg.det(axes) < 0:  # mantener un sistema de mano derecha
        axes[2] *= -1
    return centered @ axes.T, axes
