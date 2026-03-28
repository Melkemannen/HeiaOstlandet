import logging

from tripletex_client import TripletexClient

log = logging.getLogger(__name__)

# Map LLM snake_case field names to Tripletex API camelCase field names.
# Both 'phone' and 'phone_number' are kept since the LLM may output either.
_CUSTOMER_FIELD_MAP = {
    "phone": "phoneNumber",
    "phone_number": "phoneNumber",
    "organization_number": "organizationNumber",
}


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


def handle_update_customer(client: TripletexClient, fields: dict) -> None:
    name = fields.get("customer_name", "")
    field_to_update = fields.get("field_to_update", "")
    new_value = fields.get("new_value")

    customers = client.list("/customer", params={"name": name, "fields": "id,name", "count": 5})
    if not customers:
        log.warning("Customer not found: %s", name)
        return

    customer_id = customers[0]["id"]
    api_field = _CUSTOMER_FIELD_MAP.get(field_to_update, field_to_update)
    client.put(f"/customer/{customer_id}", {api_field: new_value})
    log.info("Updated customer %s: %s = %s", customer_id, api_field, new_value)
