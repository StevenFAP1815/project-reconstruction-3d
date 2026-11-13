"""Preprocesamiento: detección de fotos borrosas (criterio 4 de la rúbrica).

La **varianza del Laplaciano** mide cuántos bordes nítidos tiene una imagen:
el Laplaciano resalta los cambios bruscos de intensidad y, en una foto movida o
desenfocada, esos cambios se suavizan y la varianza baja.

El valor absoluto depende de la escena (un objeto con mucha textura da valores
más altos), así que el umbral se fija **relativo a la mediana** del propio
objeto: se marca como borrosa una foto mucho menos nítida que sus vecinas.
"""

from pathlib import Path
from statistics import median

import cv2


def laplacian_variance(image_path: str | Path, max_side: int = 1024) -> float:
    """Varianza del Laplaciano de una foto, reducida a `max_side` px de lado.

    Reducir la imagen hace el cálculo rápido y comparable entre fotos del
    mismo tamaño original.
    """
    gray = cv2.imread(str(image_path), cv2.IMREAD_GRAYSCALE)
    if gray is None:
        raise ValueError(f"No se pudo leer la imagen: {image_path}")
    scale = max_side / max(gray.shape)
    if scale < 1:
        gray = cv2.resize(gray, None, fx=scale, fy=scale, interpolation=cv2.INTER_AREA)
    return float(cv2.Laplacian(gray, cv2.CV_64F).var())


def flag_blurry(scores: dict[str, float], ratio: float = 0.35) -> list[str]:
    """Nombres cuya nitidez es menor que `ratio` × mediana del conjunto.

    Args:
        scores: nitidez por nombre de imagen (de `laplacian_variance`).
        ratio: fracción de la mediana por debajo de la cual una foto se
            considera borrosa. 0.35 = "menos de un tercio de lo habitual".
    """
    if not 0 < ratio < 1:
        raise ValueError(f"ratio debe estar entre 0 y 1: {ratio}")
    if not scores:
        return []
    threshold = ratio * median(scores.values())
    return sorted(name for name, score in scores.items() if score < threshold)
