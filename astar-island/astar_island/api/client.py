"""HTTP-klient for Astar Island API.

Håndterer autentisering, rate limiting, og alle API-endepunkter.
Simulate og submit krever eksplisitt bekreftelse via dry_run-mønster.
"""

import time
import json
import requests

from ..config import BASE_URL, SIMULATE_DELAY, SUBMIT_DELAY


class AstarClient:
    """Autentisert klient mot api.ainm.no/astar-island/."""

    def __init__(self, token):
        self.session = requests.Session()
        self.session.headers["Authorization"] = f"Bearer {token}"
        self._last_simulate = 0
        self._last_submit = 0

    # ─── Read-only endpoints (trygge, ingen budsjett-kostnad) ───

    def get_rounds(self):
        """Hent alle runder."""
        return self.session.get(f"{BASE_URL}/astar-island/rounds").json()

    def get_active_round(self):
        """Finn aktiv runde. Returnerer None hvis ingen er aktiv."""
        rounds = self.get_rounds()
        return next((r for r in rounds if r["status"] == "active"), None)

    def get_round_details(self, round_id):
        """Hent rundedetaljer inkludert initial states for alle seeds."""
        return self.session.get(f"{BASE_URL}/astar-island/rounds/{round_id}").json()

    def get_budget(self):
        """Sjekk gjenstående query-budsjett for aktiv runde."""
        return self.session.get(f"{BASE_URL}/astar-island/budget").json()

    def get_my_rounds(self):
        """Hent runder med scores, rank, og budsjett."""
        return self.session.get(f"{BASE_URL}/astar-island/my-rounds").json()

    def get_my_predictions(self, round_id):
        """Hent innsendte prediksjoner med argmax og confidence."""
        return self.session.get(
            f"{BASE_URL}/astar-island/my-predictions/{round_id}"
        ).json()

    def get_analysis(self, round_id, seed_index):
        """Hent post-runde analyse (prediksjon vs ground truth). Kun etter runden er ferdig."""
        return self.session.get(
            f"{BASE_URL}/astar-island/analysis/{round_id}/{seed_index}"
        ).json()

    def get_leaderboard(self):
        """Hent offentlig leaderboard."""
        return self.session.get(f"{BASE_URL}/astar-island/leaderboard").json()

    # ─── Budsjett-kostende endpoints (krever forsiktighet) ───

    def simulate(self, round_id, seed_index, viewport_x, viewport_y,
                 viewport_w=15, viewport_h=15):
        """Kjør én simulering og observer gjennom viewport.

        ADVARSEL: Koster 1 query fra budsjettet (50 per runde).
        """
        # Rate limiting
        elapsed = time.time() - self._last_simulate
        if elapsed < SIMULATE_DELAY:
            time.sleep(SIMULATE_DELAY - elapsed)

        resp = self.session.post(f"{BASE_URL}/astar-island/simulate", json={
            "round_id": round_id,
            "seed_index": seed_index,
            "viewport_x": viewport_x,
            "viewport_y": viewport_y,
            "viewport_w": viewport_w,
            "viewport_h": viewport_h,
        })
        self._last_simulate = time.time()

        if resp.status_code != 200:
            raise RuntimeError(
                f"Simulate feilet: {resp.status_code} - {resp.text[:300]}"
            )
        return resp.json()

    def submit(self, round_id, seed_index, prediction_list):
        """Send inn prediksjon for ett seed.

        ADVARSEL: Overskriver tidligere innsending for dette seed.
        prediction_list: height x width x 6 nested liste (ikke numpy).
        """
        # Rate limiting
        elapsed = time.time() - self._last_submit
        if elapsed < SUBMIT_DELAY:
            time.sleep(SUBMIT_DELAY - elapsed)

        resp = self.session.post(f"{BASE_URL}/astar-island/submit", json={
            "round_id": round_id,
            "seed_index": seed_index,
            "prediction": prediction_list,
        })
        self._last_submit = time.time()

        if resp.status_code != 200:
            raise RuntimeError(
                f"Submit feilet: {resp.status_code} - {resp.text[:300]}"
            )
        return resp.json()
