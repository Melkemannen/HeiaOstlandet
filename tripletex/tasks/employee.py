import logging

from tripletex_client import TripletexClient

log = logging.getLogger(__name__)

# Map role keywords to Tripletex userType values
ADMIN_KEYWORDS = {"administrator", "admin", "kontoadministrator"}


def handle_create_employee(client: TripletexClient, fields: dict) -> None:
    first_name = fields.get("first_name") or ""
    last_name = fields.get("last_name") or ""
    email = fields.get("email")
    role_raw = (fields.get("role") or "").lower()

    # Administrator = EXTENDED userType, otherwise STANDARD
    user_type = "EXTENDED" if role_raw in ADMIN_KEYWORDS else "STANDARD"

    department_id = client.get_first_department_id()
    log.info("Using department id=%s", department_id)

    employee = client.create_employee(
        first_name=first_name,
        last_name=last_name,
        email=email,
        department_id=department_id,
        user_type=user_type,
    )
    employee_id = employee["id"]
    log.info("Created employee id=%s userType=%s", employee_id, user_type)


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
