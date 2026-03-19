"""Aggregering og analyse av simulerings-observasjoner.

Samler viewport-resultater fra simulate-kall og bygger
per-celle observasjonsdata for sannsynlighetsestimering.
"""

from collections import defaultdict, Counter

from ..config import terrain_code_to_class, NUM_CLASSES, CLASS_NAMES


def collect_observations(query_results, seed_index, map_width, map_height):
    """Samle alle observasjoner for ett seed.

    Returnerer dict: (y, x) → [class_index, class_index, ...]
    Flere observasjoner per celle gir bedre probability-estimater.
    """
    observations = defaultdict(list)

    for result in query_results:
        if result["_query"]["seed_index"] != seed_index:
            continue

        grid = result.get("grid", [])
        vp = result.get("viewport", result["_query"])
        vx = vp.get("x", vp.get("viewport_x", 0))
        vy = vp.get("y", vp.get("viewport_y", 0))

        for dy, row in enumerate(grid):
            for dx, cell in enumerate(row):
                y, x = vy + dy, vx + dx
                if 0 <= y < map_height and 0 <= x < map_width:
                    cls = terrain_code_to_class(cell)
                    observations[(y, x)].append(cls)

    return observations


def compute_global_frequencies(observations):
    """Beregn globale frekvenser fra alle observasjoner.

    Returnerer numpy-kompatibel liste med frekvens per klasse.
    Brukes som fallback-prior for uobserverte celler.
    """
    all_obs = []
    for obs_list in observations.values():
        all_obs.extend(obs_list)

    if not all_obs:
        return [1.0 / NUM_CLASSES] * NUM_CLASSES

    total = len(all_obs)
    freq = Counter(all_obs)

    print(f"  Globale observerte frekvenser:")
    for cls in range(NUM_CLASSES):
        f = freq.get(cls, 0) / total
        print(f"    {CLASS_NAMES[cls]}: {f:.3f}")

    return [freq.get(cls, 0) / total for cls in range(NUM_CLASSES)]
