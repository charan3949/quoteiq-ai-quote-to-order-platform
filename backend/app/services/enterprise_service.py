from collections import defaultdict

from app.database import SessionLocal
from app.db_models import SalesOrderRecord
from app.services.data_loader import load_customers
from app.services.quote_store import get_quote, list_all_quotes_raw

APPROVED = {"APPROVED", "CONVERTED_TO_ORDER"}


def get_customer_portfolio() -> list[dict]:
    catalog = {c["customer_id"]: c for c in load_customers()}
    metrics = defaultdict(lambda: {"quote_count": 0, "approved_count": 0, "revenue": 0.0, "pipeline": 0.0})
    for q in list_all_quotes_raw():
        m = metrics[q.customer_id]
        m["quote_count"] += 1
        if q.quote_status in APPROVED:
            m["approved_count"] += 1
            m["revenue"] += q.quote_subtotal or 0.0
        if q.quote_status in {"READY_FOR_APPROVAL", "REVIEW_REQUIRED"}:
            m["pipeline"] += q.quote_subtotal or 0.0
    result = []
    for customer_id, customer in catalog.items():
        m = metrics[customer_id]
        result.append({
            **customer,
            **m,
            "revenue": round(m["revenue"], 2),
            "pipeline": round(m["pipeline"], 2),
            "approval_rate_pct": round(100 * m["approved_count"] / m["quote_count"], 1) if m["quote_count"] else 0.0,
        })
    return sorted(result, key=lambda x: x["revenue"], reverse=True)


def list_orders() -> list[dict]:
    db = SessionLocal()
    try:
        rows = db.query(SalesOrderRecord).order_by(SalesOrderRecord.created_at.desc()).all()
        return [{
            "sales_order_id": r.sales_order_id,
            "source_quote_id": r.source_quote_id,
            "customer_id": r.customer_id,
            "customer_name": r.customer_name,
            "target_erp": r.target_erp,
            "order_status": r.order_status,
            "order_total": r.order_total,
            "line_count": r.line_count,
            "created_at": r.created_at.isoformat() if r.created_at else None,
        } for r in rows]
    finally:
        db.close()


def quote_intelligence(quote_id: str) -> dict | None:
    q = get_quote(quote_id)
    if not q:
        return None
    margin = q.get("estimated_margin_pct", 0)
    confidence = q.get("quote_confidence", 0)
    risks = q.get("risk_count", 0)
    status = q.get("quote_status")
    recommendation = "APPROVE" if risks == 0 and margin >= 20 else "REVIEW"
    risk_level = "LOW" if risks == 0 and margin >= 25 else "MEDIUM" if risks <= 1 else "HIGH"
    timeline = [{"event": "QUOTE_CREATED", "timestamp": q.get("created_at"), "details": f"Created by {q.get('created_by') or 'system'}"}]
    timeline.extend(q.get("audit_trail") or [])
    reasons = [
        f"Catalog match confidence is {round(confidence * 100 if confidence <= 1 else confidence, 1)}%.",
        f"Estimated gross margin is {margin:.1f}%.",
        f"{q.get('matched_line_count', 0)} of {q.get('extracted_line_count', 0)} RFQ lines were matched.",
        "No pricing risks were detected." if risks == 0 else f"{risks} pricing or margin risk flag(s) require review.",
    ]
    return {
        "quote_id": quote_id,
        "recommendation": recommendation,
        "risk_level": risk_level,
        "confidence_pct": round(confidence * 100 if confidence <= 1 else confidence, 1),
        "reasons": reasons,
        "timeline": timeline,
        "line_explanations": q.get("line_explanations") or [],
        "status": status,
    }
