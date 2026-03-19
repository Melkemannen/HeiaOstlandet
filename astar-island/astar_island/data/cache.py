"""Cache for query-resultater og prediksjoner.

Lagrer data til JSON slik at vi kan re-analysere uten å bruke queries.
Nyttig for debugging og iterativ forbedring innenfor en runde.
"""

import json
import os
from datetime import datetime


DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "cached_data")


def ensure_data_dir():
    os.makedirs(DATA_DIR, exist_ok=True)


def save_query_results(round_id, results):
    """Lagre query-resultater til disk."""
    ensure_data_dir()
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = os.path.join(DATA_DIR, f"queries_{round_id[:8]}_{ts}.json")
    with open(path, "w") as f:
        json.dump(results, f, indent=2)
    print(f"  Query-resultater lagret: {path}")
    return path


def load_query_results(path):
    """Last query-resultater fra disk."""
    with open(path) as f:
        return json.load(f)


def save_round_details(round_id, details):
    """Lagre rundedetaljer (inkl. initial states) til disk."""
    ensure_data_dir()
    path = os.path.join(DATA_DIR, f"round_{round_id[:8]}.json")
    with open(path, "w") as f:
        json.dump(details, f, indent=2)
    print(f"  Rundedetaljer lagret: {path}")
    return path
