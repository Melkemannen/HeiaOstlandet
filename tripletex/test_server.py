"""
End-to-end test: sends a prompt to the local /solve server.

Usage:
    python test_server.py

Requires:
    - uvicorn server:app running on port 8000
    - TRIPLETEX_BASE_URL and TRIPLETEX_TOKEN env vars set
"""
import json
import os
import requests

BASE_URL = os.environ.get("TRIPLETEX_BASE_URL", "https://kkpqfuj-amager.tripletex.dev/v2")
TOKEN = os.environ.get("TRIPLETEX_TOKEN", "")

PROMPTS = [
    "Opprett en ansatt med navn Kari Hansen, kari@example.org. Hun skal være kontoadministrator.",
    "Create a customer called Bergen Bygg AS with email post@bergenbygg.no",
    "Lag et produkt som heter Skrutrekker med pris 149 kr",
]

for prompt in PROMPTS:
    print(f"\nPrompt: {prompt}")
    resp = requests.post(
        "http://localhost:8000/solve",
        json={
            "prompt": prompt,
            "files": [],
            "tripletex_credentials": {
                "base_url": BASE_URL,
                "session_token": TOKEN,
            },
        },
        timeout=120,
    )
    print(f"Status: {resp.status_code}")
    print(f"Response: {json.dumps(resp.json(), indent=2)}")
