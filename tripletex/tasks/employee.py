import logging

from tripletex_client import TripletexClient

log = logging.getLogger(__name__)

# Tripletex role identifiers
ROLE_MAP = {
    "administrator": "ROLE_ADMINISTRATOR",
    "admin": "ROLE_ADMINISTRATOR",
    "kontoadministrator": "ROLE_ADMINISTRATOR",
    "user": "ROLE_USER",
    "bruker": "ROLE_USER",
    "accountant": "ROLE_ACCOUNTANT",
    "regnskapsforer": "ROLE_ACCOUNTANT",
}


def handle_create_employee(client: TripletexClient, fields: dict) -> None:
    first_name = fields.get("first_name") or ""
    last_name = fields.get("last_name") or ""
    email = fields.get("email")
    role_raw = (fields.get("role") or "").lower()

    employee = client.create_employee(
        first_name=first_name,
        last_name=last_name,
        email=email,
    )
    employee_id = employee["id"]
    log.info("Created employee id=%s", employee_id)

    # Assign role if specified
    if role_raw:
        role = ROLE_MAP.get(role_raw, role_raw.upper())
        _assign_role(client, employee_id, role)


def _assign_role(client: TripletexClient, employee_id: int, role: str) -> None:
    try:
        client.put(f"/employee/{employee_id}", {"roles": [{"name": role}]})
        log.info("Assigned role %s to employee %s", role, employee_id)
    except Exception as e:
        log.error("Failed to assign role %s: %s", role, e)


def handle_update_employee(client: TripletexClient, fields: dict) -> None:
    name = fields.get("employee_name", "")
    field_to_update = fields.get("field_to_update", "")
    new_value = fields.get("new_value")

    # Find existing employee
    parts = name.split()
    first = parts[0] if parts else ""
    last = parts[-1] if len(parts) > 1 else ""
    employees = client.list("/employee", params={
        "firstName": first, "lastName": last,
        "fields": "id,firstName,lastName,email"
    })
    if not employees:
        log.warning("Employee not found: %s", name)
        return

    employee_id = employees[0]["id"]
    client.put(f"/employee/{employee_id}", {field_to_update: new_value})
    log.info("Updated employee %s: %s = %s", employee_id, field_to_update, new_value)
