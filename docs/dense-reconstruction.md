# Reconstrucción densa con COLMAP (MVS): decisión de no ejecutarla

El notebook `03_dense_mesh_scale.ipynb` implementa la reconstrucción densa
(PatchMatch Stereo y fusión), la limpieza de la nube, la malla de Poisson, el
escalado métrico y la exportación a `.ply`/`.obj`/`.glb`. El código está
terminado (la limpieza, la medición y la exportación tienen tests con datos
sintéticos en `tests/test_pointcloud.py`), pero **no se ejecutó sobre los cinco
objetos**. Este documento explica por qué.

## Prueba con la caja de cartón

La caja era el mejor candidato para MVS: es el único objeto con las 68 fotos
registradas en un solo modelo (`colmap-v2`), y su cartón impreso tiene la textura
que PatchMatch necesita. Se ejecutó `03` sobre ella en Colab con una GPU Tesla T4
y los parámetros por defecto del notebook (`max_image_size = 1600`).

**Resultado:** tras más de 40 minutos, la etapa densa no había terminado y la
ejecución no llegó a producir la nube fusionada. No se guardó ningún resultado
de esa corrida.

## Por qué se descartó para el resto

1. **El tiempo no es asumible para cinco objetos.** Si el objeto más favorable
   necesita más de 40 minutos sin terminar, los cinco suponen como mínimo unas
   3,5 horas de GPU, sin contar los reintentos. Es una cota inferior: el tiempo
   real de la caja es desconocido, porque no concluyó.
2. **La cuota gratuita de GPU no lo permite.** Durante el proyecto la cuota de
   Colab ya se agotó con SfM (`docs/reproducibility-ethics.md`, sección 5), y una
   sesión puede cerrarse antes de que termine una corrida larga, perdiendo todo
   el trabajo intermedio.
3. **En dos objetos el resultado sería inútil de antemano.** MVS solo calcula
   profundidad en las fotos que SfM registró. El colador tiene 8 fotos
   registradas y el vaso 4 (`docs/sfm-results.md`), todas en un arco corto: la
   nube densa cubriría una pequeña parte del objeto aunque la ejecución
   terminara. El canasto y los audífonos tienen menos de la mitad de sus fotos
   registradas, repartidas en 3 modelos que no comparten sistema de coordenadas.
4. **VGGT cubre el objetivo de obtener una nube densa por objeto.** VGGT
   produjo una nube densa de los cinco objetos con 84–93 s de inferencia por
   objeto en la misma GPU (`docs/vggt-results.md`). El tiempo y el coste que MVS
   no pudo completar son en sí un resultado de la comparación entre métodos.

## Por qué tarda tanto

PatchMatch Stereo estima un mapa de profundidad para cada foto, comparándola
con sus vecinas píxel a píxel, y repite el proceso varias veces para propagar
las buenas estimaciones. Con 68 fotos a 1600 px de lado son unos 130 millones
de píxeles, cada uno evaluado frente a varias fotos vecinas, y en una T4 eso
lleva decenas de minutos. Después, la verificación geométrica entre vistas
(`geom_consistency = True`) y la fusión de los mapas añaden más tiempo.

## Qué se habría podido hacer y no se hizo

- **Reducir la resolución** (`max_image_size = 800`): el número de píxeles baja
  a la cuarta parte y el tiempo, aproximadamente en la misma proporción, a
  cambio de perder detalle fino. No se probó.
- **Usar una GPU más rápida** (L4 o A100, de pago).

## Qué se hizo en su lugar

En vez de dedicar el tiempo de GPU a MVS, se completó y corrigió la otra vía
densa del proyecto, la de VGGT:

- Las nubes densas de VGGT de los cinco objetos se limpiaron de la superficie de
  apoyo y se volvieron a medir en local, sin GPU (`docs/vggt-results.md`). El
  error medio bajó de 21–143 % a 4,5–23 %.
- La comparación entre métodos se apoya en lo que sí se midió en ambos: fotos
  registradas, cobertura, coherencia de la focal con la calibración, tiempo y
  memoria (`docs/master-table.md`).

## Qué se mantiene

- El código de `03` queda en el repositorio como parte del método: cualquiera
  con tiempo de GPU puede ejecutarlo sin cambios.
- La reconstrucción con COLMAP del proyecto llega hasta la nube dispersa de SfM
  (`results/<objeto>/colmap*/sparse.ply`), que es la que se compara con VGGT.
