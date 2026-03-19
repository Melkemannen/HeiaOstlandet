"""Prior-sannsynligheter basert på initial state.

Brukes for celler som ikke er observert via simulate-queries.
Priors er basert på terrengtype og nærhet til settlements.
"""

import numpy as np

from ..config import NUM_CLASSES, MIN_PROB


def get_prior_for_cell(initial_code, x, y, map_width, map_height, settlement_set):
    """Beregn prior-sannsynlighetsfordeling for én celle.

    Returnerer numpy array med 6 sannsynligheter.
    """
    is_border = (y == 0 or y == map_height - 1 or x == 0 or x == map_width - 1)

    # Mountain: 100% statisk
    if initial_code == 5:
        probs = np.full(NUM_CLASSES, MIN_PROB)
        probs[5] = 1.0
        return probs

    # Ocean eller border: 100% statisk
    if initial_code == 10 or is_border:
        probs = np.full(NUM_CLASSES, MIN_PROB)
        probs[0] = 1.0
        return probs

    # Beregn avstand til nærmeste settlement
    min_dist = 999
    for sx, sy in settlement_set:
        dist = abs(x - sx) + abs(y - sy)
        if dist < min_dist:
            min_dist = dist

    # Empty/Plains
    if initial_code in (0, 11):
        if min_dist <= 5:
            return np.array([0.50, 0.15, 0.05, 0.10, 0.10, MIN_PROB])
        elif min_dist <= 10:
            return np.array([0.70, 0.05, MIN_PROB, 0.05, 0.10, MIN_PROB])
        else:
            return np.array([0.85, MIN_PROB, MIN_PROB, MIN_PROB, 0.05, MIN_PROB])

    # Forest
    if initial_code == 4:
        if min_dist <= 5:
            return np.array([0.20, 0.10, MIN_PROB, 0.05, 0.55, MIN_PROB])
        else:
            return np.array([0.05, MIN_PROB, MIN_PROB, MIN_PROB, 0.85, MIN_PROB])

    # Settlement
    if initial_code == 1:
        return np.array([0.15, 0.40, 0.05, 0.25, 0.08, MIN_PROB])

    # Port
    if initial_code == 2:
        return np.array([0.15, 0.15, 0.40, 0.20, MIN_PROB, MIN_PROB])

    # Ruin
    if initial_code == 3:
        return np.array([0.25, 0.12, 0.05, 0.30, 0.20, MIN_PROB])

    # Ukjent
    return np.full(NUM_CLASSES, 1 / NUM_CLASSES)
