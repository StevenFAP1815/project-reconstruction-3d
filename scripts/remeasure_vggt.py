"""Vuelve a medir las nubes de VGGT tras eliminar la superficie de apoyo.

El notebook `04_ai_vggt.ipynb` guardó en `results/<objeto>/vggt/` la nube del
objeto limpia y escalada (`object_clean_mm.ply`). Su limpieza no eliminó el
banquito sobre el que se apoyaba cada objeto, y las medidas incluyeron ese
disco. Este script parte de esas nubes, sin repetir la inferencia (no necesita
GPU), y para cada objeto:

1. elimina el apoyo con `recon3d.pointcloud.remove_support`;
2. conserva la mayor componente conexa;
3. recalcula el marco del objeto, la escala y el error dimensional con las
   mismas funciones y medidas que `03` y `04`;
4. escribe `results/<objeto>/vggt-nosupport/` (nube, medidas y `meta.json`) y
   una figura de comprobación en `docs/figures/vggt_nosupport_<objeto>.png`.

Los resultados originales de `vggt/` no se modifican.

Uso, desde la raíz del repositorio:

    python scripts/remeasure_vggt.py
"""

import csv
import json
import sys
import time
from pathlib import Path

import matplotlib

matplotlib.use("Agg")  # sin ventanas: solo se guardan archivos
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from recon3d.measurements import MEASUREMENTS, SCALE_BY  # noqa: E402
from recon3d.paths import OBJECTS  # noqa: E402
from recon3d.pointcloud import (  # noqa: E402
    angular_coverage, dimensional_errors, largest_component, object_frame, read_ply,
    remove_support, write_ply,
)
from recon3d.results import write_meta  # noqa: E402

SEED = 42
METHOD = "vggt-nosupport"
# Fracciones de la mayor dimensión horizontal de la nube (ver remove_support).
# band_ratio: la tela del banquito forma una capa de ~10 mm en la caja (≈ 5 %
# de 190 mm); con 6 % se cubre entera. contact_ratio: con 12 % el mango del
# colador, a ~25 mm del apoyo, contaba como contacto y dejaba tela debajo.
SUPPORT = {"band_ratio": 0.06, "contact_ratio": 0.08, "cell_ratio": 0.02}
# La normal del apoyo es una vertical medida directamente; el marco del objeto
# solo puede inclinarse 5° respecto a ella. Con 35° (valor de 03 y 04, donde la
# vertical se estimaba con las órbitas) el canasto quedaba inclinado, porque
# las flores no tienen caras planas que orienten la caja de volumen mínimo.
FRAME_MAX_TILT = 5.0
VOXEL_RATIO = 0.01          # misma resolución de la componente conexa que en 04
MIN_POINTS_PER_VOXEL = 3


def side_views(axes_row, coords, colors, title, rng, n=20_000):
    """Planta, alzado y perfil de una nube (muestra aleatoria de `n` puntos)."""
    keep = rng.choice(len(coords), size=min(n, len(coords)), replace=False)
    for ax, (i, j), label in zip(axes_row, [(0, 1), (0, 2), (1, 2)], ["planta", "alzado", "perfil"]):
        ax.scatter(coords[keep, i], coords[keep, j], c=colors[keep] / 255, s=0.3)
        ax.set_aspect("equal")
        ax.set_title(f"{title}: {label}", fontsize=9)
        ax.tick_params(labelsize=7)


def process(obj: str) -> dict:
    start = time.perf_counter()
    source = REPO_ROOT / "results" / obj / "vggt"
    original = json.loads((source / "meta.json").read_text(encoding="utf-8"))
    cloud = read_ply(source / "object_clean_mm.ply")
    points, colors = cloud["points"], cloud["colors"]

    keep, support = remove_support(points, seed=SEED, **SUPPORT)
    kept = points[keep]
    size = float(np.ptp(points[:, :2], axis=0).max())
    component = largest_component(kept, VOXEL_RATIO * size, min_points_per_voxel=MIN_POINTS_PER_VOXEL)
    object_points, object_colors = kept[component], colors[keep][component]

    coords, _, _ = object_frame(object_points, np.array(support["normal"]),
                                max_tilt_deg=FRAME_MAX_TILT, seed=SEED)
    factor, rows = dimensional_errors(coords, MEASUREMENTS[obj], SCALE_BY[obj])
    coords_mm = coords * factor
    evaluation = [r for r in rows if r["role"] == "evaluación"]
    mean_error = float(np.mean([abs(r["error_pct"]) for r in evaluation]))
    low, high = np.percentile(coords_mm, 1, axis=0), np.percentile(coords_mm, 99, axis=0)

    run_dir = REPO_ROOT / "results" / obj / METHOD
    run_dir.mkdir(parents=True, exist_ok=True)
    write_ply(run_dir / "object_mm.ply", coords_mm, colors=object_colors)
    with open(run_dir / "measurements.csv", "w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

    rng = np.random.default_rng(SEED)
    fig, axes = plt.subplots(2, 3, figsize=(15, 9))
    side_views(axes[0], points, colors, "antes", rng)
    side_views(axes[1], coords_mm, object_colors, "sin apoyo", rng)
    for ax in axes.ravel():
        ax.set_xlabel("mm", fontsize=8)
    fig.suptitle(f"{obj}: caja envolvente sin apoyo {np.round(high - low, 1)} mm "
                 f"| error medio {mean_error:.1f} %")
    fig.tight_layout()
    figure = REPO_ROOT / "docs" / "figures" / f"vggt_nosupport_{obj}.png"
    fig.savefig(figure, dpi=80)  # figura ligera: se versiona en Git
    plt.close(fig)

    extra = original["extra"]
    write_meta(
        run_dir,
        object_name=obj,
        method=METHOD,
        n_images=original["n_images"],
        n_registered=original["n_registered"],
        runtime_s=float(original["runtime_s"]),  # el coste es el de la inferencia original
        seed=SEED,
        scale_factor=float(original["scale_factor"]) * factor,
        extra={
            "stage": "IA (VGGT), sin apoyo",
            "status": "ok",
            "source_run": f"results/{obj}/vggt",
            "source_commit": original.get("environment", {}).get("code_version"),
            "n_images_used": extra.get("n_images_used"),
            "peak_gpu_gb": extra.get("peak_gpu_gb"),
            "inference_s": extra.get("inference_s"),
            "remeasure_s": round(time.perf_counter() - start, 1),
            "support": {**SUPPORT, **support},
            "n_object_points": int(len(coords_mm)),
            "scale_by": SCALE_BY[obj],
            "bounding_box_mm": np.round(high - low, 2).tolist(),
            "measurements": rows,
            "mean_abs_error_pct": round(mean_error, 2),
            # Centro = mediana horizontal: el centro de la caja envolvente se
            # desplaza hacia apéndices largos (el mango del colador) y deja
            # sectores vacíos que no corresponden a partes sin reconstruir.
            "angular_coverage_pct": angular_coverage(coords_mm, np.median(coords_mm[:, :2], axis=0)),
            "original_mean_abs_error_pct": extra.get("mean_abs_error_pct"),
        },
    )
    return {"object": obj, "points": len(points), "kept": len(coords_mm),
            "tilt": support["tilt_deg"], "box": np.round(high - low, 1).tolist(),
            "error": round(mean_error, 2), "rows": rows}


def main() -> None:
    for obj in OBJECTS:
        if not (REPO_ROOT / "results" / obj / "vggt" / "object_clean_mm.ply").exists():
            print(f"{obj}: falta results/{obj}/vggt/object_clean_mm.ply, se omite")
            continue
        r = process(obj)
        print(f"\n== {obj}: {r['kept']:,} de {r['points']:,} puntos | plano inclinado "
              f"{r['tilt']}° | caja {r['box']} mm | error medio {r['error']} %")
        for row in r["rows"]:
            print(f"   {row['name']:<18} real {row['real_mm']:>6} | modelo {row['model_mm']:>8} "
                  f"| {row['error_pct']:>7} % ({row['role']})")


if __name__ == "__main__":
    main()
