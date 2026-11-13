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

## Flujo de trabajo

- `main` contiene solo trabajo revisado.
- Cada implementación nueva se desarrolla en una rama propia y entra a `main`
  mediante un **Pull Request pequeño** que se revisa antes del merge.

## Licencia

Código bajo licencia [MIT](LICENSE). Las fotografías de `data/` no se
publican y no están cubiertas por esta licencia.
