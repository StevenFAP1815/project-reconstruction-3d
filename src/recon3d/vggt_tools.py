"""Utilidades para el método de IA (VGGT), en NumPy y sin depender de torch.

VGGT (Visual Geometry Grounded Transformer, Wang et al., CVPR 2025) es una red
que recibe un conjunto de fotos y predice, en una sola pasada y sin optimización
iterativa, la cámara de cada foto (extrínsecos e intrínsecos), un mapa de
profundidad por foto y la confianza de cada píxel. No usa puntos SIFT ni
emparejamiento explícito: el transformer compara todas las fotos entre sí con
mecanismos de atención aprendidos con millones de escenas.

Este módulo contiene la parte geométrica del uso de sus predicciones, que se
puede probar en la CI.
"""

import numpy as np


def select_frames(items: list, n: int) -> list:
    """Elige `n` elementos repartidos de forma uniforme (conserva el orden).

    Las fotos están ordenadas por hora de captura, así que tomar una de cada k
    mantiene la cobertura de todas las órbitas alrededor del objeto.
    """
    if n >= len(items):
        return list(items)
    indices = np.round(np.linspace(0, len(items) - 1, n)).astype(int)
    return [items[i] for i in indices]


def camera_rays(extrinsics: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Centros ópticos y direcciones de mirada a partir de extrínsecos (S, 3, 4).

    Convención de OpenCV (la de VGGT y COLMAP): x_cam = R x_mundo + t. El centro
    es C = -Rᵀ t y la dirección de mirada es el eje z de la cámara en el mundo,
    Rᵀ (0, 0, 1).
    """
    extrinsics = np.asarray(extrinsics, dtype=float)
    rotations, translations = extrinsics[:, :, :3], extrinsics[:, :, 3]
    centers = -np.einsum("sji,sj->si", rotations, translations)
    directions = rotations[:, 2, :]
    return centers, directions


def unproject_depth(depth: np.ndarray, extrinsics: np.ndarray, intrinsics: np.ndarray) -> np.ndarray:
    """Pasa mapas de profundidad (S, H, W) a puntos 3D en el mundo (S, H, W, 3).

    Para cada píxel (u, v) con profundidad d: punto en la cámara
    X_cam = d · K⁻¹ (u, v, 1); en el mundo X = Rᵀ (X_cam - t).
    """
    depth = np.asarray(depth, dtype=float)
    if depth.ndim == 4:
        depth = depth[..., 0]
    n, height, width = depth.shape
    u, v = np.meshgrid(np.arange(width), np.arange(height))
    pixels = np.stack([u, v, np.ones_like(u)], axis=-1).astype(float)  # (H, W, 3)
    points = np.empty((n, height, width, 3))
    for i in range(n):
        rays = pixels @ np.linalg.inv(intrinsics[i]).T
        cam = rays * depth[i][..., None]
        rotation, translation = extrinsics[i][:, :3], extrinsics[i][:, 3]
        points[i] = (cam - translation) @ rotation
    return points


def confidence_mask(confidence: np.ndarray, percentile: float) -> np.ndarray:
    """Máscara de los píxeles con confianza por encima del percentil dado.

    VGGT asigna a cada píxel una confianza; los píxeles de fondo liso, reflejos
    o bordes suelen tener confianza baja. Se descarta el `percentile` % menos
    fiable (la demo oficial de VGGT usa 50 %).
    """
    confidence = np.asarray(confidence, dtype=float)
    return confidence > np.percentile(confidence, percentile)


def content_box(original_size: tuple[int, int], target: int = 518) -> tuple[int, int, int, int]:
    """Zona de la imagen real dentro de la imagen cuadrada de VGGT (modo "pad").

    `load_and_preprocess_images(..., mode="pad")` escala la foto para que su
    lado mayor mida `target` px, redondea el otro lado a un múltiplo de 14 y
    rellena con blanco hasta un cuadrado `target` × `target`, centrando la foto.

    Args:
        original_size: (ancho, alto) de la foto original.

    Returns:
        (x0, y0, ancho, alto) de la foto dentro del cuadrado.
    """
    width, height = original_size
    if width >= height:
        new_w = target
        new_h = int(round(height * (target / width) / 14) * 14)
    else:
        new_h = target
        new_w = int(round(width * (target / height) / 14) * 14)
    return (target - new_w) // 2, (target - new_h) // 2, new_w, new_h


def expected_focal(calibrated: tuple[float, float], original_size: tuple[int, int],
                   target: int = 518) -> tuple[float, float]:
    """Focal (fx, fy) de la calibración expresada en la resolución de VGGT."""
    _, _, new_w, new_h = content_box(original_size, target)
    width, height = original_size
    return calibrated[0] * new_w / width, calibrated[1] * new_h / height
