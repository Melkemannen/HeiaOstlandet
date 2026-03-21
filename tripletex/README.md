# Tripletex AI Accounting Agent

AI agent for the NM i AI 2026 Tripletex challenge. Receives natural-language accounting tasks, executes them via the Tripletex v2 REST API, and returns `{"status": "completed"}`.

## Setup

```bash
cd tripletex/
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

You also need [Ollama](https://ollama.com) installed and running with `qwen2.5:7b`:

```bash
ollama serve          # in a separate terminal
ollama pull qwen2.5:7b
```

## How to run

**Terminal 1 — Ollama:**
```bash
ollama serve
```

**Terminal 2 — the agent server:**
```bash
cd tripletex/
source .venv/bin/activate
uvicorn server:app --host 0.0.0.0 --port 8000
```

**Terminal 3 — ngrok HTTPS tunnel:**
```bash
ngrok http 8000
```

Copy the HTTPS URL from ngrok (e.g. `https://abc123.ngrok-free.app`) and submit it as:
```
https://abc123.ngrok-free.app/solve
```
at `https://app.ainm.no/submit/tripletex`.

> **Note:** ngrok generates a new URL each restart. Update the endpoint on the platform each time.

## Sandbox credentials

Available on the platform under "Get Sandbox Account". Set as environment variables for local testing:

```bash
export TRIPLETEX_BASE_URL=https://kkpqfuj-amager.tripletex.dev/v2
export TRIPLETEX_TOKEN=your-token-here
```

## Testing

**Test a single task handler directly against the sandbox (no LLM, no server needed):**
```bash
python test_sandbox.py create_employee
python test_sandbox.py create_customer
python test_sandbox.py create_product
python test_sandbox.py create_invoice
python test_sandbox.py create_department
python test_sandbox.py create_project
```

**Test the LLM classification + field extraction:**
```bash
python test_llm.py
```

**Test the full pipeline against the local server:**
```bash
# Make sure server is running first
python test_server.py
```

## Architecture

```
server.py               # FastAPI /solve endpoint — entry point
llm.py                  # Ollama qwen2.5:7b: classify task + extract fields (2 LLM calls)
file_handler.py         # Decode base64 PDFs/images, extract text with pdfplumber
tripletex_client.py     # Thin Tripletex REST API wrapper (auth, common endpoints)
tasks/
  __init__.py           # Dispatcher: task_type string → handler function
  employee.py           # create_employee, update_employee
  customer.py           # create_customer
  product.py            # create_product
  invoice.py            # create_invoice
  payment.py            # register_payment, create_credit_note
  travel_expense.py     # create_travel_expense, delete_travel_expense
  project.py            # create_project
  department.py         # create_department
  hours.py              # register_hours (timesheet entries)
  delete_entry.py       # delete_entry (invoices, vouchers, orders)
```

**Flow per request:**
1. Decode any attached files → extract text
2. LLM call 1: classify task type (e.g. `create_employee`)
3. LLM call 2: extract field values as JSON
4. Dispatcher calls the matching handler
5. Handler makes Tripletex API calls
6. Return `{"status": "completed"}`

## Scoring notes

- **GET calls are free** — don't count toward efficiency penalty
- **Every 4xx error** reduces the efficiency bonus — validate before posting
- **Best score per task is kept** — bad runs don't hurt you
- Tier 1 tasks (×1): employee, customer, product, invoice
- Tier 2 tasks (×2): payment, credit note, travel expense, project
- Tier 3 tasks (×3): complex multi-step workflows

## Known issues / TODO

- `register_payment`: invoice query by `customerId` may still return 422 — needs verification
- `create_travel_expense`: `purpose` field assumed — not verified against API
- `register_hours`: untested against real competition sandbox
- LLM classification is not guaranteed — a 7B model may occasionally misclassify; consider adding fuzzy matching as fallback
- Efficiency: no optimization done yet — focus was on correctness first
