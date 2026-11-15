"""Normales orientadas y muestreo de mallas, para mallar nubes sin normales.

Las nubes de VGGT no traen normales (MVS sí las estima), y la reconstrucción de
superficie de Poisson las necesita. Este módulo:

1. reduce la nube con una rejilla de vóxeles (un punto medio por celda), para
   que la densidad sea uniforme y el cálculo, rápido;
2. estima la normal de cada punto con PCA de sus vecinos: la dirección de menor
   variación del vecindario es la perpendicular a la superficie;
3. orienta las normales de forma coherente (método de Hoppe et al., 1992): la
   PCA da la dirección pero no el sentido. Se construye el grafo de vecinos, se
   calcula su árbol de expansión mínima con peso 1 − |n_i · n_j| (los vecinos
   con normales casi paralelas quedan unidos) y se recorre desde el punto más
   alto, cuya normal debe apuntar hacia arriba, invirtiendo cada normal que
   apunte en sentido contrario a la de su padre en el árbol.

También muestrea puntos sobre una malla en proporción al área de cada
triángulo, para medir la malla con las mismas funciones que la nube.

Depende de scipy (árbol k-d y grafos).
"""

import numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import breadth_first_order, minimum_spanning_tree
from scipy.spatial import cKDTree


def voxel_downsample(points: np.ndarray, voxel: float,
                     colors: np.ndarray | None = None) -> tuple[np.ndarray, np.ndarray | None]:
    """Un punto (la media) por celda cúbica de lado `voxel`; ídem para el color."""
    points = np.asarray(points, dtype=float)
    keys = np.floor(points / voxel).astype(np.int64)
    _, inverse, counts = np.unique(keys, axis=0, return_inverse=True, return_counts=True)
    inverse = inverse.ravel()
    mean = np.zeros((len(counts), 3))
    np.add.at(mean, inverse, points)
    mean /= counts[:, None]
    if colors is None:
        return mean, None
    rgb = np.zeros((len(counts), 3))
    np.add.at(rgb, inverse, np.asarray(colors, dtype=float))
    return mean, (rgb / counts[:, None]).round().astype(np.uint8)


def estimate_normals(points: np.ndarray, k: int = 20) -> np.ndarray:
    """Normal (sin sentido definido) de cada punto por PCA de sus `k` vecinos."""
    points = np.asarray(points, dtype=float)
    _, idx = cKDTree(points).query(points, k=k)
    neighbors = points[idx] - points[idx].mean(axis=1, keepdims=True)   # (N, k, 3)
    covariance = np.einsum("nki,nkj->nij", neighbors, neighbors)        # (N, 3, 3)
    return np.linalg.eigh(covariance)[1][:, :, 0]                       # menor valor propio


def orient_normals(points: np.ndarray, normals: np.ndarray, *, up=(0.0, 0.0, 1.0),
                   k: int = 10) -> np.ndarray:
    """Da a las normales un sentido coherente (árbol de expansión mínima, Hoppe).

    Las componentes del grafo que no conectan con la principal se orientan por
    separado, cada una desde su punto más alto.
    """
    points = np.asarray(points, dtype=float)
    normals = np.array(normals, dtype=float)
    up = np.asarray(up, dtype=float)
    _, idx = cKDTree(points).query(points, k=k + 1)
    rows = np.repeat(np.arange(len(points)), k)
    cols = idx[:, 1:].ravel()
    weights = 1.0 - np.abs(np.einsum("ij,ij->i", normals[rows], normals[cols])) + 1e-6
    graph = coo_matrix((weights, (rows, cols)), shape=(len(points),) * 2).tocsr()
    tree = minimum_spanning_tree(graph + graph.T)
    tree = tree + tree.T

    visited = np.zeros(len(points), dtype=bool)
    heights = points @ up
    for start in np.argsort(-heights):          # cada componente, desde su punto más alto
        if visited[start]:
            continue
        if normals[start] @ up < 0:
            normals[start] = -normals[start]
        order, parents = breadth_first_order(tree, start, directed=False)
        for node in order[1:]:                  # el orden BFS garantiza el padre ya orientado
            if normals[node] @ normals[parents[node]] < 0:
                normals[node] = -normals[node]
        visited[order] = True
    return normals


def sample_surface(vertices: np.ndarray, faces: np.ndarray, n: int, *, seed: int = 0) -> np.ndarray:
    """`n` puntos al azar sobre la malla, repartidos según el área de los triángulos."""
    vertices = np.asarray(vertices, dtype=float)
    a, b, c = (vertices[faces[:, i]] for i in range(3))
    area = 0.5 * np.linalg.norm(np.cross(b - a, c - a), axis=1)
    rng = np.random.default_rng(seed)
    chosen = rng.choice(len(faces), size=n, p=area / area.sum())
    u, v = rng.uniform(size=(2, n))
    flip = u + v > 1                            # reflejar para quedar dentro del triángulo
    u[flip], v[flip] = 1 - u[flip], 1 - v[flip]
    return a[chosen] + u[:, None] * (b[chosen] - a[chosen]) + v[:, None] * (c[chosen] - a[chosen])


def nearest_colors(targets: np.ndarray, points: np.ndarray, colors: np.ndarray) -> np.ndarray:
    """Color del punto más cercano de la nube para cada vértice de la malla."""
    _, idx = cKDTree(points).query(targets, k=1)
    return np.asarray(colors)[idx]
