import logging
import re

from tripletex_client import TripletexClient

log = logging.getLogger(__name__)

ADMIN_KEYWORDS = {"administrator", "admin", "kontoadministrator"}

# Map LLM snake_case field names to Tripletex API camelCase field names.
# Both 'phone'/'phone_number' and 'national_id'/'national_identity_number' are kept
# since the LLM may output either variant.
_EMPLOYEE_FIELD_MAP = {
    "first_name": "firstName",
    "last_name": "lastName",
    "email": "email",
    "phone": "phoneNumber",
    "phone_number": "phoneNumber",
    "date_of_birth": "dateOfBirth",
    "national_id": "nationalIdentityNumber",
    "national_identity_number": "nationalIdentityNumber",
    "employee_number": "employeeNumber",
    "user_type": "userType",
    "role": "userType",
}


def handle_create_employee(client: TripletexClient, fields: dict) -> None:
    first_name = fields.get("first_name") or ""
    last_name = fields.get("last_name") or ""
    email = fields.get("email")
    role_raw = (fields.get("role") or "").lower()
    department_name = fields.get("department") or ""
    date_of_birth = _parse_date(fields.get("date_of_birth"))
    national_id = fields.get("national_id")
    phone = fields.get("phone")

    user_type = "EXTENDED" if role_raw in ADMIN_KEYWORDS else "STANDARD"
    department_id = client.find_department_id(department_name)
    log.info("Using department id=%s (%s)", department_id, department_name)

    employee = client.create_employee(
        first_name=first_name,
        last_name=last_name,
        email=email,
        department_id=department_id,
        user_type=user_type,
        date_of_birth=date_of_birth,
        national_identity_number=national_id,
        phone_number=phone,
    )
    employee_id = employee["id"]
    log.info("Created employee id=%s userType=%s", employee_id, user_type)

    # Create employment record if details provided
    start_date = _parse_date(fields.get("start_date"))
    salary = fields.get("salary")
    employment_percentage = fields.get("employment_percentage")
    occupation_code = fields.get("occupation_code")

    if start_date or salary or employment_percentage:
        _create_employment(client, employee_id, start_date, salary, employment_percentage, occupation_code)


def _create_employment(client, employee_id, start_date, salary, percentage, occupation_code):
    payload = {"employee": {"id": employee_id}}
    if start_date:
        payload["startDate"] = start_date
    if percentage is not None:
        try:
            payload["percentage"] = float(percentage)
        except (TypeError, ValueError):
            pass
    if occupation_code:
        payload["occupationCode"] = {"code": str(occupation_code)}
    try:
        result = client.post(f"/employee/{employee_id}/employment", payload)
        employment_id = result.get("value", {}).get("id")
        log.info("Created employment id=%s", employment_id)

        # Set salary if provided
        if salary and employment_id:
            try:
                salary_payload = {
                    "employment": {"id": employment_id},
                    "amount": float(salary),
                    "salaryType": {"id": 1},  # Monthly salary type
                }
                client.post(f"/employee/{employee_id}/employment/{employment_id}/employmentDetails", salary_payload)
                log.info("Set salary %s", salary)
            except Exception as e:
                log.error("Failed to set salary: %s", e)
    except Exception as e:
        log.error("Failed to create employment: %s", e)


def _parse_date(value: str | None) -> str | None:
    """Normalize dates like '22.04.2026' or '2026-04-22' to 'YYYY-MM-DD'."""
    if not value:
        return None
    value = str(value).strip()
    # Already ISO format
    if re.match(r"\d{4}-\d{2}-\d{2}", value):
        return value[:10]
    # DD.MM.YYYY
    m = re.match(r"(\d{1,2})\.(\d{1,2})\.(\d{4})", value)
    if m:
        return f"{m.group(3)}-{m.group(2).zfill(2)}-{m.group(1).zfill(2)}"
    return value


def handle_update_employee(client: TripletexClient, fields: dict) -> None:
    name = fields.get("employee_name", "")
    field_to_update = fields.get("field_to_update", "")
    new_value = fields.get("new_value")

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
    api_field = _EMPLOYEE_FIELD_MAP.get(field_to_update, field_to_update)
    client.put(f"/employee/{employee_id}", {api_field: new_value})
    log.info("Updated employee %s: %s = %s", employee_id, api_field, new_value)
