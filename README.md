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
notebooks/      # experimentos por etapa/método
results/        # salidas por objeto y método (solo meta.json en Git)
docs/           # informe y figuras livianas
requirements.txt
```

## Instalación (entorno local)

Requiere **Python 3.11** (varias dependencias, como `pycolmap 3.10`, no
publican paquetes para versiones más nuevas).

```powershell
py -3.11 -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Los métodos de IA se ejecutan en Google Colab (ver `notebooks/README.md`).

## Objetos

| Categoría | Requisito | Objeto elegido |
|---|---|---|
| O1 — Control | Textura rica, mate, forma simple | _por definir_ |
| O2 — Geometría compleja | Concavidades, huecos o detalle fino | _por definir_ |
| O3 — Superficie difícil | Poca textura, brillante o reflectante | _por definir_ |
| O4 — Escala distinta | ≤ 10 cm o ≥ 50 cm | _por definir_ |
| O5 — Libre / aplicado | Vinculado a la aplicación del proyecto | _por definir_ |

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

## Flujo de trabajo

- `main` contiene solo trabajo revisado.
- Cada implementación nueva se desarrolla en una rama propia y entra a `main`
  mediante un **Pull Request pequeño** que se revisa antes del merge.

## Licencia

_Por definir._
