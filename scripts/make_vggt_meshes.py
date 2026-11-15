"""Mallas de Poisson a partir de las nubes de VGGT sin apoyo, en local (CPU).

Parte de `results/<objeto>/vggt-nosupport/object_mm.ply` (generada por
`scripts/remeasure_vggt.py`) y para cada objeto:

1. reduce la nube con una rejilla de vóxeles;
2. estima y orienta las normales (`recon3d.meshing`);
3. reconstruye la superficie con Poisson de COLMAP (`recon3d.dense.poisson_mesh`,
   los mismos parámetros que `03`);
4. recorta la superficie inventada fuera de la caja del objeto, colorea los
   vértices con la nube y exporta `mesh_mm.ply`, `mesh_mm.obj` y `mesh.glb`;
5. mide la malla con las mismas medidas que la nube y añade el resultado al
   `meta.json` de `vggt-nosupport`.

Requiere pycolmap (la versión para CPU basta: Poisson no usa la GPU) y scipy.

Uso, desde la raíz del repositorio:

    python scripts/make_vggt_meshes.py
"""

import json
import sys
import tempfile
import time
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pycolmap  # noqa: E402
from mpl_toolkits.mplot3d.art3d import Poly3DCollection  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from recon3d.dense import poisson_mesh  # noqa: E402
from recon3d.measurements import MEASUREMENTS, SCALE_BY  # noqa: E402
from recon3d.meshing import (  # noqa: E402
    estimate_normals, nearest_colors, orient_normals, sample_surface, voxel_downsample,
)
from recon3d.paths import OBJECTS  # noqa: E402
from recon3d.pointcloud import crop_mesh, measure, read_ply, write_glb, write_obj, write_ply  # noqa: E402

SEED = 42
METHOD = "vggt-nosupport"
VOXEL_RATIO = 0.004          # celda = 0,4 % de la mayor dimensión (≈ 0,8 mm en la caja)
NORMAL_NEIGHBORS = 20
POISSON_OPTIONS = {"depth": 10, "trim": 7}   # los mismos que 03
CROP_MARGIN = 0.03           # margen del recorte, como en 03
# Poisson con depth 10 da 0,7-3,5 millones de triángulos (13-67 MB en .glb),
# demasiado para un visor web. La simplificación QEM fusiona primero las aristas
# que menos deforman la superficie; 200 000 triángulos conservan la forma.
TARGET_FACES = 200_000


def export_glb(path, vertices_mm, faces, colors):
    """glTF mide en metros y usa +Y como vertical; las mallas usan mm y +Z.

    (x, y, z) -> (x, z, -y) es un giro de -90° alrededor del eje X (no un
    reflejo), así que conserva el sentido de los triángulos.
    """
    vertices_m = np.column_stack([vertices_mm[:, 0], vertices_mm[:, 2], -vertices_mm[:, 1]]) / 1000.0
    write_glb(path, vertices_m, faces, colors)


def render(ax, vertices, faces, colors, elev, azim):
    """Dibuja la malla con el color de sus vértices, sombreado según la orientación."""
    triangles = vertices[faces]
    normals = np.cross(triangles[:, 1] - triangles[:, 0], triangles[:, 2] - triangles[:, 0])
    normals /= np.linalg.norm(normals, axis=1, keepdims=True) + 1e-12
    light = np.array([0.4, -0.6, 0.7]) / np.linalg.norm([0.4, -0.6, 0.7])
    shade = 0.45 + 0.55 * np.abs(normals @ light)
    rgb = np.clip(colors[faces].mean(axis=1) / 255 * shade[:, None] * 1.3, 0, 1)
    collection = Poly3DCollection(triangles, facecolors=rgb, linewidths=0)
    ax.add_collection3d(collection)
    low, high = vertices.min(axis=0), vertices.max(axis=0)
    ax.set_xlim(low[0], high[0])
    ax.set_ylim(low[1], high[1])
    ax.set_zlim(low[2], high[2])
    ax.set_box_aspect(high - low)
    ax.view_init(elev=elev, azim=azim)
    ax.set_axis_off()


def process(obj: str) -> dict:
    start = time.perf_counter()
    run_dir = REPO_ROOT / "results" / obj / METHOD
    cloud = read_ply(run_dir / "object_mm.ply")
    points, colors = cloud["points"], cloud["colors"]
    low, high = np.percentile(points, 1, axis=0), np.percentile(points, 99, axis=0)

    voxel = VOXEL_RATIO * float((high - low).max())
    reduced, reduced_colors = voxel_downsample(points, voxel, colors)
    normals = orient_normals(reduced, estimate_normals(reduced, k=NORMAL_NEIGHBORS))

    with tempfile.TemporaryDirectory() as tmp:
        oriented = write_ply(Path(tmp) / "oriented.ply", reduced, colors=reduced_colors, normals=normals)
        t0 = time.perf_counter()
        raw = read_ply(poisson_mesh(oriented, Path(tmp) / "poisson.ply", options=POISSON_OPTIONS))
        poisson_s = time.perf_counter() - t0

        margin = CROP_MARGIN * (high - low)
        vertices, faces, _ = crop_mesh(raw["points"], raw["faces"], low - margin, high + margin)
        n_faces_poisson = len(faces)
        full = write_ply(Path(tmp) / "full.ply", vertices, colors=nearest_colors(vertices, points, colors),
                         faces=faces)
        simplify = pycolmap.MeshSimplificationOptions()
        simplify.target_face_ratio = min(1.0, TARGET_FACES / len(faces))
        pycolmap.simplify_mesh(full, Path(tmp) / "simple.ply", simplify)
        simple = read_ply(Path(tmp) / "simple.ply")
    vertices, faces = simple["points"], simple["faces"]
    vertex_colors = simple["colors"] if "colors" in simple else nearest_colors(vertices, points, colors)

    write_ply(run_dir / "mesh_mm.ply", vertices, colors=vertex_colors, faces=faces)
    write_obj(run_dir / "mesh_mm.obj", vertices, faces, vertex_colors)
    export_glb(run_dir / "mesh.glb", vertices, faces, vertex_colors)

    # Medidas de la malla con la escala de la nube (no se vuelve a escalar).
    surface = sample_surface(vertices, faces, 200_000, seed=SEED)
    rows = []
    for spec in MEASUREMENTS[obj]:
        model = measure(surface, spec)
        rows.append({"name": spec["name"], "real_mm": spec["mm"], "mesh_mm": round(model, 2),
                     "error_pct": round(100 * (model - spec["mm"]) / spec["mm"], 2),
                     "role": "escala" if spec["name"] == SCALE_BY[obj] else "evaluación"})
    mean_error = float(np.mean([abs(r["error_pct"]) for r in rows if r["role"] == "evaluación"]))

    fig = plt.figure(figsize=(15, 5))
    for i, (elev, azim, title) in enumerate([(15, -60, "frente"), (15, 30, "lateral"), (70, -60, "desde arriba")]):
        ax = fig.add_subplot(1, 3, i + 1, projection="3d")
        render(ax, vertices, faces, vertex_colors, elev, azim)
        ax.set_title(title, fontsize=10)
    fig.suptitle(f"{obj}: malla de Poisson desde VGGT ({len(faces):,} triángulos)")
    fig.tight_layout()
    fig.savefig(REPO_ROOT / "docs" / "figures" / f"vggt_mesh_{obj}.png", dpi=80)
    plt.close(fig)

    meta_path = run_dir / "meta.json"
    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    meta["extra"]["mesh"] = {
        "source": "object_mm.ply",
        "voxel_mm": round(voxel, 3),
        "n_points_meshed": int(len(reduced)),
        "normal_neighbors": NORMAL_NEIGHBORS,
        "poisson_options": POISSON_OPTIONS,
        "crop_margin": CROP_MARGIN,
        "n_faces_poisson": int(n_faces_poisson),
        "simplification": {"method": "QEM (pycolmap.simplify_mesh)", "target_faces": TARGET_FACES},
        "n_vertices": int(len(vertices)),
        "n_faces": int(len(faces)),
        "poisson_s": round(poisson_s, 1),
        "total_s": round(time.perf_counter() - start, 1),
        "measurements": rows,
        "mean_abs_error_pct": round(mean_error, 2),
        "files": ["mesh_mm.ply", "mesh_mm.obj", "mesh.glb"],
    }
    meta_path.write_text(json.dumps(meta, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return meta["extra"]["mesh"]


def main() -> None:
    if "--glb-only" in sys.argv:   # vuelve a exportar los .glb desde mesh_mm.ply, sin Poisson
        for obj in OBJECTS:
            mesh_path = REPO_ROOT / "results" / obj / METHOD / "mesh_mm.ply"
            if mesh_path.exists():
                mesh = read_ply(mesh_path)
                export_glb(mesh_path.with_name("mesh.glb"), mesh["points"], mesh["faces"], mesh["colors"])
                print(f"{obj}: mesh.glb exportado")
        return
    for obj in OBJECTS:
        if not (REPO_ROOT / "results" / obj / METHOD / "object_mm.ply").exists():
            print(f"{obj}: falta {METHOD}/object_mm.ply (ejecutar antes remeasure_vggt.py)")
            continue
        m = process(obj)
        print(f"\n== {obj}: {m['n_points_meshed']:,} puntos -> {m['n_faces']:,} triángulos "
              f"| Poisson {m['poisson_s']} s, total {m['total_s']} s | error medio {m['mean_abs_error_pct']} %")
        for r in m["measurements"]:
            print(f"   {r['name']:<18} real {r['real_mm']:>6} | malla {r['mesh_mm']:>8} | {r['error_pct']:>7} % ({r['role']})")


if __name__ == "__main__":
    main()
