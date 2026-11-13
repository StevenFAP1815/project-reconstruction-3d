"""Semillas aleatorias para que las corridas se puedan repetir."""

import random


def set_seed(seed: int) -> int:
    """Fija la semilla de `random`, y de NumPy y PyTorch si están instalados.

    Se importan dentro de la función para que este módulo funcione también en
    entornos sin NumPy ni PyTorch (como la CI de tests).

    Nota: algunas operaciones en GPU no son deterministas aunque se fije la
    semilla; por eso además se registra la semilla en meta.json.
    """
    random.seed(seed)

    try:
        import numpy as np
    except ImportError:
        pass
    else:
        np.random.seed(seed)

    try:
        import torch
    except ImportError:
        pass
    else:
        torch.manual_seed(seed)
        torch.cuda.manual_seed_all(seed)

    return seed
