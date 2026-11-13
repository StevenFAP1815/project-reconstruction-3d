"""Comprime las fotos de cada objeto en data/zips/<objeto>.zip.

Uso (desde la raíz del repositorio):

    python scripts/make_data_zips.py

Después se sube el contenido de data/zips/ a
`Mi unidad/project-reconstruction-3d/data/zips/` en Google Drive.

Se usa ZIP_STORED (sin compresión): los JPEG ya están comprimidos, así que
comprimirlos otra vez apenas reduce el tamaño y hace todo más lento.
"""

import sys
import zipfile
from pathlib import Path

# Permite importar recon3d sin instalar el paquete.
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from recon3d.dataset import list_images  # noqa: E402
from recon3d.paths import CALIBRATION, OBJECTS, get_paths  # noqa: E402


def main() -> None:
    paths = get_paths()
    paths.zips.mkdir(parents=True, exist_ok=True)

    for name in (*OBJECTS, CALIBRATION):
        source = paths.data / name
        if not source.is_dir():
            print(f"[omitido] {name}: no existe {source}")
            continue

        images = list_images(source)
        if not images:
            print(f"[omitido] {name}: carpeta sin imágenes")
            continue

        zip_path = paths.data_zip(name)
        with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_STORED) as archive:
            for image in images:
                archive.write(image, arcname=image.name)

        size_mb = zip_path.stat().st_size / 1_000_000
        print(f"[ok] {name}: {len(images)} imágenes -> {zip_path.name} ({size_mb:.0f} MB)")


if __name__ == "__main__":
    main()
