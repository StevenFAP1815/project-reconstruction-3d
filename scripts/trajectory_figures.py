"""Diagramas de trayectoria de captura y solapamiento estimado (criterio 2).

Usa las poses estimadas por SfM (`results/<objeto>/<metodo>/poses.npz`) y la
nube dispersa (`sparse.ply`), que se descargan de Drive a local. Escribe:

- `docs/figures/trajectory_<objeto>.png`: vista desde arriba y vista lateral.
- `docs/figures/trajectory_summary.csv`: alturas, giro entre fotos y solapamiento.

Uso, desde la raíz del repositorio:

    python scripts/trajectory_figures.py
"""

import csv
import json
import sys
from pathlib import Path

import cv2
import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from recon3d.geometry import overlap_from_step, trajectory_frame, viewing_angle_steps  # noqa: E402
from recon3d.paths import OBJECTS  # noqa: E402
from recon3d.pointcloud import look_at_point, read_ply  # noqa: E402

# Modelo disperso de cada objeto: el más completo disponible.
SPARSE_METHOD = {name: "colmap" for name in OBJECTS} | {"caja-carton-leche": "colmap-v2"}
PANEL = 560
LIMIT = 1.4  # medio lado de cada panel, en distancias cámara-objeto


def horizontal_fov_deg() -> float:
    calibration = json.loads((REPO_ROOT / "results" / "calibration" / "calibration.json").read_text(encoding="utf-8"))
    width = calibration["image_size"][0]
    return float(np.degrees(2 * np.arctan(width / 2 / calibration["fx"])))


def to_pixels(xy: np.ndarray) -> np.ndarray:
    scaled = (xy / LIMIT + 1) / 2 * (PANEL - 1)
    return np.column_stack([scaled[:, 0], PANEL - 1 - scaled[:, 1]]).round().astype(int)


def draw(object_name: str, coords: np.ndarray, cloud: np.ndarray, directions: np.ndarray) -> np.ndarray:
    """Panel izquierdo: planta (x, y). Panel derecho: distancia al eje frente a altura."""
    canvas = np.full((PANEL + 60, 2 * PANEL + 20, 3), 255, np.uint8)
    top = canvas[60:, :PANEL]
    side = canvas[60:, PANEL + 20:]
    for panel in (top, side):
        cv2.rectangle(panel, (0, 0), (PANEL - 1, PANEL - 1), (200, 200, 200), 1)
        center = to_pixels(np.zeros((1, 2)))[0]
        cv2.line(panel, (center[0], 0), (center[0], PANEL - 1), (230, 230, 230), 1)
        cv2.line(panel, (0, center[1]), (PANEL - 1, center[1]), (230, 230, 230), 1)

    radius = np.hypot(cloud[:, 0], cloud[:, 1])
    for u, v in to_pixels(cloud[:, :2]):
        if 0 <= u < PANEL and 0 <= v < PANEL:
            top[v, u] = (150, 150, 150)
    for u, v in to_pixels(np.column_stack([radius, cloud[:, 2]])):
        if 0 <= u < PANEL and 0 <= v < PANEL:
            side[v, u] = (150, 150, 150)

    colors = cv2.applyColorMap(np.linspace(0, 255, len(coords)).astype(np.uint8)[:, None], cv2.COLORMAP_VIRIDIS)[:, 0]
    cam_top = to_pixels(coords[:, :2])
    tips = to_pixels(coords[:, :2] + 0.15 * directions[:, :2])
    cam_side = to_pixels(np.column_stack([np.hypot(coords[:, 0], coords[:, 1]), coords[:, 2]]))
    for i in range(len(coords)):
        color = tuple(int(c) for c in colors[i])
        cv2.line(top, tuple(cam_top[i]), tuple(tips[i]), color, 1, cv2.LINE_AA)
        cv2.circle(top, tuple(cam_top[i]), 4, color, -1, cv2.LINE_AA)
        cv2.circle(side, tuple(cam_side[i]), 4, color, -1, cv2.LINE_AA)

    font = cv2.FONT_HERSHEY_SIMPLEX
    cv2.putText(canvas, f"{object_name}: {len(coords)} camaras (color: orden de captura, oscuro -> claro)",
                (10, 25), font, 0.6, (0, 0, 0), 1, cv2.LINE_AA)
    cv2.putText(canvas, "Planta (desde arriba)", (10, 52), font, 0.5, (60, 60, 60), 1, cv2.LINE_AA)
    cv2.putText(canvas, "Lateral: distancia al eje vs altura", (PANEL + 30, 52), font, 0.5, (60, 60, 60), 1, cv2.LINE_AA)
    return canvas


def main() -> None:
    fov = horizontal_fov_deg()
    out_dir = REPO_ROOT / "docs" / "figures"
    out_dir.mkdir(parents=True, exist_ok=True)
    rows = []
    for name in OBJECTS:
        run = REPO_ROOT / "results" / name / SPARSE_METHOD[name]
        if not (run / "poses.npz").exists():
            print(f"{name}: sin poses.npz en {run}, se omite")
            continue
        poses = np.load(run / "poses.npz")
        centers, directions = poses["centers"], poses["R"][:, 2, :]
        target = look_at_point(centers, directions)
        _, axes = trajectory_frame(centers)
        if np.mean((centers - target) @ axes[2]) < 0:  # z hacia las cámaras (arriba)
            axes = axes * np.array([[1], [-1], [-1]])
        distance = float(np.median(np.linalg.norm(centers - target, axis=1)))
        coords = (centers - target) @ axes.T / distance
        cloud = (read_ply(run / "sparse.ply")["points"] - target) @ axes.T / distance
        cloud = cloud[np.linalg.norm(cloud, axis=1) < LIMIT]
        dirs = directions @ axes.T

        # cv2.imwrite falla en silencio con rutas con tildes en Windows ("Visión"):
        # se codifica el PNG en memoria y se escribe con Python.
        ok, png = cv2.imencode(".png", draw(name, coords, cloud, dirs))
        if not ok:
            raise RuntimeError(f"No se pudo codificar la figura de {name}")
        (out_dir / f"trajectory_{name}.png").write_bytes(png.tobytes())
        steps = viewing_angle_steps(directions)
        heights = coords[:, 2]
        rows.append({
            "object": name,
            "method": SPARSE_METHOD[name],
            "n_cameras": len(centers),
            "height_min": round(float(heights.min()), 2),
            "height_max": round(float(heights.max()), 2),
            "elevation_deg_median": round(float(np.degrees(np.median(np.arctan2(heights, np.hypot(coords[:, 0], coords[:, 1]))))), 1),
            "step_deg_median": round(float(np.median(steps)), 2),
            "overlap_pct_median": round(100 * float(np.median(overlap_from_step(steps, fov))), 1),
            "hfov_deg": round(fov, 1),
        })
        print(f"{name}: {len(centers)} cámaras, giro mediano {rows[-1]['step_deg_median']}°, "
              f"solapamiento ~{rows[-1]['overlap_pct_median']} %")

    with open(out_dir / "trajectory_summary.csv", "w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


if __name__ == "__main__":
    main()
