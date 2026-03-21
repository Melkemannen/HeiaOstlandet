import logging
from datetime import date

from tripletex_client import TripletexClient

log = logging.getLogger(__name__)


def handle_create_travel_expense(client: TripletexClient, fields: dict) -> None:
    description = fields.get("description") or ""
    expense_date = fields.get("date") or str(date.today())
    amount = fields.get("amount")

    payload = {
        "description": description,
        "date": expense_date,
    }
    if amount is not None:
        try:
            payload["totalAmountCurrency"] = float(amount)
        except (TypeError, ValueError):
            pass

    result = client.post("/travelExpense", payload)
    log.info("Created travel expense id=%s", result.get("value", {}).get("id"))


def handle_delete_travel_expense(client: TripletexClient, fields: dict) -> None:
    description = fields.get("description", "").lower()

    expenses = client.get_travel_expenses()
    if not expenses:
        log.warning("No travel expenses found to delete")
        return

    # Match by description if given, otherwise delete the first one
    target = None
    if description:
        for exp in expenses:
            if description in (exp.get("description") or "").lower():
                target = exp
                break

    if target is None:
        target = expenses[0]

    client.delete_travel_expense(target["id"])
    log.info("Deleted travel expense id=%s", target["id"])
