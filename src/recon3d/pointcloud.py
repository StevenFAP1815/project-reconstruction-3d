"""Nubes de puntos y mallas con NumPy: lectura/escritura, limpieza y medición.

No depende de COLMAP ni de librerías 3D externas, para poder probarse en la CI.
Las etapas de limpieza de la nube densa (ver `clean_object_cloud`) son:

1. Recorte esférico alrededor del punto al que miran las cámaras: elimina el
   fondo lejano (paredes, muebles).
2. Plano de la mesa con RANSAC: se eliminan sus puntos y todo lo que queda por
   debajo de ella.
3. Componente conexa más grande: el objeto es la mayor "isla" de puntos; las
   islas pequeñas son ruido o restos del fondo.
"""

from collections import deque
from pathlib import Path
import json
import struct

import numpy as np

# ---------------------------------------------------------------------------
# PLY (formato de COLMAP para nubes densas y mallas)
# ---------------------------------------------------------------------------

_PLY_TYPES = {
    "char": "i1", "int8": "i1", "uchar": "u1", "uint8": "u1",
    "short": "i2", "int16": "i2", "ushort": "u2", "uint16": "u2",
    "int": "i4", "int32": "i4", "uint": "u4", "uint32": "u4",
    "float": "f4", "float32": "f4", "double": "f8", "float64": "f8",
}


def read_ply(path: str | Path) -> dict[str, np.ndarray]:
    """Lee un PLY (binario little-endian o ASCII) con vértices y, opcionalmente, caras.

    Returns:
        Diccionario con "points" (N, 3) y, si existen, "normals" (N, 3),
        "colors" (N, 3, uint8) y "faces" (M, 3, int).
    """
    with open(path, "rb") as file:
        if file.readline().strip() != b"ply":
            raise ValueError(f"{path} no es un archivo PLY")
        fmt, elements, current = None, [], None
        while True:
            line = file.readline().decode("ascii").strip()
            if not line:
                continue
            words = line.split()
            if words[0] == "format":
                fmt = words[1]
            elif words[0] == "element":
                current = {"name": words[1], "count": int(words[2]), "props": []}
                elements.append(current)
            elif words[0] == "property":
                if words[1] == "list":
                    current["props"].append((words[4], "list", _PLY_TYPES[words[2]], _PLY_TYPES[words[3]]))
                else:
                    current["props"].append((words[2], _PLY_TYPES[words[1]]))
            elif words[0] == "end_header":
                break
        if fmt not in ("binary_little_endian", "ascii"):
            raise ValueError(f"Formato PLY no soportado: {fmt}")

        data = {}
        for element in elements:
            if fmt == "ascii":
                data[element["name"]] = _read_ascii_element(file, element)
            else:
                data[element["name"]] = _read_binary_element(file, element)

    vertex = data["vertex"]
    if isinstance(vertex, np.ndarray):  # binario: array estructurado -> diccionario
        vertex = {name: vertex[name] for name in vertex.dtype.names}
    result = {"points": np.column_stack([vertex["x"], vertex["y"], vertex["z"]]).astype(np.float64)}
    if "nx" in vertex:
        result["normals"] = np.column_stack([vertex["nx"], vertex["ny"], vertex["nz"]]).astype(np.float64)
    if "red" in vertex:
        result["colors"] = np.column_stack([vertex["red"], vertex["green"], vertex["blue"]]).astype(np.uint8)
    if "face" in data and len(data["face"]):
        result["faces"] = data["face"]
    return result


def _read_binary_element(file, element) -> dict | np.ndarray:
    props = element["props"]
    if element["name"] == "face":
        if len(props) != 1 or props[0][1] != "list":
            raise ValueError("Solo se admiten caras con una única lista de índices")
        _, _, count_type, index_type = props[0]
        count_size, index_size = np.dtype(count_type).itemsize, np.dtype(index_type).itemsize
        raw = file.read(element["count"] * (count_size + 3 * index_size))
        dtype = np.dtype([("n", "<" + count_type), ("idx", "<" + index_type, 3)])
        faces = np.frombuffer(raw, dtype=dtype, count=element["count"])
        if element["count"] and np.any(faces["n"] != 3):
            raise ValueError("Solo se admiten mallas de triángulos")
        return faces["idx"].astype(np.int64)
    dtype = np.dtype([(name, "<" + kind) for name, kind in props])
    raw = file.read(dtype.itemsize * element["count"])
    return np.frombuffer(raw, dtype=dtype, count=element["count"])


def _read_ascii_element(file, element) -> dict | np.ndarray:
    rows = [file.readline().decode("ascii").split() for _ in range(element["count"])]
    if element["name"] == "face":
        return np.array([[int(v) for v in row[1:4]] for row in rows], dtype=np.int64).reshape(-1, 3)
    names = [prop[0] for prop in element["props"]]
    table = np.array(rows, dtype=np.float64).reshape(-1, len(names))
    return {name: table[:, i] for i, name in enumerate(names)}


def write_ply(path: str | Path, points: np.ndarray, *, colors: np.ndarray | None = None,
              normals: np.ndarray | None = None, faces: np.ndarray | None = None) -> Path:
    """Escribe un PLY binario little-endian (nube de puntos o malla de triángulos)."""
    points = np.asarray(points, dtype=np.float32)
    fields = [("x", "<f4"), ("y", "<f4"), ("z", "<f4")]
    if normals is not None:
        fields += [("nx", "<f4"), ("ny", "<f4"), ("nz", "<f4")]
    if colors is not None:
        fields += [("red", "u1"), ("green", "u1"), ("blue", "u1")]
    vertex = np.empty(len(points), dtype=fields)
    vertex["x"], vertex["y"], vertex["z"] = points.T
    if normals is not None:
        vertex["nx"], vertex["ny"], vertex["nz"] = np.asarray(normals, dtype=np.float32).T
    if colors is not None:
        vertex["red"], vertex["green"], vertex["blue"] = np.asarray(colors, dtype=np.uint8).T

    types = {"<f4": "float", "u1": "uchar"}
    header = ["ply", "format binary_little_endian 1.0", f"element vertex {len(points)}"]
    header += [f"property {types[kind]} {name}" for name, kind in fields]
    if faces is not None:
        header += [f"element face {len(faces)}", "property list uchar int vertex_indices"]
    header.append("end_header")

    path = Path(path)
    with open(path, "wb") as file:
        file.write(("\n".join(header) + "\n").encode("ascii"))
        file.write(vertex.tobytes())
        if faces is not None:
            face = np.empty(len(faces), dtype=[("n", "u1"), ("idx", "<i4", 3)])
            face["n"] = 3
            face["idx"] = np.asarray(faces, dtype=np.int32)
            file.write(face.tobytes())
    return path


# ---------------------------------------------------------------------------
# Geometría de la escena
# ---------------------------------------------------------------------------

def look_at_point(centers: np.ndarray, directions: np.ndarray) -> np.ndarray:
    """Punto más cercano (mínimos cuadrados) a todos los ejes ópticos.

    Al fotografiar un objeto girando a su alrededor, todas las cámaras apuntan
    aproximadamente al objeto: el punto que minimiza la distancia a todos los
    ejes ópticos es una buena estimación de su centro.
    """
    centers = np.asarray(centers, dtype=float)
    directions = np.asarray(directions, dtype=float)
    directions = directions / np.linalg.norm(directions, axis=1, keepdims=True)
    # Para cada recta: (I - d dᵀ)(p - c) = 0  ->  sum(I - d dᵀ) p = sum((I - d dᵀ) c)
    projectors = np.eye(3)[None] - directions[:, :, None] * directions[:, None, :]
    lhs = projectors.sum(axis=0)
    rhs = np.einsum("nij,nj->i", projectors, centers)
    return np.linalg.lstsq(lhs, rhs, rcond=None)[0]


def fit_plane_ransac(points: np.ndarray, threshold: float, *, iterations: int = 500,
                     seed: int = 0) -> tuple[np.ndarray, float, np.ndarray]:
    """Plano dominante con RANSAC: devuelve (normal unitaria, d, máscara de inliers).

    El plano es n·x + d = 0. RANSAC prueba planos definidos por 3 puntos al azar
    y se queda con el que tiene más puntos a menos de `threshold`; después se
    reajusta con todos sus inliers (mínimos cuadrados con SVD).
    """
    points = np.asarray(points, dtype=float)
    if len(points) < 3:
        raise ValueError("Se necesitan al menos 3 puntos")
    rng = np.random.default_rng(seed)
    best_mask, best_count = None, -1
    for _ in range(iterations):
        a, b, c = points[rng.choice(len(points), 3, replace=False)]
        normal = np.cross(b - a, c - a)
        norm = np.linalg.norm(normal)
        if norm < 1e-12:
            continue
        normal /= norm
        mask = np.abs((points - a) @ normal) < threshold
        count = int(mask.sum())
        if count > best_count:
            best_mask, best_count = mask, count
    if best_mask is None:
        raise ValueError("Los puntos son colineales: no definen un plano")
    inliers = points[best_mask]
    centroid = inliers.mean(axis=0)
    normal = np.linalg.svd(inliers - centroid, full_matrices=False)[2][-1]
    d = -float(normal @ centroid)
    mask = np.abs(points @ normal + d) < threshold
    return normal, d, mask


def voxel_keys(points: np.ndarray, voxel: float) -> np.ndarray:
    """Índice entero (i, j, k) de la celda cúbica de lado `voxel` de cada punto."""
    return np.floor(np.asarray(points) / voxel).astype(np.int64)


def largest_component(points: np.ndarray, voxel: float, *, min_points_per_voxel: int = 1) -> np.ndarray:
    """Máscara de los puntos de la mayor componente conexa.

    Los puntos se agrupan en celdas (vóxeles) de lado `voxel`. Dos celdas
    ocupadas están conectadas si se tocan (26 vecinos). Las celdas con menos de
    `min_points_per_voxel` puntos se tratan como ruido.
    """
    keys = voxel_keys(points, voxel)
    unique, inverse, counts = np.unique(keys, axis=0, return_inverse=True, return_counts=True)
    inverse = inverse.ravel()
    occupied = counts >= min_points_per_voxel
    index = {tuple(key): i for i, key in enumerate(unique) if occupied[i]}
    offsets = [(dx, dy, dz) for dx in (-1, 0, 1) for dy in (-1, 0, 1) for dz in (-1, 0, 1)
               if (dx, dy, dz) != (0, 0, 0)]

    label = np.full(len(unique), -1)
    sizes = []
    for start in index.values():
        if label[start] >= 0:
            continue
        component = len(sizes)
        label[start] = component
        queue, size = deque([start]), 0
        while queue:
            current = queue.popleft()
            size += counts[current]
            x, y, z = unique[current]
            for dx, dy, dz in offsets:
                neighbor = index.get((x + dx, y + dy, z + dz))
                if neighbor is not None and label[neighbor] < 0:
                    label[neighbor] = component
                    queue.append(neighbor)
        sizes.append(size)
    if not sizes:
        return np.zeros(len(points), dtype=bool)
    return label[inverse] == int(np.argmax(sizes))


def clean_object_cloud(points: np.ndarray, centers: np.ndarray, directions: np.ndarray,
                       up: np.ndarray, *, crop_ratio: float = 0.6, plane_ratio: float = 0.01,
                       voxel_ratio: float = 0.01, min_points_per_voxel: int = 3,
                       seed: int = 0) -> tuple[np.ndarray, dict]:
    """Aísla el objeto en la nube densa (ver las etapas en la cabecera del módulo).

    Las distancias son relativas a la distancia mediana entre las cámaras y el
    objeto, porque la nube de SfM no tiene escala métrica todavía.

    Args:
        up: dirección vertical aproximada (de la mesa hacia las cámaras).
        crop_ratio: radio del recorte, como fracción de la distancia cámara-objeto.
        plane_ratio: tolerancia del plano de la mesa (misma referencia).
        voxel_ratio: lado de las celdas para la componente conexa (misma referencia).

    Returns:
        (máscara de puntos del objeto, informe con los puntos que quedan tras cada etapa)
    """
    points = np.asarray(points, dtype=float)
    up = np.asarray(up, dtype=float) / np.linalg.norm(up)
    center = look_at_point(centers, directions)
    distance = float(np.median(np.linalg.norm(np.asarray(centers) - center, axis=1)))
    report = {"input": len(points), "center": center.tolist(), "camera_distance": distance}

    mask = np.linalg.norm(points - center, axis=1) < crop_ratio * distance
    report["after_crop"] = int(mask.sum())

    idx = np.flatnonzero(mask)
    normal, d, on_plane = fit_plane_ransac(points[idx], plane_ratio * distance, seed=seed)
    if normal @ up < 0:  # orientar la normal hacia las cámaras
        normal, d = -normal, -d
    signed = points[idx] @ normal + d
    above = signed > plane_ratio * distance
    below = signed < -plane_ratio * distance
    # Solo se acepta como mesa un plano casi horizontal (< 30° respecto a la
    # vertical) con pocos puntos por debajo (< 10 %): la mesa es lo más bajo de
    # la escena. Así no se confunde con la cara superior del objeto, que tiene
    # el resto del objeto debajo.
    is_table = abs(float(normal @ up)) > np.cos(np.radians(30)) and below.mean() < 0.10
    if is_table:
        mask[idx[~above]] = False
        up = normal
    report["table_plane_found"] = bool(is_table)
    report["after_table"] = int(mask.sum())

    idx = np.flatnonzero(mask)
    keep = largest_component(points[idx], voxel_ratio * distance, min_points_per_voxel=min_points_per_voxel)
    mask[idx[~keep]] = False
    report["after_component"] = int(mask.sum())
    report["up"] = up.tolist()
    return mask, report


# ---------------------------------------------------------------------------
# Marco del objeto y medidas
# ---------------------------------------------------------------------------

def _perpendicular_basis(z: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    helper = np.array([1.0, 0, 0]) if abs(z[0]) < 0.9 else np.array([0, 1.0, 0])
    a = np.cross(z, helper)
    a /= np.linalg.norm(a)
    return a, np.cross(z, a)


def _tilted(axis: np.ndarray, max_tilt_deg: float, step_deg: float) -> np.ndarray:
    """Direcciones dentro de un cono alrededor de `axis`, separadas ~`step_deg` grados."""
    a, b = _perpendicular_basis(axis)
    directions = [axis]
    for tilt in np.arange(step_deg, max_tilt_deg + 1e-9, step_deg):
        n_azimuth = max(6, int(round(360 * np.sin(np.radians(tilt)) / step_deg)))
        for azimuth in np.linspace(0, 2 * np.pi, n_azimuth, endpoint=False):
            t = np.radians(tilt)
            directions.append(np.cos(t) * axis + np.sin(t) * (np.cos(azimuth) * a + np.sin(azimuth) * b))
    return np.array(directions)


def _best_box(points, z_candidates, angles, trim):
    """Para cada z candidata y cada giro en el plano, volumen de la caja recortada."""
    best = (np.inf, None, None)
    for z in z_candidates:
        a, b = _perpendicular_basis(z)
        u, v = points @ a, points @ b
        height = np.subtract(*np.percentile(points @ z, [100 - trim, trim]))
        cos, sin = np.cos(angles), np.sin(angles)
        along = np.outer(u, cos) + np.outer(v, sin)
        across = np.outer(v, cos) - np.outer(u, sin)
        width = np.subtract(*np.percentile(along, [100 - trim, trim], axis=0))
        depth = np.subtract(*np.percentile(across, [100 - trim, trim], axis=0))
        volume = height * width * depth
        i = int(np.argmin(volume))
        if volume[i] < best[0]:
            x = cos[i] * a + sin[i] * b
            best = (volume[i], z, x)
    return best[1], best[2]


def object_frame(points: np.ndarray, up: np.ndarray, *, max_tilt_deg: float = 35.0,
                 trim: float = 1.0, sample: int = 8000,
                 seed: int = 0) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Coordenadas del objeto alineadas con su caja envolvente de volumen mínimo.

    La vertical estimada con las órbitas de la cámara (`up`) es solo aproximada:
    las órbitas no son perfectamente horizontales. Por eso se busca, entre las
    direcciones a menos de `max_tilt_deg` de `up`, el eje z y el giro horizontal
    que dan la caja de menor volumen; en un objeto como una caja, esa caja tiene
    las caras paralelas a las del objeto. Primero se busca en una rejilla gruesa
    (2,5°) y después se afina (0,5°). Los extremos se recortan un `trim` % para
    que los puntos sueltos no agranden la caja. El origen queda en la base del
    objeto (z = 0).

    Returns:
        coords (N, 3), la rotación (3, 3) cuyas filas son los ejes y el origen
        (3,). Cualquier otro punto p (p. ej. los vértices de la malla) pasa al
        mismo marco con `(p - origin) @ rotation.T`.
    """
    points = np.asarray(points, dtype=float)
    up = np.asarray(up, dtype=float) / np.linalg.norm(up)
    mean = points.mean(axis=0)
    centered = points - mean
    rng = np.random.default_rng(seed)
    subset = centered[rng.choice(len(centered), min(sample, len(centered)), replace=False)]

    z, x = _best_box(subset, _tilted(up, max_tilt_deg, 2.5), np.radians(np.arange(0, 90, 2.5)), trim)
    theta = np.arctan2(x @ _perpendicular_basis(z)[1], x @ _perpendicular_basis(z)[0])
    fine_z = _tilted(z, 2.5, 0.5)
    fine_z = fine_z[np.degrees(np.arccos(np.clip(fine_z @ up, -1, 1))) <= max_tilt_deg + 1e-9]
    fine_angles = theta + np.radians(np.arange(-2.5, 2.51, 0.5))
    # El giro se mide respecto a la base de cada z; al cambiar z un poco, la base
    # apenas cambia, así que se reutiliza el ángulo de la búsqueda gruesa.
    z, x = _best_box(subset, fine_z, fine_angles, trim)

    rotation = np.vstack([x, np.cross(z, x), z])
    base = np.percentile(centered @ z, trim)  # recorta los puntos sueltos bajo la base
    origin = mean + base * z
    return (points - origin) @ rotation.T, rotation, origin


def _extent(values: np.ndarray, trim: float) -> float:
    low, high = np.percentile(values, [trim, 100 - trim])
    return float(high - low)


def measure(coords: np.ndarray, spec: dict, *, trim: float = 1.0) -> float:
    """Mide una dimensión del objeto en su marco (`object_frame`), en sus unidades.

    Tipos de medida (`spec["kind"]`):

    - "extent": i-ésima dimensión de la caja envolvente, de mayor a menor
      (`spec["rank"]` = 0, 1 o 2).
    - "height": alto (eje vertical).
    - "max_width": mayor anchura horizontal.
    - "slice_width": anchura horizontal media (diámetro) de la franja de alturas
      entre `spec["from"]` y `spec["to"]`, como fracción del alto total.

    `trim` descarta ese porcentaje de puntos en cada extremo, para que unos pocos
    puntos sueltos no alarguen la medida.
    """
    kind = spec["kind"]
    if kind == "extent":
        extents = sorted((_extent(coords[:, i], trim) for i in range(3)), reverse=True)
        return extents[spec["rank"]]
    if kind == "height":
        return _extent(coords[:, 2], trim)
    if kind == "max_width":
        return max(_extent(coords[:, 0], trim), _extent(coords[:, 1], trim))
    if kind == "slice_width":
        height = _extent(coords[:, 2], trim)
        low = np.percentile(coords[:, 2], trim)
        z = coords[:, 2] - low
        band = coords[(z >= spec["from"] * height) & (z <= spec["to"] * height)]
        if len(band) < 10:
            raise ValueError(f"La franja {spec['from']}-{spec['to']} tiene muy pocos puntos")
        return float(np.mean([_extent(band[:, 0], trim), _extent(band[:, 1], trim)]))
    raise ValueError(f"Tipo de medida desconocido: {kind}")


def dimensional_errors(coords: np.ndarray, measurements: list[dict], scale_by: str,
                       *, trim: float = 1.0) -> tuple[float, list[dict]]:
    """Escala con una medida y evalúa el error con las demás (estrategia de escalado A).

    Args:
        measurements: lista de {"name", "mm", "kind", ...} (ver `measure`).
        scale_by: nombre de la medida que fija la escala.

    Returns:
        (factor de escala en mm por unidad de SfM, tabla con cada medida).
    """
    by_name = {m["name"]: m for m in measurements}
    if scale_by not in by_name:
        raise ValueError(f"La medida de escala {scale_by!r} no está en la lista")
    scale = by_name[scale_by]["mm"] / measure(coords, by_name[scale_by], trim=trim)
    rows = []
    for m in measurements:
        model_mm = scale * measure(coords, m, trim=trim)
        rows.append({
            "name": m["name"],
            "real_mm": m["mm"],
            "model_mm": round(model_mm, 2),
            "error_mm": round(model_mm - m["mm"], 2),
            "error_pct": round(100 * (model_mm - m["mm"]) / m["mm"], 2),
            "role": "escala" if m["name"] == scale_by else "evaluación",
        })
    return scale, rows


# ---------------------------------------------------------------------------
# Mallas
# ---------------------------------------------------------------------------

def crop_mesh(vertices: np.ndarray, faces: np.ndarray, low: np.ndarray,
              high: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Conserva los triángulos con los tres vértices dentro de la caja [low, high].

    Poisson genera una superficie cerrada y puede "inventar" superficie lejos
    de los puntos (por ejemplo, bajo la mesa). Este recorte la elimina.

    Returns:
        (vértices conservados, caras reindexadas, índices originales de esos vértices)
    """
    vertices = np.asarray(vertices)
    faces = np.asarray(faces)
    inside = np.all((vertices >= low) & (vertices <= high), axis=1)
    faces = faces[inside[faces].all(axis=1)]
    used = np.unique(faces)
    remap = np.full(len(vertices), -1)
    remap[used] = np.arange(len(used))
    return vertices[used], remap[faces], used


# ---------------------------------------------------------------------------
# Exportación de mallas
# ---------------------------------------------------------------------------

def write_obj(path: str | Path, vertices: np.ndarray, faces: np.ndarray,
              colors: np.ndarray | None = None) -> Path:
    """Escribe una malla OBJ. Los colores van tras cada vértice (extensión habitual)."""
    path = Path(path)
    vertices = np.asarray(vertices, dtype=float)
    with open(path, "w", encoding="ascii") as file:
        file.write("# Malla exportada por recon3d (unidades: mm)\n")
        if colors is not None:
            rgb = np.asarray(colors, dtype=float) / 255.0
            for (x, y, z), (r, g, b) in zip(vertices, rgb):
                file.write(f"v {x:.4f} {y:.4f} {z:.4f} {r:.3f} {g:.3f} {b:.3f}\n")
        else:
            for x, y, z in vertices:
                file.write(f"v {x:.4f} {y:.4f} {z:.4f}\n")
        for a, b, c in np.asarray(faces, dtype=np.int64) + 1:  # OBJ empieza en 1
            file.write(f"f {a} {b} {c}\n")
    return path


def write_glb(path: str | Path, vertices: np.ndarray, faces: np.ndarray,
              colors: np.ndarray | None = None) -> Path:
    """Escribe una malla glTF binaria (.glb), el formato de los visores web.

    glTF mide en metros: quien llame debe pasar los vértices ya en metros.
    Estructura: cabecera de 12 bytes + bloque JSON (descripción) + bloque BIN
    (posiciones, colores e índices), cada bloque alineado a 4 bytes.
    """
    positions = np.ascontiguousarray(vertices, dtype=np.float32)
    indices = np.ascontiguousarray(faces, dtype=np.uint32).ravel()
    blobs = [positions.tobytes(), indices.tobytes()]
    if colors is not None:
        rgba = np.hstack([np.asarray(colors, dtype=np.uint8),
                          np.full((len(positions), 1), 255, dtype=np.uint8)])
        blobs.append(np.ascontiguousarray(rgba).tobytes())

    views, offset, binary = [], 0, b""
    targets = [34962, 34963, 34962]  # ARRAY_BUFFER, ELEMENT_ARRAY_BUFFER
    for blob, target in zip(blobs, targets):
        views.append({"buffer": 0, "byteOffset": offset, "byteLength": len(blob), "target": target})
        padded = blob + b"\x00" * (-len(blob) % 4)
        binary += padded
        offset += len(padded)

    accessors = [
        {"bufferView": 0, "componentType": 5126, "count": len(positions), "type": "VEC3",
         "min": positions.min(axis=0).tolist(), "max": positions.max(axis=0).tolist()},
        {"bufferView": 1, "componentType": 5125, "count": len(indices), "type": "SCALAR"},
    ]
    attributes = {"POSITION": 0}
    if colors is not None:
        accessors.append({"bufferView": 2, "componentType": 5121, "normalized": True,
                          "count": len(positions), "type": "VEC4"})
        attributes["COLOR_0"] = 2
    document = {
        "asset": {"version": "2.0", "generator": "recon3d"},
        "scene": 0,
        "scenes": [{"nodes": [0]}],
        "nodes": [{"mesh": 0}],
        "meshes": [{"primitives": [{"attributes": attributes, "indices": 1, "mode": 4}]}],
        "buffers": [{"byteLength": len(binary)}],
        "bufferViews": views,
        "accessors": accessors,
    }
    text = json.dumps(document, separators=(",", ":")).encode("utf-8")
    text += b" " * (-len(text) % 4)
    total = 12 + 8 + len(text) + 8 + len(binary)

    path = Path(path)
    with open(path, "wb") as file:
        file.write(struct.pack("<4sII", b"glTF", 2, total))
        file.write(struct.pack("<I4s", len(text), b"JSON") + text)
        file.write(struct.pack("<I4s", len(binary), b"BIN\x00") + binary)
    return path
