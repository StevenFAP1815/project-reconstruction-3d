# Protocolo de captura

Este documento registra **cómo** se tomaron las fotografías de cada objeto.

## 1. Equipo

Datos extraídos de los metadatos EXIF de las fotografías:

| Campo | Valor |
|---|---|
| Cámara | Teléfono móvil, modelo `ALT-LX3` |
| Resolución | 3000 × 4000 px (vertical) |
| Distancia focal | 5,25 mm (≈ 24 mm equivalente en 35 mm) |
| Zoom | Sin zoom: la focal es la misma en los 5 objetos |
| Formato | JPEG |
| Trípode / soporte | A pulso de mano |
| Modo de enfoque y exposición (auto / bloqueado) | manual/bloqueado |

La focal no cambia entre objetos, **una sola calibración de cámara** sirve
para todo el conjunto.

## 2. Condiciones generales

| Campo | Valor |
|---|---|
| Fecha de captura | 2026-11-13 |
| Lugar (interior / exterior) |interior |
| Iluminación (natural, lámpara, difusa, dirección) | difusa/ luces calidas |
| Fondo y superficie de apoyo | fondo negro y un banquito de apoyo, tambien con fondo negro |
| Patrón de movimiento (órbitas, alturas, solapamiento aprox.) | 2-3 orbitas a distintas alturas según el objeto. 4-5 fotos de solapamiento |

## 3. Referencia de escala métrica

Las reconstrucciones por SfM y por IA salen en una escala arbitraria. Para
convertirlas a milímetros hace falta una referencia de tamaño conocido
visible en las fotos.

| Campo | Valor |
|---|---|
| Objeto de referencia (regla, tablero de ajedrez, marcador ArUco, ...) | No se aplicó un objeto de referencia |
| Medida conocida de la referencia (mm) | No se aplicó un objeto de referencia |
| Instrumento usado para medir los objetos (regla, calibre) | regla escolar estándar |

## 4. Registro por objeto

Las horas salen del nombre de los archivos (`IMG_AAAAMMDD_HHMMSS`).

| Objeto | Categoría | Fotos | Hora (inicio–fin) | Medidas reales aprox. (alto × ancho × fondo, mm) | Observaciones |
|---|---|---|---|---|---|
| `caja-carton-leche` | O1 | 73 | 01:43–02:08 | 196 x 93 x 58 |medición facil esquinas definidas |
| `canasto-flores` | O2 | 93 | 02:08–02:17 | 202 x diametro (240) | medición complicada las medidas son muy aproximadas, considerar que el florero es circular |
| `vaso-vidrio` | O3 | 81 | 03:13–03:16 | 143 x diametro (79) | medición relativamente sencilla, considerar diametro para profundidad |
| `audifonos` | O4 | 121 | 12:57–13:03 | 43 x 60 x 20 | medición relativamente sencilla, bordes redondeados dificultan una medidad precisa |
| `colador-cocina` | O5 | 86 | 02:34–02:38 | 45 x 206 x diametro (91) | medición compleja: la longitud total (206 mm) abarca el eje mayor desde el extremo distal del mango hasta el borde opuesto del aro; mientras que la sección funcional de filtrado se caracterizó de forma independiente mediante el diámetro externo del aro (91 mm) y la altura o profundidad máxima de la malla (45 mm) medida perpendicularmente al plano del aro. |

## 5. Privacidad

Las fotos conservan metadatos EXIF, incluida posiblemente la ubicación GPS.
Por eso `data/` está excluida de Git. Si alguna foto se publica (por ejemplo,
en el informe), se debe eliminar antes su EXIF.
