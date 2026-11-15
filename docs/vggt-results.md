# Resultados de VGGT en los cinco objetos

Este documento resume la ejecución de `04_ai_vggt.ipynb` sobre los cinco
objetos (`notebooks/runs/04_ai_vggt_<objeto>.ipynb`, commit `a244b86`), la
corrección posterior de sus medidas y la comparación con SfM de COLMAP.

## Configuración

- Modelo `facebook/VGGT-1B` (commit `a288dd0` del repositorio oficial), en
  float16 sobre una GPU Tesla T4.
- 60 fotos por objeto, repartidas de forma uniforme entre las nítidas (mismo
  filtro de borrosas que en SfM), reducidas a 518 px de lado.
- Se descarta el 50 % de los píxeles de menor confianza.
- Limpieza, escala y medición con el mismo código que `03`
  (`recon3d.pointcloud`), más la eliminación de la superficie de apoyo descrita
  en la sección "Corrección de las medidas".

## Resultado final

Medidas tras eliminar la superficie de apoyo (`results/<objeto>/vggt-nosupport/`):

| Objeto | Medida de escala | Medidas de evaluación (modelo / real) | Error medio | Cobertura | f VGGT vs tablero |
|---|---|---|---|---|---|
| Caja de cartón | Alto 196 mm | Ancho 95,6 / 93 (+2,8 %) · Fondo 64,4 / 58 (+11,0 %) | 6,9 % | 100 % | +1,1 % |
| Canasto con flores | Diámetro 150 mm | Alto total 194,9 / 202 (−3,5 %) · Ancho de las flores 226,9 / 240 (−5,5 %) | 4,5 % | 100 % | +0,3 % |
| Audífonos | Ancho 60 mm | Alto 36,5 / 43 (−15,1 %) · Fondo 26,2 / 20 (+31,1 %) | 23,1 % | 100 % | +10,6 % |
| Colador de cocina | Largo 206 mm | Aro 93,7 / 91 (+3,0 %) · Profundidad 49,7 / 45 (+10,5 %) | 6,7 % | 100 % | +4,5 % |
| Vaso de vidrio | Alto 143 mm | Boca 81,1 / 79 (+2,7 %) · Base 86,8 / 72 (+20,6 %) | 11,6 % | 100 % | +0,6 % |

- **Error medio**: media del error absoluto de las medidas que no se usaron para
  escalar.
- **Cobertura**: sectores de 10° alrededor del objeto con puntos.
- **f VGGT vs tablero**: diferencia entre la focal mediana que predice la red y
  la de la calibración convertida a 518 px (372,65 px).

| Objeto | Inferencia (s) | Total (min) | GPU máx. (GB) |
|---|---|---|---|
| Caja de cartón | 83,9 | 8,2 | 12,57 |
| Canasto con flores | 90,1 | 11,9 | 13,15 |
| Audífonos | 90,4 | 4,6 | 13,15 |
| Colador de cocina | 92,1 | 4,8 | 13,15 |
| Vaso de vidrio | 93,5 | 4,5 | 13,15 |

El tiempo total incluye la carga del modelo; en la caja, también su descarga
(209 s), por ser la primera corrida de la sesión. La corrección de las medidas
se ejecutó en local, sin GPU, en unos 5–8 s por objeto.

## Qué muestran los resultados

**VGGT reconstruye los cinco objetos por todos sus lados.** Se reconocen la
caja con su impreso, el canasto con el asa y las flores, el aro y el mango del
colador, los audífonos y el vaso con su asa
(`docs/figures/vggt_nosupport_<objeto>.png`). SfM registró el 63 % de las fotos
de la caja con la configuración base y solo el 9 % del colador y el 5 % del vaso.

**Las cámaras son coherentes con la calibración.** Sin conocer la cámara, VGGT
predice una focal que difiere menos de un 1,5 % de la calibrada en la caja, el
canasto y el vaso. La diferencia sube en el colador (4,5 %) y en los audífonos
(10,6 %), el objeto fotografiado más de cerca y desde más arriba (elevación
mediana de 61°).

**El vaso, el caso imposible para SfM, queda reconstruido.** SfM obtuvo 41
puntos de 4 fotos y una focal un 32,5 % alejada de la calibrada. VGGT
reconstruye el cuerpo y el asa, con la focal a un 0,6 % y el diámetro de la boca
a un 2,7 %. VGGT no busca correspondencias entre fotos: lo que aprendió de
millones de escenas le permite inferir la forma aunque el vidrio no ofrezca
puntos fiables.

**Ningún objeto alcanza un error medio ≤ 2 %**, pero tres medidas quedan cerca:
el ancho de la caja (2,8 %), la boca del vaso (2,7 %) y el aro del colador
(3,0 %). El error está concentrado en medidas concretas, no repartido:

- **Profundidad del colador** (+10,5 %): es una medida vertical, y la base del
  objeto se fija a mitad de la capa de tela del apoyo (ver la corrección), que
  mide unos 10 mm. Sobre 45 mm, medio grosor de la capa basta para explicar el
  +10 %. Es una causa probable, no verificada por separado.
- **Fondo de la caja** (+11,0 %): es la dimensión más corta (58 mm) y la que se
  ve más de canto en las fotos. En la planta quedan algunos puntos sueltos del
  apoyo junto a una cara. La causa no está verificada.
- **Base del vaso** (+20,6 %): el vidrio refracta el fondo, y la base es la zona
  donde el vaso, su reflejo en la tela y el apoyo se confunden. La causa no está
  verificada.
- **Audífonos** (23,1 %): es el objeto más pequeño (60 mm). A 518 px, una
  dimensión de 20 mm ocupa pocas decenas de píxeles, y las fotos se tomaron
  desde arriba, lo que deja los laterales poco observados. Tras quitar el apoyo
  solo quedan 189 239 puntos (el 10 % de la nube), porque el apoyo ocupaba casi
  todo el encuadre.

**Coste.** La inferencia tarda entre 84 y 93 s por objeto, independientemente
del material, frente a los 3–22 minutos de SfM y a la etapa densa de COLMAP,
que no concluyó en más de 40 minutos (`docs/dense-reconstruction.md`). A cambio,
necesita unos 13 GB de memoria de GPU, casi toda la T4, y por eso solo acepta
60 fotos a 518 px.

## Corrección de las medidas: la superficie de apoyo

### El problema

La limpieza de `04` no eliminó el banquito cubierto de tela sobre el que se
apoyaba cada objeto: en las nubes aparecía como un disco de 200–250 mm. Como la
caja envolvente lo incluía, las medidas originales (`results/<objeto>/vggt/`)
mezclaban objeto y apoyo, con errores medios del 21 al 143 %. En los audífonos,
la escala misma se fijó con el diámetro del disco.

`clean_object_cloud` busca la mesa como el plano dominante de toda la escena y
solo la acepta si casi no hay puntos por debajo. Con un disco de tela que forma
una capa de unos 10 mm de grosor, inclinado 12° en la caja, esas condiciones no
se cumplieron en cuatro de los cinco objetos.

### La solución

`recon3d.pointcloud.remove_support`, aplicada con `scripts/remeasure_vggt.py`
sobre las nubes ya guardadas (sin repetir la inferencia):

1. **Plano del apoyo** con RANSAC, limitado a planos a menos de 30° de la
   vertical: el disco es el plano casi horizontal con más puntos.
2. **Capa de tela.** Se elimina todo lo que queda por debajo de la parte alta de
   la capa (6 % de la anchura del apoyo, unos 11 mm en la caja).
3. **Base del objeto.** Donde el objeto toca el apoyo (celdas de una rejilla
   horizontal con puntos justo por encima de la capa), se conserva la mitad
   superior de la capa, para no recortar la base. Las celdas bajo partes que no
   tocan el apoyo, como el mango del colador, no cuentan como contacto.
4. **Componente principal**, marco del objeto con la normal del apoyo como
   vertical, escala y error dimensional, con las mismas funciones que `03`.

Los parámetros se eligieron mirando las figuras de comprobación, y cada uno
corrige un fallo observado:

| Parámetro | Valor | Motivo |
|---|---|---|
| Grosor de la capa | 6 % | Con 1 %, la tela de la caja (≈ 5 % de grosor) seguía casi entera. |
| Altura de contacto | 8 % | Con 12 %, el mango del colador contaba como contacto y quedaba tela debajo. |
| Inclinación del marco | ≤ 5° respecto al apoyo | Con 35°, el valor de `04`, el canasto quedaba inclinado: las flores no tienen caras planas que orienten la caja envolvente. La normal del apoyo es una vertical medida directamente. En la caja el resultado es idéntico con 5° y con 35°. |
| Centro de la cobertura | Mediana de los puntos | El centro de la caja envolvente se desplazaba hacia el mango del colador y daba un 56 % de cobertura sin que faltara ninguna parte. |

Un test sintético (`tests/test_pointcloud.py`) comprueba que se elimina un disco
de tela, también inclinado 12°, sin perder la base del objeto ni un mango
horizontal.

### Cambio en la medida del canasto

El diámetro del canasto, que fija su escala, se medía en la franja del 5 al 35 %
de la altura. Una vez quitado el apoyo, las figuras muestran flores colgando por
los lados hasta un 25 % de la altura. El diámetro medido es estable entre las
franjas 5–15 % y 5–20 % (126 mm) y salta a 150 mm con la franja 5–35 %, porque
incluye flores. Por eso la franja pasó a 5–20 % (`recon3d/measurements.py`).

Este cambio se hizo después de ver los resultados, por lo que se declara con
los dos valores:

| Franja del diámetro | Alto total | Ancho de las flores | Error medio |
|---|---|---|---|
| 5–35 % (original) | 164,1 mm (−18,8 %) | 191,1 mm (−20,4 %) | 19,6 % |
| 5–20 % (corregida) | 194,9 mm (−3,5 %) | 226,9 mm (−5,5 %) | 4,5 % |

Que las dos medidas de evaluación tuvieran casi el mismo error (−19 y −20 %)
indicaba un problema en la escala y no en la forma: si la escala es errónea,
todas las medidas se desvían en la misma proporción.

### Limitaciones de la corrección

- La base se fija a mitad de la capa de tela, así que las alturas tienen una
  incertidumbre de hasta medio grosor de la capa (≈ 3 % del ancho del apoyo).
- Los parámetros se ajustaron con estas cinco nubes. Son fracciones del tamaño
  del apoyo, no milímetros, pero no se han probado con otros datos.

## Archivos

- Ejecuciones: `notebooks/runs/04_ai_vggt_<objeto>.ipynb`.
- Corrida original: `results/<objeto>/vggt/` (`meta.json`, `measurements.csv`,
  `cleaning.csv`). Se conserva sin cambios.
- Medidas corregidas: `results/<objeto>/vggt-nosupport/` (`meta.json`,
  `measurements.csv`) y figuras en `docs/figures/vggt_nosupport_<objeto>.png`.
- Las nubes (`object_clean_mm.ply`, `object_mm.ply`) y las cámaras
  (`cameras.npz`) quedan en Drive y en local, fuera de Git.
