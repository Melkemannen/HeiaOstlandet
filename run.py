"""Hovedskript for Astar Island solver.

Kjører i faser med eksplisitt godkjenning mellom hver fase:
  1. Analyse (gratis) – les initial states, analyser kartet
  2. Planlegging – lag query-plan, vis til bruker
  3. Utførelse (krever godkjenning) – kjør queries i batches
  4. Prediksjon – bygg sannsynlighetsfordelinger
  5. Innsending (krever godkjenning) – submit predictions

Bruk: python run.py [--token TOKEN] [--phase PHASE] [--cached PATH]
"""

import argparse
import os
import sys

from astar_island.config import NUM_CLASSES
from astar_island.api.client import AstarClient
from astar_island.analysis.initial_state import analyze_initial_state, find_dynamic_regions
from astar_island.query_planning.planner import plan_viewports
from astar_island.prediction.builder import build_predictions
from astar_island.prediction.submit import submit_predictions
from astar_island.data.cache import save_query_results, save_round_details, load_query_results


def get_token(args):
    """Hent token fra argument, env-variabel, eller .env-fil."""
    if args.token:
        return args.token
    if os.environ.get("ASTAR_TOKEN"):
        return os.environ["ASTAR_TOKEN"]
    for env_file in [".env.astar", ".env"]:
        if os.path.exists(env_file):
            with open(env_file) as f:
                for line in f:
                    if line.strip().startswith("ASTAR_TOKEN="):
                        return line.strip().split("=", 1)[1].strip().strip('"')
    print("FEIL: Ingen token funnet. Bruk --token, ASTAR_TOKEN env, eller .env.astar fil.")
    sys.exit(1)


def phase_analyze(client):
    """Fase 1: Analyser initial states (gratis, ingen queries brukt)."""
    print("\n" + "=" * 60)
    print("FASE 1: ANALYSE (gratis)")
    print("=" * 60)

    round_info = client.get_active_round()
    if not round_info:
        print("Ingen aktiv runde funnet.")
        return None, None, None

    round_id = round_info["id"]
    print(f"Aktiv runde: {round_id}")
    print(f"Status: {round_info.get('status')}")

    # Sjekk budsjett
    budget = client.get_budget()
    print(f"Budsjett: {budget}")

    # Hent rundedetaljer med initial states
    details = client.get_round_details(round_id)
    seeds = details.get("seeds", details.get("initial_states", []))
    num_seeds = len(seeds)
    print(f"Antall seeds: {num_seeds}")

    # Analyser initial states
    initial_data_list = []
    for i, seed in enumerate(seeds):
        data = analyze_initial_state(seed, i)
        find_dynamic_regions(data)
        initial_data_list.append(data)

    # Cache rundedetaljer
    save_round_details(round_id, details)

    return round_id, initial_data_list, num_seeds


def phase_plan(initial_data_list, budget_remaining=50):
    """Fase 2: Planlegg queries (ingen API-kall)."""
    print("\n" + "=" * 60)
    print("FASE 2: PLANLEGGING")
    print("=" * 60)

    queries = plan_viewports(initial_data_list, total_budget=budget_remaining)

    print(f"\n--- PLAN KLAR ---")
    print(f"Totalt {len(queries)} queries planlagt.")
    print("Vis plan til bruker og vent på godkjenning før utførelse.")

    return queries


def phase_execute(client, round_id, queries, batch_size=10):
    """Fase 3: Kjør queries i batches (krever godkjenning).

    ADVARSEL: Denne funksjonen bruker query-budsjettet.
    """
    print("\n" + "=" * 60)
    print(f"FASE 3: UTFØRELSE ({len(queries)} queries)")
    print("=" * 60)

    all_results = []

    for batch_start in range(0, len(queries), batch_size):
        batch = queries[batch_start:batch_start + batch_size]
        batch_end = batch_start + len(batch)
        print(f"\n--- Batch {batch_start + 1}-{batch_end} av {len(queries)} ---")

        for q in batch:
            try:
                result = client.simulate(
                    round_id,
                    q["seed_index"],
                    q["viewport_x"],
                    q["viewport_y"],
                    q.get("viewport_w", 15),
                    q.get("viewport_h", 15),
                )
                result["_query"] = q
                all_results.append(result)
                print(f"  OK: seed={q['seed_index']} "
                      f"vp=({q['viewport_x']},{q['viewport_y']}) "
                      f"queries_used={result.get('queries_used', '?')}")
            except RuntimeError as e:
                print(f"  FEIL: {e}")

    # Cache resultater
    cache_path = save_query_results(round_id, all_results)
    print(f"\nFerdig: {len(all_results)}/{len(queries)} queries utført.")
    print(f"Resultater cachet: {cache_path}")

    return all_results


def phase_predict(initial_data_list, query_results, map_width=40, map_height=40,
                  num_seeds=5):
    """Fase 4: Bygg prediksjoner (ingen API-kall)."""
    print("\n" + "=" * 60)
    print("FASE 4: PREDIKSJON")
    print("=" * 60)

    predictions = build_predictions(
        initial_data_list, query_results,
        map_width, map_height, num_seeds
    )

    return predictions


def phase_submit(client, round_id, predictions, num_seeds):
    """Fase 5: Send inn prediksjoner (krever godkjenning).

    ADVARSEL: Overskriver eventuelle tidligere innsendinger.
    """
    print("\n" + "=" * 60)
    print(f"FASE 5: INNSENDING ({num_seeds} seeds)")
    print("=" * 60)

    results = submit_predictions(client, round_id, predictions, num_seeds)
    print("\nInnsending fullført.")
    return results


def main():
    parser = argparse.ArgumentParser(description="Astar Island Solver")
    parser.add_argument("--token", help="JWT token for API-autentisering")
    parser.add_argument("--phase", choices=["analyze", "plan", "execute", "predict", "submit", "all"],
                        default="analyze", help="Hvilken fase som skal kjøres")
    parser.add_argument("--cached", help="Sti til cached query-resultater (skip execute)")
    parser.add_argument("--batch-size", type=int, default=10, help="Queries per batch")
    args = parser.parse_args()

    token = get_token(args)
    client = AstarClient(token)

    # Fase 1: Analyse
    round_id, initial_data_list, num_seeds = phase_analyze(client)
    if not round_id:
        return

    if args.phase == "analyze":
        print("\nFase 1 ferdig. Kjør med --phase plan for neste steg.")
        return

    # Fase 2: Planlegging
    budget = client.get_budget()
    remaining = budget.get("remaining", budget.get("queries_remaining", 50))
    queries = phase_plan(initial_data_list, budget_remaining=remaining)

    if args.phase == "plan":
        print("\nFase 2 ferdig. Godkjenn planen og kjør med --phase execute.")
        return

    # Fase 3: Utførelse (eller bruk cached data)
    if args.cached:
        print(f"\nBruker cached data: {args.cached}")
        query_results = load_query_results(args.cached)
    else:
        if args.phase not in ("execute", "all"):
            print("\nBruk --phase execute eller --cached for å fortsette.")
            return
        query_results = phase_execute(client, round_id, queries, args.batch_size)

    if args.phase == "execute":
        print("\nFase 3 ferdig. Kjør med --phase predict --cached <path> for neste steg.")
        return

    # Fase 4: Prediksjon
    map_w = initial_data_list[0]["w"]
    map_h = initial_data_list[0]["h"]
    predictions = phase_predict(initial_data_list, query_results, map_w, map_h, num_seeds)

    if args.phase == "predict":
        print("\nFase 4 ferdig. Kjør med --phase submit for å sende inn.")
        return

    # Fase 5: Innsending
    phase_submit(client, round_id, predictions, num_seeds)


if __name__ == "__main__":
    main()
