# Protocolo de captura

Este documento registra **cómo** se tomaron las fotografías de cada objeto. Es
la base de la sección "Protocolo de captura" del informe (criterio 2 de la
rúbrica) y justifica la estrategia de escala métrica.

El dataset es definitivo: el proyecto trabaja con las fotografías existentes y
no se repetirá la captura.

## 1. Equipo

Datos extraídos de los metadatos EXIF de las fotografías:

| Campo | Valor |
|---|---|
| Cámara | Teléfono móvil, modelo `ALT-LX3` |
| Lente | Principal (1×), sin zoom |
| Resolución | 3000 × 4000 px (vertical) |
| Distancia focal | 5,25 mm (≈ 24 mm equivalente en 35 mm), igual en todas las fotos |
| Formato | JPEG |
| Soporte | A pulso (sin trípode) |

Como la focal no cambia entre objetos, **una sola calibración de cámara** sirve
para todo el conjunto, siempre que la calibración se haga con la misma lente,
sin zoom y con un enfoque similar (ver `docs/calibration/README.md`).

## 2. Configuración de la cámara

La captura se realizó en dos sesiones, ambas en modo Pro/Manual y con todos
los ajustes fijos dentro de cada sesión. La columna "EXIF" muestra lo que
registró el teléfono; la columna "Configuración aplicada", lo que el autor
ajustó antes de disparar.

### Sesión 1: caja, canasto, colador y vaso (2026-11-13, 01:43–03:16)

| Ajuste | Qué controla | EXIF | Configuración aplicada |
|---|---|---|---|
| Modo de la app de cámara | Automático, Pro/Manual, Retrato, Noche... | — | Pro/Manual |
| ISO | Sensibilidad del sensor; más alto = más ruido | 100 (fijo) | 100 |
| Velocidad de obturación | Tiempo de exposición; más lento = riesgo de movimiento | 1/5 s (fija) | 1/5 s |
| Compensación de exposición (EV) | Brillo general | — | 0 |
| Balance de blancos | Tono de la luz | Manual | Manual (valor en K no registrado) |
| Enfoque | AF automático, AF bloqueado o MF (manual) | — | MF (manual) |
| Estabilización / HDR / IA de escena | Procesado automático que altera la imagen | — | Desactivados |
| Flash | Encendido / apagado | — | Apagado |
| Iluminación | Tipo y dirección de la luz | — | Luz difusa de lámparas cálidas |

### Sesión 2: audífonos (2026-11-13, 12:57–13:03)

| Ajuste | Qué controla | EXIF | Configuración aplicada |
|---|---|---|---|
| Modo de la app de cámara | Automático, Pro/Manual, Retrato, Noche... | — | Pro/Manual |
| ISO | Sensibilidad del sensor; más alto = más ruido | 200 (fijo) | 200 |
| Velocidad de obturación | Tiempo de exposición; más lento = riesgo de movimiento | 1/200 s (fija) | 1/200 s |
| Compensación de exposición (EV) | Brillo general | — | 0 |
| Balance de blancos | Tono de la luz | Manual | Manual (valor en K no registrado) |
| Enfoque | AF automático, AF bloqueado o MF (manual) | — | MF (manual) |
| Estabilización / HDR / IA de escena | Procesado automático que altera la imagen | — | Desactivados |
| Flash | Encendido / apagado | — | Apagado |
| Iluminación | Tipo y dirección de la luz | — | Luz cálida ambiental, incidiendo de forma aproximadamente perpendicular al objeto |

> **Riesgo identificado:** en la sesión 1, la obturación de 1/5 s con el
> teléfono a pulso puede producir fotos movidas. Se verificará en el
> preprocesamiento con un criterio cuantitativo de nitidez (varianza del
> Laplaciano) y se documentará cuántas fotos se descartan por objeto.

## 3. Escena y trayectoria

| Campo | Valor |
|---|---|
| Lugar | Interior |
| Fondo y superficie de apoyo | Fondo negro; el objeto se apoya en un banquito cubierto también de negro |
| Trayectoria | 2–3 órbitas completas alrededor del objeto, a distintas alturas según el objeto |
| Solapamiento | Cada punto del objeto aparece en unas 4–5 fotos consecutivas, lo que equivale a un solapamiento estimado del 75–80 % entre vistas consecutivas |
| Diagrama de la trayectoria | Se generará a partir de las posiciones de cámara estimadas por SfM (notebook de SfM), que muestran la trayectoria real de cada captura |

El solapamiento se estima así: si un punto aparece en N fotos seguidas, cada
foto comparte con la siguiente aproximadamente (N − 1) / N de su contenido;
con N = 4–5 resulta 75–80 %, dentro del rango de 60–80 % que pide la rúbrica.
El valor real se comprobará con la longitud media de *track* que reporta SfM
(número medio de fotos en que aparece cada punto 3D).

## 4. Escala métrica

Las reconstrucciones por SfM y por IA salen sin unidades. Para expresarlas en
milímetros hace falta al menos una medida conocida.

| Campo | Valor |
|---|---|
| Referencia de escala en la escena | No se incluyó (ni regla ni tablero) |
| Instrumento de medición de los objetos | Regla escolar (resolución de 1 mm) |
| Estrategia de escalado | Escalado con una medida física del propio objeto |

**Justificación.** El dataset no se repetirá, por lo que no es posible añadir
una referencia de escala a la escena. Como alternativa, cada modelo se escala
con una medida física del propio objeto y el error dimensional se calcula con
las **otras** medidas, que no intervienen en el escalado. La medida usada
para escalar no sirve para evaluar: su error sería 0 por construcción.

Para escalar se elige la mayor medida bien definida de cada objeto, porque el
error de lectura de la regla (≈ 1 mm) pesa menos en términos relativos
(1 mm sobre 196 mm ≈ 0,5 %).

| Objeto | Medida para escalar | Medidas para evaluar el error |
|---|---|---|
| `caja-carton-leche` | Alto: 196 mm | Ancho: 93 mm · Fondo: 58 mm |
| `canasto-flores` | Diámetro del canasto: 150 mm | Alto del canasto: 85 mm · Alto total: 202 mm |
| `vaso-vidrio` | Alto: 143 mm | Diámetro de la boca: 79 mm · Diámetro de la base: 72 mm |
| `audifonos` | Ancho: 60 mm | Alto: 43 mm · Fondo: 20 mm |
| `colador-cocina` | Largo total: 206 mm | Diámetro del aro: 91 mm · Profundidad de la malla: 45 mm |

Limitación que se debe discutir en el informe: en medidas pequeñas, la
resolución de la regla limita la precisión alcanzable. Por ejemplo, ± 1 mm
sobre los 20 mm del fondo de los audífonos supone ± 5 %, por encima de la
referencia de error ≤ 2 % de la rúbrica.

## 5. Registro por objeto

Horas tomadas del nombre de los archivos (`IMG_AAAAMMDD_HHMMSS`). Medidas en
milímetros, tomadas con regla (± 1 mm aprox., salvo donde se indica).

| Objeto | Cat. | Fotos | Hora | Medida 1 | Medida 2 | Medida 3 | Dificultad de medición |
|---|---|---|---|---|---|---|---|
| `caja-carton-leche` | O1 | 73 | 01:43–02:08 | Alto: 196 | Ancho: 93 | Fondo: 58 | Baja: aristas bien definidas |
| `canasto-flores` | O2 | 93 | 02:08–02:17 | Alto total (con flores): 202 | Alto del canasto: 85 | Diámetro del canasto: 150 | Alta: las flores no tienen una superficie definida |
| `vaso-vidrio` | O3 | 81 | 03:13–03:16 | Alto: 143 | Diámetro de la boca: 79 | Diámetro de la base: 72 | Media: sección circular |
| `audifonos` | O4 | 121 | 12:57–13:03 | Alto: 43 | Ancho: 60 | Fondo: 20 | Media: bordes redondeados |
| `colador-cocina` | O5 | 86 | 02:34–02:38 | Largo total: 206 | Diámetro del aro: 91 | Profundidad de la malla: 45 | Alta: ver nota |

Los cinco objetos cuentan con las tres medidas físicas que exige la rúbrica.
O4 cumple además el requisito de escala distinta: la mayor dimensión de los
audífonos es 60 mm (≤ 100 mm).

**Nota sobre el canasto.** Las flores sobresalen 117 mm por encima del
canasto (202 − 85). Ese valor se deriva de otras dos medidas, por lo que no
cuenta como medida independiente. Como las flores no forman una superficie
lisa, el alto total tiene una incertidumbre mayor que el resto
(aproximadamente ± 5 mm).

**Nota sobre el colador.** El largo total (206 mm) va desde el extremo del
mango hasta el borde opuesto del aro. La parte que filtra se midió por
separado: diámetro externo del aro (91 mm) y profundidad máxima de la malla
(45 mm), medida en perpendicular al plano del aro.

## 6. Estrategia de mitigación para O3 (vaso de vidrio)

La rúbrica pide documentar al menos una estrategia de mitigación para la
superficie difícil, o justificar por qué no se aplicó.

| Campo | Valor |
|---|---|
| Estrategias aplicadas | Fondo negro, que resalta los bordes del vidrio, y luz difusa, que reduce los reflejos especulares |
| Estrategias no aplicadas y motivo | No se aplicó ningún recubrimiento temporal que vuelva mate la superficie (spray mate, talco o polvo similar) por no disponer de estos materiales |

## 7. Privacidad

Las fotos conservan metadatos EXIF, que pueden incluir la ubicación GPS. Por
eso `data/` está excluida de Git. Si alguna foto se publica (por ejemplo, en el
informe), antes se le debe eliminar el EXIF.
