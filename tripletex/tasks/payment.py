import logging
from datetime import date

from tripletex_client import TripletexClient

log = logging.getLogger(__name__)


def handle_register_payment(client: TripletexClient, fields: dict) -> None:
    invoice_id = fields.get("invoice_id")
    amount = fields.get("amount")
    payment_date = fields.get("payment_date") or str(date.today())
    customer_name = fields.get("customer_name")

    # Find invoice if not given directly
    if not invoice_id and customer_name:
        customer = client.find_customer(customer_name)
        if customer:
            invoices = client.list("/invoice", params={
                "customerId": customer["id"],
                "fields": "id",
                "count": 5,
            })
            if invoices:
                invoice_id = invoices[0]["id"]
                log.info("Found invoice id=%s", invoice_id)

    if not invoice_id:
        log.warning("No invoice found to register payment on")
        return

    # Get payment types and use first available
    payment_types = client.list("/ledger/paymentType", params={"fields": "id,name", "count": 5})
    payment_type_id = payment_types[0]["id"] if payment_types else None

    payload = {"paymentDate": payment_date}
    if amount is not None:
        try:
            payload["paidAmount"] = float(amount)
        except (TypeError, ValueError):
            pass
    if payment_type_id:
        payload["paymentTypeId"] = payment_type_id

    result = client.post(f"/invoice/{invoice_id}/:payment", payload)
    log.info("Registered payment on invoice %s: %s", invoice_id, result)


def handle_create_credit_note(client: TripletexClient, fields: dict) -> None:
    invoice_id = fields.get("invoice_id")
    customer_name = fields.get("customer_name")
    credit_date = fields.get("date") or str(date.today())

    # Find invoice if not given directly
    if not invoice_id and customer_name:
        customer = client.find_customer(customer_name)
        if customer:
            invoices = client.list("/invoice", params={
                "customerId": customer["id"],
                "fields": "id",
                "count": 5,
            })
            if invoices:
                invoice_id = invoices[0]["id"]
                log.info("Found invoice id=%s for credit note", invoice_id)

    if not invoice_id:
        log.warning("No invoice found to create credit note for")
        return

    result = client.post(f"/invoice/{invoice_id}/:createCreditNote", {"date": credit_date})
    log.info("Created credit note: %s", result)
