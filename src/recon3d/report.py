"""Tabla maestra objeto × método a partir de los `meta.json` de cada corrida (criterio 8).

Cada corrida guarda en `results/<objeto>/<metodo>/meta.json` su registro; este
módulo los recorre y resume cada uno en una fila con las mismas columnas, sea
cual sea el método. Así la tabla se regenera sola cada vez que se añade una
corrida (por ejemplo, la del método de IA).
"""

import csv
import json
from pathlib import Path

from recon3d.paths import OBJECTS

# Etapa de cada método conocido; los métodos nuevos la declaran en extra["stage"].
STAGES = {
    "colmap": "SfM disperso (base)",
    "colmap-v2": "SfM disperso (D_calibrada)",
    "colmap-mvs": "MVS + malla",
    "vggt": "IA (VGGT)",
}

COLUMNS = [
    "object", "method", "stage", "status", "n_images", "n_used", "n_registered",
    "registered_pct", "n_models", "n_points", "reprojection_error_px",
    "scale_factor", "mean_abs_error_pct", "coverage_pct", "runtime_s", "peak_gpu_gb",
    "gpu", "code_version",
]

HEADERS = {
    "object": "Objeto", "method": "Método", "stage": "Etapa", "status": "Estado",
    "n_images": "Fotos", "n_used": "Usadas", "n_registered": "Registradas",
    "registered_pct": "Registradas (%)", "n_models": "Modelos", "n_points": "Puntos",
    "reprojection_error_px": "Error reproy. (px)", "scale_factor": "Escala (mm/u)",
    "mean_abs_error_pct": "Error dim. medio (%)", "coverage_pct": "Cobertura (%)",
    "runtime_s": "Tiempo (s)", "peak_gpu_gb": "Memoria GPU (GB)",
    "gpu": "GPU", "code_version": "Commit",
}


def _experiment_row(run_dir: Path, config: str) -> dict:
    """Fila de `experiments.csv` (notebook 02b) para la configuración elegida."""
    path = run_dir / "experiments.csv"
    if not path.exists():
        return {}
    with open(path, encoding="utf-8") as file:
        for row in csv.DictReader(file):
            if row.get("config") == config:
                return row
    return {}


def _number(value):
    if value in (None, ""):
        return None
    value = float(value)
    return int(value) if value.is_integer() else value


def summarize_run(meta: dict, run_dir: Path) -> dict:
    """Resume un `meta.json` en una fila con las columnas de `COLUMNS`."""
    extra = meta.get("extra") or {}
    stats = dict(extra.get("stats") or {})
    if not stats and extra.get("best_config"):
        stats = _experiment_row(Path(run_dir), extra["best_config"])

    n_used = _number(stats.get("n_images") or extra.get("n_images_used"))
    n_registered = meta.get("n_registered")
    if stats.get("registered_pct") not in (None, ""):
        registered_pct = _number(stats["registered_pct"])
    elif n_used:
        registered_pct = round(100 * n_registered / n_used, 2)
    else:
        registered_pct = None

    n_models = extra.get("n_models") or stats.get("n_models")
    if n_models is None and extra.get("model_sizes"):
        n_models = len(extra["model_sizes"])

    method = meta["method"]
    return {
        "object": meta["object"],
        "method": method,
        "stage": extra.get("stage") or STAGES.get(method, "otro"),
        "status": extra.get("status", "ok"),
        "n_images": meta.get("n_images"),
        "n_used": n_used,
        "n_registered": n_registered,
        "registered_pct": registered_pct,
        "n_models": _number(n_models),
        # Disperso: puntos 3D de SfM. Denso: puntos del objeto tras la limpieza.
        "n_points": _number(extra.get("n_object_points") or stats.get("n_points3d")),
        "reprojection_error_px": _number(stats.get("mean_reprojection_error_px")),
        "scale_factor": meta.get("scale_factor"),
        "mean_abs_error_pct": extra.get("mean_abs_error_pct"),
        "coverage_pct": extra.get("angular_coverage_pct"),
        "runtime_s": meta.get("runtime_s"),
        "peak_gpu_gb": extra.get("peak_gpu_gb"),
        "gpu": (meta.get("environment") or {}).get("gpu"),
        "code_version": (meta.get("environment") or {}).get("code_version"),
    }


def collect_runs(results_dir: str | Path) -> list[dict]:
    """Filas de todas las corridas de `results/<objeto>/<metodo>/meta.json`.

    Se ignoran las carpetas que no son objetos (por ejemplo, `calibration`). El
    orden sigue `recon3d.paths.OBJECTS` y, dentro de cada objeto, el nombre del
    método.
    """
    rows = []
    for meta_path in sorted(Path(results_dir).glob("*/*/meta.json")):
        if meta_path.parent.parent.name not in OBJECTS:
            continue
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        rows.append(summarize_run(meta, meta_path.parent))
    return sorted(rows, key=lambda r: (OBJECTS.index(r["object"]), r["method"]))


def write_csv(rows: list[dict], path: str | Path) -> Path:
    path = Path(path)
    with open(path, "w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=COLUMNS)
        writer.writeheader()
        writer.writerows(rows)
    return path


def _format(value) -> str:
    if value is None:
        return "–"
    if isinstance(value, float):
        return f"{value:,.2f}".replace(",", " ").replace(".", ",")
    if isinstance(value, int):
        return f"{value:,}".replace(",", " ")
    return str(value)


def to_markdown(rows: list[dict], columns: list[str] | None = None) -> str:
    """Tabla en Markdown, con números en formato español (coma decimal)."""
    columns = columns or [c for c in COLUMNS if c not in ("gpu", "code_version")]
    lines = [
        "| " + " | ".join(HEADERS[c] for c in columns) + " |",
        "|" + "|".join("---" for _ in columns) + "|",
    ]
    for row in rows:
        cells = [f"`{row[c]}`" if c in ("object", "method") else _format(row[c]) for c in columns]
        lines.append("| " + " | ".join(cells) + " |")
    return "\n".join(lines) + "\n"
