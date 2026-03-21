"""Thin wrapper around the Tripletex v2 REST API."""
import logging

import requests

log = logging.getLogger(__name__)


class TripletexClient:
    def __init__(self, base_url: str, session_token: str):
        self.base_url = base_url.rstrip("/")
        self.auth = ("0", session_token)

    def _url(self, path: str) -> str:
        return f"{self.base_url}/{path.lstrip('/')}"

    def get(self, path: str, params: dict = None) -> dict:
        resp = requests.get(self._url(path), auth=self.auth, params=params)
        resp.raise_for_status()
        return resp.json()

    def post(self, path: str, json: dict) -> dict:
        log.info("POST %s %s", path, json)
        resp = requests.post(self._url(path), auth=self.auth, json=json)
        if not resp.ok:
            log.error("POST %s failed %s: %s", path, resp.status_code, resp.text)
        resp.raise_for_status()
        return resp.json()

    def put(self, path: str, json: dict) -> dict:
        log.info("PUT %s %s", path, json)
        resp = requests.put(self._url(path), auth=self.auth, json=json)
        if not resp.ok:
            log.error("PUT %s failed %s: %s", path, resp.status_code, resp.text)
        resp.raise_for_status()
        return resp.json()

    def delete(self, path: str) -> None:
        log.info("DELETE %s", path)
        resp = requests.delete(self._url(path), auth=self.auth)
        if not resp.ok:
            log.error("DELETE %s failed %s: %s", path, resp.status_code, resp.text)
        resp.raise_for_status()

    # --- Convenience methods ---

    def list(self, path: str, params: dict = None) -> list:
        """Return the 'values' list from a list endpoint."""
        data = self.get(path, params=params)
        return data.get("values", [])

    def get_first_department_id(self) -> int | None:
        departments = self.list("/department", params={"fields": "id,name", "count": 1})
        return departments[0]["id"] if departments else None

    def find_department_id(self, name: str) -> int | None:
        if not name:
            return self.get_first_department_id()
        departments = self.list("/department", params={"name": name, "fields": "id,name", "count": 5})
        if departments:
            return departments[0]["id"]
        # Fallback: search case-insensitively through all departments
        all_depts = self.list("/department", params={"fields": "id,name", "count": 100})
        for d in all_depts:
            if name.lower() in (d.get("name") or "").lower():
                return d["id"]
        return self.get_first_department_id()

    def create_employee(self, first_name: str, last_name: str, email: str = None,
                        employee_number: str = None, department_id: int = None,
                        user_type: str = "STANDARD", date_of_birth: str = None,
                        national_identity_number: str = None, phone_number: str = None) -> dict:
        payload = {"firstName": first_name, "lastName": last_name, "userType": user_type}
        if email:
            payload["email"] = email
        if employee_number:
            payload["employeeNumber"] = employee_number
        if department_id:
            payload["department"] = {"id": department_id}
        if date_of_birth:
            payload["dateOfBirth"] = date_of_birth
        if national_identity_number:
            payload["nationalIdentityNumber"] = national_identity_number
        if phone_number:
            payload["phoneNumber"] = phone_number
        return self.post("/employee", payload)["value"]

    def create_customer(self, name: str, email: str = None,
                        phone_number: str = None, organization_number: str = None) -> dict:
        payload = {"name": name, "isCustomer": True}
        if email:
            payload["email"] = email
        if phone_number:
            payload["phoneNumber"] = phone_number
        if organization_number:
            payload["organizationNumber"] = organization_number
        return self.post("/customer", payload)["value"]

    def create_product(self, name: str, price: float = None,
                       product_number: str = None) -> dict:
        payload = {"name": name}
        if price is not None:
            payload["costExcludingVatCurrency"] = price
        if product_number:
            payload["number"] = product_number
        return self.post("/product", payload)["value"]

    def find_customer(self, name: str) -> dict | None:
        results = self.list("/customer", params={"name": name, "fields": "id,name,email", "count": 5})
        return results[0] if results else None

    def create_order(self, customer_id: int, order_date: str, delivery_date: str = None) -> dict:
        payload = {
            "customer": {"id": customer_id},
            "orderDate": order_date,
            "deliveryDate": delivery_date or order_date,
        }
        return self.post("/order", payload)["value"]

    def create_invoice(self, customer_id: int, order_id: int,
                       invoice_date: str, due_date: str) -> dict:
        payload = {
            "invoiceDate": invoice_date,
            "invoiceDueDate": due_date,
            "customer": {"id": customer_id},
            "orders": [{"id": order_id}],
        }
        return self.post("/invoice", payload)["value"]

    def get_travel_expenses(self) -> list:
        return self.list("/travelExpense", params={"fields": "id,description,employee"})

    def delete_travel_expense(self, expense_id: int) -> None:
        self.delete(f"/travelExpense/{expense_id}")

    def create_project(self, name: str, customer_id: int, start_date: str) -> dict:
        payload = {
            "name": name,
            "startDate": start_date,
        }
        if customer_id is not None:
            payload["customer"] = {"id": customer_id}
        return self.post("/project", payload)["value"]

    def create_department(self, name: str) -> dict:
        return self.post("/department", {"name": name})["value"]
