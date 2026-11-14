"""Genera la tabla maestra objeto × método (criterio 8 de la rúbrica).

Lee todos los `results/<objeto>/<metodo>/meta.json` del repositorio y escribe:

- `results/master_table.csv`: datos completos, para análisis o gráficas.
- `docs/master-table.md`: la misma tabla en Markdown, para el informe.

Uso, desde la raíz del repositorio:

    python scripts/build_master_table.py
"""

import sys
from datetime import date
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from recon3d.report import collect_runs, to_markdown, write_csv  # noqa: E402

INTRO = """# Tabla maestra objeto × método

Generada con `python scripts/build_master_table.py` a partir de los `meta.json`
de `results/` ({today}). No se edita a mano: se regenera tras cada corrida.

- **Registradas (%)**: sobre las fotos usadas (tras descartar las borrosas).
- **Puntos**: puntos 3D de SfM en las filas dispersas; puntos del objeto tras
  la limpieza en las filas densas.
- **Error dim. medio (%)**: media del error absoluto de las medidas que no se
  usaron para escalar (referencia de la rúbrica: ≤ 2 %).
- **Estado** `omitido`: el método no pudo ejecutarse (por ejemplo, MVS con
  menos de 10 fotos registradas).

"""


def main() -> None:
    rows = collect_runs(REPO_ROOT / "results")
    csv_path = write_csv(rows, REPO_ROOT / "results" / "master_table.csv")
    md_path = REPO_ROOT / "docs" / "master-table.md"
    md_path.write_text(INTRO.format(today=date.today().isoformat()) + to_markdown(rows), encoding="utf-8")
    print(f"{len(rows)} corridas -> {csv_path.relative_to(REPO_ROOT)} y {md_path.relative_to(REPO_ROOT)}")


if __name__ == "__main__":
    main()
