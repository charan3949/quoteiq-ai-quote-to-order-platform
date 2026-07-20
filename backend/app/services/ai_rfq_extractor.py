import json
import logging
from typing import Any

import httpx
from pydantic import BaseModel, ValidationError

from app.config import settings
from app.services.rfq_extractor import extract_rfq_lines as regex_extract_rfq_lines

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are an RFQ (request for quotation) extraction engine for a \
building-materials distributor. Extract every requested product line item from the \
customer's message.

Rules:
- Only extract information that is explicitly present in the text. Never invent a \
quantity, unit, part number, or requirement that isn't stated.
- If a field is not present for a line item, omit it or set it to null — do not guess.
- Set "confidence" to "high" only when quantity, unit, and description are all \
unambiguous. Use "medium" when something is inferred (e.g. unit of measure implied by \
context). Use "low" when the line item is unclear or ambiguous.
- Set "needs_review" to true whenever confidence is not "high", or whenever you are \
uncertain about any part of the line.
- Respond with ONLY valid JSON matching this exact shape, no prose, no markdown \
fences:
{"line_items": [{"description_raw": string, "quantity": number, "uom_raw": string or \
null, "customer_part_number": string or null, "requirements": string or null, \
"confidence": "high" | "medium" | "low", "needs_review": boolean}]}
"""


class AIExtractedLine(BaseModel):
    description_raw: str
    quantity: float
    uom_raw: str | None = None
    customer_part_number: str | None = None
    requirements: str | None = None
    confidence: str = "low"
    needs_review: bool = True


class AIExtractionResult(BaseModel):
    line_items: list[AIExtractedLine]


def _parse_ai_response(payload: dict[str, Any]) -> str:
    direct = payload.get("output_text")
    if isinstance(direct, str) and direct.strip():
        return direct.strip()

    parts: list[str] = []
    for item in payload.get("output", []):
        if not isinstance(item, dict):
            continue
        for content in item.get("content", []):
            if not isinstance(content, dict):
                continue
            text = content.get("text")
            if isinstance(text, str) and text.strip():
                parts.append(text.strip())
    return "\n".join(parts).strip()


def _strip_json_fences(text: str) -> str:
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.strip("`")
        if cleaned.lower().startswith("json"):
            cleaned = cleaned[4:]
    return cleaned.strip()


def _call_openai_extraction(rfq_text: str) -> AIExtractionResult:
    request_payload = {
        "model": settings.openai_model,
        "instructions": SYSTEM_PROMPT,
        "input": rfq_text,
        "temperature": 0,
        "max_output_tokens": 1500,
    }

    headers = {
        "Authorization": f"Bearer {settings.openai_api_key}",
        "Content-Type": "application/json",
    }

    with httpx.Client(timeout=30.0) as client:
        response = client.post(
            f"{settings.openai_base_url.rstrip('/')}/responses",
            headers=headers,
            json=request_payload,
        )
    response.raise_for_status()

    payload = response.json()
    raw_text = _parse_ai_response(payload)
    if not raw_text:
        raise RuntimeError("AI extraction returned an empty response")

    cleaned = _strip_json_fences(raw_text)
    parsed_json = json.loads(cleaned)
    return AIExtractionResult.model_validate(parsed_json)


def extract_rfq_lines_ai(rfq_text: str) -> list[dict]:
    """
    Attempts real LLM-based extraction. Falls back to the deterministic
    regex extractor (with extraction_method='regex_fallback') if:
      - no API key is configured
      - the AI call fails (network, HTTP error, bad JSON, schema mismatch)
    This guarantees the RFQ pipeline never hard-fails just because the
    AI provider is unavailable — it degrades to a known-working path
    and flags every line for human review instead.
    """
    if not settings.openai_api_key:
        logger.info("OPENAI_API_KEY not set; using regex RFQ extraction fallback")
        return [
            {**line, "extraction_method": "regex_fallback", "confidence": "low", "needs_review": True}
            for line in regex_extract_rfq_lines(rfq_text)
        ]

    try:
        result = _call_openai_extraction(rfq_text)
        return [
            {**line.model_dump(), "extraction_method": "ai"}
            for line in result.line_items
        ]
    except (httpx.HTTPError, json.JSONDecodeError, ValidationError, RuntimeError) as error:
        logger.warning(
            "AI RFQ extraction failed (%s); falling back to regex extraction",
            error,
        )
        return [
            {**line, "extraction_method": "regex_fallback", "confidence": "low", "needs_review": True}
            for line in regex_extract_rfq_lines(rfq_text)
        ]