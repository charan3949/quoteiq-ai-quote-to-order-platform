"""Aggregation logic for the executive dashboard and related views.

This module intentionally does not touch quote_store's write paths.
It only reads QuoteRecord rows (via list_all_quotes_raw) and derives
metrics from them, so it can evolve independently of the core
quote-to-order workflow.
"""
from collections import defaultdict
from datetime import datetime, timezone

from app.services.quote_store import list_all_quotes_raw

TERMINAL_APPROVED_STATUSES = {"APPROVED", "CONVERTED_TO_ORDER"}
PENDING_STATUSES = {"READY_FOR_APPROVAL", "REVIEW_REQUIRED"}


def _as_utc(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def get_summary() -> dict:
    records = list_all_quotes_raw()

    total_quotes = len(records)
    pending = 0
    approved = 0
    rejected = 0
    converted = 0
    revenue = 0.0
    approval_hours: list[float] = []
    quote_values: list[float] = []

    for record in records:
        status = record.quote_status
        quote_values.append(record.quote_subtotal or 0.0)

        if status in PENDING_STATUSES:
            pending += 1
        elif status == "REJECTED":
            rejected += 1
        elif status == "APPROVED":
            approved += 1
        elif status == "CONVERTED_TO_ORDER":
            converted += 1
            approved += 1

        if status in TERMINAL_APPROVED_STATUSES:
            revenue += record.quote_subtotal or 0.0

            created = _as_utc(record.created_at)
            approved_at = _as_utc(record.approved_at)

            if created and approved_at:
                delta_hours = (
                    approved_at - created
                ).total_seconds() / 3600.0
                approval_hours.append(delta_hours)

    conversion_rate = (
        round(100.0 * converted / total_quotes, 2)
        if total_quotes
        else 0.0
    )

    avg_approval_hours = (
        round(sum(approval_hours) / len(approval_hours), 1)
        if approval_hours
        else None
    )

    avg_quote_value = (
        round(sum(quote_values) / len(quote_values), 2)
        if quote_values
        else 0.0
    )

    return {
        "total_quotes": total_quotes,
        "pending_quotes": pending,
        "approved_quotes": approved,
        "rejected_quotes": rejected,
        "converted_quotes": converted,
        "revenue": round(revenue, 2),
        "conversion_rate_pct": conversion_rate,
        "avg_approval_time_hours": avg_approval_hours,
        "avg_quote_value": avg_quote_value,
    }


def get_monthly_trend(months: int = 6) -> list[dict]:
    records = list_all_quotes_raw()

    buckets: dict[str, dict] = defaultdict(
        lambda: {"quotes": 0, "revenue": 0.0, "converted": 0}
    )

    for record in records:
        created = _as_utc(record.created_at)
        if created is None:
            continue

        key = created.strftime("%Y-%m")
        buckets[key]["quotes"] += 1

        if record.quote_status in TERMINAL_APPROVED_STATUSES:
            buckets[key]["revenue"] += record.quote_subtotal or 0.0

        if record.quote_status == "CONVERTED_TO_ORDER":
            buckets[key]["converted"] += 1

    ordered_keys = sorted(buckets.keys())[-months:]

    return [
        {
            "month": key,
            "quotes": buckets[key]["quotes"],
            "revenue": round(buckets[key]["revenue"], 2),
            "converted": buckets[key]["converted"],
        }
        for key in ordered_keys
    ]


def get_top_customers(limit: int = 5) -> list[dict]:
    records = list_all_quotes_raw()

    by_customer: dict[str, dict] = {}

    for record in records:
        key = record.customer_id
        entry = by_customer.setdefault(
            key,
            {
                "customer_id": record.customer_id,
                "customer_name": record.customer_name,
                "quote_count": 0,
                "revenue": 0.0,
                "approved_count": 0,
            },
        )

        entry["quote_count"] += 1

        if record.quote_status in TERMINAL_APPROVED_STATUSES:
            entry["revenue"] += record.quote_subtotal or 0.0
            entry["approved_count"] += 1

    customers = list(by_customer.values())

    for customer in customers:
        customer["revenue"] = round(customer["revenue"], 2)
        customer["approval_rate_pct"] = (
            round(
                100.0
                * customer["approved_count"]
                / customer["quote_count"],
                1,
            )
            if customer["quote_count"]
            else 0.0
        )

    customers.sort(key=lambda c: c["revenue"], reverse=True)

    return customers[:limit]


def get_rep_performance() -> list[dict]:
    records = list_all_quotes_raw()

    by_rep: dict[str, dict] = {}

    for record in records:
        rep = record.created_by or "unassigned"
        entry = by_rep.setdefault(
            rep,
            {
                "sales_rep": rep,
                "quote_count": 0,
                "revenue": 0.0,
                "approved_count": 0,
                "margin_sum": 0.0,
                "approval_hours": [],
            },
        )

        entry["quote_count"] += 1
        entry["margin_sum"] += record.estimated_margin_pct or 0.0

        if record.quote_status in TERMINAL_APPROVED_STATUSES:
            entry["revenue"] += record.quote_subtotal or 0.0
            entry["approved_count"] += 1

            created = _as_utc(record.created_at)
            approved_at = _as_utc(record.approved_at)

            if created and approved_at:
                entry["approval_hours"].append(
                    (approved_at - created).total_seconds() / 3600.0
                )

    reps = []

    for entry in by_rep.values():
        quote_count = entry["quote_count"]
        approval_hours = entry.pop("approval_hours")

        reps.append({
            **entry,
            "revenue": round(entry["revenue"], 2),
            "avg_margin_pct": (
                round(entry["margin_sum"] / quote_count, 2)
                if quote_count
                else 0.0
            ),
            "conversion_rate_pct": (
                round(
                    100.0 * entry["approved_count"] / quote_count, 1
                )
                if quote_count
                else 0.0
            ),
            "avg_approval_time_hours": (
                round(
                    sum(approval_hours) / len(approval_hours), 1
                )
                if approval_hours
                else None
            ),
        })

        del reps[-1]["margin_sum"]

    reps.sort(key=lambda r: r["revenue"], reverse=True)

    return reps


def get_approval_bottlenecks(limit: int = 10) -> dict:
    records = list_all_quotes_raw()
    now = datetime.now(timezone.utc)

    pending = [
        record
        for record in records
        if record.quote_status in PENDING_STATUSES
    ]

    at_risk_revenue = sum(
        record.quote_subtotal or 0.0 for record in pending
    )

    aged = []

    for record in pending:
        created = _as_utc(record.created_at)
        age_hours = (
            round((now - created).total_seconds() / 3600.0, 1)
            if created
            else None
        )

        aged.append({
            "quote_id": record.quote_id,
            "customer_name": record.customer_name,
            "quote_subtotal": record.quote_subtotal,
            "risk_count": record.risk_count,
            "created_by": record.created_by,
            "age_hours": age_hours,
        })

    aged.sort(
        key=lambda q: q["age_hours"] or 0,
        reverse=True,
    )

    return {
        "pending_count": len(pending),
        "revenue_at_risk": round(at_risk_revenue, 2),
        "oldest_pending": aged[:limit],
    }
