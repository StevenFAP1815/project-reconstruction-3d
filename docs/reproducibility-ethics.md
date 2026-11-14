# Reproducibilidad, ética y viabilidad

Sección 10 del informe (criterio 9 de la rúbrica). Los valores numéricos
proceden de los `meta.json` de `results/` y de `docs/master-table.md`; se
actualizan cuando se añaden las corridas de MVS y VGGT.

## 1. Reproducibilidad

### Cómo se reproduce una corrida

1. Clonar el repositorio y subir los zips de fotos a la carpeta de Drive
   `project-reconstruction-3d/data/zips/` (`scripts/make_data_zips.py`).
2. Ejecutar `notebooks/00_setup_colab.ipynb` una vez para crear las carpetas.
3. Ejecutar de inicio a fin, en Colab con GPU, el notebook de la etapa
   (`01` a `04`), eligiendo el objeto con la variable `OBJECT`.

Cada notebook descarga el código de `main`, lo recarga en memoria y muestra el
commit en uso. Así, la salida guardada indica con qué versión exacta del código
se obtuvo cada resultado.

### Qué se registra en cada corrida

Cada corrida escribe `results/<objeto>/<metodo>/meta.json` con
`recon3d.results.write_meta`. Contiene el número de fotos y de fotos
registradas, el tiempo total, la semilla, el factor de escala, la GPU, la
versión de Python, las versiones de los paquetes, el commit del código y todos
los parámetros del método. Los notebooks ejecutados se guardan con sus salidas
en `notebooks/runs/` como evidencia.

### Versiones

| Componente | Versión | Cómo se fija |
|---|---|---|
| Python (Colab) | 3.13 | Imagen de Colab, registrada en cada `meta.json` |
| pycolmap (COLMAP con CUDA) | `pycolmap-cuda12` 4.2.1 | `requirements-colab.txt` |
| VGGT | commit `a288dd0` del repositorio oficial | Instalación fijada en `04_ai_vggt.ipynb` |
| numpy, OpenCV, torch | 2.4.6, 5.0.0.93, 2.14.1 | Las trae Colab; no se reinstalan para no romper el entorno y quedan registradas en cada `meta.json` |
| Tests (local y CI) | Python 3.13, pytest 8.3.3, numpy 2.2.6, OpenCV 4.11.0.86 | `requirements-dev.txt` |

### Semillas y determinismo

- Todas las corridas usan `SEED = 42` (`recon3d.reproducibility.set_seed`), que
  fija las semillas de `random`, NumPy y, si está instalado, PyTorch.
- Las muestras aleatorias de los notebooks (pares epipolares, puntos mostrados,
  RANSAC propio de la limpieza) usan generadores creados con esa semilla.
- Algunas partes de COLMAP en GPU no son deterministas: dos ejecuciones de SfM
  de la caja con la misma configuración dieron 5857 y 5931 puntos 3D, con el
  mismo número de fotos registradas (43 de 68). El resultado principal se
  repite; los valores finos varían menos de un 2 %.

### Pruebas automáticas

La lógica reutilizable está en `src/recon3d/` y se prueba con pytest con datos
sintéticos: calibración de un tablero simulado, geometría epipolar, limpieza
de nubes, medidas sobre cajas y cilindros, escritura de PLY, OBJ y GLB, y
utilidades de VGGT. GitHub Actions ejecuta los tests en cada Pull Request, y
`main` solo acepta cambios con los tests en verde.

## 2. Costo computacional

Todas las corridas se ejecutaron en Google Colab con una GPU NVIDIA Tesla T4
(16 GB), salvo la calibración, que usa solo CPU.

| Etapa | Objeto | Fotos | Tiempo total |
|---|---|---|---|
| Calibración | Tablero | 49 | 7,0 min (CPU) |
| SfM base | Caja | 73 | 9,2 min |
| SfM `D_calibrada` | Caja | 73 | 9,5 min |
| SfM base | Canasto | 93 | 12,6 min |
| SfM base | Audífonos | 121 | 22,1 min |
| SfM base | Colador | 86 | 7,0 min |
| SfM base | Vaso | 81 | 3,3 min |
| MVS + malla | (pendiente) | | |
| VGGT | (pendiente) | | |

- El tiempo de SfM crece con el número de fotos, porque el emparejamiento
  exhaustivo compara todos los pares: con n fotos hay n(n − 1)/2 pares (2278
  con 68 fotos y 4851 con 99).
- Los objetos que SfM no reconstruye (colador y vaso) tardan menos: el mapeo se
  detiene pronto al no encontrar fotos que registrar.
- La memoria máxima de GPU se mide en VGGT (`peak_gpu_gb` en su `meta.json`),
  porque es el factor que limita el número de fotos que acepta.

## 3. Licencias

| Componente | Licencia | Uso en este proyecto |
|---|---|---|
| Código del proyecto | MIT (`LICENSE`) | Propio |
| COLMAP y pycolmap | BSD de 3 cláusulas | Permitido, incluido el uso comercial |
| OpenCV | Apache 2.0 | Permitido |
| NumPy, PyTorch | BSD | Permitido |
| Código de VGGT | Licencia propia de VGGT (permite uso comercial, excepto militar) | Permitido |
| Pesos `facebook/VGGT-1B` | Solo uso no comercial | Permitido en un trabajo académico. Una aplicación comercial (la de catálogos de comercio electrónico) tendría que usar el checkpoint `VGGT-1B-Commercial`, que requiere solicitud |
| Fotografías | Propias, no publicadas | Fuera de la licencia MIT del código |

## 4. Ética y privacidad

- **Datos propios.** Todas las fotografías las tomó el autor del proyecto, de
  objetos de su propiedad, en un espacio privado. No aparecen personas, rostros
  ni información personal.
- **Metadatos.** Las fotos conservan EXIF, que puede incluir la ubicación GPS.
  Por eso `data/` está excluida de Git y las fotos no se publican. Cualquier
  imagen que se incluya en el informe se publica sin EXIF.
- **Uso de modelos preentrenados.** VGGT se entrenó con conjuntos de datos
  públicos de terceros. Se usa sin reentrenar y respetando su licencia, y sus
  resultados se presentan junto a los del método clásico, con las mismas
  métricas, para no atribuirle más precisión de la que demuestra.
- **Riesgos de la aplicación.** En un catálogo de comercio electrónico, un
  modelo 3D con dimensiones erróneas puede inducir a error al comprador. Por eso
  cada modelo se publica con su error dimensional medido, y los objetos en los
  que el método falla (vidrio, metal calado) se identifican explícitamente en
  lugar de presentar un modelo incompleto como válido.

## 5. Viabilidad

- **Captura.** Fotografiar un objeto llevó entre 3 y 25 minutos con un teléfono
  y luz ambiental (`docs/capture-protocol.md`), sin equipo adicional.
- **Cómputo.** El procesamiento de un objeto con COLMAP tarda entre 3 y 22
  minutos de GPU solo en SfM, más el tiempo de MVS. Con la cuota gratuita de
  Colab, la GPU se agotó durante el proyecto y hubo que esperar a que se
  renovara. Para un uso continuado (por ejemplo, un catálogo con muchos
  productos) haría falta una GPU propia o de pago.
- **Calidad según el objeto.** El método clásico es viable para objetos opacos
  y con textura (caja). Para objetos transparentes, metálicos o con patrones
  repetitivos no es viable sin cambiar la captura (por ejemplo, un recubrimiento
  mate temporal, que no se aplicó; ver `docs/capture-protocol.md`, sección 6) o
  sin recurrir a un método de IA.
