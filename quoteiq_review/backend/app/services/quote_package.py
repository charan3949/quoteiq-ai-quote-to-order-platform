from datetime import datetime, timezone
from uuid import uuid4


def _calculate_quote_confidence(
    matched_lines: list[dict],
    risk_count: int
) -> float:
    score = 100.0

    for line in matched_lines:
        confidence = line.get("match_confidence", "low")

        if confidence == "medium":
            score -= 10

        if confidence == "low":
            score -= 25

    score -= risk_count * 15

    return round(max(0.0, min(score, 100.0)), 2)


def _build_pricing_explanation(priced_line: dict) -> str:
    rule = priced_line.get("pricing_rule_applied", "list_price")
    list_price = priced_line.get("list_price", 0)
    unit_price = priced_line.get("unit_price", 0)
    margin_pct = priced_line.get("margin_pct", 0)

    if rule.startswith("fixed_price"):
        pricing_text = (
            f"Customer-specific fixed pricing changed the list price "
            f"from ${list_price:.2f} to ${unit_price:.2f}."
        )

    elif rule.startswith("discount_pct"):
        pricing_text = (
            f"A customer price-class discount changed the list price "
            f"from ${list_price:.2f} to ${unit_price:.2f}."
        )

    else:
        pricing_text = (
            f"No special pricing rule was applied. "
            f"The list price of ${list_price:.2f} was used."
        )

    return (
        f"{pricing_text} "
        f"The resulting estimated gross margin is {margin_pct:.2f}%."
    )


def _build_line_explanations(
    matched_lines: list[dict],
    priced_lines: list[dict]
) -> list[dict]:
    explanations = []

    for index, priced_line in enumerate(priced_lines):
        matched_line = matched_lines[index]

        explanations.append({
            "line_number": index + 1,
            "customer_description": matched_line["description_raw"],
            "selected_sku": priced_line["sku"],
            "selected_product": priced_line["product_name"],
            "match_score": matched_line["match_score"],
            "match_confidence": matched_line["match_confidence"],
            "pricing_rule_applied": priced_line["pricing_rule_applied"],
            "pricing_explanation": _build_pricing_explanation(priced_line),
            "requires_review": priced_line["risk_flag"],
            "review_reason": priced_line["risk_reason"]
        })

    return explanations


def _build_erp_payload(
    quote_id: str,
    priced_quote: dict
) -> dict:
    erp_lines = []

    for index, line in enumerate(priced_quote["priced_lines"]):
        erp_lines.append({
            "line_number": index + 1,
            "sku": line["sku"],
            "description": line["product_name"],
            "quantity": line["quantity"],
            "uom": line.get("uom_raw"),
            "unit_price": line["unit_price"],
            "extended_price": line["line_total"]
        })

    return {
        "source_system": "QuoteIQ",
        "document_type": "QUOTE_DRAFT",
        "quote_id": quote_id,
        "customer_id": priced_quote["customer_id"],
        "customer_name": priced_quote["customer_name"],
        "currency": "USD",
        "status": "DRAFT",
        "subtotal": priced_quote["subtotal"],
        "lines": erp_lines
    }


def build_quote_package(
    customer_id: str,
    rfq_text: str,
    extracted_lines: list[dict],
    matched_lines: list[dict],
    priced_quote: dict
) -> dict:
    quote_id = f"QIQ-{uuid4().hex[:8].upper()}"
    timestamp = datetime.now(timezone.utc).isoformat()

    quote_confidence = _calculate_quote_confidence(
        matched_lines=matched_lines,
        risk_count=priced_quote["risk_count"]
    )

    review_required = (
        priced_quote["risk_count"] > 0
        or quote_confidence < 85
    )

    quote_status = (
        "REVIEW_REQUIRED"
        if review_required
        else "READY_FOR_APPROVAL"
    )

    line_explanations = _build_line_explanations(
        matched_lines=matched_lines,
        priced_lines=priced_quote["priced_lines"]
    )

    erp_payload = _build_erp_payload(
        quote_id=quote_id,
        priced_quote=priced_quote
    )

    audit_trail = [
        {
            "event": "RFQ_RECEIVED",
            "timestamp": timestamp,
            "details": f"RFQ received for customer {customer_id}"
        },
        {
            "event": "LINES_EXTRACTED",
            "timestamp": timestamp,
            "details": f"{len(extracted_lines)} RFQ lines extracted"
        },
        {
            "event": "SKUS_MATCHED",
            "timestamp": timestamp,
            "details": f"{len(matched_lines)} catalog matches generated"
        },
        {
            "event": "PRICING_CALCULATED",
            "timestamp": timestamp,
            "details": (
                f"Quote subtotal calculated as "
                f"${priced_quote['subtotal']:.2f}"
            )
        },
        {
            "event": "ERP_DRAFT_GENERATED",
            "timestamp": timestamp,
            "details": "ERP-ready quote draft generated"
        }
    ]

    return {
        "quote_id": quote_id,
        "quote_status": quote_status,
        "review_required": review_required,
        "quote_confidence": quote_confidence,
        "customer_id": priced_quote["customer_id"],
        "customer_name": priced_quote["customer_name"],
        "price_class": priced_quote["price_class"],
        "rfq_text": rfq_text,
        "extracted_line_count": len(extracted_lines),
        "matched_line_count": len(matched_lines),
        "quote_subtotal": priced_quote["subtotal"],
        "estimated_margin_pct": priced_quote["estimated_margin_pct"],
        "risk_count": priced_quote["risk_count"],
        "extracted_lines": extracted_lines,
        "matched_lines": matched_lines,
        "priced_lines": priced_quote["priced_lines"],
        "line_explanations": line_explanations,
        "erp_payload": erp_payload,
        "audit_trail": audit_trail
    }