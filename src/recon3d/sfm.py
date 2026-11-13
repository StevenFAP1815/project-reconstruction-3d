"""Structure from Motion incremental con COLMAP (pycolmap 4.x).

Etapas (ver `run_sfm`):

1. Extracción: SIFT detecta puntos característicos en cada foto y les asigna
   un descriptor de 128 valores.
2. Emparejamiento: compara descriptores entre pares de fotos y verifica
   geométricamente las correspondencias con RANSAC (matrices F, E u H).
3. Mapeo incremental: elige un par inicial, registra nuevas fotos por PnP,
   triangula puntos 3D y refina todo con bundle adjustment.

Requiere pycolmap, que solo se instala en Colab (requirements-colab.txt).
"""

import shutil
import time
from pathlib import Path

import numpy as np
import pycolmap


def run_sfm(
    image_dir: str | Path,
    work_dir: str | Path,
    *,
    max_features: int = 8192,
    camera_model: str = "SIMPLE_RADIAL",
    camera_params: list[float] | None = None,
    refine_intrinsics: bool = True,
) -> tuple["pycolmap.Reconstruction", dict, int]:
    """Ejecuta el pipeline completo y devuelve (reconstrucción, tiempos, n.º de modelos).

    Todas las fotos comparten una única cámara (`CameraMode.SINGLE`), porque se
    tomaron con el mismo teléfono, la misma lente y el mismo enfoque.

    Args:
        camera_model: modelo de cámara de COLMAP. "SIMPLE_RADIAL" (f, cx, cy, k)
            para autocalibración; "FULL_OPENCV" para usar la calibración.
        camera_params: intrínsecos iniciales en el orden del modelo. None =
            COLMAP los estima a partir del EXIF y de las propias fotos.
        refine_intrinsics: False = mantener fijos los intrínsecos dados.

    Raises:
        RuntimeError: si COLMAP no logra iniciar ninguna reconstrucción.
    """
    work = Path(work_dir)
    shutil.rmtree(work, ignore_errors=True)  # cada corrida empieza limpia
    (work / "sparse").mkdir(parents=True)
    database = work / "database.db"
    device = pycolmap.Device.auto

    reader = pycolmap.ImageReaderOptions()
    reader.camera_model = camera_model
    if camera_params is not None:
        reader.camera_params = ",".join(f"{value:.10g}" for value in camera_params)
    extraction = pycolmap.FeatureExtractionOptions()
    extraction.sift.max_num_features = max_features

    timings = {}
    start = time.perf_counter()
    pycolmap.extract_features(
        database,
        image_dir,
        camera_mode=pycolmap.CameraMode.SINGLE,
        reader_options=reader,
        extraction_options=extraction,
        device=device,
    )
    timings["extraction_s"] = time.perf_counter() - start

    start = time.perf_counter()
    pycolmap.match_exhaustive(database, device=device)
    timings["matching_s"] = time.perf_counter() - start

    options = pycolmap.IncrementalPipelineOptions()
    if not refine_intrinsics:
        options.ba_refine_focal_length = False
        options.ba_refine_principal_point = False
        options.ba_refine_extra_params = False

    start = time.perf_counter()
    models = pycolmap.incremental_mapping(database, image_dir, work / "sparse", options=options)
    timings["mapping_s"] = time.perf_counter() - start
    timings["total_s"] = sum(timings.values())

    if not models:
        raise RuntimeError("COLMAP no pudo iniciar ninguna reconstrucción")
    best = max(models.values(), key=lambda rec: rec.num_reg_images())
    return best, timings, len(models)


def sfm_stats(rec: "pycolmap.Reconstruction", n_images: int) -> dict:
    """Métricas de la rúbrica (criterio 5) para una reconstrucción."""
    registered = rec.num_reg_images()
    return {
        "n_images": n_images,
        "n_registered": registered,
        "registered_pct": round(100.0 * registered / n_images, 2),
        "n_points3d": rec.num_points3D(),
        "mean_track_length": round(rec.compute_mean_track_length(), 3),
        "mean_reprojection_error_px": round(rec.compute_mean_reprojection_error(), 4),
        "mean_observations_per_image": round(rec.compute_mean_observations_per_reg_image(), 1),
    }


def camera_pose(image: "pycolmap.Image") -> tuple[np.ndarray, np.ndarray]:
    """Rotación R (3x3) y traslación t (3,) de la pose mundo -> cámara.

    Según la versión de pycolmap, `cam_from_world` es un atributo o un método;
    esta función acepta ambos.
    """
    cam_from_world = image.cam_from_world
    if callable(cam_from_world):
        cam_from_world = cam_from_world()
    return np.asarray(cam_from_world.rotation.matrix()), np.asarray(cam_from_world.translation)


def camera_centers(rec: "pycolmap.Reconstruction") -> tuple[list[str], np.ndarray]:
    """Nombres y centros ópticos (C = -Rᵀ t) de las fotos registradas, ordenados."""
    names, centers = [], []
    for image in sorted(rec.images.values(), key=lambda img: img.name):
        if hasattr(image, "has_pose") and not image.has_pose:
            continue
        rotation, translation = camera_pose(image)
        names.append(image.name)
        centers.append(-rotation.T @ translation)
    return names, np.array(centers)


def save_sparse_results(rec: "pycolmap.Reconstruction", run_dir: str | Path) -> dict[str, Path]:
    """Guarda la reconstrucción según la convención results/<objeto>/<metodo>/.

    - `sparse/`: modelo COLMAP completo (lo reutilizan MVS y 3DGS).
    - `sparse.ply`: nube dispersa coloreada.
    - `poses.npz`: nombres, R, t, centros e intrínsecos de la cámara.
    """
    folder = Path(run_dir)
    (folder / "sparse").mkdir(parents=True, exist_ok=True)
    rec.write(folder / "sparse")
    rec.export_PLY(str(folder / "sparse.ply"))

    names, rotations, translations = [], [], []
    for image in sorted(rec.images.values(), key=lambda img: img.name):
        if hasattr(image, "has_pose") and not image.has_pose:
            continue
        rotation, translation = camera_pose(image)
        names.append(image.name)
        rotations.append(rotation)
        translations.append(translation)
    camera = next(iter(rec.cameras.values()))
    np.savez(
        folder / "poses.npz",
        names=np.array(names),
        R=np.array(rotations),
        t=np.array(translations),
        centers=np.array([-r.T @ t for r, t in zip(rotations, translations)]),
        camera_model=str(camera.model),
        camera_params=np.asarray(camera.params),
        K=np.asarray(camera.calibration_matrix()),
    )
    return {
        "sparse": folder / "sparse",
        "ply": folder / "sparse.ply",
        "poses": folder / "poses.npz",
    }
