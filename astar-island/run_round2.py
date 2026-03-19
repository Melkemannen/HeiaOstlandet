"""Runde 2 runner med to-runde adaptiv strategi.

Bruk:
  python run_round2.py --phase a     # Kjør Fase A (25 utforskende queries)
  python run_round2.py --phase ab    # Analyser A-resultater, planlegg B
  python run_round2.py --phase b     # Kjør Fase B (25 målrettede queries)
  python run_round2.py --phase predict  # Bygg prediksjoner
  python run_round2.py --phase submit   # Send inn

Hvert steg viser hva det vil gjøre og krever bekreftelse.
"""

import argparse
import os
import sys
import pickle
import json

sys.path.insert(0, ".")

from astar_island.api.client import AstarClient
from astar_island.analysis.initial_state import analyze_initial_state
from astar_island.analysis.observations import collect_observations, compute_global_frequencies
from astar_island.query_planning.planner import plan_phase_a, plan_phase_b
from astar_island.prediction.builder import build_predictions
from astar_island.prediction.submit import submit_predictions
from astar_island.data.cache import save_query_results, load_query_results

CACHE_DIR = "cached_data"
TOKEN_FILE = os.path.join("..", "..", "NMiAI2026", ".env.astar")


def get_token():
    if os.environ.get("ASTAR_TOKEN"):
        return os.environ["ASTAR_TOKEN"]
    for path in [TOKEN_FILE, ".env.astar", ".env"]:
        if os.path.exists(path):
            with open(path) as f:
                for line in f:
                    if "ASTAR_TOKEN=" in line:
                        return line.strip().split("=", 1)[1].strip().strip('"')
    print("FEIL: Ingen token funnet")
    sys.exit(1)


def load_initial_data():
    path = os.path.join(CACHE_DIR, "initial_data.pkl")
    with open(path, "rb") as f:
        return pickle.load(f)


def save_pickle(name, data):
    os.makedirs(CACHE_DIR, exist_ok=True)
    path = os.path.join(CACHE_DIR, name)
    with open(path, "wb") as f:
        pickle.dump(data, f)
    print(f"  Lagret: {path}")


def load_pickle(name):
    path = os.path.join(CACHE_DIR, name)
    with open(path, "rb") as f:
        return pickle.load(f)


def run_queries(client, round_id, queries):
    """Kjør queries med rate limiting. Returnerer resultater."""
    results = []
    for i, q in enumerate(queries):
        try:
            result = client.simulate(
                round_id,
                q["seed_index"],
                q["viewport_x"], q["viewport_y"],
                q.get("viewport_w", 15), q.get("viewport_h", 15),
            )
            result["_query"] = q
            results.append(result)
            used = result.get("queries_used", "?")
            print(f"  [{i+1}/{len(queries)}] seed={q['seed_index']} "
                  f"vp=({q['viewport_x']},{q['viewport_y']}) "
                  f"budget={used} — OK")
        except RuntimeError as e:
            print(f"  [{i+1}/{len(queries)}] FEIL: {e}")
    return results


def phase_a(client, round_id):
    """Fase A: 25 utforskende queries."""
    initial_data = load_initial_data()

    # Planlegg
    queries, viewport_info = plan_phase_a(initial_data, budget=25)
    save_pickle("viewport_info.pkl", viewport_info)

    print(f"\n*** KLAR TIL Å KJØRE {len(queries)} QUERIES ***")
    print(f"*** Dette bruker {len(queries)} av 50 queries ***")

    # Kjør
    results = run_queries(client, round_id, queries)
    save_query_results(round_id, results)
    save_pickle("phase_a_results.pkl", results)

    print(f"\nFase A ferdig: {len(results)}/{len(queries)} queries utført.")
    return results


def analyze_phase_a():
    """Analyser Fase A-resultater og planlegg Fase B."""
    initial_data = load_initial_data()
    results = load_pickle("phase_a_results.pkl")
    viewport_info = load_pickle("viewport_info.pkl")

    print("\n=== ANALYSE AV FASE A ===")

    for seed_idx in range(len(initial_data)):
        h = initial_data[seed_idx]["h"]
        w = initial_data[seed_idx]["w"]
        obs = collect_observations(results, seed_idx, w, h)

        n_obs = len(obs)
        print(f"\nSeed {seed_idx}: {n_obs} celler observert")

        # Tell terrengtyper
        from collections import Counter
        type_counts = Counter()
        for cell_obs in obs.values():
            for cls in cell_obs:
                type_counts[cls] += 1

        total = sum(type_counts.values())
        from astar_island.config import CLASS_NAMES
        for cls in range(6):
            count = type_counts.get(cls, 0)
            pct = 100 * count / total if total > 0 else 0
            print(f"  {CLASS_NAMES[cls]}: {count} ({pct:.1f}%)")

    # Planlegg Fase B
    print("\n=== FASE B PLAN ===")
    queries_b = plan_phase_b(initial_data, results, viewport_info, budget=25)
    save_pickle("phase_b_plan.pkl", queries_b)

    return queries_b


def phase_b(client, round_id):
    """Fase B: 25 målrettede repeat-queries."""
    queries = load_pickle("phase_b_plan.pkl")

    print(f"\n*** KLAR TIL Å KJØRE {len(queries)} QUERIES ***")
    print(f"*** Dette bruker de siste {len(queries)} av 50 queries ***")

    results = run_queries(client, round_id, queries)
    save_pickle("phase_b_results.pkl", results)

    # Kombiner med Fase A-resultater
    phase_a = load_pickle("phase_a_results.pkl")
    all_results = phase_a + results
    save_query_results(round_id + "_all", all_results)
    save_pickle("all_results.pkl", all_results)

    print(f"\nFase B ferdig: {len(results)}/{len(queries)} queries utført.")
    print(f"Totalt: {len(all_results)} queries.")
    return all_results


def predict():
    """Bygg prediksjoner fra alle resultater."""
    initial_data = load_initial_data()
    all_results = load_pickle("all_results.pkl")

    predictions = build_predictions(
        initial_data, all_results,
        map_width=40, map_height=40, num_seeds=5
    )

    save_pickle("predictions.pkl", predictions)
    print("\nPrediksjoner lagret.")
    return predictions


def submit(client, round_id):
    """Send inn prediksjoner."""
    predictions = load_pickle("predictions.pkl")

    print(f"\n*** KLAR TIL Å SENDE INN 5 SEEDS ***")
    print(f"*** Dette OVERSKRIVER eventuelle tidligere innsendinger ***")

    results = submit_predictions(client, round_id, predictions, num_seeds=5)
    print("\nInnsending fullført!")
    return results


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--phase", required=True,
                        choices=["a", "ab", "b", "predict", "submit"])
    args = parser.parse_args()

    token = get_token()
    client = AstarClient(token)

    # Finn aktiv runde
    active = client.get_active_round()
    if not active:
        print("Ingen aktiv runde!")
        return
    round_id = active["id"]
    budget = client.get_budget()
    print(f"Runde: {round_id}")
    print(f"Budsjett: {budget['queries_used']}/{budget['queries_max']} brukt")

    if args.phase == "a":
        phase_a(client, round_id)
    elif args.phase == "ab":
        analyze_phase_a()
    elif args.phase == "b":
        phase_b(client, round_id)
    elif args.phase == "predict":
        predict()
    elif args.phase == "submit":
        submit(client, round_id)


if __name__ == "__main__":
    main()
