import logging
from datetime import date, timedelta

from tripletex_client import TripletexClient

log = logging.getLogger(__name__)


def handle_create_invoice(client: TripletexClient, fields: dict) -> None:
    customer_name = fields.get("customer_name") or ""
    invoice_date = fields.get("invoice_date") or str(date.today())
    due_date = fields.get("due_date") or str(date.today() + timedelta(days=30))

    # Find or create customer
    customer = client.find_customer(customer_name)
    if not customer:
        log.info("Customer not found, creating: %s", customer_name)
        customer = client.create_customer(name=customer_name)

    customer_id = customer["id"]

    # Create order first (required before invoice)
    order = client.create_order(customer_id=customer_id, order_date=invoice_date)
    order_id = order["id"]
    log.info("Created order id=%s", order_id)

    # Create invoice
    invoice = client.create_invoice(
        customer_id=customer_id,
        order_id=order_id,
        invoice_date=invoice_date,
        due_date=due_date,
    )
    log.info("Created invoice id=%s", invoice["id"])
