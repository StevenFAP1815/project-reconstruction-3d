# Problema, aplicación y objetivos

Sección 1 del informe (criterio 1 de la rúbrica: problema, objetivos y objetos).

## Problema

Digitalizar un objeto físico en 3D con medidas reales suele requerir equipos
dedicados: escáneres láser, cámaras de profundidad o estudios de fotogrametría
con iluminación controlada. Un teléfono móvil, en cambio, está al alcance de
cualquiera, pero sus fotos no contienen información de profundidad ni de
escala. El problema que aborda este proyecto es **reconstruir en 3D objetos
cotidianos, con su tamaño real, a partir únicamente de fotografías tomadas con
un teléfono**, y determinar hasta qué punto es fiable el resultado según el
material del objeto.

Para ello se comparan dos familias de métodos:

- **Pipeline clásico (COLMAP):** Structure from Motion (SfM) para estimar las
  cámaras y una nube dispersa, y estéreo multivista (MVS) para la nube densa y
  la malla. Se basa en correspondencias explícitas entre fotos (puntos SIFT), y
  por eso depende de que el objeto tenga textura propia, sea opaco y no refleje.
- **Método de IA (VGGT):** una red neuronal que predice las cámaras y la
  profundidad directamente a partir de las fotos, apoyándose en lo aprendido de
  millones de escenas, sin correspondencias explícitas.

## Aplicación

El caso de uso es la **digitalización de artículos del hogar para catálogos de
comercio electrónico e inventarios**: un vendedor o un usuario fotografía un
producto con su teléfono y obtiene un modelo 3D que se puede girar en una página
web (formato `.glb`) y del que se pueden leer las dimensiones. En este contexto,
un error de medida de unos pocos milímetros es aceptable, pero un modelo
incompleto o deformado no lo es.

Los objetos elegidos representan las situaciones que esta aplicación encontraría
en la práctica: envases impresos, objetos de formas complejas, objetos pequeños
y utensilios de cocina metálicos o de vidrio, que son los más difíciles para la
fotogrametría.

## Objetos

| Categoría | Objeto | Por qué representa la categoría | Dificultad anticipada |
|---|---|---|---|
| O1 — Control | Caja de cartón de leche | Superficie mate e impresa, con mucha textura, y forma de prisma con medidas bien definidas | Baja: caso de referencia para validar el pipeline |
| O2 — Geometría compleja | Canasto con flores | Tejido de mimbre con huecos y flores finas que se tapan entre sí | Media: patrón repetitivo y oclusiones |
| O3 — Superficie difícil | Vaso de vidrio | Transparente y reflectante: lo que se ve en la foto es el fondo deformado | Muy alta: casi no hay puntos propios del objeto |
| O4 — Escala distinta | Audífonos | Mayor dimensión de 60 mm (≤ 100 mm) | Media-alta: poca superficie útil por foto y plástico brillante |
| O5 — Aplicado | Colador de cocina | Utensilio de cocina típico de un catálogo del hogar; malla metálica calada | Alta: reflejos, fondo visible a través de la malla y agujeros repetidos |

## Objetivo general

Reconstruir en 3D, con escala métrica, cinco objetos cotidianos a partir de
fotografías propias tomadas con un teléfono, y comparar un pipeline clásico
(SfM + MVS con COLMAP) con un método de IA (VGGT) en precisión, completitud,
tiempo y memoria, para determinar qué método conviene según el tipo de objeto.

## Objetivos específicos y criterios de éxito

| # | Objetivo específico | Criterio de éxito (medible) | Evidencia |
|---|---|---|---|
| OE1 | Calibrar la cámara del teléfono con un tablero de ajedrez | ≥ 15 vistas válidas y error RMS ≤ 0,5 px | `results/calibration/`, notebook `01` |
| OE2 | Estimar las cámaras y la nube dispersa de cada objeto con SfM | ≥ 90 % de fotos registradas en un único modelo y error de reproyección < 1 px | `docs/sfm-results.md`, notebook `02` |
| OE3 | Obtener una nube densa limpia y una malla escalada en milímetros | Error dimensional ≤ 2 % en las medidas que no se usan para escalar; malla exportada en `.ply`, `.obj` y `.glb` | notebook `03` |
| OE4 | Reconstruir los mismos objetos con VGGT y compararlo con COLMAP | Tabla con error dimensional, cobertura angular, tiempo y memoria de GPU de ambos métodos para los cinco objetos | notebook `04`, `docs/master-table.md` |
| OE5 | Explicar los fallos de cada método y recomendar uno por tipo de objeto | Cada fallo asociado a una causa verificada con los datos (por ejemplo, n.º de puntos SIFT o focal estimada) y una recomendación por categoría O1-O5 | `docs/sfm-results.md`, sección de discusión |

## Hipótesis

- **H1.** El pipeline clásico reconstruye bien los objetos opacos y con textura
  (O1) y alcanza el error dimensional ≤ 2 %.
- **H2.** El pipeline clásico falla, o reconstruye solo una parte, en los objetos
  transparentes, reflectantes o con patrones repetitivos (O2, O3, O5), porque
  esos materiales no producen correspondencias SIFT fiables.
- **H3.** VGGT reconstruye los cinco objetos, incluidos los que COLMAP no
  consigue, a cambio de un error dimensional mayor en los objetos con textura,
  porque trabaja a menor resolución (518 px) y no refina las cámaras con bundle
  adjustment.

## Alcance y limitaciones

- El dataset se capturó una sola vez y no se repetirá. La escena no incluye una
  referencia de escala, por lo que cada modelo se escala con una medida física
  del propio objeto y el error se evalúa con las demás medidas
  (`docs/capture-protocol.md`).
- Las medidas físicas se tomaron con una regla de 1 mm de resolución. En las
  medidas pequeñas (por ejemplo, los 20 mm de fondo de los audífonos), esa
  resolución supone hasta ± 5 %, por encima del umbral de 2 %.
- El cómputo se realiza en Google Colab con una GPU Tesla T4, con cuota de uso
  limitada. Esto condiciona la resolución de MVS (1600 px) y el número de fotos
  que recibe VGGT.
