"""Extract text from base64-encoded file attachments (PDFs, images)."""
import base64
import io
import logging
import tempfile

log = logging.getLogger(__name__)


def extract_text_from_files(files: list) -> str:
    """
    Given a list of file dicts (filename, content_base64, mime_type),
    return concatenated extracted text.
    """
    parts = []
    for f in files:
        filename = f.get("filename", "unknown")
        mime = f.get("mime_type", "")
        data = base64.b64decode(f["content_base64"])

        try:
            if mime == "application/pdf" or filename.lower().endswith(".pdf"):
                text = _extract_pdf(data)
            elif mime.startswith("image/"):
                text = _extract_image(data)
            else:
                log.warning("Unsupported file type: %s (%s)", filename, mime)
                continue

            if text:
                parts.append(f"[{filename}]\n{text}")
        except Exception as e:
            log.error("Failed to extract text from %s: %s", filename, e)

    return "\n\n".join(parts)


def _extract_pdf(data: bytes) -> str:
    import pdfplumber

    with pdfplumber.open(io.BytesIO(data)) as pdf:
        pages = []
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                pages.append(text)
    return "\n".join(pages)


def _extract_image(data: bytes) -> str:
    """Basic image text extraction. Returns empty string if pytesseract not available."""
    try:
        import pytesseract
        from PIL import Image

        img = Image.open(io.BytesIO(data))
        return pytesseract.image_to_string(img)
    except ImportError:
        log.warning("pytesseract not installed — skipping image OCR")
        return ""
