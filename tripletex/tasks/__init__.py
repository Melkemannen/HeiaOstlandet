"""Dispatcher: routes task_type to the appropriate handler."""
import logging

from tripletex_client import TripletexClient

from tasks.customer import handle_create_customer
from tasks.department import handle_create_department
from tasks.employee import handle_create_employee, handle_update_employee
from tasks.invoice import handle_create_invoice
from tasks.product import handle_create_product
from tasks.project import handle_create_project
from tasks.travel_expense import handle_create_travel_expense, handle_delete_travel_expense

log = logging.getLogger(__name__)

HANDLERS = {
    "create_employee": handle_create_employee,
    "update_employee": handle_update_employee,
    "create_customer": handle_create_customer,
    "create_product": handle_create_product,
    "create_invoice": handle_create_invoice,
    "create_travel_expense": handle_create_travel_expense,
    "delete_travel_expense": handle_delete_travel_expense,
    "create_project": handle_create_project,
    "create_department": handle_create_department,
}


def dispatch(task_type: str, fields: dict, base_url: str, session_token: str) -> None:
    client = TripletexClient(base_url, session_token)
    handler = HANDLERS.get(task_type)
    if handler is None:
        log.warning("No handler for task type: %s — skipping", task_type)
        return
    handler(client, fields)
