"""Analyse av initial states fra API-et.

Brukes til å forstå kartet FØR vi bruker simulate-queries.
Initial states er gratis og gir oss terreng-grid + settlement-posisjoner.
"""

import numpy as np
from collections import Counter

from ..config import STATIC_TERRAIN


def analyze_initial_state(state, seed_idx):
    """Analyser initial state for ett seed. Returnerer strukturert data-dict."""
    grid = state["grid"]
    settlements = state.get("settlements", [])
    h, w = len(grid), len(grid[0])

    counts = Counter()
    for row in grid:
        for cell in row:
            counts[cell] += 1

    print(f"\n--- Seed {seed_idx} ---")
    print(f"  Grid: {h}x{w}")
    print(f"  Terrengfordeling: {dict(sorted(counts.items()))}")
    print(f"  Settlements: {len(settlements)}")
    for s in settlements[:5]:
        print(f"    pos=({s.get('x')},{s.get('y')}) "
              f"port={s.get('has_port')} alive={s.get('alive')}")
    if len(settlements) > 5:
        print(f"    ... og {len(settlements)-5} til")

    return {
        "grid": grid,
        "settlements": settlements,
        "h": h,
        "w": w,
    }


def find_dynamic_regions(initial_data, radius=8):
    """Identifiser celler som sannsynligvis endrer seg under simulering.

    Dynamiske celler: landceller innen `radius` av en settlement.
    Statiske celler: fjell og hav (endrer seg aldri).
    """
    grid = initial_data["grid"]
    settlements = initial_data["settlements"]
    h, w = initial_data["h"], initial_data["w"]

    dynamic = np.zeros((h, w), dtype=bool)

    for s in settlements:
        sx, sy = s.get("x", 0), s.get("y", 0)
        for dy in range(-radius, radius + 1):
            for dx in range(-radius, radius + 1):
                ny, nx = sy + dy, sx + dx
                if 0 <= ny < h and 0 <= nx < w:
                    dynamic[ny][nx] = True

    # Fjern statiske celler
    for y in range(h):
        for x in range(w):
            if grid[y][x] in STATIC_TERRAIN:
                dynamic[y][x] = False

    n_dynamic = int(np.sum(dynamic))
    print(f"  Dynamiske celler: {n_dynamic}/{h*w} ({100*n_dynamic/(h*w):.0f}%)")
    return dynamic
