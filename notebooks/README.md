# notebooks/

Notebooks de experimentación, uno por etapa o método, numerados en el orden
del pipeline.

| Notebook | Propósito |
|---|---|
| `00_setup_colab.ipynb` | Prepara la sesión de Colab: Drive, código, dependencias, carpetas, GPU y fotos. |
| `01_calibration.ipynb` | Calibra la cámara con el tablero: K, distorsión y error RMS (criterio 3). |
| `02_sfm_colmap.ipynb` | SfM definitivo con la configuración `D_calibrada` (nitidez, CLAHE, SIFT sensible, intrínsecos calibrados), métricas, líneas epipolares y trayectoria (criterios 4 y 5). Un objeto por ejecución (`OBJECT`). |
| `02b_sfm_experiments.ipynb` | Mide el efecto de cada mejora de SfM (CLAHE, SIFT sensible, intrínsecos calibrados) sobre un objeto y guarda la mejor en `colmap-v2`. |
| `03_dense_mesh_scale.ipynb` | Reconstrucción densa (MVS), limpieza de la nube, malla de Poisson, escala métrica con error dimensional y exportación `.ply`/`.obj`/`.glb` (criterio 6). Un objeto por ejecución (`OBJECT`). |
| `04_ai_vggt.ipynb` | Método de IA (VGGT): cámaras, profundidad y nube 3D predichas por una red, con la misma limpieza, escala y error dimensional que `03`, más tiempo y memoria de GPU (criterio 7). Un objeto por ejecución (`OBJECT`). |
| `runs/` | Copias ejecutadas por objeto (evidencia); ver `runs/README.md`. |

Reglas:

- La lógica reutilizable va en `src/recon3d/`; el notebook solo la llama y
  muestra resultados.
- Todos se ejecutan en Google Colab con GPU. Cada notebook empieza con las
  celdas 1 a 5 de `00_setup_colab.ipynb`, porque cada sesión de Colab empieza
  vacía.
- Las rutas se obtienen con `recon3d.paths.get_paths()`, nunca escritas a mano.
- Cada corrida termina con `recon3d.results.write_meta(...)`.
- Los notebooks se guardan **con las celdas ejecutadas** (salidas incluidas),
  porque son evidencia para la evaluación. Antes de hacer commit, ejecutarlos
  de inicio a fin (*Entorno de ejecución → Ejecutar todas*) para que las
  salidas correspondan al código.
