import base64
import logging

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from file_handler import extract_text_from_files
from llm import classify_and_extract
from tasks import dispatch

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)

app = FastAPI()


@app.post("/solve")
async def solve(request: Request):
    body = await request.json()

    prompt: str = body["prompt"]
    files: list = body.get("files", [])
    creds: dict = body["tripletex_credentials"]

    base_url: str = creds["base_url"]
    session_token: str = creds["session_token"]

    log.info("Received task: %s", prompt[:120])

    # Extract text from any attached files and append to prompt context
    file_context = extract_text_from_files(files)
    full_context = prompt
    if file_context:
        full_context = f"{prompt}\n\n[Attached files]\n{file_context}"

    # LLM: classify task type + extract field values
    task_type, fields = classify_and_extract(full_context)
    log.info("Task type: %s | Fields: %s", task_type, fields)

    # Execute the appropriate task handler
    dispatch(task_type, fields, base_url, session_token)

    return JSONResponse({"status": "completed"})
