"""Dispatcher: routes task_type to the appropriate handler."""
import logging

from tripletex_client import TripletexClient

from tasks.customer import handle_create_customer, handle_update_customer
from tasks.delete_entry import handle_delete_entry
from tasks.department import handle_create_department
from tasks.employee import handle_create_employee, handle_update_employee
from tasks.hours import handle_register_hours
from tasks.invoice import handle_create_invoice
from tasks.payment import handle_create_credit_note, handle_register_payment
from tasks.product import handle_create_product
from tasks.project import handle_create_project
from tasks.travel_expense import handle_create_travel_expense, handle_delete_travel_expense

log = logging.getLogger(__name__)

HANDLERS = {
    "create_employee": handle_create_employee,
    "update_employee": handle_update_employee,
    "create_customer": handle_create_customer,
    "update_customer": handle_update_customer,
    "create_product": handle_create_product,
    "create_invoice": handle_create_invoice,
    "register_payment": handle_register_payment,
    "create_credit_note": handle_create_credit_note,
    "create_travel_expense": handle_create_travel_expense,
    "delete_travel_expense": handle_delete_travel_expense,
    "create_project": handle_create_project,
    "create_department": handle_create_department,
    "register_hours": handle_register_hours,
    "delete_entry": handle_delete_entry,
}


def dispatch(task_type: str, fields: dict, base_url: str, session_token: str) -> None:
    client = TripletexClient(base_url, session_token)
    handler = HANDLERS.get(task_type)
    if handler is None:
        log.warning("No handler for task type: %s — skipping", task_type)
        return
    handler(client, fields)
