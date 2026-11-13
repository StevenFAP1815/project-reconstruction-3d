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
| Fecha de las fotos | _por completar_ |
| Pantalla | Portátil, 1920 × 1080 px, aprox. 34 × 19 cm |
| Tablero | 10 × 7 cuadros (9 × 6 esquinas internas) |
| Ancho de 10 cuadros medido con regla (mm) | _por completar_ |
| Tamaño de un cuadro (mm) | _por completar_ (ancho de 10 cuadros / 10) |
| N.º de fotos tomadas | _por completar_ |
