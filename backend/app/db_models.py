from datetime import datetime

from sqlalchemy import (
    Column,
    DateTime,
    Float,
    Integer,
    JSON,
    String,
    Text,
)

from app.database import Base


class QuoteRecord(Base):
    __tablename__ = "quotes"

    id = Column(Integer, primary_key=True, index=True)
    quote_id = Column(String(50), unique=True, index=True, nullable=False)

    customer_id = Column(String(50), nullable=False)
    customer_name = Column(String(255), nullable=False)
    price_class = Column(String(100), nullable=False)

    quote_status = Column(String(50), nullable=False)
    review_required = Column(Integer, nullable=False, default=0)
    quote_confidence = Column(Float, nullable=False, default=0.0)

    rfq_text = Column(Text, nullable=False)

    extracted_line_count = Column(Integer, nullable=False, default=0)
    matched_line_count = Column(Integer, nullable=False, default=0)

    quote_subtotal = Column(Float, nullable=False, default=0.0)
    estimated_margin_pct = Column(Float, nullable=False, default=0.0)
    risk_count = Column(Integer, nullable=False, default=0)

    extracted_lines = Column(JSON, nullable=False)
    matched_lines = Column(JSON, nullable=False)
    priced_lines = Column(JSON, nullable=False)
    line_explanations = Column(JSON, nullable=False)
    erp_payload = Column(JSON, nullable=False)
    audit_trail = Column(JSON, nullable=False)

    approved_by = Column(String(255), nullable=True)
    approved_at = Column(DateTime, nullable=True)

    rejected_by = Column(String(255), nullable=True)
    rejected_at = Column(DateTime, nullable=True)
    rejection_reason = Column(Text, nullable=True)

    sales_order_id = Column(String(50), nullable=True)

    created_at = Column(
        DateTime,
        nullable=False,
        default=datetime.utcnow
    )

    updated_at = Column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )


class SalesOrderRecord(Base):
    __tablename__ = "sales_orders"

    id = Column(Integer, primary_key=True, index=True)
    sales_order_id = Column(
        String(50),
        unique=True,
        index=True,
        nullable=False
    )

    source_quote_id = Column(String(50), index=True, nullable=False)

    source_system = Column(String(100), nullable=False)
    target_erp = Column(String(100), nullable=False)
    document_type = Column(String(100), nullable=False)

    customer_id = Column(String(50), nullable=False)
    customer_name = Column(String(255), nullable=False)

    currency = Column(String(10), nullable=False)
    order_status = Column(String(50), nullable=False)

    order_total = Column(Float, nullable=False)
    line_count = Column(Integer, nullable=False)

    lines = Column(JSON, nullable=False)

    created_at = Column(
        DateTime,
        nullable=False,
        default=datetime.utcnow
    )
class UserRecord(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)

    email = Column(
        String(255),
        unique=True,
        index=True,
        nullable=False
    )

    full_name = Column(
        String(255),
        nullable=False
    )

    hashed_password = Column(
        String(255),
        nullable=False
    )

    role = Column(
        String(50),
        nullable=False,
        default="sales_rep"
    )

    is_active = Column(
        Integer,
        nullable=False,
        default=1
    )

    created_at = Column(
        DateTime,
        nullable=False,
        default=datetime.utcnow
    )

    updated_at = Column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )