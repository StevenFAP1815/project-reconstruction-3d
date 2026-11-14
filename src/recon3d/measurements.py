"""Medidas físicas de los objetos (docs/capture-protocol.md) y cómo medirlas en 3D.

Cada medida indica cómo se obtiene en la nube del objeto (`kind`, ver
`recon3d.pointcloud.measure`). `SCALE_BY` es la medida que fija la escala; las
demás sirven para evaluar el error dimensional (estrategia de escalado A).

Medidas que no se pueden obtener automáticamente de la caja envolvente (por
ejemplo, el alto del canasto sin las flores) se dejan fuera y se listan en
`NOT_AUTOMATIC`.
"""

MEASUREMENTS = {
    "caja-carton-leche": [
        {"name": "alto", "mm": 196, "kind": "extent", "rank": 0},
        {"name": "ancho", "mm": 93, "kind": "extent", "rank": 1},
        {"name": "fondo", "mm": 58, "kind": "extent", "rank": 2},
    ],
    "canasto-flores": [
        # El canasto ocupa el 42 % inferior del alto total (85 / 202 mm); la
        # franja 5-35 % evita la base y el arranque de las flores.
        {"name": "diametro_canasto", "mm": 150, "kind": "slice_width", "from": 0.05, "to": 0.35},
        {"name": "alto_total", "mm": 202, "kind": "height"},
        {"name": "ancho_flores", "mm": 240, "kind": "max_width"},
    ],
    "vaso-vidrio": [
        {"name": "alto", "mm": 143, "kind": "height"},
        {"name": "diametro_boca", "mm": 79, "kind": "slice_width", "from": 0.9, "to": 1.0},
        {"name": "diametro_base", "mm": 72, "kind": "slice_width", "from": 0.0, "to": 0.1},
    ],
    "audifonos": [
        {"name": "ancho", "mm": 60, "kind": "extent", "rank": 0},
        {"name": "alto", "mm": 43, "kind": "extent", "rank": 1},
        {"name": "fondo", "mm": 20, "kind": "extent", "rank": 2},
    ],
    "colador-cocina": [
        {"name": "largo_total", "mm": 206, "kind": "extent", "rank": 0},
        {"name": "diametro_aro", "mm": 91, "kind": "extent", "rank": 1},
        {"name": "profundidad_malla", "mm": 45, "kind": "extent", "rank": 2},
    ],
}

SCALE_BY = {
    "caja-carton-leche": "alto",
    "canasto-flores": "diametro_canasto",
    "vaso-vidrio": "alto",
    "audifonos": "ancho",
    "colador-cocina": "largo_total",
}

NOT_AUTOMATIC = {
    "canasto-flores": ["alto del canasto (85 mm): requiere separar el canasto de las flores"],
}
