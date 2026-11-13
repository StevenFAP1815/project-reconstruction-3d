# notebooks/

Notebooks de experimentación, uno por etapa o método, numerados en el orden
del pipeline.

| Notebook | Propósito |
|---|---|
| `00_setup_colab.ipynb` | Prepara la sesión de Colab: Drive, código, dependencias, carpetas, GPU y fotos. |

Reglas:

- La lógica reutilizable va en `src/recon3d/`; el notebook solo la llama y
  muestra resultados.
- Todos se ejecutan en Google Colab con GPU. Cada notebook empieza con las
  celdas 1 a 5 de `00_setup_colab.ipynb`, porque cada sesión de Colab empieza
  vacía.
- Las rutas se obtienen con `recon3d.paths.get_paths()`, nunca escritas a mano.
- Cada corrida termina con `recon3d.results.write_meta(...)`.
- Los notebooks se guardan **con las celdas ejecutadas** (salidas incluidas),
  porque son evidencia para la evaluación. Antes de hacer commit, ejecutarlos
  de inicio a fin (*Entorno de ejecución → Ejecutar todas*) para que las
  salidas correspondan al código.
