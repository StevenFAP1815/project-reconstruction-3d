# notebooks/

Notebooks de experimentación, uno por etapa o método, numerados en el orden
del pipeline (por ejemplo `01_calibration.ipynb`, `02_sfm_colmap.ipynb`).

- La lógica reutilizable va en `src/recon3d/`; el notebook solo la llama y
  muestra resultados.
- Los métodos de IA (VGGT, DUSt3R/MASt3R, Gaussian Splatting, NeRF) necesitan
  GPU y se ejecutan en Google Colab; cada notebook instala sus propias
  dependencias pesadas en su primera celda.
