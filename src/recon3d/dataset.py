"""Acceso a las fotografías de cada objeto guardadas en data/<objeto>/."""

import zipfile
from pathlib import Path, PurePosixPath

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


def extract_object_zip(zip_path: str | Path, dest_dir: str | Path) -> list[Path]:
    """Extrae las imágenes de un zip en `dest_dir` y devuelve la lista ordenada.

    En Colab, leer cientos de archivos sueltos desde Drive es lento; leer un
    único zip y extraerlo al disco local de la sesión (/content) es mucho más
    rápido.

    Solo se extraen imágenes y se guardan con su nombre de archivo, sin las
    carpetas internas del zip. Esto también evita que un zip con rutas como
    `../../archivo` escriba fuera de `dest_dir` (ataque conocido como "zip slip").

    Raises:
        FileNotFoundError: si el zip no existe.
        ValueError: si dos imágenes del zip tienen el mismo nombre.
    """
    zip_file = Path(zip_path)
    if not zip_file.is_file():
        raise FileNotFoundError(f"No existe el zip: {zip_file}")

    destination = Path(dest_dir)
    destination.mkdir(parents=True, exist_ok=True)

    seen: set[str] = set()
    with zipfile.ZipFile(zip_file) as archive:
        for member in archive.infolist():
            name = PurePosixPath(member.filename).name
            if member.is_dir() or Path(name).suffix.lower() not in IMAGE_EXTENSIONS:
                continue
            if name in seen:
                raise ValueError(f"Nombre de imagen repetido en el zip: {name}")
            seen.add(name)
            (destination / name).write_bytes(archive.read(member))

    return list_images(destination)
