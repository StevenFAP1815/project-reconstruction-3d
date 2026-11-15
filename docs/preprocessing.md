# Preprocesamiento

Este documento reúne los pasos que se aplican a las fotos antes de reconstruir,
el efecto medido de cada uno y la justificación de los pasos que no se
aplicaron.

| Paso | Dónde se aplica | Estado |
|---|---|---|
| Descarte de fotos borrosas | `02` y `02b` | Aplicado en los cinco objetos |
| Mejora de contraste (CLAHE) | `02b` (caja) | Evaluado; efecto medido |
| Corrección de distorsión | `03` (antes de MVS) | Aplicado en los cinco objetos |
| Máscaras del objeto | — | No aplicado; justificado en la sección 4 |

## 1. Descarte de fotos borrosas

Cada foto se puntúa con la **varianza del laplaciano**: el laplaciano resalta
los bordes, y una foto nítida tiene bordes marcados, por lo que su varianza es
alta. Se descartan las fotos con una varianza menor que 0,35 × la mediana de su
propio objeto. Usar la mediana del objeto, y no un umbral fijo, evita castigar a
los objetos con poca textura, cuyas fotos tienen varianza baja aunque estén
enfocadas.

| Objeto | Fotos | Descartadas | % |
|---|---|---|---|
| Caja de cartón | 73 | 5 | 7 % |
| Canasto con flores | 93 | 6 | 6 % |
| Audífonos | 121 | 22 | 18 % |
| Colador de cocina | 86 | 0 | 0 % |
| Vaso de vidrio | 81 | 1 | 1 % |

Las puntuaciones de cada foto están en `results/<objeto>/colmap/sharpness.csv`.
Los audífonos concentran los descartes porque se fotografiaron de cerca, con
poca profundidad de campo (`docs/sfm-results.md`).

## 2. Mejora de contraste (CLAHE)

CLAHE (*Contrast Limited Adaptive Histogram Equalization*) aclara las zonas
oscuras por regiones, sin saturar las claras. Se evaluó sobre la caja en
`02b_sfm_experiments.ipynb`, añadiendo las mejoras de una en una
(`results/caja-carton-leche/colmap-v2/experiments.csv`):

| Configuración | Registradas | Puntos 3D | Track medio | Error (px) | Modelos |
|---|---|---|---|---|---|
| `A_base` | 43 / 68 (63 %) | 5861 | 5,03 | 1,115 | 2 |
| `B_clahe` (A + CLAHE) | 43 / 68 (63 %) | 6970 | 4,78 | 1,127 | 2 |
| `C_sensible` (B + SIFT sensible) | 68 / 68 (100 %) | 19 449 | 3,64 | 1,126 | 1 |
| `D_calibrada` (C + intrínsecos fijos) | 68 / 68 (100 %) | 19 279 | 3,75 | 1,116 | 1 |

CLAHE por sí solo añade un 19 % de puntos 3D, pero no registra ninguna foto
nueva. El salto a 100 % lo produce el detector SIFT más sensible. El experimento
no se repitió en el resto de objetos por su tiempo de ejecución, y porque
`D_calibrada` deformó el canasto y los audífonos (`docs/sfm-results.md`).

## 3. Corrección de distorsión

COLMAP corrige la distorsión de la lente al inicio de la etapa densa
(`pycolmap.undistort_images` en `recon3d.dense.run_mvs`), con los coeficientes
del modelo de cámara de SfM: estimados por autocalibración en `colmap`, o
fijados con la calibración del tablero en `colmap-v2`. PatchMatch busca correspondencias a lo largo de líneas epipolares
rectas, algo que solo es cierto en imágenes sin distorsión. En SfM no hace falta
corregirla antes, porque el modelo de cámara incluye la distorsión y la estima
junto con las poses.

## 4. Máscaras del objeto: por qué no se usan

Una **máscara** es una imagen binaria que indica qué píxeles pertenecen al
objeto. Sirve para que SfM y MVS ignoren el fondo. En este proyecto no se
generaron, por cuatro motivos.

**1. El fondo no se mueve respecto del objeto.** El objeto queda quieto y la
cámara gira a su alrededor. El fondo y la superficie de apoyo forman, junto con
el objeto, una única escena rígida, así que sus puntos cumplen la misma
geometría epipolar que los del objeto y aportan correspondencias válidas para
estimar las poses. Las máscaras son imprescindibles en el caso contrario: cuando
el objeto gira sobre una plataforma y la cámara está fija, el fondo inmóvil
contradice el movimiento del objeto y confunde a SfM.

**2. El fondo negro ya actúa como máscara.** El objeto se fotografió sobre fondo
negro y un apoyo cubierto de negro (`docs/capture-protocol.md`, sección 3). Una
zona oscura y uniforme no tiene gradientes, y SIFT detecta sus puntos donde hay
gradientes, de modo que casi no genera puntos en el fondo. El tejido del apoyo
sí aporta algunos, como se ve en la nube dispersa de los audífonos, pero están
en la misma escena rígida (motivo 1).

**3. La limpieza 3D elimina el fondo después de reconstruir.** El notebook `03`
aísla el objeto en la nube densa (`recon3d.pointcloud.clean_object_cloud`) en
tres pasos: un recorte esférico alrededor del punto al que miran todas las
cámaras, la eliminación del plano de apoyo con RANSAC y la conservación de la
mayor componente conexa. Esto cumple la función de la máscara, pero en 3D, donde
la separación es más fácil: el objeto ocupa una región compacta en el centro de
la órbita, mientras que en cada foto se superpone con el fondo.

**4. Las máscaras fallarían justo en los objetos difíciles.** Segmentar a mano
unas 450 fotos no es viable, y un modelo de segmentación automática separa mal
el vidrio transparente del vaso y la malla calada del colador, porque a través
de ellos se ve el fondo. Una máscara que recorte parte del objeto elimina puntos
válidos y no se puede corregir después; un punto de fondo que se cuela, en
cambio, lo elimina la limpieza 3D.

**Límite de esta decisión.** La limpieza 3D solo actúa sobre la nube densa. Si
un punto del fondo produjera una correspondencia falsa en SfM, la máscara la
habría evitado y la limpieza no. Los resultados no indican que ocurra: en la
caja, el error de reproyección es de 1,1 px y la focal autocalibrada coincide
con la del tablero a menos de un 1 %. Los
fallos de registro del resto de objetos se explican por su material
(`docs/sfm-results.md`), no por el fondo.
