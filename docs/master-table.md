# Tabla maestra objeto × método

Generada con `python scripts/build_master_table.py` a partir de los `meta.json`
de `results/` (2026-11-14). No se edita a mano: se regenera tras cada corrida.

- **Registradas (%)**: sobre las fotos usadas (tras descartar las borrosas).
- **Puntos**: puntos 3D de SfM en las filas dispersas; puntos del objeto tras
  la limpieza en las filas densas.
- **Error dim. medio (%)**: media del error absoluto de las medidas que no se
  usaron para escalar (referencia de la rúbrica: ≤ 2 %).
- **Cobertura (%)**: sectores de 10° alrededor del objeto con puntos
  (completitud; 100 % = reconstruido por todos sus lados).
- **Estado** `omitido`: el método no pudo ejecutarse (por ejemplo, MVS con
  menos de 10 fotos registradas).

| Objeto | Método | Etapa | Estado | Fotos | Usadas | Registradas | Registradas (%) | Modelos | Puntos | Error reproy. (px) | Escala (mm/u) | Error dim. medio (%) | Cobertura (%) | Tiempo (s) | Memoria GPU (GB) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `caja-carton-leche` | `colmap` | SfM disperso (base) | ok | 73 | 68 | 43 | 63,24 | 2 | 5 857 | 1,11 | – | – | – | 554,42 | – |
| `caja-carton-leche` | `colmap-v2` | SfM disperso (D_calibrada) | ok | 73 | 68 | 68 | 100 | 1 | 19 279 | 1,12 | – | – | – | 567,80 | – |
| `canasto-flores` | `colmap` | SfM disperso (base) | ok | 93 | 87 | 40 | 45,98 | 3 | 3 284 | 1,22 | – | – | – | 756,26 | – |
| `vaso-vidrio` | `colmap` | SfM disperso (base) | ok | 81 | 80 | 4 | 5 | 1 | 41 | 1,36 | – | – | – | 199,61 | – |
| `audifonos` | `colmap` | SfM disperso (base) | ok | 121 | 99 | 48 | 48,48 | 3 | 57 820 | 0,83 | – | – | – | 1 325,76 | – |
| `colador-cocina` | `colmap` | SfM disperso (base) | ok | 86 | 86 | 8 | 9,30 | 1 | 190 | 1,14 | – | – | – | 417,18 | – |
