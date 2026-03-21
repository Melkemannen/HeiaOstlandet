import logging

from tripletex_client import TripletexClient

log = logging.getLogger(__name__)


def handle_create_product(client: TripletexClient, fields: dict) -> None:
    name = fields.get("name") or ""
    price = fields.get("price")
    product_number = fields.get("product_number")

    if price is not None:
        try:
            price = float(price)
        except (TypeError, ValueError):
            price = None

    product = client.create_product(name=name, price=price, product_number=product_number)
    log.info("Created product id=%s name=%s", product["id"], product["name"])
