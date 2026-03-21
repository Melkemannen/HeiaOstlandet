# Tripletex AI Accounting Agent — Goals & Plan

## Context
NM i AI 2026 competition (ends March 22). Build an AI agent that receives natural-language
accounting tasks (7 languages), executes them via the Tripletex v2 REST API, and scores
on correctness + efficiency.

**Key decisions:**
- LLM: Ollama with `qwen2.5:7b` (local, free, strong multilingual)
- Hosting: FastAPI locally + ngrok HTTPS tunnel
- Approach: LLM classifies task + extracts fields → deterministic Python executes API calls

---

## Main Goal

> **Build an AI agent that receives natural-language accounting tasks and executes them
> correctly and efficiently via the Tripletex API — maximizing score across all 30 task types.**

---

## Subgoals (in build order)

### 1. Server infrastructure
- FastAPI `/solve` endpoint accepting POST with `prompt`, `files`, `tripletex_credentials`
- Exposes via ngrok for HTTPS
- Returns `{"status": "completed"}` within 5 minutes
- Files: `server.py`, `requirements.txt`, `run.sh`

### 2. Tripletex API client
- Thin Python wrapper around Tripletex v2 REST API
- Basic Auth: username `0`, password = session_token
- Covers: `/employee`, `/customer`, `/product`, `/invoice`, `/order`,
  `/travelExpense`, `/project`, `/department`, `/ledger/voucher`
- Returns Python dicts, raises clearly on errors
- File: `tripletex_client.py`

### 3. LLM task interpreter (Ollama qwen2.5:7b)
- **Two-step approach** suited for a 7B local model:
  1. **Classify**: Ask LLM to identify the task type from a fixed list
  2. **Extract**: Ask LLM to extract field values (name, email, role, amount, etc.) as structured JSON
- Use clear JSON output schemas to keep the small model on track
- Handle all 7 languages (qwen2.5 is designed for multilingual)
- File: `llm.py`

### 4. Task handlers (one per task type, Tier 1 first)
- Deterministic Python: maps (task_type + extracted_fields) → sequence of Tripletex API calls
- Start with Tier 1:
  - `employee.py` — create employee, set role
  - `customer.py` — create customer
  - `product.py` — create product
  - `invoice.py` — create basic invoice
- Add Tier 2/3 later: payments, credit notes, travel expenses, projects, departments
- Folder: `tasks/`

### 5. File attachment handling
- Decode base64 PDFs/images from request
- Extract text with `pdfplumber` (PDFs) or pytesseract (images)
- Feed extracted text into LLM context alongside the prompt
- File: `file_handler.py`

### 6. Sandbox testing
- Use team sandbox at `https://kkpqfuj-amager.tripletex.dev/v2` to manually test each handler
- Verify field-by-field before submitting to competition

### 7. Efficiency optimization
- Parse prompt fully before any API calls
- Use IDs from POST responses — don't re-fetch what you just created
- Validate required fields before sending (avoid 4xx errors)
- Log all write calls to track efficiency

---

## File Structure
```
tripletex/
  server.py             # FastAPI /solve endpoint
  tripletex_client.py   # Tripletex REST API wrapper
  llm.py                # Ollama qwen2.5:7b integration
  file_handler.py       # PDF/image text extraction
  tasks/
    __init__.py         # Dispatcher: task_type → handler
    employee.py
    customer.py
    product.py
    invoice.py
  requirements.txt
  run.sh                # uvicorn + ngrok startup
  lessons.md            # Competition lessons (already exists)
```

---

## Implementation Order
1. `requirements.txt` + `run.sh`
2. `tripletex_client.py` (test against sandbox)
3. `llm.py` (test qwen2.5:7b locally)
4. `tasks/employee.py` + `tasks/customer.py` (Tier 1 baseline)
5. `server.py` + `tasks/__init__.py` (wire it all together)
6. Test end-to-end via ngrok + sandbox
7. Submit to competition, iterate on remaining task types

---

## Verification
- Manually POST to `/solve` with sample prompts to test locally
- Check results in sandbox Tripletex UI (`https://kkpqfuj-amager.tripletex.dev`)
- Compare fields against expected values before submitting to competition
