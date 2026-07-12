from fastapi import Depends, FastAPI, HTTPException
from fastapi.responses import FileResponse

from app.database import Base, engine
import app.db_models

from app.models.schemas import (
    RFQRequest,
    RFQExtractionResponse,
    MatchLinesRequest,
    MatchLinesResponse,
    PriceQuoteRequest,
    PriceQuoteResponse,
    ProcessRFQRequest,
    ProcessRFQResponse,
    QuoteApprovalRequest,
    QuoteRejectionRequest,
)

from app.routers.auth import (
    get_current_user,
    require_roles,
    router as auth_router,
)

from app.services.data_loader import (
    load_product_catalog,
    load_customers,
    load_price_rules,
    load_margin_policies,
)

from app.services.rfq_extractor import extract_rfq_lines
from app.services.sku_matcher import match_lines_to_catalog
from app.services.pricing_engine import price_quote
from app.services.quote_package import build_quote_package
from app.services.quote_pdf import generate_quote_pdf

from app.services.quote_store import (
    save_quote,
    get_quote,
    approve_quote,
    reject_quote,
)

from app.services.order_service import (
    create_sales_order,
    get_sales_order,
)


Base.metadata.create_all(bind=engine)


app = FastAPI(
    title="QuoteIQ API",
    description=(
        "AI-assisted quote-to-order platform "
        "for building materials distributors"
    ),
    version="0.7.0"
)


app.include_router(auth_router)


@app.get("/")
def root():
    return {
        "message": "QuoteIQ API is running",
        "project": "AI Quote-to-Order Platform",
        "status": "healthy",
        "database": "SQLite",
        "authentication": "JWT",
        "authorization": "Role-Based Access Control"
    }


@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "database": "connected",
        "authentication": "enabled"
    }


@app.get("/catalog")
def get_catalog(
    current_user=Depends(get_current_user)
):
    catalog = load_product_catalog()

    return {
        "count": len(catalog),
        "products": catalog,
        "requested_by": current_user.email
    }


@app.get("/customers")
def get_customers(
    current_user=Depends(get_current_user)
):
    customers = load_customers()

    return {
        "count": len(customers),
        "customers": customers,
        "requested_by": current_user.email
    }


@app.post(
    "/rfqs/extract",
    response_model=RFQExtractionResponse
)
def extract_rfq(
    request: RFQRequest,
    current_user=Depends(
        require_roles(
            "sales_rep",
            "manager",
            "admin"
        )
    )
):
    lines = extract_rfq_lines(
        request.rfq_text
    )

    return {
        "line_count": len(lines),
        "lines": lines
    }


@app.post(
    "/match-lines",
    response_model=MatchLinesResponse
)
def match_lines(
    request: MatchLinesRequest,
    current_user=Depends(
        require_roles(
            "sales_rep",
            "manager",
            "admin"
        )
    )
):
    catalog = load_product_catalog()

    raw_lines = [
        line.model_dump()
        for line in request.lines
    ]

    matched_lines = match_lines_to_catalog(
        raw_lines,
        catalog
    )

    return {
        "match_count": len(matched_lines),
        "matched_lines": matched_lines
    }


@app.post(
    "/price-quote",
    response_model=PriceQuoteResponse
)
def price_quote_endpoint(
    request: PriceQuoteRequest,
    current_user=Depends(
        require_roles(
            "sales_rep",
            "manager",
            "admin"
        )
    )
):
    catalog = load_product_catalog()
    customers = load_customers()
    price_rules = load_price_rules()
    margin_policies = load_margin_policies()

    raw_matched_lines = [
        line.model_dump()
        for line in request.matched_lines
    ]

    priced_quote = price_quote(
        customer_id=request.customer_id,
        matched_lines=raw_matched_lines,
        catalog=catalog,
        customers=customers,
        price_rules=price_rules,
        margin_policies=margin_policies
    )

    return priced_quote


@app.post(
    "/rfqs/process",
    response_model=ProcessRFQResponse
)
def process_rfq(
    request: ProcessRFQRequest,
    current_user=Depends(
        require_roles(
            "sales_rep",
            "manager",
            "admin"
        )
    )
):
    catalog = load_product_catalog()
    customers = load_customers()
    price_rules = load_price_rules()
    margin_policies = load_margin_policies()

    extracted_lines = extract_rfq_lines(
        request.rfq_text
    )

    matched_lines = match_lines_to_catalog(
        extracted_lines,
        catalog
    )

    priced_quote = price_quote(
        customer_id=request.customer_id,
        matched_lines=matched_lines,
        catalog=catalog,
        customers=customers,
        price_rules=price_rules,
        margin_policies=margin_policies
    )

    return {
        "customer_id": priced_quote["customer_id"],
        "customer_name": priced_quote["customer_name"],
        "price_class": priced_quote["price_class"],
        "extracted_line_count": len(
            extracted_lines
        ),
        "matched_line_count": len(
            matched_lines
        ),
        "quote_subtotal": priced_quote[
            "subtotal"
        ],
        "estimated_margin_pct": priced_quote[
            "estimated_margin_pct"
        ],
        "risk_count": priced_quote[
            "risk_count"
        ],
        "extracted_lines": extracted_lines,
        "matched_lines": matched_lines,
        "priced_lines": priced_quote[
            "priced_lines"
        ]
    }


@app.post("/rfqs/process-v2")
def process_rfq_v2(
    request: ProcessRFQRequest,
    current_user=Depends(
        require_roles(
            "sales_rep",
            "manager",
            "admin"
        )
    )
):
    catalog = load_product_catalog()
    customers = load_customers()
    price_rules = load_price_rules()
    margin_policies = load_margin_policies()

    extracted_lines = extract_rfq_lines(
        request.rfq_text
    )

    matched_lines = match_lines_to_catalog(
        extracted_lines,
        catalog
    )

    priced_quote = price_quote(
        customer_id=request.customer_id,
        matched_lines=matched_lines,
        catalog=catalog,
        customers=customers,
        price_rules=price_rules,
        margin_policies=margin_policies
    )

    quote_package = build_quote_package(
        customer_id=request.customer_id,
        rfq_text=request.rfq_text,
        extracted_lines=extracted_lines,
        matched_lines=matched_lines,
        priced_quote=priced_quote
    )

    quote_package["created_by"] = (
        current_user.email
    )

    return save_quote(
        quote_package
    )


@app.get("/quotes/{quote_id}")
def retrieve_quote(
    quote_id: str,
    current_user=Depends(get_current_user)
):
    quote = get_quote(
        quote_id
    )

    if quote is None:
        raise HTTPException(
            status_code=404,
            detail=(
                f"Quote not found: "
                f"{quote_id}"
            )
        )

    return quote


@app.post("/quotes/{quote_id}/approve")
def approve_quote_endpoint(
    quote_id: str,
    request: QuoteApprovalRequest,
    current_user=Depends(
        require_roles(
            "manager",
            "admin"
        )
    )
):
    quote = approve_quote(
        quote_id=quote_id,
        reviewed_by=request.reviewed_by
    )

    if quote is None:
        raise HTTPException(
            status_code=404,
            detail=(
                f"Quote not found: "
                f"{quote_id}"
            )
        )

    return {
        "message": (
            "Quote approved successfully"
        ),
        "quote_id": quote_id,
        "quote_status": quote[
            "quote_status"
        ],
        "approved_by": quote[
            "approved_by"
        ],
        "approved_at": quote[
            "approved_at"
        ],
        "authenticated_user": (
            current_user.email
        ),
        "authenticated_role": (
            current_user.role
        ),
        "erp_status": quote[
            "erp_payload"
        ]["status"],
        "audit_trail": quote[
            "audit_trail"
        ]
    }


@app.post("/quotes/{quote_id}/reject")
def reject_quote_endpoint(
    quote_id: str,
    request: QuoteRejectionRequest,
    current_user=Depends(
        require_roles(
            "manager",
            "admin"
        )
    )
):
    quote = reject_quote(
        quote_id=quote_id,
        reviewed_by=request.reviewed_by,
        reason=request.reason
    )

    if quote is None:
        raise HTTPException(
            status_code=404,
            detail=(
                f"Quote not found: "
                f"{quote_id}"
            )
        )

    return {
        "message": (
            "Quote rejected successfully"
        ),
        "quote_id": quote_id,
        "quote_status": quote[
            "quote_status"
        ],
        "rejected_by": quote[
            "rejected_by"
        ],
        "rejected_at": quote[
            "rejected_at"
        ],
        "rejection_reason": quote[
            "rejection_reason"
        ],
        "authenticated_user": (
            current_user.email
        ),
        "authenticated_role": (
            current_user.role
        ),
        "erp_status": quote[
            "erp_payload"
        ]["status"],
        "audit_trail": quote[
            "audit_trail"
        ]
    }


@app.get("/quotes/{quote_id}/pdf")
def download_quote_pdf(
    quote_id: str,
    current_user=Depends(get_current_user)
):
    quote = get_quote(
        quote_id
    )

    if quote is None:
        raise HTTPException(
            status_code=404,
            detail=(
                f"Quote not found: "
                f"{quote_id}"
            )
        )

    if quote.get(
        "quote_status"
    ) not in {
        "APPROVED",
        "CONVERTED_TO_ORDER"
    }:
        raise HTTPException(
            status_code=400,
            detail=(
                "Quote must be approved "
                "before generating a PDF"
            )
        )

    pdf_path = generate_quote_pdf(
        quote
    )

    return FileResponse(
        path=str(pdf_path),
        media_type="application/pdf",
        filename=f"{quote_id}.pdf"
    )


@app.post(
    "/quotes/{quote_id}/create-order"
)
def create_order_endpoint(
    quote_id: str,
    current_user=Depends(
        require_roles(
            "manager",
            "admin"
        )
    )
):
    quote = get_quote(
        quote_id
    )

    if quote is None:
        raise HTTPException(
            status_code=404,
            detail=(
                f"Quote not found: "
                f"{quote_id}"
            )
        )

    try:
        sales_order = create_sales_order(
            quote
        )

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error)
        ) from error

    updated_quote = get_quote(
        quote_id
    )

    return {
        "message": (
            "Sales order created "
            "successfully"
        ),
        "sales_order": sales_order,
        "created_by": (
            current_user.email
        ),
        "created_by_role": (
            current_user.role
        ),
        "quote_status": updated_quote[
            "quote_status"
        ],
        "erp_status": updated_quote[
            "erp_payload"
        ]["status"],
        "audit_trail": updated_quote[
            "audit_trail"
        ]
    }


@app.get("/orders/{order_id}")
def retrieve_sales_order(
    order_id: str,
    current_user=Depends(get_current_user)
):
    sales_order = get_sales_order(
        order_id
    )

    if sales_order is None:
        raise HTTPException(
            status_code=404,
            detail=(
                f"Sales order not found: "
                f"{order_id}"
            )
        )

    return sales_order