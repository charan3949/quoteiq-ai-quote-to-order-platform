from datetime import datetime, timezone

from app.database import SessionLocal
from app.db_models import QuoteRecord


def _parse_datetime(value):
    if value is None:
        return None

    if isinstance(value, datetime):
        return value

    return datetime.fromisoformat(
        str(value).replace("Z", "+00:00")
    )


def _record_to_dict(record: QuoteRecord) -> dict:
    quote = {
        "quote_id": record.quote_id,
        "quote_status": record.quote_status,
        "review_required": bool(record.review_required),
        "quote_confidence": record.quote_confidence,
        "customer_id": record.customer_id,
        "customer_name": record.customer_name,
        "price_class": record.price_class,
        "rfq_text": record.rfq_text,
        "extracted_line_count": record.extracted_line_count,
        "matched_line_count": record.matched_line_count,
        "quote_subtotal": record.quote_subtotal,
        "estimated_margin_pct": record.estimated_margin_pct,
        "risk_count": record.risk_count,
        "extracted_lines": record.extracted_lines,
        "matched_lines": record.matched_lines,
        "priced_lines": record.priced_lines,
        "line_explanations": record.line_explanations,
        "erp_payload": record.erp_payload,
        "audit_trail": record.audit_trail,
        "approved_by": record.approved_by,
        "approved_at": (
            record.approved_at.isoformat()
            if record.approved_at
            else None
        ),
        "rejected_by": record.rejected_by,
        "rejected_at": (
            record.rejected_at.isoformat()
            if record.rejected_at
            else None
        ),
        "rejection_reason": record.rejection_reason,
        "sales_order_id": record.sales_order_id,
        "created_at": (
            record.created_at.isoformat()
            if record.created_at
            else None
        ),
        "updated_at": (
            record.updated_at.isoformat()
            if record.updated_at
            else None
        )
    }

    return quote


def save_quote(quote: dict) -> dict:
    database = SessionLocal()

    try:
        existing = (
            database.query(QuoteRecord)
            .filter(
                QuoteRecord.quote_id == quote["quote_id"]
            )
            .first()
        )

        if existing:
            return _record_to_dict(existing)

        record = QuoteRecord(
            quote_id=quote["quote_id"],
            customer_id=quote["customer_id"],
            customer_name=quote["customer_name"],
            price_class=quote["price_class"],
            quote_status=quote["quote_status"],
            review_required=int(
                quote.get("review_required", False)
            ),
            quote_confidence=quote.get(
                "quote_confidence",
                0.0
            ),
            rfq_text=quote["rfq_text"],
            extracted_line_count=quote.get(
                "extracted_line_count",
                0
            ),
            matched_line_count=quote.get(
                "matched_line_count",
                0
            ),
            quote_subtotal=quote.get(
                "quote_subtotal",
                0.0
            ),
            estimated_margin_pct=quote.get(
                "estimated_margin_pct",
                0.0
            ),
            risk_count=quote.get("risk_count", 0),
            extracted_lines=quote.get(
                "extracted_lines",
                []
            ),
            matched_lines=quote.get(
                "matched_lines",
                []
            ),
            priced_lines=quote.get(
                "priced_lines",
                []
            ),
            line_explanations=quote.get(
                "line_explanations",
                []
            ),
            erp_payload=quote.get(
                "erp_payload",
                {}
            ),
            audit_trail=quote.get(
                "audit_trail",
                []
            )
        )

        database.add(record)
        database.commit()
        database.refresh(record)

        return _record_to_dict(record)

    finally:
        database.close()


def get_quote(quote_id: str) -> dict | None:
    database = SessionLocal()

    try:
        record = (
            database.query(QuoteRecord)
            .filter(
                QuoteRecord.quote_id == quote_id
            )
            .first()
        )

        if record is None:
            return None

        return _record_to_dict(record)

    finally:
        database.close()


def approve_quote(
    quote_id: str,
    reviewed_by: str
) -> dict | None:
    database = SessionLocal()

    try:
        record = (
            database.query(QuoteRecord)
            .filter(
                QuoteRecord.quote_id == quote_id
            )
            .first()
        )

        if record is None:
            return None

        timestamp = datetime.now(timezone.utc)

        record.quote_status = "APPROVED"
        record.review_required = 0
        record.approved_by = reviewed_by
        record.approved_at = timestamp

        erp_payload = dict(record.erp_payload or {})
        erp_payload["status"] = "APPROVED"
        record.erp_payload = erp_payload

        audit_trail = list(record.audit_trail or [])
        audit_trail.append({
            "event": "QUOTE_APPROVED",
            "timestamp": timestamp.isoformat(),
            "details": f"Quote approved by {reviewed_by}"
        })
        record.audit_trail = audit_trail

        database.commit()
        database.refresh(record)

        return _record_to_dict(record)

    finally:
        database.close()


def reject_quote(
    quote_id: str,
    reviewed_by: str,
    reason: str
) -> dict | None:
    database = SessionLocal()

    try:
        record = (
            database.query(QuoteRecord)
            .filter(
                QuoteRecord.quote_id == quote_id
            )
            .first()
        )

        if record is None:
            return None

        timestamp = datetime.now(timezone.utc)

        record.quote_status = "REJECTED"
        record.review_required = 1
        record.rejected_by = reviewed_by
        record.rejected_at = timestamp
        record.rejection_reason = reason

        erp_payload = dict(record.erp_payload or {})
        erp_payload["status"] = "REJECTED"
        record.erp_payload = erp_payload

        audit_trail = list(record.audit_trail or [])
        audit_trail.append({
            "event": "QUOTE_REJECTED",
            "timestamp": timestamp.isoformat(),
            "details": (
                f"Quote rejected by {reviewed_by}. "
                f"Reason: {reason}"
            )
        })
        record.audit_trail = audit_trail

        database.commit()
        database.refresh(record)

        return _record_to_dict(record)

    finally:
        database.close()


def update_quote_after_order(
    quote_id: str,
    sales_order_id: str
) -> dict | None:
    database = SessionLocal()

    try:
        record = (
            database.query(QuoteRecord)
            .filter(
                QuoteRecord.quote_id == quote_id
            )
            .first()
        )

        if record is None:
            return None

        timestamp = datetime.now(timezone.utc)

        record.sales_order_id = sales_order_id
        record.quote_status = "CONVERTED_TO_ORDER"

        erp_payload = dict(record.erp_payload or {})
        erp_payload["status"] = "ORDER_CREATED"
        record.erp_payload = erp_payload

        audit_trail = list(record.audit_trail or [])
        audit_trail.append({
            "event": "SALES_ORDER_CREATED",
            "timestamp": timestamp.isoformat(),
            "details": (
                f"Sales order {sales_order_id} created from "
                f"quote {quote_id}"
            )
        })
        record.audit_trail = audit_trail

        database.commit()
        database.refresh(record)

        return _record_to_dict(record)

    finally:
        database.close()