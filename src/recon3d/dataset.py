"""Acceso a las fotografías de cada objeto guardadas en data/<objeto>/."""

from pathlib import Path

# Extensiones aceptadas, en minúsculas; la comparación ignora mayúsculas.
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png"}


def list_images(object_dir: str | Path) -> list[Path]:
    """Devuelve las imágenes de una carpeta de objeto, ordenadas por nombre.

    El orden estable importa para la reproducibilidad: dos corridas sobre la
    misma carpeta procesan las fotos en el mismo orden.

    Args:
        object_dir: carpeta con las fotos de un objeto (p. ej. data/vaso-vidrio).

    Returns:
        Lista de rutas a imágenes. Ignora subcarpetas y archivos de otro tipo.

    Raises:
        FileNotFoundError: si la carpeta no existe.
    """
    folder = Path(object_dir)
    if not folder.is_dir():
        raise FileNotFoundError(f"No existe la carpeta de objeto: {folder}")

    images = [
        path
        for path in folder.iterdir()
        if path.is_file() and path.suffix.lower() in IMAGE_EXTENSIONS
    ]
    return sorted(images, key=lambda path: path.name)
