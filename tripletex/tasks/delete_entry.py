import logging

from tripletex_client import TripletexClient

log = logging.getLogger(__name__)


def handle_delete_entry(client: TripletexClient, fields: dict) -> None:
    """
    Generic delete/reverse handler. Tries to identify what to delete based on fields.
    Supports: invoice, voucher, travel expense, order.
    """
    entity_type = (fields.get("entity_type") or "").lower()
    entity_id = fields.get("entity_id")
    customer_name = fields.get("customer_name") or ""

    if entity_type in ("invoice", "faktura"):
        _delete_invoice(client, entity_id, customer_name)
    elif entity_type in ("voucher", "bilag"):
        _delete_voucher(client, entity_id)
    elif entity_type in ("travel_expense", "reise", "reiseregning"):
        if entity_id:
            client.delete(f"/travelExpense/{entity_id}")
        else:
            expenses = client.get_travel_expenses()
            if expenses:
                client.delete_travel_expense(expenses[0]["id"])
    elif entity_type in ("order", "ordre"):
        if entity_id:
            client.delete(f"/order/{entity_id}")
    else:
        log.warning("delete_entry: unknown entity_type '%s', trying invoice", entity_type)
        _delete_invoice(client, entity_id, customer_name)


def _delete_invoice(client: TripletexClient, invoice_id, customer_name: str) -> None:
    if not invoice_id and customer_name:
        customer = client.find_customer(customer_name)
        if customer:
            invoices = client.list("/invoice", params={
                "customerId": customer["id"], "fields": "id", "count": 1
            })
            if invoices:
                invoice_id = invoices[0]["id"]

    if invoice_id:
        client.delete(f"/invoice/{invoice_id}")
        log.info("Deleted invoice id=%s", invoice_id)
    else:
        log.warning("No invoice found to delete")


def _delete_voucher(client: TripletexClient, voucher_id) -> None:
    if voucher_id:
        client.delete(f"/ledger/voucher/{voucher_id}")
        log.info("Deleted voucher id=%s", voucher_id)
    else:
        log.warning("No voucher id provided")
