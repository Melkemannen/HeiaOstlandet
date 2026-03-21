import logging
from datetime import date

from tripletex_client import TripletexClient

log = logging.getLogger(__name__)


def handle_create_project(client: TripletexClient, fields: dict) -> None:
    name = fields.get("name") or ""
    customer_name = fields.get("customer_name") or ""
    start_date = fields.get("start_date") or str(date.today())

    # Find or create customer
    customer = client.find_customer(customer_name) if customer_name else None
    if not customer and customer_name:
        log.info("Customer not found, creating: %s", customer_name)
        customer = client.create_customer(name=customer_name)

    customer_id = customer["id"] if customer else None
    if not customer_id:
        log.warning("No customer for project — creating without customer")

    project = client.create_project(name=name, customer_id=customer_id, start_date=start_date)
    log.info("Created project id=%s name=%s", project["id"], project["name"])
