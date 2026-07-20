import io

from fastapi import UploadFile
from pypdf import PdfReader

MAX_UPLOAD_BYTES = 2 * 1024 * 1024  # 2 MB — plenty for an RFQ document
ALLOWED_EXTENSIONS = {".txt", ".pdf", ".csv"}


class RFQUploadError(ValueError):
    """Raised for any invalid/unsafe upload; caller maps this to HTTP 400."""


def _get_extension(filename: str) -> str:
    if "." not in filename:
        return ""

    return "." + filename.rsplit(".", 1)[-1].lower()


def _extract_pdf_text(raw_bytes: bytes) -> str:
    reader = PdfReader(io.BytesIO(raw_bytes))

    pages_text = []
    for page in reader.pages:
        pages_text.append(page.extract_text() or "")

    return "\n".join(pages_text).strip()


def _extract_plain_text(raw_bytes: bytes) -> str:
    try:
        return raw_bytes.decode("utf-8").strip()
    except UnicodeDecodeError as error:
        raise RFQUploadError(
            "File is not valid UTF-8 text. "
            "Please upload a plain .txt/.csv file or a .pdf."
        ) from error


async def extract_text_from_upload(upload: UploadFile) -> str:
    filename = upload.filename or ""
    extension = _get_extension(filename)

    if extension not in ALLOWED_EXTENSIONS:
        raise RFQUploadError(
            f"Unsupported file type '{extension or 'unknown'}'. "
            f"Allowed types: {', '.join(sorted(ALLOWED_EXTENSIONS))}"
        )

    raw_bytes = await upload.read()

    if len(raw_bytes) == 0:
        raise RFQUploadError("Uploaded file is empty.")

    if len(raw_bytes) > MAX_UPLOAD_BYTES:
        raise RFQUploadError(
            f"File is too large. Maximum size is "
            f"{MAX_UPLOAD_BYTES // (1024 * 1024)} MB."
        )

    if extension == ".pdf":
        text = _extract_pdf_text(raw_bytes)
    else:
        text = _extract_plain_text(raw_bytes)

    if not text:
        raise RFQUploadError(
            "No readable text could be extracted from this file. "
            "Scanned/image-only PDFs are not supported yet — "
            "please paste the RFQ text directly instead."
        )

    return text