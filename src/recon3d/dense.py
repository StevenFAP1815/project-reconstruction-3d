"""Reconstrucción densa (MVS) y malla con COLMAP (pycolmap 4.x).

Etapas (ver `run_mvs` y `poisson_mesh`):

1. Corrección de distorsión: COLMAP reproyecta cada foto a un modelo pinhole
   ideal (sin distorsión), que es lo que asume el estéreo multivista.
2. PatchMatch Stereo: para cada píxel de cada foto estima una profundidad y una
   normal comparando pequeñas ventanas con las fotos vecinas. Con
   `geom_consistency` exige además que las profundidades de fotos distintas
   sean coherentes entre sí. Requiere GPU (CUDA).
3. Fusión: combina los mapas de profundidad en una única nube densa, con
   normal y color por punto, aceptando solo los puntos que varias fotos
   confirman.
4. Malla de Poisson: ajusta una superficie cerrada y suave a los puntos
   orientados (con normal).

Requiere pycolmap con CUDA, que solo se instala en Colab (requirements-colab.txt).
"""

import shutil
import time
from pathlib import Path

import numpy as np

from recon3d.sfm import camera_pose, set_options

try:
    import pycolmap
except ImportError:  # p. ej. en la CI
    pycolmap = None


def _options(*class_names: str):
    """Crea el objeto de opciones con el primer nombre de clase que exista.

    Algunas clases de opciones se renombraron entre versiones de pycolmap.
    """
    for name in class_names:
        if hasattr(pycolmap, name):
            return getattr(pycolmap, name)()
    raise AttributeError(f"Esta versión de pycolmap no tiene {class_names}")


def run_mvs(
    sparse_dir: str | Path,
    image_dir: str | Path,
    work_dir: str | Path,
    *,
    max_image_size: int = 1600,
    patch_match_options: dict | None = None,
    fusion_options: dict | None = None,
    report: dict | None = None,
) -> tuple[Path, dict]:
    """Ejecuta corrección de distorsión, PatchMatch y fusión. Devuelve (fused.ply, tiempos).

    Args:
        sparse_dir: modelo disperso de COLMAP (cameras/images/points3D).
        image_dir: fotos originales, con los mismos nombres que en el modelo.
        max_image_size: lado máximo (px) con el que trabaja MVS. Menos píxeles
            = más rápido y menos memoria, a costa de detalle fino.
        patch_match_options / fusion_options: opciones extra de pycolmap, p. ej.
            {"window_radius": 7} o {"min_num_pixels": 5}.
        report: diccionario opcional donde se anotan las opciones no reconocidas.
    """
    work = Path(work_dir)
    shutil.rmtree(work, ignore_errors=True)  # cada corrida empieza limpia
    work.mkdir(parents=True)
    ignored, timings = [], {}

    undistort = _options("UndistortCameraOptions")
    ignored += [f"undistort.{n}" for n in set_options(undistort, {"max_image_size": max_image_size})]
    start = time.perf_counter()
    pycolmap.undistort_images(work, sparse_dir, image_dir, undistort_options=undistort)
    timings["undistort_s"] = time.perf_counter() - start

    patch_match = _options("PatchMatchOptions", "PatchMatchStereoOptions")
    values = {"max_image_size": max_image_size, "geom_consistency": True, **(patch_match_options or {})}
    ignored += [f"patch_match.{n}" for n in set_options(patch_match, values)]
    start = time.perf_counter()
    pycolmap.patch_match_stereo(work, options=patch_match)
    timings["patch_match_s"] = time.perf_counter() - start

    fusion = _options("StereoFusionOptions")
    values = {"max_image_size": max_image_size, **(fusion_options or {})}
    ignored += [f"fusion.{n}" for n in set_options(fusion, values)]
    fused = work / "fused.ply"
    start = time.perf_counter()
    rec = pycolmap.stereo_fusion(fused, work, options=fusion)
    if not fused.exists():  # versiones que solo devuelven la reconstrucción
        rec.export_PLY(str(fused))
    timings["fusion_s"] = time.perf_counter() - start
    timings["total_s"] = sum(timings.values())

    if report is not None:
        report["ignored_options"] = ignored
    return fused, timings


def poisson_mesh(input_ply: str | Path, output_ply: str | Path, *, options: dict | None = None,
                 report: dict | None = None) -> Path:
    """Malla de Poisson de COLMAP a partir de una nube con normales.

    Opciones habituales: `depth` (profundidad del octree: más = más detalle y
    más ruido) y `trim` (recorta las zonas de la superficie con poca densidad de
    puntos, es decir, inventadas por la interpolación).
    """
    poisson = _options("PoissonMeshingOptions")
    ignored = set_options(poisson, options)
    if report is not None:
        report["ignored_options"] = ignored
    pycolmap.poisson_meshing(Path(input_ply), Path(output_ply), options=poisson)
    return Path(output_ply)


def read_colmap_array(path: str | Path) -> np.ndarray:
    """Lee un mapa de profundidad o de normales de COLMAP (`.bin` de stereo/).

    El archivo empieza con el texto "ancho&alto&canales&" y sigue con los
    valores float32 en orden de columnas (el mismo formato que usa el lector
    oficial `read_write_dense.py` de COLMAP).
    """
    with open(path, "rb") as file:
        header = b""
        while header.count(b"&") < 3:
            char = file.read(1)
            if not char:
                raise ValueError(f"Cabecera incompleta en {path}")
            header += char
        width, height, channels = (int(v) for v in header.split(b"&")[:3])
        data = np.fromfile(file, dtype=np.float32)
    if data.size != width * height * channels:
        raise ValueError(f"{path}: se esperaban {width * height * channels} valores y hay {data.size}")
    array = data.reshape((width, height, channels), order="F")
    return np.transpose(array, (1, 0, 2)).squeeze()


def viewing_directions(rec: "pycolmap.Reconstruction") -> tuple[np.ndarray, np.ndarray]:
    """Centros ópticos y direcciones de mirada (eje z de cada cámara) en el mundo."""
    centers, directions = [], []
    for image in sorted(rec.images.values(), key=lambda img: img.name):
        if hasattr(image, "has_pose") and not image.has_pose:
            continue
        rotation, translation = camera_pose(image)
        centers.append(-rotation.T @ translation)
        directions.append(rotation.T @ np.array([0.0, 0.0, 1.0]))
    return np.array(centers), np.array(directions)
