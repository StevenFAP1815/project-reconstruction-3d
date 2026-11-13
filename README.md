# Reconstrucción 3D de 5 objetos

Proyecto Integrador — Bloque 2 de **Visión por Computador**.

Reconstrucción 3D de cinco objetos reales a partir de fotografías 2D propias, con
**escala métrica verificada**, comparando un pipeline clásico (SfM + MVS) con al
menos un enfoque basado en IA (VGGT, DUSt3R/MASt3R, 3D Gaussian Splatting o NeRF).

> 🚧 Proyecto en desarrollo. Este README se irá completando en cada etapa.

## Pipeline

```
captura → calibración → preprocesamiento → SfM (poses + nube dispersa)
        → reconstrucción densa (MVS) → malla → escala métrica y evaluación
```

## Estructura del repositorio

```
data/           # fotografías por objeto (no se versiona)
src/recon3d/    # código reutilizable (paquete Python)
tests/          # tests automatizados (pytest)
scripts/        # utilidades de línea de comandos (p. ej. crear zips de fotos)
notebooks/      # experimentos por etapa/método
results/        # salidas por objeto y método (solo meta.json en Git)
docs/           # informe y figuras livianas
requirements-dev.txt   # entorno local y CI (tests)
```

## Entorno local (solo tests)

El pipeline se ejecuta en **Google Colab** (GPU). En local solo se necesita un
entorno ligero para ejecutar los tests, con **Python 3.13**:

```powershell
py -3.13 -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements-dev.txt
pytest
```

Los tests viven en `tests/` y usan carpetas temporales, no las fotos de `data/`.
GitHub Actions los ejecuta automáticamente en cada Pull Request
(`.github/workflows/tests.yml`).

## Objetos

| Categoría | Requisito | Objeto elegido | Fotos | Dificultad esperada |
|---|---|---|---|---|
| O1 — Control | Textura rica, mate, forma simple | Caja de cartón de leche (`caja-carton-leche`) | 73 | Baja: superficie impresa y mate, ideal como referencia |
| O2 — Geometría compleja | Concavidades, huecos o detalle fino | Canasto de flores (`canasto-flores`) | 93 | Media: tejido con huecos y oclusiones |
| O3 — Superficie difícil | Poca textura, brillante o reflectante | Vaso de vidrio (`vaso-vidrio`) | 81 | Muy alta: transparente y reflectante, casi sin puntos estables |
| O4 — Escala distinta | ≤ 10 cm o ≥ 50 cm | Audífonos (`audifonos`) | 121 | Media-alta: objeto pequeño, poco área útil por foto |
| O5 — Libre / aplicado | Vinculado a la aplicación del proyecto | Colador de cocina (`colador-cocina`) | 86 | Alta: malla con patrón repetitivo (falsas coincidencias) |

> El vaso y el colador son casos difíciles a propósito: forman parte del
> experimento para comparar dónde fallan SfM y los métodos de IA.

## Estructura de resultados

Cada corrida guarda sus salidas con esta convención:

```
results/<objeto>/<metodo>/
    poses.npz      # intrínsecos y extrínsecos estimados
    sparse.ply     # nube dispersa (SfM)
    dense.ply      # nube densa (MVS o método IA)
    mesh.ply|.obj|.glb
    meta.json      # n.º imágenes, registradas, tiempo, GPU, versión, semilla, factor de escala
```

Las fotografías y los modelos 3D **no se versionan en Git** por su tamaño
(ver `.gitignore`); se compartirán mediante enlaces externos.

## Flujo de trabajo: GitHub + Colab + Drive

Cada herramienta tiene un único papel:

| Herramienta | Papel |
|---|---|
| **GitHub** | Fuente oficial del código y de los notebooks. |
| **Google Colab** | Ejecución con GPU. Los notebooks se abren desde GitHub. |
| **Google Drive** | Fotos (zips) y resultados pesados de cada corrida. |

La carpeta de Drive `Mi unidad/project-reconstruction-3d/` es un espejo del
repositorio y la crea automáticamente `notebooks/00_setup_colab.ipynb`:

```
project-reconstruction-3d/
├── data/
│   ├── zips/<objeto>.zip      # fotos subidas desde local
│   └── calibration/           # fotos del tablero/ChArUco
├── results/<objeto>/<metodo>/ # salidas de cada corrida + meta.json
├── work/                      # temporales (no se descargan)
└── checkpoints/               # pesos de modelos de IA (no se descargan)
```

Pasos:

1. **Preparar las fotos (local):** `python scripts/make_data_zips.py` crea
   `data/zips/<objeto>.zip`.
2. **Crear la estructura en Drive:** abrir `00_setup_colab.ipynb` en Colab
   (insignia "Abrir en Colab") y ejecutarlo una vez.
3. **Subir las fotos:** copiar el contenido de `data/zips/` local a
   `data/zips/` en Drive.
4. **Trabajar en Colab:** cada notebook guarda sus salidas en
   `results/<objeto>/<metodo>/` y registra un `meta.json`
   (`recon3d.results.write_meta`).
5. **Traer resultados a local:** descargar `results/` de Drive y pegar su
   contenido en `results/` del repositorio. Git solo versiona los `meta.json`.
6. **Guardar cambios de un notebook:** en Colab, *Archivo → Guardar una copia
   en GitHub* sobre una rama nueva, o descargar el `.ipynb` y hacer commit en
   local. Nunca se edita la misma versión en dos sitios a la vez.

Las dependencias del pipeline están fijadas en `requirements-colab.txt`; las
que Colab ya trae no se reinstalan y sus versiones quedan registradas en cada
`meta.json`.

### Ramas y Pull Requests

- `main` está protegida y contiene solo trabajo revisado.
- Cada implementación nueva se desarrolla en una rama propia y entra a `main`
  mediante un **Pull Request pequeño** que se revisa antes del merge.

## Licencia

Código bajo licencia [MIT](LICENSE). Las fotografías de `data/` no se
publican y no están cubiertas por esta licencia.
