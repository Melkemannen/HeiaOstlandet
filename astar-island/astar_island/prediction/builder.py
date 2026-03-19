"""Hovedlogikk for å bygge sannsynlighetsprediksjoner.

Kombinerer observasjoner fra simulate-queries med prior-kunnskap
fra initial state for å bygge H x W x 6 probability tensorer.
"""

import numpy as np
from collections import Counter

from ..config import NUM_CLASSES, MIN_PROB, CLASS_NAMES, terrain_code_to_class
from ..analysis.observations import collect_observations, compute_global_frequencies
from .priors import get_prior_for_cell


def build_predictions(initial_data_list, query_results, map_width, map_height,
                      num_seeds):
    """Bygg sannsynlighetsfordelinger for alle seeds.

    For hver celle:
    - Observert multiple ganger: empirisk frekvensfordeling + smoothing
    - Observert én gang: observasjon med usikkerhets-blending
    - Uobservert: prior basert på initial state + global frekvenser

    Returnerer dict: seed_index → numpy array (H, W, 6)
    """
    predictions = {}

    for seed_idx in range(num_seeds):
        print(f"\n--- Bygger prediksjon for seed {seed_idx} ---")

        observations = collect_observations(
            query_results, seed_idx, map_width, map_height
        )

        n_observed = len(observations)
        n_multi = sum(1 for v in observations.values() if len(v) > 1)
        print(f"  Celler observert: {n_observed}/{map_width * map_height}")
        print(f"  Celler med multiple observasjoner: {n_multi}")

        # Globale frekvenser for fallback
        global_probs = np.array(compute_global_frequencies(observations))

        # Hent initial state data
        initial = initial_data_list[seed_idx]
        initial_grid = initial["grid"]
        settlement_set = set(
            (s.get("x", 0), s.get("y", 0)) for s in initial["settlements"]
        )

        # Bygg prediction tensor
        pred = np.full((map_height, map_width, NUM_CLASSES), MIN_PROB)

        for y in range(map_height):
            for x in range(map_width):
                if (y, x) in observations:
                    pred[y][x] = _probs_from_observations(observations[(y, x)])
                else:
                    pred[y][x] = get_prior_for_cell(
                        initial_grid[y][x], x, y,
                        map_width, map_height, settlement_set
                    )

        # Bland uobserverte dynamiske celler med global fordeling
        if observations:
            for y in range(map_height):
                for x in range(map_width):
                    if (y, x) not in observations:
                        code = initial_grid[y][x]
                        if code not in (5, 10):
                            blend = 0.15
                            pred[y][x] = (1 - blend) * pred[y][x] + blend * global_probs

        # Enforce minimum floor og normaliser
        pred = np.maximum(pred, MIN_PROB)
        pred = pred / pred.sum(axis=2, keepdims=True)

        predictions[seed_idx] = pred
        _print_prediction_stats(pred)

    return predictions


def _probs_from_observations(obs_list):
    """Bygg sannsynlighetsvektor fra observasjoner med Bayesian smoothing."""
    counts = Counter(obs_list)
    total = len(obs_list)

    probs = np.full(NUM_CLASSES, MIN_PROB)
    for cls, count in counts.items():
        probs[cls] = count / total

    # Smoothing: mer usikkerhet med færre observasjoner
    if total == 1:
        alpha = 0.15
    elif total <= 3:
        alpha = 0.05
    else:
        alpha = 0.02

    uniform = np.full(NUM_CLASSES, 1 / NUM_CLASSES)
    return (1 - alpha) * probs + alpha * uniform


def _print_prediction_stats(pred):
    """Skriv ut oppsummering av prediksjonen."""
    argmax = np.argmax(pred, axis=2)
    for cls in range(NUM_CLASSES):
        count = int(np.sum(argmax == cls))
        print(f"  Predikert dominant {CLASS_NAMES[cls]}: {count} celler")
