# Protocolo de captura

Este documento registra **cómo** se tomaron las fotografías de cada objeto.
Sin esta información los resultados no se pueden reproducir ni comparar, y la
escala métrica no se puede justificar en el informe.

Los campos marcados como _por completar_ los debe llenar quien hizo la captura.

## 1. Equipo

Datos extraídos de los metadatos EXIF de las fotografías:

| Campo | Valor |
|---|---|
| Cámara | Teléfono móvil, modelo `ALT-LX3` |
| Resolución | 3000 × 4000 px (vertical) |
| Distancia focal | 5,25 mm (≈ 24 mm equivalente en 35 mm) |
| Zoom | Sin zoom: la focal es la misma en los 5 objetos |
| Formato | JPEG |
| Trípode / soporte | _por completar_ |
| Modo de enfoque y exposición (auto / bloqueado) | _por completar_ |

Como la focal no cambia entre objetos, **una sola calibración de cámara** sirve
para todo el conjunto, siempre que no se haya usado zoom digital ni otra lente.

## 2. Condiciones generales

| Campo | Valor |
|---|---|
| Fecha de captura | 2026-11-13 |
| Lugar (interior / exterior) | _por completar_ |
| Iluminación (natural, lámpara, difusa, dirección) | _por completar_ |
| Fondo y superficie de apoyo | _por completar_ |
| Patrón de movimiento (órbitas, alturas, solapamiento aprox.) | _por completar_ |

## 3. Referencia de escala métrica

Las reconstrucciones por SfM y por IA salen en una escala arbitraria. Para
convertirlas a milímetros hace falta una referencia de tamaño conocido
visible en las fotos.

| Campo | Valor |
|---|---|
| Objeto de referencia (regla, tablero de ajedrez, marcador ArUco, ...) | _por completar_ |
| Medida conocida de la referencia (mm) | _por completar_ |
| Instrumento usado para medir los objetos (regla, calibre) | _por completar_ |

## 4. Registro por objeto

Las horas salen del nombre de los archivos (`IMG_AAAAMMDD_HHMMSS`).

| Objeto | Categoría | Fotos | Hora (inicio–fin) | Medidas reales (alto × ancho × fondo, mm) | Observaciones |
|---|---|---|---|---|---|
| `caja-carton-leche` | O1 | 73 | 01:43–02:08 | _por completar_ | _por completar_ |
| `canasto-flores` | O2 | 93 | 02:08–02:17 | _por completar_ | _por completar_ |
| `vaso-vidrio` | O3 | 81 | 03:13–03:16 | _por completar_ | _por completar_ |
| `audifonos` | O4 | 121 | 12:57–13:03 | _por completar_ (debe ser ≤ 100 mm o ≥ 500 mm) | _por completar_ |
| `colador-cocina` | O5 | 86 | 02:34–02:38 | _por completar_ | _por completar_ |

## 5. Privacidad

Las fotos conservan metadatos EXIF, incluida posiblemente la ubicación GPS.
Por eso `data/` está excluida de Git. Si alguna foto se publica (por ejemplo,
en el informe), se debe eliminar antes su EXIF.
