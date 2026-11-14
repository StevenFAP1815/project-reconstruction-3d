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


def enhance_contrast(
    image_path: str | Path,
    output_path: str | Path,
    clip_limit: float = 2.0,
    tile_grid: int = 8,
) -> Path:
    """Mejora el contraste de una foto oscura con CLAHE y la guarda.

    CLAHE (Contrast Limited Adaptive Histogram Equalization) ecualiza el
    histograma por zonas (`tile_grid` x `tile_grid`), de modo que aclara las
    regiones oscuras sin quemar las claras. Se aplica solo a la luminosidad
    (canal L del espacio de color LAB), para no alterar los colores.

    En fotos subexpuestas, SIFT encuentra más puntos tras este paso porque sus
    umbrales dependen del contraste local.
    """
    image = cv2.imread(str(image_path), cv2.IMREAD_COLOR)
    if image is None:
        raise ValueError(f"No se pudo leer la imagen: {image_path}")
    lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
    clahe = cv2.createCLAHE(clipLimit=clip_limit, tileGridSize=(tile_grid, tile_grid))
    lab[:, :, 0] = clahe.apply(lab[:, :, 0])
    enhanced = cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)

    target = Path(output_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    if not cv2.imwrite(str(target), enhanced, [cv2.IMWRITE_JPEG_QUALITY, 95]):
        raise ValueError(f"No se pudo escribir la imagen: {target}")
    return target


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
