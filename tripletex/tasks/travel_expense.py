import logging
from datetime import date

from tripletex_client import TripletexClient

log = logging.getLogger(__name__)


def handle_create_travel_expense(client: TripletexClient, fields: dict) -> None:
    purpose = fields.get("description") or fields.get("purpose") or ""
    start_date = fields.get("date") or fields.get("start_date") or str(date.today())
    end_date = fields.get("end_date") or start_date
    employee_name = fields.get("employee_name") or ""

    # Find employee (required field)
    employee_id = _find_employee_id(client, employee_name)

    payload = {
        "startDate": start_date,
        "endDate": end_date,
        "isCompleted": False,
    }
    if purpose:
        payload["purpose"] = purpose
    if employee_id:
        payload["employee"] = {"id": employee_id}

    result = client.post("/travelExpense", payload)
    log.info("Created travel expense id=%s", result.get("value", {}).get("id"))


def handle_delete_travel_expense(client: TripletexClient, fields: dict) -> None:
    description = fields.get("description", "").lower()

    expenses = client.get_travel_expenses()
    if not expenses:
        log.warning("No travel expenses found to delete")
        return

    # Match by purpose/description if given, otherwise delete the first one
    target = None
    if description:
        for exp in expenses:
            exp_text = (exp.get("purpose") or exp.get("description") or "").lower()
            if description in exp_text:
                target = exp
                break

    if target is None:
        target = expenses[0]

    client.delete_travel_expense(target["id"])
    log.info("Deleted travel expense id=%s", target["id"])


def _find_employee_id(client: TripletexClient, name: str) -> int | None:
    if not name:
        # Fall back to first employee
        employees = client.list("/employee", params={"fields": "id", "count": 1})
        return employees[0]["id"] if employees else None
    parts = name.split()
    first = parts[0] if parts else ""
    last = parts[-1] if len(parts) > 1 else ""
    employees = client.list("/employee", params={
        "firstName": first, "lastName": last, "fields": "id,firstName,lastName"
    })
    return employees[0]["id"] if employees else None
