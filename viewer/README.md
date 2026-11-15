# viewer/

Visor web de las cinco mallas para la demostración en vivo (`index.html`, con
`<model-viewer>` de Google).

## Cómo abrirlo

Las mallas (`results/<objeto>/vggt-nosupport/mesh.glb`) no están en Git por su
tamaño; se generan con `scripts/remeasure_vggt.py` y
`scripts/make_vggt_meshes.py`. El navegador no deja cargar archivos locales
desde `file://`, así que hay que servir el repositorio. Desde la raíz:

```powershell
.\.venv\Scripts\python.exe -m http.server 8000
```

y abrir http://localhost:8000/viewer/ en el navegador. `model-viewer` se
descarga de unpkg, así que hace falta conexión a internet.

Controles: arrastrar para girar, rueda para acercar, clic derecho para
desplazar. Los botones superiores cambian de objeto.
