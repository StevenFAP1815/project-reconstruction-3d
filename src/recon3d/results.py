"""Registro de cada corrida en `results/<objeto>/<metodo>/meta.json`.

La rúbrica (criterio 9) exige un meta.json por corrida con: n.º de imágenes,
imágenes registradas, tiempo, GPU, versión, semilla y factor de escala. Esta
función garantiza que todas las corridas guardan los mismos campos.
"""

import json
import platform
import subprocess
from datetime import datetime, timezone
from importlib import metadata
from pathlib import Path

from recon3d.paths import REPO_ROOT

# Paquetes cuya versión se registra si están instalados.
TRACKED_PACKAGES = (
    "numpy",
    "opencv-python",
    "opencv-python-headless",
    "pycolmap",
    "pycolmap-cuda12",
    "torch",
    "open3d",
    "trimesh",
)


def detect_gpu() -> str | None:
    """Nombre de la GPU NVIDIA disponible, o None si no hay (o no hay drivers)."""
    try:
        output = subprocess.run(
            ["nvidia-smi", "--query-gpu=name", "--format=csv,noheader"],
            capture_output=True,
            text=True,
            check=True,
            timeout=10,
        ).stdout.strip()
    except (OSError, subprocess.SubprocessError):
        return None
    return output.splitlines()[0] if output else None


def code_version() -> str | None:
    """Commit de Git del código usado (p. ej. 'a1b2c3d'), o None si no se sabe."""
    try:
        return subprocess.run(
            ["git", "-C", str(REPO_ROOT), "rev-parse", "--short", "HEAD"],
            capture_output=True,
            text=True,
            check=True,
            timeout=10,
        ).stdout.strip() or None
    except (OSError, subprocess.SubprocessError):
        return None


def environment_info() -> dict:
    """Versiones de Python, paquetes, GPU y código del entorno actual."""
    packages = {}
    for name in TRACKED_PACKAGES:
        try:
            packages[name] = metadata.version(name)
        except metadata.PackageNotFoundError:
            continue
    return {
        "python": platform.python_version(),
        "platform": platform.platform(),
        "gpu": detect_gpu(),
        "code_version": code_version(),
        "packages": packages,
    }


def write_meta(
    run_dir: str | Path,
    *,
    object_name: str,
    method: str,
    n_images: int,
    n_registered: int,
    runtime_s: float,
    seed: int,
    scale_factor: float | None = None,
    extra: dict | None = None,
) -> Path:
    """Escribe `meta.json` en `run_dir` y devuelve su ruta.

    Los argumentos van después de `*`, por lo que deben pasarse por nombre
    (`n_images=81`); así es imposible confundir el orden de dos números.

    Args:
        run_dir: carpeta de la corrida (normalmente `paths.run_dir(obj, metodo)`).
        object_name: nombre del objeto (p. ej. "vaso-vidrio").
        method: método usado (p. ej. "colmap", "vggt").
        n_images: imágenes de entrada.
        n_registered: imágenes con pose estimada.
        runtime_s: tiempo total de la corrida en segundos.
        seed: semilla aleatoria usada.
        scale_factor: factor que convierte unidades del modelo a milímetros;
            None si todavía no se ha calculado.
        extra: campos adicionales propios del método (parámetros, métricas).

    Raises:
        ValueError: si los valores numéricos son incoherentes.
    """
    if n_images < 0 or not 0 <= n_registered <= n_images:
        raise ValueError(
            f"Se requiere 0 <= n_registered <= n_images "
            f"(recibido n_registered={n_registered}, n_images={n_images})"
        )
    if runtime_s < 0:
        raise ValueError(f"runtime_s no puede ser negativo: {runtime_s}")
    if scale_factor is not None and scale_factor <= 0:
        raise ValueError(f"scale_factor debe ser positivo: {scale_factor}")

    meta = {
        "object": object_name,
        "method": method,
        "created_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "n_images": n_images,
        "n_registered": n_registered,
        "registered_ratio": round(n_registered / n_images, 4) if n_images else None,
        "runtime_s": round(runtime_s, 2),
        "seed": seed,
        "scale_factor": scale_factor,
        "environment": environment_info(),
        "extra": extra or {},
    }

    folder = Path(run_dir)
    folder.mkdir(parents=True, exist_ok=True)
    meta_path = folder / "meta.json"
    meta_path.write_text(
        json.dumps(meta, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    return meta_path
