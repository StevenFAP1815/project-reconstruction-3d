"""Tests de recon3d.reproducibility."""

import random

from recon3d.reproducibility import set_seed


def test_set_seed_makes_random_repeatable():
    set_seed(123)
    first = [random.random() for _ in range(3)]
    set_seed(123)
    second = [random.random() for _ in range(3)]

    assert first == second
