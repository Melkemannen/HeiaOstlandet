"""Validering og innsending av prediksjoner.

VIKTIG: submit_predictions sender data til konkurranse-API-et.
Kall denne BARE etter eksplisitt godkjenning fra brukeren.
"""

import numpy as np

from ..config import NUM_CLASSES, MIN_PROB


def validate_prediction(pred, map_height, map_width):
    """Valider at prediksjon-tensor har korrekt format."""
    assert pred.shape == (map_height, map_width, NUM_CLASSES), \
        f"Feil shape: {pred.shape}, forventet ({map_height}, {map_width}, {NUM_CLASSES})"

    sums = pred.sum(axis=2)
    assert np.allclose(sums, 1.0, atol=0.01), \
        f"Sums ikke 1.0: min={sums.min():.4f}, max={sums.max():.4f}"

    assert pred.min() >= MIN_PROB * 0.99, \
        f"Under minimum: {pred.min():.6f}"


def normalize_prediction(pred):
    """Enforce minimum floor og normaliser."""
    pred = np.maximum(pred, MIN_PROB)
    return pred / pred.sum(axis=2, keepdims=True)


def submit_predictions(client, round_id, predictions, num_seeds):
    """Send inn prediksjoner for alle seeds.

    ADVARSEL: Overskriver tidligere innsendinger. Siste submission teller.
    """
    results = {}
    for seed_idx in range(num_seeds):
        if seed_idx not in predictions:
            print(f"ADVARSEL: Ingen prediksjon for seed {seed_idx}, bruker uniform")
            pred = np.full((40, 40, NUM_CLASSES), 1 / NUM_CLASSES)
        else:
            pred = normalize_prediction(predictions[seed_idx])

        validate_prediction(pred, pred.shape[0], pred.shape[1])

        print(f"  Sender seed {seed_idx}...")
        resp = client.submit(round_id, seed_idx, pred.tolist())
        print(f"  Seed {seed_idx}: {resp.get('status', 'OK')}")
        results[seed_idx] = resp

    return results
