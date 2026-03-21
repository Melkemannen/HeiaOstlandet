import logging

from tripletex_client import TripletexClient

log = logging.getLogger(__name__)


def handle_create_customer(client: TripletexClient, fields: dict) -> None:
    name = fields.get("name") or ""
    email = fields.get("email")
    phone = fields.get("phone")
    org_number = fields.get("organization_number")

    customer = client.create_customer(
        name=name,
        email=email,
        phone_number=phone,
        organization_number=org_number,
    )
    log.info("Created customer id=%s name=%s", customer["id"], customer["name"])
