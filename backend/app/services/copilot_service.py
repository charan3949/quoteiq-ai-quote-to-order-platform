import json
import logging
from typing import Any

import httpx

from app.config import settings
from app.services.enterprise_service import quote_intelligence
from app.services.quote_store import get_quote

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are QuoteIQ Copilot, an enterprise sales-operations assistant for a building-materials distributor.
Use only the supplied QuoteIQ context. Never invent customer, price, inventory, margin, order, or policy facts.
When data is missing, say exactly what is missing. Keep answers concise, operational, and auditable.
For pricing suggestions, explain the tradeoff and show calculations when the context supports them.
You may recommend actions, but you cannot approve quotes, change prices, send email, or create ERP orders.
Use short sections and bullets. End with a clear recommended next step when useful."""


def _quote_context(quote_id: str | None) -> dict[str, Any] | None:
    if not quote_id:
        return None
    quote = get_quote(quote_id)
    if not quote:
        return None
    intelligence = quote_intelligence(quote_id)
    return {
        "quote": quote,
        "intelligence": intelligence,
    }


def _extract_text(payload: dict[str, Any]) -> str:
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


def ask_copilot(
    *,
    message: str,
    quote_id: str | None,
    history: list[dict[str, str]],
    actor_email: str,
    actor_role: str,
) -> dict[str, Any]:
    if not settings.openai_api_key:
        raise RuntimeError(
            "OPENAI_API_KEY is not configured on the backend service."
        )

    context = _quote_context(quote_id)
    if quote_id and context is None:
        raise ValueError("Quote not found")

    compact_history = [
        {
            "role": item.get("role", "user"),
            "content": item.get("content", "")[:2000],
        }
        for item in history[-10:]
        if item.get("role") in {"user", "assistant"}
        and item.get("content")
    ]

    user_payload = {
        "requesting_user": {
            "email": actor_email,
            "role": actor_role,
        },
        "selected_quote_id": quote_id,
        "quoteiq_context": context,
        "conversation_history": compact_history,
        "question": message,
    }

    request_payload = {
        "model": settings.openai_model,
        "instructions": SYSTEM_PROMPT,
        "input": json.dumps(user_payload, default=str),
        "temperature": 0.2,
        "max_output_tokens": 700,
    }

    headers = {
        "Authorization": f"Bearer {settings.openai_api_key}",
        "Content-Type": "application/json",
    }

    try:
        with httpx.Client(timeout=45.0) as client:
            response = client.post(
                f"{settings.openai_base_url.rstrip('/')}/responses",
                headers=headers,
                json=request_payload,
            )
        response.raise_for_status()
    except httpx.HTTPStatusError as exc:
        logger.exception("OpenAI API returned an error")
        detail = exc.response.text[:500]
        raise RuntimeError(f"LLM provider error: {detail}") from exc
    except httpx.HTTPError as exc:
        logger.exception("OpenAI API request failed")
        raise RuntimeError("Unable to reach the LLM provider") from exc

    payload = response.json()
    answer = _extract_text(payload)
    if not answer:
        raise RuntimeError("The LLM provider returned an empty response")

    usage = payload.get("usage") or {}
    return {
        "answer": answer,
        "quote_id": quote_id,
        "model": payload.get("model", settings.openai_model),
        "usage": {
            "input_tokens": usage.get("input_tokens"),
            "output_tokens": usage.get("output_tokens"),
            "total_tokens": usage.get("total_tokens"),
        },
        "grounded": context is not None,
        "disclaimer": "Copilot provides decision support; final commercial decisions remain with authorized users.",
    }
