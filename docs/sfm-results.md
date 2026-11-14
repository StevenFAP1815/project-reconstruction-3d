# Resultados de SfM (COLMAP) en los cinco objetos

Este documento resume la ejecución del notebook `02_sfm_colmap.ipynb` sobre los
cinco objetos y explica por qué cada objeto obtiene el resultado que obtiene.
Los resultados se conservan tal como salieron; no se repitieron ni se ajustaron
por objeto.

## Configuración usada

Las cinco ejecuciones usan el **commit `4af6802`**, es decir, la configuración
de **línea base** (`A_base`):

- descarte de fotos borrosas (varianza del laplaciano < 0,35 × mediana);
- SIFT con hasta 8192 puntos por foto, sin CLAHE;
- emparejamiento exhaustivo;
- modelo de cámara `SIMPLE_RADIAL` con autocalibración (los intrínsecos no se
  fijan con la calibración del tablero).

La misma configuración en los cinco objetos permite compararlos entre sí: las
diferencias se deben al objeto y a sus fotos, no a ajustes distintos.

La configuración mejorada (`D_calibrada`: CLAHE, SIFT sensible, emparejamiento
guiado e intrínsecos fijos) solo se evaluó sobre la caja, en
`02b_sfm_experiments.ipynb` (`results/caja-carton-leche/colmap-v2/`), donde pasó
de 63 % a 100 % de fotos registradas en un único modelo.

## Resumen

| Objeto | Fotos (usadas / total) | Borrosas | Registradas | Modelos | Puntos 3D | Track medio | Error (px) | f SfM vs tablero |
|---|---|---|---|---|---|---|---|---|
| Caja de cartón | 68 / 73 | 5 | 43 (63 %) | 2 | 5931 | 4,99 | 1,11 | +0,7 % |
| Canasto con flores | 87 / 93 | 6 | 40 (46 %) | 3 | 3284 | 4,26 | 1,22 | +2,4 % |
| Audífonos | 99 / 121 | 22 | 48 (48 %) | 3 | 57 820 | 6,35 | 0,83 | +2,9 % |
| Colador de cocina | 86 / 86 | 0 | 8 (9 %) | 1 | 190 | 4,52 | 1,14 | +5,6 % |
| Vaso de vidrio | 80 / 81 | 1 | 4 (5 %) | 1 | 41 | 2,27 | 1,36 | +32,5 % |

- **Registradas**: fotos cuya pose se estimó, sobre las fotos usadas.
- **Modelos**: número de reconstrucciones independientes; 1 indica que todas las
  fotos registradas comparten un mismo sistema de coordenadas.
- **Track medio**: número medio de fotos en las que se observa cada punto 3D.
- **f SfM vs tablero**: diferencia entre la focal estimada por autocalibración y
  la focal de la calibración (2851,9 px). Una diferencia pequeña indica que la
  geometría reconstruida es coherente.

Los objetos están ordenados de menor a mayor dificultad esperada para SfM. El
porcentaje de registro baja en ese mismo orden, a medida que el material cumple
peor las hipótesis del método.

## Por qué cada resultado

SfM supone que el objeto es **rígido, opaco y con textura propia**, y que su
apariencia no cambia con el punto de vista (superficie *lambertiana*, que refleja
la luz por igual en todas direcciones). Cuanto más se aleja un objeto de esas
hipótesis, menos puntos SIFT fiables produce y menos fotos se registran.

### Caja de cartón: 63 %, 2 modelos

El impreso del cartón aporta mucha textura, por eso el error es bajo y la focal
coincide con la del tablero (+0,7 %). Una de las caras tiene poca textura y las
fotos de esa zona no alcanzan suficientes correspondencias con el modelo
principal: forman un segundo modelo de 25 fotos. El experimento `02b` muestra que
no es un límite del objeto sino de la configuración: con SIFT más sensible e
intrínsecos fijos se registran las 68 fotos en un solo modelo.

### Canasto con flores: 46 %, 3 modelos

El mimbre es un patrón **repetitivo**: muchas zonas se parecen entre sí y SIFT
genera correspondencias ambiguas. Lo confirma el par de ejemplo, con solo un 47 %
de inliers tras RANSAC, frente a un 73 % en la caja. Las flores son estructuras
finas que se tapan entre sí al girar alrededor del objeto. Las fotos se reparten
en tres modelos que no se pueden unir, y el error (1,22 px) es el segundo más alto.

### Audífonos: 48 %, 3 modelos

Es el objeto con más fotos borrosas (22 de 121, un 18 %): es pequeño, se
fotografió de cerca y con poca profundidad de campo. El plástico brillante produce
reflejos que cambian con la posición de la cámara. Aun así, la parte registrada es
la de **mejor calidad** de los cinco: el error más bajo (0,83 px), el track medio
más largo (6,35) y el mayor número de puntos 3D. El problema es de cobertura, no de
precisión: el recorrido queda partido en tres modelos.

### Colador de cocina: 9 %

La malla metálica reúne tres dificultades:

- es **especular**: los reflejos se mueven con la cámara y no corresponden a
  puntos fijos del objeto;
- es **calada**: a través de ella se ve el fondo, así que muchos puntos no
  pertenecen al colador y se mueven de forma distinta;
- es **repetitiva**: los agujeros son idénticos entre sí.

El par de ejemplo tiene solo 125 y 107 puntos SIFT (frente a ~650–950 en la caja)
y el emparejamiento tarda 2,5 s, señal de que casi no hay candidatos. Solo 8 fotos
consecutivas forman un modelo.

### Vaso de vidrio: 5 %

El vidrio es **transparente y refracta la luz**: lo que se ve en la foto es el
fondo deformado por el vaso, y esa deformación cambia con cada punto de vista. Los
puntos detectados no están sobre el vaso ni siguen la geometría de un objeto
rígido. Solo 4 fotos se registran, con 41 puntos 3D y un 31 % de inliers en el par
de ejemplo. La focal estimada se aleja un 32,5 % de la del tablero, lo que indica
que ese pequeño modelo es **degenerado** (la geometría no basta para fijar la
cámara) y no debe usarse como reconstrucción. Es una limitación conocida de los
métodos clásicos basados en correspondencias.

## Conclusiones para el informe

- El rendimiento de SfM depende sobre todo del **material** del objeto: textura
  rica y opaca (caja) frente a superficies repetitivas (canasto), brillantes
  (audífonos), metálicas caladas (colador) y transparentes (vaso).
- La **calibración** sirve como control de calidad: cuando el modelo es fiable la
  focal autocalibrada queda a menos de un 3 % de la del tablero; cuando el modelo
  es degenerado (vaso) se aleja más de un 30 %.
- El **error de reproyección** (0,83–1,36 px) no basta por sí solo para juzgar una
  reconstrucción: el vaso tiene un error razonable con solo 4 fotos. Hay que
  leerlo junto con el porcentaje de registro y el número de modelos.
- El colador y el vaso son los casos en los que el método de IA tiene más margen
  para mejorar al clásico, y por eso son los más informativos para la comparación.

## Reproducibilidad

`results/caja-carton-leche/colmap/meta.json` corresponde a una ejecución
anterior con la misma configuración (commit `9f5d708`): 43 fotos registradas,
5857 puntos 3D y error de 1,110 px, frente a 5931 puntos y 1,113 px en
`notebooks/runs/02_sfm_caja-carton-leche.ipynb`. La pequeña diferencia procede
de partes no deterministas de SIFT en GPU y de RANSAC; el resultado principal
(43 de 68 fotos en 2 modelos) se repite.

## Archivos

- Ejecuciones: `notebooks/runs/02_sfm_<objeto>.ipynb`.
- Métricas: `results/<objeto>/colmap/meta.json` y `sharpness.csv`.
- El modelo binario (`sparse/`), la nube (`sparse.ply`) y las poses
  (`poses.npz`) quedan en Drive y en local, fuera de Git.
