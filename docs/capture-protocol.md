# Protocolo de captura

Este documento registra **cómo** se tomaron las fotografías de cada objeto. Es
la base de la sección "Protocolo de captura" del informe (criterio 2 de la
rúbrica) y permite justificar la escala métrica.

Convención: los campos `_por completar_` los rellena quien hizo la captura.

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
para todo el conjunto, siempre que la calibración se haga con la misma lente y
sin zoom.

## 2. Configuración de la cámara

La captura se hizo en dos sesiones con ajustes distintos. La columna "EXIF"
muestra lo que registró el teléfono en las fotos; la columna "Configuración
aplicada" la rellena el autor con lo que ajustó manualmente antes de disparar.

### Sesión 1: caja, canasto, colador y vaso (2026-11-13, 01:43–03:16)

| Ajuste | Qué controla | EXIF | Configuración aplicada |
|---|---|---|---|
| Modo de la app de cámara | Automático, Pro/Manual, Retrato, Noche... | — | _por completar_ |
| ISO | Sensibilidad del sensor; más alto = más ruido | 100 (fijo) | _por completar_ |
| Velocidad de obturación | Tiempo de exposición; más lento = riesgo de movimiento | 1/5 s (fija) | _por completar_ |
| Compensación de exposición (EV) | Brillo general (p. ej. −0,7, 0, +1) | — | _por completar_ |
| Balance de blancos | Tono de la luz (p. ej. 4000 K, "Fluorescente") | Manual | _por completar_ |
| Enfoque | AF automático, AF bloqueado o MF (manual) | — | _por completar_ |
| Estabilización / HDR / IA de escena | Procesado automático que altera la imagen | — | _por completar_ |
| Flash | Encendido / apagado | — | _por completar_ |

### Sesión 2: audífonos (2026-11-13, 12:57–13:03)

| Ajuste | Qué controla | EXIF | Configuración aplicada |
|---|---|---|---|
| Modo de la app de cámara | Automático, Pro/Manual, Retrato, Noche... | — | _por completar_ |
| ISO | Sensibilidad del sensor; más alto = más ruido | 200 (fijo) | _por completar_ |
| Velocidad de obturación | Tiempo de exposición; más lento = riesgo de movimiento | 1/200 s (fija) | _por completar_ |
| Compensación de exposición (EV) | Brillo general (p. ej. −0,7, 0, +1) | — | _por completar_ |
| Balance de blancos | Tono de la luz (p. ej. 4000 K, "Fluorescente") | Manual | _por completar_ |
| Enfoque | AF automático, AF bloqueado o MF (manual) | — | _por completar_ |
| Estabilización / HDR / IA de escena | Procesado automático que altera la imagen | — | _por completar_ |
| Flash | Encendido / apagado | — | _por completar_ |
| Iluminación (si difiere de la sesión 1) | Tipo y dirección de la luz | — | _por completar_ |

> **Riesgo identificado:** en la sesión 1 la obturación de 1/5 s con el
> teléfono a pulso puede producir fotos movidas. Se verificará en el
> preprocesamiento con un criterio cuantitativo de nitidez (varianza del
> Laplaciano) y se documentará cuántas fotos se descartan por objeto.

## 3. Condiciones generales

| Campo | Valor |
|---|---|
| Lugar | Interior |
| Iluminación | Luz difusa de lámparas cálidas |
| Fondo y superficie de apoyo | Fondo negro; el objeto se apoya en un banquito cubierto también de negro |
| Trayectoria | 2–3 órbitas completas alrededor del objeto, a distintas alturas según el objeto |
| Solapamiento | Cada punto del objeto aparece en unas 4–5 fotos consecutivas. Solapamiento estimado entre vistas consecutivas: _por completar_ (la rúbrica pide 60–80 %) |
| Diagrama de la trayectoria | _por completar_ (la rúbrica lo pide; puede ser un esquema a mano de las órbitas vistas desde arriba y de lado) |

## 4. Referencia de escala métrica

Las reconstrucciones por SfM y por IA salen sin unidades. Para convertirlas a
milímetros hace falta una medida conocida.

| Campo | Valor |
|---|---|
| Referencia de escala en la escena | **No se incluyó** (ni regla ni tablero) |
| Instrumento de medición de los objetos | Regla escolar (resolución de 1 mm) |
| Estrategia de escalado | _por decidir_: (A) escalar con una medida del propio objeto y evaluar el error con las demás, o (B) repetir la captura con una referencia visible |

> **Pendiente:** la rúbrica exige una referencia de escala visible en la
> escena para todos los objetos. Si se opta por la estrategia A, el informe
> debe justificarlo y la medida usada para escalar no puede usarse después
> para calcular el error dimensional (su error sería 0 por construcción).

## 5. Registro por objeto

Horas tomadas del nombre de los archivos (`IMG_AAAAMMDD_HHMMSS`). Medidas en
milímetros, tomadas con regla (± 1 mm aprox.).

| Objeto | Cat. | Fotos | Hora | Medida 1 | Medida 2 | Medida 3 | Dificultad de medición |
|---|---|---|---|---|---|---|---|
| `caja-carton-leche` | O1 | 73 | 01:43–02:08 | Alto: 196 | Ancho: 93 | Fondo: 58 | Baja: aristas bien definidas |
| `canasto-flores` | O2 | 93 | 02:08–02:17 | Alto: 202 | Diámetro: 240 | _por completar_ | Alta: forma circular e irregular; medidas aproximadas |
| `vaso-vidrio` | O3 | 81 | 03:13–03:16 | Alto: 143 | Diámetro: 79 | _por completar_ | Media: el diámetro sirve como ancho y fondo |
| `audifonos` | O4 | 121 | 12:57–13:03 | Alto: 43 | Ancho: 60 | Fondo: 20 | Media: bordes redondeados |
| `colador-cocina` | O5 | 86 | 02:34–02:38 | Largo total: 206 | Diámetro del aro: 91 | Profundidad de la malla: 45 | Alta: ver nota |

La rúbrica pide **al menos tres medidas físicas por objeto**. Al canasto y al
vaso les falta una tercera; por ejemplo, el diámetro de la base o el de la
boca (en el vaso suelen ser distintos).

O4 cumple el requisito de escala: la mayor dimensión de los audífonos es
60 mm (≤ 100 mm).

**Nota sobre el colador.** El largo total (206 mm) va desde el extremo del
mango hasta el borde opuesto del aro. La parte que filtra se midió por
separado: diámetro externo del aro (91 mm) y profundidad máxima de la malla
(45 mm), medida en perpendicular al plano del aro.

## 6. Estrategia de mitigación para O3 (vaso de vidrio)

La rúbrica pide documentar al menos una estrategia de mitigación para la
superficie difícil, o justificar por qué no se aplicó.

| Campo | Valor |
|---|---|
| Estrategia aplicada | _por completar_ (p. ej. el fondo negro resalta los bordes del vidrio; luz difusa para reducir reflejos) |
| Estrategias no aplicadas y motivo | _por completar_ (p. ej. no se usó spray mate porque el experimento busca ver cómo falla cada método con vidrio real) |

## 7. Privacidad

Las fotos conservan metadatos EXIF, que pueden incluir la ubicación GPS. Por
eso `data/` está excluida de Git. Si alguna foto se publica (por ejemplo, en el
informe), antes se le debe eliminar el EXIF.
