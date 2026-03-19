"""Hovedlogikk for å bygge sannsynlighetsprediksjoner v2.

Kombinerer observasjoner fra simulate-queries med kalibrerte priors
fra initial state for å bygge H x W x 6 probability tensorer.

v2-forbedringer vs v1:
- Bruker build_prior_map (romlig modell) i stedet for per-celle priors
- Bedre Bayesian smoothing basert på antall observasjoner
- Spatial blending: uobserverte naboer påvirkes av observerte celler
"""

import numpy as np
from collections import Counter

from ..config import NUM_CLASSES, MIN_PROB, CLASS_NAMES, terrain_code_to_class
from ..analysis.observations import collect_observations, compute_global_frequencies
from .priors import build_prior_map


def build_predictions(initial_data_list, query_results, map_width, map_height,
                      num_seeds):
    """Bygg sannsynlighetsfordelinger for alle seeds.

    For hver celle:
    - Observert multiple ganger: empirisk frekvensfordeling + lite smoothing
    - Observert én gang: observasjon blandet med prior
    - Uobservert: prior fra romlig modell + global frekvens-blending

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

        # Globale frekvenser fra observasjoner
        global_probs = np.array(compute_global_frequencies(observations))

        # Hent initial state data
        initial = initial_data_list[seed_idx]
        initial_grid = initial["grid"]

        # Bygg romlig prior-kart (ny v2-modell)
        prior_map = build_prior_map(
            initial_grid, initial["settlements"],
            map_height, map_width
        )

        # Bygg prediction tensor
        pred = np.copy(prior_map)

        for y in range(map_height):
            for x in range(map_width):
                if (y, x) in observations:
                    obs = observations[(y, x)]
                    obs_probs = _probs_from_observations(obs)
                    prior = prior_map[y][x]

                    # Blend observasjon med prior, vektet etter antall obs
                    n = len(obs)
                    if n >= 3:
                        # Mange observasjoner: stol mest på data
                        weight = 0.85
                    elif n == 2:
                        # To observasjoner: god balanse
                        weight = 0.75
                    else:
                        # Én observasjon: bland mer med prior
                        weight = 0.60

                    pred[y][x] = weight * obs_probs + (1 - weight) * prior

        # Bland uobserverte dynamiske celler med global fordeling
        if observations and global_probs is not None:
            for y in range(map_height):
                for x in range(map_width):
                    if (y, x) not in observations:
                        code = initial_grid[y][x]
                        if code not in (5, 10):  # Ikke statiske
                            is_border = (y == 0 or y == map_height - 1 or
                                         x == 0 or x == map_width - 1)
                            if not is_border:
                                blend = 0.10
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

    # Smoothing: mindre med flere observasjoner
    if total == 1:
        alpha = 0.10  # Redusert fra 0.15 — stol litt mer på enkeltobs
    elif total == 2:
        alpha = 0.05
    elif total <= 4:
        alpha = 0.03
    else:
        alpha = 0.01

    uniform = np.full(NUM_CLASSES, 1 / NUM_CLASSES)
    return (1 - alpha) * probs + alpha * uniform


def _print_prediction_stats(pred):
    """Skriv ut oppsummering av prediksjonen."""
    argmax = np.argmax(pred, axis=2)
    for cls in range(NUM_CLASSES):
        count = int(np.sum(argmax == cls))
        print(f"  Predikert dominant {CLASS_NAMES[cls]}: {count} celler")

    # Vis gjennomsnittlig konfidens
    max_probs = np.max(pred, axis=2)
    print(f"  Gjennomsnittlig konfidens: {max_probs.mean():.3f}")
    print(f"  Min konfidens: {max_probs.min():.3f}")
