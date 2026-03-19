"""Viewport query-planlegging v3: To-runde adaptiv strategi.

Runde A (utforskende): 25 queries — 1 obs per viewport, bred dekking
Mellomanalyse: Juster basert på faktisk data
Runde B (målrettet): 25 queries — repeat-obs der usikkerheten er størst

VIKTIG: Denne modulen PLANLEGGER queries. Selve utførelsen krever
eksplisitt godkjenning fra brukeren.
"""

import numpy as np
from collections import Counter

# 3x3 grid av 15x15 viewports som dekker 40x40
# Posisjonene 0, 13, 25 gir overlapp: 0-14, 13-27, 25-39
GRID_POSITIONS = [(vx, vy) for vy in [0, 13, 25] for vx in [0, 13, 25]]


def _score_viewport(data, vx, vy, vw, vh):
    """Ranger et viewport etter hvor dynamisk/interessant det er.

    Høyere score = mer verdi å observere.
    """
    settlements = data["settlements"]
    grid = data["grid"]
    h, w = data["h"], data["w"]

    score = 0

    # Tell settlements innenfor viewport
    settlement_count = sum(
        1 for s in settlements
        if vx <= s.get("x", 0) < vx + vw
        and vy <= s.get("y", 0) < vy + vh
    )
    score += settlement_count * 10

    # Tell dynamiske landceller (ikke ocean, ikke mountain)
    land_cells = 0
    ocean_mountain = 0
    for y in range(vy, min(vy + vh, h)):
        for x in range(vx, min(vx + vw, w)):
            code = grid[y][x]
            if code in (5, 10):
                ocean_mountain += 1
            else:
                land_cells += 1

    score += land_cells
    score -= ocean_mountain * 0.5

    return score, settlement_count, land_cells, ocean_mountain


def plan_phase_a(initial_data_list, budget=25):
    """Runde A: Utforskende queries — 1 obs per viewport, bred dekking.

    Velger de beste 5 viewports per seed (basert på settlement-tetthet).
    5 seeds × 5 viewports × 1 obs = 25 queries.

    Returnerer (queries, viewport_scores) der viewport_scores brukes i fase B.
    """
    queries = []
    viewport_info = {}  # (seed_idx, vx, vy) → score info
    queries_per_seed = budget // len(initial_data_list)

    for seed_idx, data in enumerate(initial_data_list):
        h, w = data["h"], data["w"]

        scored = []
        for vx, vy in GRID_POSITIONS:
            vw = min(15, w - vx)
            vh = min(15, h - vy)
            score, n_sett, n_land, n_static = _score_viewport(data, vx, vy, vw, vh)
            scored.append((score, vx, vy, vw, vh, n_sett, n_land, n_static))
            viewport_info[(seed_idx, vx, vy)] = {
                "score": score,
                "settlements": n_sett,
                "land_cells": n_land,
                "static_cells": n_static,
            }

        scored.sort(key=lambda x: -x[0])

        # Velg topp viewports innen budsjettet
        for i in range(min(queries_per_seed, len(scored))):
            score, vx, vy, vw, vh, n_sett, n_land, n_static = scored[i]
            queries.append({
                "seed_index": seed_idx,
                "viewport_x": vx, "viewport_y": vy,
                "viewport_w": vw, "viewport_h": vh,
                "reason": f"explore_rank{i+1}_sett{n_sett}",
                "_score": score,
            })

    queries = queries[:budget]
    _print_plan("FASE A (utforskende)", queries)
    return queries, viewport_info


def plan_phase_b(initial_data_list, phase_a_results, viewport_info, budget=25):
    """Runde B: Målrettede repeat-queries basert på Fase A-resultater.

    Analyserer Fase A-data og bestemmer:
    1. Hvilke viewports hadde mest variasjon/usikkerhet? → Repeat-obs
    2. Hvilke viewports fra Fase A bør IKKE re-observeres? → Stabile/forutsigbare
    3. Er det uobserverte viewports som burde inkluderes? → Coverage-gaps

    Returnerer queries-liste.
    """
    from ..analysis.observations import collect_observations
    from ..config import terrain_code_to_class

    queries = []
    queries_per_seed = budget // len(initial_data_list)

    for seed_idx, data in enumerate(initial_data_list):
        h, w = data["h"], data["w"]

        # Samle observasjoner fra Fase A for dette seed
        observations = collect_observations(phase_a_results, seed_idx, w, h)

        # Analyser hvert viewport vi observerte i Fase A
        phase_a_viewports = set()
        for q in phase_a_results:
            if q.get("_query", q).get("seed_index") == seed_idx:
                qinfo = q.get("_query", q)
                phase_a_viewports.add((qinfo["viewport_x"], qinfo["viewport_y"]))

        # Scorer viewports for Fase B basert på observert data
        candidates = []

        for vx, vy in GRID_POSITIONS:
            vw = min(15, w - vx)
            vh = min(15, h - vy)

            # Tell observerte terrengtyper i dette viewport
            type_counts = Counter()
            n_observed = 0
            n_settlement_obs = 0
            n_unique_types = 0

            for y in range(vy, min(vy + vh, h)):
                for x in range(vx, min(vx + vw, w)):
                    if (y, x) in observations:
                        n_observed += 1
                        for cls in observations[(y, x)]:
                            type_counts[cls] += 1
                            if cls == 1:  # Settlement
                                n_settlement_obs += 1

            n_unique_types = len(type_counts)

            # Beregn repeat-verdi
            repeat_value = 0

            if (vx, vy) in phase_a_viewports and n_observed > 0:
                # Viewport vi allerede har observert:
                # Høy verdi hvis mye variasjon (mange terrengtyper)
                # Høy verdi hvis mange settlements (stokastisk)
                repeat_value += n_unique_types * 5
                repeat_value += n_settlement_obs * 3

                # Settlement-andel: høyere → mer interessant å re-observere
                sett_ratio = n_settlement_obs / max(n_observed, 1)
                repeat_value += sett_ratio * 50

            else:
                # Viewport vi IKKE observerte i Fase A:
                # Bruk initial state score som fallback
                info = viewport_info.get((seed_idx, vx, vy), {})
                # Lavere prioritet enn repeat av observerte viewports
                repeat_value = info.get("score", 0) * 0.3

            candidates.append((repeat_value, vx, vy, vw, vh,
                               (vx, vy) in phase_a_viewports))

        candidates.sort(key=lambda x: -x[0])

        # Velg topp viewports
        selected = 0
        for value, vx, vy, vw, vh, was_observed in candidates:
            if selected >= queries_per_seed:
                break
            reason = "repeat" if was_observed else "new_coverage"
            queries.append({
                "seed_index": seed_idx,
                "viewport_x": vx, "viewport_y": vy,
                "viewport_w": vw, "viewport_h": vh,
                "reason": f"{reason}_value{value:.0f}",
                "_score": value,
            })
            selected += 1

    queries = queries[:budget]
    _print_plan("FASE B (målrettet)", queries)
    return queries


def _print_plan(title, queries):
    """Skriv ut query-plan oversikt."""
    print(f"\n{'='*50}")
    print(f"  {title}: {len(queries)} queries")
    print(f"{'='*50}")

    per_seed = Counter(q["seed_index"] for q in queries)
    for sid in sorted(per_seed):
        sq = [q for q in queries if q["seed_index"] == sid]
        vps = set((q["viewport_x"], q["viewport_y"]) for q in sq)
        print(f"  Seed {sid}: {per_seed[sid]} queries, {len(vps)} unike viewports")
        for q in sq:
            print(f"    vp=({q['viewport_x']:2d},{q['viewport_y']:2d}) {q['reason']}")


# === Legacy/convenience exports ===

def plan_viewports(initial_data_list, total_budget=50):
    """Legacy: full plan i én runde. Bruk plan_phase_a + plan_phase_b for v3."""
    queries, _ = plan_phase_a(initial_data_list, budget=total_budget)
    return queries
