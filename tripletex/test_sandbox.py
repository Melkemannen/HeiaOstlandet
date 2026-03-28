"""
Standalone sandbox test script.

Tests task handlers directly against the Tripletex sandbox — no server or ngrok needed.

Usage:
    python test_sandbox.py <task_type>

Task types:
    create_employee
    create_customer
    create_product
    create_invoice
    create_travel_expense
    delete_travel_expense
    create_project
    create_department

Credentials via environment variables:
    TRIPLETEX_BASE_URL   e.g. https://kkpqfuj-amager.tripletex.dev/v2
    TRIPLETEX_TOKEN      your session token

Example:
    export TRIPLETEX_BASE_URL=https://kkpqfuj-amager.tripletex.dev/v2
    export TRIPLETEX_TOKEN=your-token-here
    python test_sandbox.py create_employee
"""
import json
import logging
import os
import sys

from tripletex_client import TripletexClient
from tasks.employee import handle_create_employee
from tasks.customer import handle_create_customer
from tasks.product import handle_create_product
from tasks.invoice import handle_create_invoice
from tasks.travel_expense import handle_create_travel_expense, handle_delete_travel_expense
from tasks.project import handle_create_project
from tasks.department import handle_create_department

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

# Hardcoded test fields per task type
TEST_CASES = {
    "create_employee": {
        "first_name": "Ola",
        "last_name": "Nordmann",
        "email": "ola.nordmann2@example.org",
        "role": "administrator",
    },
    "create_customer": {
        "name": "Acme AS",
        "email": "post@acme.no",
        "phone": "12345678",
    },
    "create_product": {
        "name": "Hammer",
        "price": 99.0,
        "product_number": "PRD-001",
    },
    "create_invoice": {
        "customer_name": "Acme AS",
        "invoice_date": "2026-03-21",
        "due_date": "2026-04-21",
    },
    "create_travel_expense": {
        "description": "Test reise Oslo-Bergen",
        "date": "2026-03-21",
        "amount": 1500.0,
    },
    "delete_travel_expense": {
        "description": "Test reise Oslo-Bergen",
    },
    "create_project": {
        "name": "Testprosjekt Alpha",
        "customer_name": "Acme AS",
        "start_date": "2026-03-21",
    },
    "create_department": {
        "name": "Testavdeling",
    },
}

HANDLERS = {
    "create_employee": handle_create_employee,
    "create_customer": handle_create_customer,
    "create_product": handle_create_product,
    "create_invoice": handle_create_invoice,
    "create_travel_expense": handle_create_travel_expense,
    "delete_travel_expense": handle_delete_travel_expense,
    "create_project": handle_create_project,
    "create_department": handle_create_department,
}


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        print("Available task types:")
        for t in TEST_CASES:
            print(f"  {t}")
        sys.exit(1)

    task_type = sys.argv[1]

    base_url = os.environ.get("TRIPLETEX_BASE_URL")
    token = os.environ.get("TRIPLETEX_TOKEN")
    if not base_url or not token:
        print("ERROR: Set TRIPLETEX_BASE_URL and TRIPLETEX_TOKEN environment variables.")
        sys.exit(1)

    if task_type not in HANDLERS:
        print(f"ERROR: Unknown task type '{task_type}'")
        print(f"Available: {', '.join(HANDLERS)}")
        sys.exit(1)

    fields = TEST_CASES[task_type]
    print(f"\nRunning: {task_type}")
    print(f"Fields:  {json.dumps(fields, indent=2)}\n")

    client = TripletexClient(base_url, token)
    HANDLERS[task_type](client, fields)

    print(f"\nDone. Check the sandbox UI to verify:")
    print(f"  https://kkpqfuj-amager.tripletex.dev")


if __name__ == "__main__":
    main()
