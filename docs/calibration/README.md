# Guía de calibración de la cámara

La calibración mide la **cámara**, no la escena: obtiene la matriz de
intrínsecos K (focal y centro óptico, en píxeles) y los coeficientes de
distorsión de la lente. Por eso se hace con una tanda de fotos aparte, solo
del tablero, y **no obliga a repetir las fotos de los objetos**.

## Tablero en pantalla (sin impresora)

En lugar de imprimirlo, el tablero se muestra en la pantalla del portátil con
`checkerboard.html`. Una pantalla es perfectamente plana, que es justo lo que
exige la calibración (un papel doblado introduce error).

1. Abrir `docs/calibration/checkerboard.html` en el navegador (doble clic).
2. Pulsar `F` para pantalla completa y hacer clic para ocultar el panel.
3. Medir con la regla el ancho total de los **10 cuadros** de una fila y
   dividir entre 10. Anotar el resultado en la tabla de abajo. Medir 10
   cuadros en lugar de 1 reduce el error de la regla a la décima parte.
4. Ajustes de la pantalla:
   - Brillo al 60–80 % y la luz nocturna o el filtro de luz azul desactivados.
   - Sin lámparas reflejándose en la pantalla (mirar a través de la cámara del
     móvil antes de disparar).
5. El portátil se queda quieto; **se mueve el móvil**. Para la calibración da
   igual mover el tablero o la cámara: solo importa su posición relativa.

## Configuración del móvil

Debe ser **la misma que en la sesión 1** de captura (ver
`docs/capture-protocol.md`):

- Lente principal 1×, sin zoom, resolución 3000 × 4000.
- **Móvil en vertical**, igual que en las fotos de los objetos. En horizontal
  las fotos saldrían de 4000 × 3000 px y la calibración no sería aplicable;
  `01_calibration.ipynb` lo detecta y avisa.
- Modo Pro/Manual con el mismo enfoque manual (distancia parecida a la usada
  con los objetos, unos 30–50 cm).
- ISO, obturación y balance de blancos pueden ajustarse para que el tablero se
  vea bien expuesto: no afectan a K. Conviene una obturación rápida
  (1/60 s o más) para evitar fotos movidas.
- HDR, modo belleza e IA de escena desactivados.

## Fotos a tomar (25–30)

El tablero debe verse **entero y nítido** en todas. Se necesitan al menos 15
válidas; se toman más porque algunas se descartan.

| N.º | Posición del tablero en la foto | Inclinación del móvil |
|---|---|---|
| 1–3 | Centro, llenando la foto | De frente |
| 4–7 | Centro | Girado ~30–45° a izquierda, derecha, arriba y abajo |
| 8–11 | En cada una de las 4 esquinas de la foto | De frente |
| 12–15 | En cada una de las 4 esquinas | Ligeramente inclinado |
| 16–19 | En los bordes (arriba, abajo, izquierda, derecha) | De frente |
| 20–25 | Combinaciones libres a distinta distancia | Variada |

Las esquinas y los bordes de la foto son importantes: allí la distorsión de la
lente es mayor y es donde mejor se mide.

Las fotos se guardan en `data/calibration/` y se suben a Drive como
`data/zips/calibration.zip` con `python scripts/make_data_zips.py`.

## Registro

| Campo | Valor |
|---|---|
| Fecha de las fotos | 2026-11-13, 18:12–18:15 |
| Pantalla | Portátil, 1920 × 1080 px, aprox. 34 × 19 cm |
| Tablero | 10 × 7 cuadros (9 × 6 esquinas internas) |
| Tamaño de un cuadro (mm) | 22 × 22, medido con regla sobre un cuadro |
| Cámara | Mismo teléfono (`ALT-LX3`), lente 1×, 5,25 mm, vertical (3000 × 4000) |
| Configuración | Pro/Manual, enfoque manual (MF), 1/60 s, ISO 250 (ISO 125 en las 3 primeras) |
| N.º de fotos tomadas | 162 |
| N.º de fotos seleccionadas | 49, guardadas en `data/calibration/` (28 en la primera selección + 21 añadidas) |

### Criterios de selección

Las 162 fotos se revisaron visualmente y se conservaron 28. Se descartaron:

- **Ráfagas:** fotos tomadas en el mismo segundo (sufijos `_1`, `_2`...), casi
  idénticas entre sí; se conservó una por posición.
- **Tablero incompleto:** fotos donde alguna fila o columna del tablero toca o
  sale del borde de la imagen. El detector necesita el tablero completo.
- **Reflejos:** fotos con un reflejo de luz sobre las esquinas del tablero
  (serie 18:15:17–18:15:20).

Las 28 seleccionadas combinan vistas frontales y oblicuas, a distintas
distancias y con el tablero en el centro, a la izquierda y a la derecha del
encuadre.

**Ampliación de la selección.** En la primera ejecución de
`01_calibration.ipynb` el detector solo encontró el tablero en 8 de las 28
fotos, por debajo de las 15 vistas que exige la rúbrica. Se tomaron dos
medidas:

1. Se añadieron 21 fotos más con el tablero completo, priorizando las vistas
   inclinadas, que son las que más información aportan sobre la focal.
2. Se hizo más robusta la detección: primero se busca el tablero en la foto
   reducida a 2000 px, donde desaparece el moiré de la pantalla, y las
   esquinas se refinan después sobre la foto completa.

Las 113 fotos restantes se conservan fuera del repositorio.

### Observaciones

- En parte de las fotos el navegador no estaba en pantalla completa y la barra
  de tareas de Windows aparece justo debajo del tablero. Esto no afecta a la
  calibración: si el tablero cambia de tamaño entre fotos, la diferencia queda
  absorbida por la posición estimada de la cámara en cada vista, y K y la
  distorsión no dependen del tamaño del cuadro. Si el margen blanco inferior
  queda muy reducido, el detector puede descartar esas fotos.
- **Limitación de cobertura:** con el móvil en vertical y la pantalla en
  horizontal, el tablero ocupa sobre todo la franja central de la foto; los
  extremos superior e inferior del encuadre quedan poco cubiertos. La gráfica
  de cobertura de `01_calibration.ipynb` permite valorar este efecto.
