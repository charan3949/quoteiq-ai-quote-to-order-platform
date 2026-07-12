from datetime import datetime, timezone
from uuid import uuid4

from app.database import SessionLocal
from app.db_models import SalesOrderRecord
from app.services.quote_store import update_quote_after_order


def _record_to_dict(record: SalesOrderRecord) -> dict:
    return {
        "sales_order_id": record.sales_order_id,
        "source_quote_id": record.source_quote_id,
        "source_system": record.source_system,
        "target_erp": record.target_erp,
        "document_type": record.document_type,
        "customer_id": record.customer_id,
        "customer_name": record.customer_name,
        "currency": record.currency,
        "order_status": record.order_status,
        "created_at": (
            record.created_at.isoformat()
            if record.created_at
            else None
        ),
        "order_total": record.order_total,
        "line_count": record.line_count,
        "lines": record.lines
    }


def create_sales_order(quote: dict) -> dict:
    if quote.get("quote_status") != "APPROVED":
        raise ValueError(
            "Only approved quotes can be converted into sales orders"
        )

    database = SessionLocal()

    try:
        existing_order_id = quote.get("sales_order_id")

        if existing_order_id:
            existing_record = (
                database.query(SalesOrderRecord)
                .filter(
                    SalesOrderRecord.sales_order_id
                    == existing_order_id
                )
                .first()
            )

            if existing_record:
                return _record_to_dict(existing_record)

        existing_for_quote = (
            database.query(SalesOrderRecord)
            .filter(
                SalesOrderRecord.source_quote_id
                == quote["quote_id"]
            )
            .first()
        )

        if existing_for_quote:
            return _record_to_dict(existing_for_quote)

        timestamp = datetime.now(timezone.utc)
        order_id = f"SO-{uuid4().hex[:8].upper()}"

        order_lines = []

        for index, line in enumerate(quote["priced_lines"]):
            order_lines.append({
                "line_number": index + 1,
                "sku": line["sku"],
                "description": line["product_name"],
                "quantity": line["quantity"],
                "uom": line.get("uom_raw"),
                "unit_price": line["unit_price"],
                "extended_price": line["line_total"],
                "fulfillment_status": "PENDING"
            })

        record = SalesOrderRecord(
            sales_order_id=order_id,
            source_quote_id=quote["quote_id"],
            source_system="QuoteIQ",
            target_erp="MOCK_ERP",
            document_type="SALES_ORDER",
            customer_id=quote["customer_id"],
            customer_name=quote["customer_name"],
            currency="USD",
            order_status="CREATED",
            order_total=quote["quote_subtotal"],
            line_count=len(order_lines),
            lines=order_lines,
            created_at=timestamp
        )

        database.add(record)
        database.commit()
        database.refresh(record)

        update_quote_after_order(
            quote_id=quote["quote_id"],
            sales_order_id=order_id
        )

        return _record_to_dict(record)

    finally:
        database.close()


def get_sales_order(order_id: str) -> dict | None:
    database = SessionLocal()

    try:
        record = (
            database.query(SalesOrderRecord)
            .filter(
                SalesOrderRecord.sales_order_id == order_id
            )
            .first()
        )

        if record is None:
            return None

        return _record_to_dict(record)

    finally:
        database.close()