"""Prior-sannsynligheter basert på initial state og R1-kalibrerte modeller.

Brukes for celler som ikke er observert via simulate-queries.
Kalibrert mot Round 1 replay-data:
  - Settlements vokser 5-8x (30→220+)
  - Porter: 1 initial → 12-25 ved kystceller nær settlements
  - Ruiner oppstår ved faction-grenser
  - Skog er delvis resistent men kan overtas
"""

import numpy as np

from ..config import NUM_CLASSES, MIN_PROB


def compute_settlement_distance_map(grid, settlements, h, w):
    """BFS-basert avstandskart fra alle initial settlements.

    Returnerer 2D array med Manhattan-avstand til nærmeste settlement.
    Hav og fjell blokkerer IKKE (settlements kan ekspandere forbi dem
    i termer av territoriell innflytelse, selv om de ikke kan bygges der).
    """
    dist = np.full((h, w), 999, dtype=np.int32)

    for s in settlements:
        sx, sy = s.get("x", 0), s.get("y", 0)
        if 0 <= sy < h and 0 <= sx < w:
            for y in range(h):
                for x in range(w):
                    d = abs(x - sx) + abs(y - sy)
                    if d < dist[y][x]:
                        dist[y][x] = d

    return dist


def compute_ocean_adjacency(grid, h, w):
    """Finn celler som grenser til ocean (kystceller).

    Returnerer boolean 2D array.
    """
    coastal = np.zeros((h, w), dtype=bool)
    for y in range(h):
        for x in range(w):
            if grid[y][x] == 10:  # Ocean
                continue
            for dy, dx in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                ny, nx = y + dy, x + dx
                if 0 <= ny < h and 0 <= nx < w and grid[ny][nx] == 10:
                    coastal[y][x] = True
                    break
    return coastal


def compute_settlement_density(settlements, h, w, radius=6):
    """Beregn settlement-tetthet per celle (antall settlements innen radius).

    Høyere tetthet → mer ekspansjon, mer konflikt, flere porter.
    """
    density = np.zeros((h, w), dtype=np.int32)
    for s in settlements:
        sx, sy = s.get("x", 0), s.get("y", 0)
        for y in range(max(0, sy - radius), min(h, sy + radius + 1)):
            for x in range(max(0, sx - radius), min(w, sx + radius + 1)):
                if abs(x - sx) + abs(y - sy) <= radius:
                    density[y][x] += 1
    return density


def build_prior_map(grid, settlements, h, w):
    """Bygg komplett prior-kart for alle celler.

    Returnerer (h, w, 6) numpy array med sannsynlighetsfordelinger.

    Kalibrert mot R1 replay-data:
    - ~15% av landceller blir settlements etter 50 år
    - Porter: coastal cells nær settlements
    - Ruiner: ~2-3% av celler, mest ved settlement-grenser
    """
    dist_map = compute_settlement_distance_map(grid, settlements, h, w)
    coastal = compute_ocean_adjacency(grid, h, w)
    density = compute_settlement_density(settlements, h, w)

    priors = np.full((h, w, NUM_CLASSES), MIN_PROB)
    num_settlements = len(settlements)

    for y in range(h):
        for x in range(w):
            code = grid[y][x]
            is_border = (y == 0 or y == h - 1 or x == 0 or x == w - 1)
            d = dist_map[y][x]
            is_coastal = coastal[y][x]
            local_density = density[y][x]

            # === Statiske celler (100% sikker) ===
            if code == 5:  # Mountain
                priors[y][x][5] = 1.0
                continue
            if code == 10 or is_border:  # Ocean / border
                priors[y][x][0] = 1.0
                continue

            # === Dynamiske celler ===
            # Base-sannsynligheter avhenger av avstand til settlements
            # Kalibrert fra R1: settlements dekker ~15% av kartet ved step 50

            if code in (1, 2):
                # Initial settlement/port: høy sjanse for å forbli settlement
                p_settlement = 0.55
                p_empty = 0.10
                p_port = 0.15 if is_coastal else 0.03
                p_ruin = 0.08
                p_forest = 0.05
            elif d <= 2:
                # Veldig nær settlement: stor sjanse for ekspansjon
                p_settlement = 0.45
                p_empty = 0.15
                p_port = 0.12 if is_coastal else 0.02
                p_ruin = 0.06
                p_forest = 0.10 if code == 4 else 0.05
            elif d <= 5:
                # Nær settlement: moderat ekspansjonszone
                p_settlement = 0.30
                p_empty = 0.25
                p_port = 0.10 if is_coastal else 0.02
                p_ruin = 0.05
                p_forest = 0.20 if code == 4 else 0.08
            elif d <= 8:
                # Medium avstand
                p_settlement = 0.15
                p_empty = 0.35
                p_port = 0.06 if is_coastal else 0.01
                p_ruin = 0.03
                p_forest = 0.30 if code == 4 else 0.10
            elif d <= 12:
                # Lengre unna
                p_settlement = 0.08
                p_empty = 0.45
                p_port = 0.03 if is_coastal else 0.01
                p_ruin = 0.02
                p_forest = 0.35 if code == 4 else 0.10
            else:
                # Langt fra settlements
                p_settlement = 0.03
                p_empty = 0.55
                p_port = 0.02 if is_coastal else 0.01
                p_ruin = 0.01
                p_forest = 0.35 if code == 4 else 0.05

            # Juster for settlement-tetthet (mange naboer → mer ekspansjon)
            if local_density >= 3 and d <= 8:
                boost = min(0.10, local_density * 0.02)
                p_settlement += boost
                p_empty -= boost * 0.7
                p_ruin += boost * 0.3  # Mer tetthet → mer konflikt → mer ruin

            # Kystceller med settlements nær har ekstra port-sjanse
            if is_coastal and d <= 5 and local_density >= 2:
                p_port += 0.05
                p_empty -= 0.05

            # Ruin mellom settlement-clustere (grensesone)
            if 3 <= d <= 8 and local_density >= 2:
                p_ruin += 0.03
                p_empty -= 0.03

            p_mountain = MIN_PROB
            probs = np.array([p_empty, p_settlement, p_port, p_ruin, p_forest, p_mountain])

            # Normaliser
            probs = np.maximum(probs, MIN_PROB)
            probs = probs / probs.sum()
            priors[y][x] = probs

    return priors


# Legacy interface for backward compatibility
def get_prior_for_cell(initial_code, x, y, map_width, map_height, settlement_set):
    """Legacy: Beregn prior for én celle. Bruk build_prior_map for bedre ytelse."""
    is_border = (y == 0 or y == map_height - 1 or x == 0 or x == map_width - 1)

    if initial_code == 5:
        probs = np.full(NUM_CLASSES, MIN_PROB)
        probs[5] = 1.0
        return probs

    if initial_code == 10 or is_border:
        probs = np.full(NUM_CLASSES, MIN_PROB)
        probs[0] = 1.0
        return probs

    min_dist = 999
    for sx, sy in settlement_set:
        dist = abs(x - sx) + abs(y - sy)
        if dist < min_dist:
            min_dist = dist

    # Bruk kalibrerte verdier fra R1
    if initial_code in (1, 2):
        return np.array([0.10, 0.55, 0.10, 0.08, 0.05, MIN_PROB])

    if min_dist <= 3:
        if initial_code == 4:
            return np.array([0.15, 0.35, 0.03, 0.05, 0.30, MIN_PROB])
        return np.array([0.15, 0.45, 0.05, 0.06, 0.10, MIN_PROB])
    elif min_dist <= 7:
        if initial_code == 4:
            return np.array([0.25, 0.20, 0.02, 0.04, 0.40, MIN_PROB])
        return np.array([0.30, 0.25, 0.03, 0.04, 0.15, MIN_PROB])
    elif min_dist <= 12:
        if initial_code == 4:
            return np.array([0.30, 0.08, 0.01, 0.02, 0.50, MIN_PROB])
        return np.array([0.50, 0.10, 0.02, 0.02, 0.15, MIN_PROB])
    else:
        if initial_code == 4:
            return np.array([0.15, 0.03, MIN_PROB, 0.01, 0.70, MIN_PROB])
        return np.array([0.65, 0.03, MIN_PROB, 0.01, 0.10, MIN_PROB])
