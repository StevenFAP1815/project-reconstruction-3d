# Resultados de VGGT en los cinco objetos

Este documento resume la ejecución de `04_ai_vggt.ipynb` sobre los cinco
objetos (`notebooks/runs/04_ai_vggt_<objeto>.ipynb`, commit `a244b86`) y la
compara con SfM de COLMAP.

## Configuración

- Modelo `facebook/VGGT-1B` (commit `a288dd0` del repositorio oficial), en
  float16 sobre una GPU Tesla T4.
- 60 fotos por objeto, repartidas de forma uniforme entre las nítidas (mismo
  filtro de borrosas que en SfM), reducidas a 518 px de lado.
- Se descarta el 50 % de los píxeles de menor confianza.
- Limpieza, escala y medición con el mismo código y los mismos parámetros que
  `03` (`recon3d.pointcloud`).

## Resumen

| Objeto | Fotos a VGGT | Cobertura | f VGGT vs tablero | Inferencia (s) | Total (min) | GPU máx. (GB) | Puntos del objeto |
|---|---|---|---|---|---|---|---|
| Caja de cartón | 60 / 68 nítidas | 100 % | +1,1 % | 83,9 | 8,2 | 12,57 | 1 532 215 |
| Canasto con flores | 60 / 87 | 100 % | +0,3 % | 90,1 | 11,9 | 13,15 | 1 866 615 |
| Audífonos | 60 / 99 | 100 % | +10,6 % | 90,4 | 4,6 | 13,15 | 1 928 428 |
| Colador de cocina | 60 / 86 | 100 % | +4,5 % | 92,1 | 4,8 | 13,15 | 1 488 793 |
| Vaso de vidrio | 60 / 80 | 100 % | +0,6 % | 93,5 | 4,5 | 13,15 | 674 215 |

- **Cobertura**: sectores de 10° alrededor del objeto con puntos.
- **f VGGT vs tablero**: diferencia entre la focal mediana que predice la red y
  la de la calibración, convertida a 518 px (372,65 px).
- **Total**: incluye la carga del modelo. En la caja incluye además su descarga
  (209 s), porque fue la primera corrida de la sesión.

## Qué muestran los resultados

**La forma de los cinco objetos se reconoce.** Las vistas en planta, alzado y
perfil (celda 17 de cada notebook) muestran la caja con su impreso, el canasto
con el asa y las flores, el aro y el mango del colador, los audífonos y el vaso
con su asa. Es la diferencia principal con SfM, que registró el 5 % de las fotos
del vaso y el 9 % de las del colador.

**Las cámaras son coherentes con la calibración.** Sin conocer la cámara, VGGT
predice una focal que difiere menos de un 1,5 % de la calibrada en la caja, el
canasto y el vaso. La diferencia sube en el colador (4,5 %) y en los audífonos
(10,6 %), el objeto fotografiado más de cerca y desde más arriba (elevación
mediana de 61°).

**El vaso, el caso más difícil para SfM, es el resultado más destacado.** SfM
obtuvo 41 puntos de 4 fotos y una focal un 32,5 % alejada de la calibrada. VGGT
reconstruye el cuerpo y el asa del vaso, con la focal a un 0,6 %, y su diámetro
de boca (medido en el 10 % superior, lejos del apoyo) queda a 79,98 mm frente a
79 mm reales: un 1,2 % de error. VGGT no busca correspondencias entre fotos: lo
que aprendió de millones de escenas le permite inferir la forma aunque el
vidrio no ofrezca puntos fiables.

**Coste.** La inferencia tarda entre 84 y 93 s por objeto, independientemente
del material, frente a los 3–22 minutos de SfM y a la etapa densa de COLMAP,
que no concluyó en más de 40 minutos (`docs/dense-reconstruction.md`). A cambio,
necesita unos 13 GB de memoria de GPU, casi toda la T4, y por eso solo acepta
60 fotos a 518 px.

## Limitación: el error dimensional no es válido todavía

La limpieza no eliminó la **superficie de apoyo** (el banquito cubierto de
negro). En las figuras aparece como un disco de unos 200–250 mm bajo cada
objeto. El paso que busca el plano de la mesa con RANSAC solo lo detectó en el
vaso (`table_plane_found` en `meta.json`), y aun ahí quedó parte del disco.
`clean_object_cloud` solo acepta un plano como mesa si forma menos de 30° con
la horizontal de la órbita y tiene menos de un 10 % de puntos por debajo. Hay
dos causas posibles, aún sin verificar: que el plano dominante que encuentra
RANSAC sea otra superficie (por ejemplo, una cara de la caja), o que el disco
no cumpla esas condiciones porque la tela cae por los bordes del asiento.

Como la caja envolvente incluye el disco, las medidas de la tabla siguiente
mezclan el objeto con su apoyo:

| Objeto | Error medio (%) | Efecto del apoyo |
|---|---|---|
| Caja de cartón | 142,9 | Ancho y fondo miden el disco (187 y 165 mm frente a 93 y 58 mm). |
| Canasto con flores | 21,3 | Afecta en parte; el diámetro de escala se mide entre el 5 y el 35 % de la altura. |
| Audífonos | 30,8 | La **escala** se fijó con el disco: el ancho de 60 mm se asignó a su diámetro. |
| Colador de cocina | 64,8 | El "diámetro del aro" mide el disco (197 mm frente a 91 mm). |
| Vaso de vidrio | 133,5 | Solo el diámetro de la base (263 mm) está afectado; la boca es válida (1,2 %). |

Estos valores **no miden la precisión de VGGT** y no deben citarse como tal.
Para hacerlo hay que eliminar el apoyo y volver a medir. Las nubes ya escaladas
(`object_clean_mm.ply`) están guardadas, así que la nueva medición no necesita
GPU.

## Archivos

- Ejecuciones: `notebooks/runs/04_ai_vggt_<objeto>.ipynb`.
- Métricas: `results/<objeto>/vggt/meta.json`, `measurements.csv` y
  `cleaning.csv`.
- Nube limpia en mm (`object_clean_mm.ply`) y cámaras (`cameras.npz`): en Drive
  y en local, fuera de Git.
