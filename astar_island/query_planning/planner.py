"""Viewport query-planlegging.

Bestemmer hvilke viewports som skal observeres og i hvilken rekkefølge.
Balanserer coverage (dekke kartet) vs. depth (multiple observasjoner).

VIKTIG: Denne modulen PLANLEGGER queries. Selve utførelsen krever
eksplisitt godkjenning fra brukeren.
"""

from collections import Counter

# Full 40x40 coverage med 3x3 grid av 15x15 viewports
# Posisjonene 0, 13, 25 gir overlapp: 0-14, 13-27, 25-39
GRID_POSITIONS = [(vx, vy) for vy in [0, 13, 25] for vx in [0, 13, 25]]


def plan_viewports(initial_data_list, total_budget=50):
    """Planlegg viewport-queries for å maksimere informasjon.

    Strategi:
    - 9 viewports per seed dekker hele 40x40 kartet (full coverage)
    - 9 x 5 = 45 queries for full dekning
    - Resterende queries brukes på repeat-observasjoner i settlement-tette områder

    Returnerer liste med query-dicts (klar til å sendes til API).
    """
    queries = []

    for seed_idx, data in enumerate(initial_data_list):
        h, w = data["h"], data["w"]

        for vx, vy in GRID_POSITIONS:
            vw = min(15, w - vx)
            vh = min(15, h - vy)
            queries.append({
                "seed_index": seed_idx,
                "viewport_x": vx, "viewport_y": vy,
                "viewport_w": vw, "viewport_h": vh,
                "reason": "coverage"
            })

    # Repeat-queries på settlement-tette områder
    remaining = total_budget - len(queries)
    if remaining > 0:
        repeat_candidates = []
        for seed_idx, data in enumerate(initial_data_list):
            settlements = data["settlements"]
            for vx, vy in GRID_POSITIONS:
                vw = min(15, data["w"] - vx)
                vh = min(15, data["h"] - vy)
                count = sum(
                    1 for s in settlements
                    if vx <= s.get("x", 0) < vx + vw
                    and vy <= s.get("y", 0) < vy + vh
                )
                if count > 0:
                    repeat_candidates.append((count, seed_idx, vx, vy, vw, vh))

        repeat_candidates.sort(key=lambda x: -x[0])
        for i, (count, seed_idx, vx, vy, vw, vh) in enumerate(repeat_candidates):
            if i >= remaining:
                break
            queries.append({
                "seed_index": seed_idx,
                "viewport_x": vx, "viewport_y": vy,
                "viewport_w": vw, "viewport_h": vh,
                "reason": f"repeat_settlements_{count}"
            })

    queries = queries[:total_budget]

    # Oppsummering
    print(f"\nPlanlagte queries: {len(queries)}/{total_budget}")
    per_seed = Counter(q["seed_index"] for q in queries)
    for sid in sorted(per_seed):
        print(f"  Seed {sid}: {per_seed[sid]} queries")

    return queries
