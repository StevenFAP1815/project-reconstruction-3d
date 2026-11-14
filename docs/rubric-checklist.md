# Checklist de la rúbrica (Bloque 2)

Resumen operativo de la *Rúbrica Proyecto Integrador — Bloque 2: Reconstrucción
3D de 5 objetos*. No sustituye al documento original; sirve para seguir el
avance del proyecto. Se actualiza en cada PR que avance un criterio.

Estados: `pendiente` · `en curso` · `listo`.

## Hito de avance (Clase 29)

| Entregable | Estado |
|---|---|
| Problema y objetivos | listo (`docs/problem-objectives.md`) |
| 5 objetos elegidos y justificados | en curso (tabla O1-O5 en README) |
| Calibración terminada | listo (`results/calibration/`, RMS 0,81 px) |
| Dataset de al menos 2 objetos capturado | listo (5 objetos) |
| SfM disperso de al menos 1 objeto | listo (5 objetos, `docs/sfm-results.md`) |
| Plan de evaluación (métricas y medidas físicas) | en curso (medidas y estrategia de escala en `docs/capture-protocol.md`) |

## Criterios (100 pts)

| # | Criterio | Pts | Requisitos clave para "Excelente" | Estado |
|---|---|---|---|---|
| 1 | Problema, objetivos y objetos | 8 | Aplicación real, objetivos medibles, O1-O5 con dificultad anticipada | listo (`docs/problem-objectives.md`) |
| 2 | Protocolo de captura y dataset | 10 | Focal fija; ISO, exposición y enfoque bloqueados; iluminación difusa; ≥ 2 órbitas con 60-80 % de solapamiento; referencia de escala; medidas físicas; tabla por objeto; **diagrama de trayectoria** | en curso (`docs/capture-protocol.md`; diagramas de trayectoria y solapamiento medido en `docs/figures/`) |
| 3 | Calibración | 8 | Tablero o ChArUco con ≥ 15 vistas; K, distorsión, RMS ≤ 0,5 px; modelo pinhole; comparar con intrínsecos de SfM | listo (42 vistas, RMS 0,81 px justificado por moiré; comparación en `docs/sfm-results.md`) |
| 4 | Preprocesamiento | 6 | Filtro de borrosas cuantitativo (varianza del Laplaciano); corrección de distorsión; máscaras; **medir el efecto** de cada paso | en curso (borrosas y CLAHE medidos en `02b`; distorsión en `03`; sin máscaras) |
| 5 | SfM y geometría epipolar | 14 | SIFT, RANSAC, F/E, registro incremental, triangulación, BA; por objeto: % registradas (≥ 90 %), n.º de puntos, longitud media de track, error de reproyección (< 1 px); líneas epipolares en un par | listo (5 objetos; ≥ 90 % solo en la caja con `D_calibrada`; ver `docs/sfm-results.md`) |
| 6 | Densa, malla y escala | 12 | MVS; limpieza de outliers; malla Poisson o ball pivoting; escala en mm; exportar .ply/.obj/.glb; justificar parámetros | en curso (`03_dense_mesh_scale.ipynb`) |
| 7 | Comparación con IA | 10 | Mismo objeto y mismas imágenes; explicar el principio del método; comparar precisión, completitud, tiempo y memoria | en curso (`04_ai_vggt.ipynb`: error dimensional, cobertura angular, tiempo y memoria de GPU) |
| 8 | Evaluación y discusión | 14 | Tabla maestra objeto × método; error dimensional (≤ 2 %); figuras de los 5 modelos; análisis de fallos con causas verificadas | en curso (tabla maestra automática en `docs/master-table.md`; análisis de SfM en `docs/sfm-results.md`) |
| 9 | Reproducibilidad, ética y viabilidad | 6 | Notebook de inicio a fin; versiones fijadas; semillas; `results/` y `meta.json` por corrida; costo computacional; licencias; ética | en curso (`docs/reproducibility-ethics.md`; faltan los costos de MVS y VGGT) |
| 10 | Conclusiones | 4 | Responder a cada objetivo; qué método conviene para cada tipo de objeto | pendiente |
| 11 | Exposición y demostración | 8 | Demostración en vivo de los 5 modelos en un visor 3D | pendiente |

## Condiciones para todos los objetos

- [x] Captura propia con 40-150 fotos por objeto (73-121 en todos).
- [x] Solapamiento de 60-80 % y al menos 2 órbitas de cámara (documentado en `docs/capture-protocol.md`, sección 3).
- [ ] Referencia de escala visible en la escena (regla, ArUco/ChArUco o tablero).
- [x] Al menos 3 medidas físicas por objeto con calibrador o cinta (regla, ± 1 mm).
- [ ] O3 (vaso de vidrio): documentar al menos una estrategia de mitigación o justificar por qué no se aplicó.

Si se reconstruyen menos de 5 objetos, los criterios 5, 6 y 8 se califican de
forma proporcional.

## Verificación por objeto (sección 6 de la rúbrica)

| Evidencia | O1 caja | O2 canasto | O3 vaso | O4 audífonos | O5 colador |
|---|---|---|---|---|---|
| Dataset propio (40-150) con referencia de escala | sí (73), escala por medida | sí (93), escala por medida | sí (81), escala por medida | sí (121), escala por medida | sí (86), escala por medida |
| ≥ 3 medidas físicas registradas | sí | sí (4) | sí | sí | sí |
| SfM: poses + nube dispersa (≥ 90 % registradas) | 100 % (`D`), 63 % (base) | 46 % | 5 % | 48 % | 9 % |
| Nube densa limpia | | | | | |
| Malla exportada y escalada (mm) | | | | | |
| Reconstrucción con método de IA | | | | | |
| Error dimensional (%) | | | | | |
| `results/` y `meta.json` completos | | | | | |

## Estructura mínima para posterior elaboración de informe

1. Problema, aplicación y objetivos.
2. Selección y caracterización de los 5 objetos.
3. Protocolo de captura.
4. Calibración y modelo de formación de la imagen.
5. Preprocesamiento.
6. Reconstrucción dispersa (SfM).
7. Reconstrucción densa, malla y escalado métrico.
8. Comparación con el enfoque de IA.
9. Evaluación y discusión.
10. Reproducibilidad, ética y viabilidad.
11. Conclusiones y trabajo futuro.
12. Referencias y anexos (código, enlaces a los modelos 3D).
