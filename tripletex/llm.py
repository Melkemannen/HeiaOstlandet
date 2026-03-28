"""
LLM task interpreter using Ollama (qwen2.5:7b).

Two-step approach:
  1. Classify: identify the task type from a fixed list
  2. Extract: pull out field values as structured JSON
"""
import json
import logging
import re

import ollama

log = logging.getLogger(__name__)

MODEL = "qwen2.5:7b"

TASK_TYPES = [
    "create_employee",
    "create_customer",
    "create_product",
    "create_invoice",
    "register_payment",
    "create_credit_note",
    "create_travel_expense",
    "delete_travel_expense",
    "create_project",
    "create_department",
    "update_employee",
    "update_customer",
    "delete_entry",
    "register_hours",
    "unknown",
]

CLASSIFY_PROMPT = """You are classifying an accounting task. Given the task description below,
return ONLY the task type as a single word from this list:

{task_list}

Task: {prompt}

Reply with only the task type, nothing else."""

EXTRACT_PROMPT = """You are extracting structured data from an accounting task description.
Return a JSON object with the relevant fields. Use null for missing values.

Task type: {task_type}
Task: {prompt}

For reference, common fields per task type:
- create_employee: first_name, last_name, email, phone, role (e.g. "ADMINISTRATOR", "USER")
- create_customer: name, email, phone, organization_number
- create_product: name, price, product_number
- create_invoice: customer_name, invoice_date, due_date
- register_payment: invoice_id, customer_name, amount, payment_date
- create_credit_note: invoice_id, customer_name, date
- create_travel_expense: employee_name, description, date, amount
- delete_travel_expense: description (to identify which one)
- create_project: name, customer_name, start_date
- create_department: name
- update_employee: employee_name, field_to_update, new_value
- update_customer: customer_name, field_to_update, new_value
- register_hours: employee_email, project_name, activity_name, date, hours
- delete_entry: entity_type (invoice/voucher/order/travel_expense), entity_id, customer_name

Return only the JSON object, no explanation."""


def _call(prompt: str) -> str:
    response = ollama.chat(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        options={"temperature": 0},
    )
    return response["message"]["content"].strip()


def _extract_json(text: str) -> dict:
    """Extract JSON from LLM output, tolerating markdown code fences."""
    # Strip markdown code fences if present
    text = re.sub(r"```(?:json)?", "", text).strip().rstrip("`").strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        log.warning("Could not parse LLM JSON output: %s", text)
        return {}


def classify_and_extract(prompt: str) -> tuple[str, dict]:
    """
    Returns (task_type, fields_dict).
    task_type is one of TASK_TYPES.
    fields_dict contains extracted field values (strings/None).
    """
    task_list = "\n".join(f"- {t}" for t in TASK_TYPES)
    classify_input = CLASSIFY_PROMPT.format(task_list=task_list, prompt=prompt)
    raw_type = _call(classify_input).strip().lower().replace("-", "_")

    # Normalize to known type
    task_type = raw_type if raw_type in TASK_TYPES else "unknown"
    log.info("Classified as: %s (raw: %s)", task_type, raw_type)

    extract_input = EXTRACT_PROMPT.format(task_type=task_type, prompt=prompt)
    raw_fields = _call(extract_input)
    fields = _extract_json(raw_fields)

    # Unwrap if model returned {"create_employee": {...}} instead of flat dict
    if len(fields) == 1:
        only_key = next(iter(fields))
        if isinstance(fields[only_key], dict):
            fields = fields[only_key]

    log.info("Extracted fields: %s", fields)

    return task_type, fields
