"""Rutas del proyecto, con la misma estructura en Google Drive y en local.

La carpeta del proyecto en Drive (`Mi unidad/project-reconstruction-3d`) es un
espejo del repositorio: `results/` en Drive se descarga y se pega tal cual en
`results/` del repositorio local.

    <raíz>/
    ├── data/
    │   ├── zips/<objeto>.zip   # fotos comprimidas que se suben a Drive
    │   ├── calibration/        # fotos del tablero/ChArUco
    │   └── <objeto>/           # fotos sueltas (solo en local)
    ├── results/
    │   ├── calibration/        # K y distorsión de la cámara
    │   └── <objeto>/<metodo>/
    ├── work/                   # temporales (bases de datos COLMAP, etc.)
    └── checkpoints/            # pesos de modelos de IA

Todos los notebooks construyen sus rutas con `get_paths()` en lugar de
escribirlas a mano, así un cambio de estructura se hace en un solo lugar.
"""

import re
import sys
from dataclasses import dataclass
from pathlib import Path

# Nombres de carpeta de los 5 objetos (ver tabla O1-O5 del README).
OBJECTS = (
    "caja-carton-leche",
    "canasto-flores",
    "vaso-vidrio",
    "audifonos",
    "colador-cocina",
)

CALIBRATION = "calibration"

DRIVE_ROOT = Path("/content/drive/MyDrive/project-reconstruction-3d")

# src/recon3d/paths.py -> parents[2] es la raíz del repositorio.
REPO_ROOT = Path(__file__).resolve().parents[2]

# Nombres de método válidos: minúsculas, dígitos, "-" y "_" (p. ej. "colmap", "vggt").
_METHOD_PATTERN = re.compile(r"^[a-z0-9][a-z0-9_-]*$")


def _check_object(object_name: str) -> None:
    if object_name not in OBJECTS:
        raise ValueError(
            f"Objeto desconocido: {object_name!r}. Válidos: {', '.join(OBJECTS)}"
        )


@dataclass(frozen=True)
class ProjectPaths:
    """Rutas derivadas de una carpeta raíz (Drive o repositorio local)."""

    root: Path

    @property
    def data(self) -> Path:
        return self.root / "data"

    @property
    def zips(self) -> Path:
        return self.data / "zips"

    @property
    def calibration(self) -> Path:
        return self.data / CALIBRATION

    @property
    def results(self) -> Path:
        return self.root / "results"

    @property
    def calibration_results(self) -> Path:
        """Resultados de la calibración (K, distorsión), comunes a todos los objetos."""
        return self.results / CALIBRATION

    @property
    def work(self) -> Path:
        return self.root / "work"

    @property
    def checkpoints(self) -> Path:
        return self.root / "checkpoints"

    def object_data(self, object_name: str) -> Path:
        """Carpeta con las fotos sueltas de un objeto."""
        _check_object(object_name)
        return self.data / object_name

    def data_zip(self, name: str) -> Path:
        """Zip de fotos de un objeto o de la calibración (`"calibration"`)."""
        if name != CALIBRATION:
            _check_object(name)
        return self.zips / f"{name}.zip"

    def run_dir(self, object_name: str, method: str) -> Path:
        """Carpeta de resultados `results/<objeto>/<metodo>/` (no la crea)."""
        _check_object(object_name)
        if not _METHOD_PATTERN.match(method):
            raise ValueError(
                f"Nombre de método inválido: {method!r}. "
                "Usar minúsculas, dígitos, '-' o '_' (p. ej. 'colmap')."
            )
        return self.results / object_name / method

    def create(self) -> list[Path]:
        """Crea la estructura de carpetas y devuelve las rutas creadas o existentes.

        Usa `exist_ok=True`: ejecutarlo varias veces no borra ni modifica nada.
        """
        folders = [
            self.zips,
            self.calibration,
            self.calibration_results,
            self.work,
            self.checkpoints,
            *(self.results / name for name in OBJECTS),
        ]
        for folder in folders:
            folder.mkdir(parents=True, exist_ok=True)
        return folders


def in_colab() -> bool:
    """True si el código se ejecuta dentro de Google Colab."""
    return "google.colab" in sys.modules


def get_paths(root: str | Path | None = None) -> ProjectPaths:
    """Devuelve las rutas del proyecto.

    Sin argumento: usa Drive si se ejecuta en Colab y el repositorio local en
    caso contrario. Con `root` se fuerza una raíz concreta (útil en tests).
    """
    if root is not None:
        return ProjectPaths(Path(root))
    return ProjectPaths(DRIVE_ROOT if in_colab() else REPO_ROOT)
