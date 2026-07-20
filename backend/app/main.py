import logging

from fastapi import Depends, FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

import app.db_models
from app.config import settings
from app.database import Base, SessionLocal, engine
from app.logging_config import configure_logging
from app.models.audit import AuditLogRecord
from app.models.schemas import (
    MatchLinesRequest,
    MatchLinesResponse,
    PriceQuoteRequest,
    PriceQuoteResponse,
    ProcessRFQRequest,
    ProcessRFQResponse,
    QuoteApprovalRequest,
    QuoteRejectionRequest,
    RFQExtractionResponse,
    RFQRequest,
    RFQUploadResponse,
)
from app.routers.admin import router as admin_router
from app.routers.analytics import router as analytics_router
from app.routers.enterprise import router as enterprise_router
from app.routers.auth import (
    get_current_user,
    require_roles,
    router as auth_router,
)
from app.services.audit_service import record_audit_event
from app.services.data_loader import (
    load_customers,
    load_margin_policies,
    load_price_rules,
    load_product_catalog,
)
from app.services.order_service import (
    create_sales_order,
    get_sales_order,
)
from app.services.pricing_engine import price_quote
from app.services.quote_package import build_quote_package
from app.services.quote_pdf import generate_quote_pdf
from app.services.quote_excel import generate_quote_excel
from app.services.quote_store import (
    approve_quote,
    get_quote,
    list_quotes,
    reject_quote,
    save_quote,
)
from app.services.ai_rfq_extractor import extract_rfq_lines_ai
from app.services.rfq_upload import RFQUploadError, extract_text_from_upload
from app.services.sku_matcher import match_lines_to_catalog
from app.seed import seed_demo_users


configure_logging()
logger = logging.getLogger(__name__)

Base.metadata.create_all(bind=engine)

_seed_session = SessionLocal()
try:
    seed_demo_users(_seed_session)
finally:
    _seed_session.close()


app = FastAPI(
    title=settings.app_name,
    description=(
        "AI-assisted quote-to-order platform "
        "for building materials distributors"
    ),
    version=settings.app_version,
    debug=settings.debug,
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:3001",
        "http://localhost:3002",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3001",
        "http://127.0.0.1:3002",
        "https://quoteiq-ai-quote-to-order-platform.vercel.app",
        "https://quoteiq-ai-quote-to-order-platf-git-bd9b21-charan3949s-projects.vercel.app",
    ],
    allow_origin_regex=r"https://.*\.vercel\.app",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(auth_router)
app.include_router(admin_router)
app.include_router(analytics_router)
app.include_router(enterprise_router)


@app.get("/")
def root():
    logger.info("Root health endpoint accessed")

    return {
        "message": "QuoteIQ API is running",
        "project": "AI Quote-to-Order Platform",
        "status": "healthy",
        "database": (
            "SQLite"
            if settings.database_url.startswith("sqlite")
            else "PostgreSQL"
        ),
        "authentication": "JWT",
        "authorization": "Role-Based Access Control",
        "environment": settings.environment,
        "version": settings.app_version,
    }


@app.get("/health")
def health_check():
    logger.info("Health check endpoint accessed")

    return {
        "status": "ok",
        "database": "connected",
        "authentication": "enabled",
        "environment": settings.environment,
    }


@app.get("/catalog")
def get_catalog(
    current_user=Depends(get_current_user),
):
    logger.info(
        "Catalog requested by user %s",
        current_user.email,
    )

    catalog = load_product_catalog()

    return {
        "count": len(catalog),
        "products": catalog,
        "requested_by": current_user.email,
    }


@app.get("/customers")
def get_customers(
    current_user=Depends(get_current_user),
):
    logger.info(
        "Customers requested by user %s",
        current_user.email,
    )

    customers = load_customers()

    return {
        "count": len(customers),
        "customers": customers,
        "requested_by": current_user.email,
    }


@app.post(
    "/rfqs/upload",
    response_model=RFQUploadResponse,
)
async def upload_rfq(
    file: UploadFile = File(...),
    current_user=Depends(
        require_roles(
            "sales_rep",
            "manager",
            "admin",
        )
    ),
):
    logger.info(
        "RFQ file upload by user %s: %s",
        current_user.email,
        file.filename,
    )

    try:
        rfq_text = await extract_text_from_upload(file)
    except RFQUploadError as error:
        record_audit_event(
            actor_email=current_user.email,
            actor_role=current_user.role,
            action="RFQ_UPLOAD_REJECTED",
            entity_type="RFQ_FILE",
            entity_id=file.filename or "unknown",
            status="FAILURE",
            details={"reason": str(error)},
        )
        raise HTTPException(
            status_code=400,
            detail=str(error),
        ) from error

    record_audit_event(
        actor_email=current_user.email,
        actor_role=current_user.role,
        action="RFQ_UPLOADED",
        entity_type="RFQ_FILE",
        entity_id=file.filename or "unknown",
        status="SUCCESS",
        details={"character_count": len(rfq_text)},
    )

    return {
        "filename": file.filename or "unknown",
        "rfq_text": rfq_text,
        "character_count": len(rfq_text),
    }


@app.post(
    "/rfqs/extract",
    response_model=RFQExtractionResponse,
)
def extract_rfq(
    request: RFQRequest,
    current_user=Depends(
        require_roles(
            "sales_rep",
            "manager",
            "admin",
        )
    ),
):
    logger.info(
        "RFQ extraction requested by user %s",
        current_user.email,
    )

    lines = extract_rfq_lines_ai(request.rfq_text)

    return {
        "line_count": len(lines),
        "lines": lines,
    }


@app.post(
    "/match-lines",
    response_model=MatchLinesResponse,
)
def match_lines(
    request: MatchLinesRequest,
    current_user=Depends(
        require_roles(
            "sales_rep",
            "manager",
            "admin",
        )
    ),
):
    logger.info(
        "SKU matching requested by user %s",
        current_user.email,
    )

    catalog = load_product_catalog()

    raw_lines = [
        line.model_dump()
        for line in request.lines
    ]

    matched_lines = match_lines_to_catalog(
        raw_lines,
        catalog,
    )

    return {
        "match_count": len(matched_lines),
        "matched_lines": matched_lines,
    }


@app.post(
    "/price-quote",
    response_model=PriceQuoteResponse,
)
def price_quote_endpoint(
    request: PriceQuoteRequest,
    current_user=Depends(
        require_roles(
            "sales_rep",
            "manager",
            "admin",
        )
    ),
):
    logger.info(
        "Quote pricing requested by user %s for customer %s",
        current_user.email,
        request.customer_id,
    )

    catalog = load_product_catalog()
    customers = load_customers()
    price_rules = load_price_rules()
    margin_policies = load_margin_policies()

    raw_matched_lines = [
        line.model_dump()
        for line in request.matched_lines
    ]

    return price_quote(
        customer_id=request.customer_id,
        matched_lines=raw_matched_lines,
        catalog=catalog,
        customers=customers,
        price_rules=price_rules,
        margin_policies=margin_policies,
    )


@app.post(
    "/rfqs/process",
    response_model=ProcessRFQResponse,
)
def process_rfq(
    request: ProcessRFQRequest,
    current_user=Depends(
        require_roles(
            "sales_rep",
            "manager",
            "admin",
        )
    ),
):
    logger.info(
        "RFQ processing requested by user %s for customer %s",
        current_user.email,
        request.customer_id,
    )

    catalog = load_product_catalog()
    customers = load_customers()
    price_rules = load_price_rules()
    margin_policies = load_margin_policies()

    extracted_lines = extract_rfq_lines_ai(
        request.rfq_text
    )

    matched_lines = match_lines_to_catalog(
        extracted_lines,
        catalog,
    )

    priced_quote = price_quote(
        customer_id=request.customer_id,
        matched_lines=matched_lines,
        catalog=catalog,
        customers=customers,
        price_rules=price_rules,
        margin_policies=margin_policies,
    )

    return {
        "customer_id": priced_quote["customer_id"],
        "customer_name": priced_quote["customer_name"],
        "price_class": priced_quote["price_class"],
        "extracted_line_count": len(extracted_lines),
        "matched_line_count": len(matched_lines),
        "quote_subtotal": priced_quote["subtotal"],
        "estimated_margin_pct": priced_quote[
            "estimated_margin_pct"
        ],
        "risk_count": priced_quote["risk_count"],
        "extracted_lines": extracted_lines,
        "matched_lines": matched_lines,
        "priced_lines": priced_quote["priced_lines"],
    }


@app.post("/rfqs/process-v2")
def process_rfq_v2(
    request: ProcessRFQRequest,
    current_user=Depends(
        require_roles(
            "sales_rep",
            "manager",
            "admin",
        )
    ),
):
    logger.info(
        "RFQ process-v2 requested by user %s for customer %s",
        current_user.email,
        request.customer_id,
    )

    catalog = load_product_catalog()
    customers = load_customers()
    price_rules = load_price_rules()
    margin_policies = load_margin_policies()

    extracted_lines = extract_rfq_lines_ai(
        request.rfq_text
    )

    matched_lines = match_lines_to_catalog(
        extracted_lines,
        catalog,
    )

    priced_quote = price_quote(
        customer_id=request.customer_id,
        matched_lines=matched_lines,
        catalog=catalog,
        customers=customers,
        price_rules=price_rules,
        margin_policies=margin_policies,
    )

    quote_package = build_quote_package(
        customer_id=request.customer_id,
        rfq_text=request.rfq_text,
        extracted_lines=extracted_lines,
        matched_lines=matched_lines,
        priced_quote=priced_quote,
    )

    quote_package["created_by"] = current_user.email

    try:
        saved_quote = save_quote(
            quote_package
        )
    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        ) from error

    record_audit_event(
        actor_email=current_user.email,
        actor_role=current_user.role,
        action="QUOTE_CREATED",
        entity_type="QUOTE",
        entity_id=saved_quote["quote_id"],
        status="SUCCESS",
        details={
            "customer_id": saved_quote["customer_id"],
            "customer_name": saved_quote["customer_name"],
            "quote_subtotal": saved_quote["quote_subtotal"],
            "risk_count": saved_quote["risk_count"],
        },
    )

    logger.info(
        "Quote %s created by user %s",
        saved_quote.get("quote_id"),
        current_user.email,
    )

    return saved_quote


@app.get("/quotes")
def list_quotes_endpoint(
    skip: int = 0,
    limit: int = 50,
    status: str | None = None,
    customer_id: str | None = None,
    created_by: str | None = None,
    search: str | None = None,
    current_user=Depends(get_current_user),
):
    logger.info(
        "Quote list requested by user %s",
        current_user.email,
    )

    # RBAC: sales reps can only ever see their own quotes.
    # A sales_rep-supplied created_by is ignored outright rather
    # than validated, so there is no path where a crafted query
    # param widens visibility beyond the caller's own quotes.
    if current_user.role == "sales_rep":
        effective_created_by = current_user.email
    else:
        effective_created_by = created_by

    quotes, total = list_quotes(
        skip=skip,
        limit=limit,
        status=status,
        customer_id=customer_id,
        created_by=effective_created_by,
        search=search,
    )

    return {
        "count": len(quotes),
        "total": total,
        "skip": skip,
        "limit": limit,
        "quotes": quotes,
    }


@app.get("/quotes/{quote_id}")
def retrieve_quote(
    quote_id: str,
    current_user=Depends(get_current_user),
):
    logger.info(
        "Quote %s requested by user %s",
        quote_id,
        current_user.email,
    )

    quote = get_quote(quote_id)

    if quote is None:
        raise HTTPException(
            status_code=404,
            detail=f"Quote not found: {quote_id}",
        )

    if (
        current_user.role == "sales_rep"
        and quote.get("created_by") != current_user.email
    ):
        raise HTTPException(
            status_code=404,
            detail=f"Quote not found: {quote_id}",
        )

    return quote


@app.post("/quotes/{quote_id}/approve")
def approve_quote_endpoint(
    quote_id: str,
    request: QuoteApprovalRequest,
    current_user=Depends(
        require_roles(
            "manager",
            "admin",
        )
    ),
):
    quote = approve_quote(
        quote_id=quote_id,
        reviewed_by=request.reviewed_by,
    )

    if quote is None:
        raise HTTPException(
            status_code=404,
            detail=f"Quote not found: {quote_id}",
        )

    record_audit_event(
        actor_email=current_user.email,
        actor_role=current_user.role,
        action="QUOTE_APPROVED",
        entity_type="QUOTE",
        entity_id=quote_id,
        status="SUCCESS",
        details={
            "approved_by": quote["approved_by"],
            "quote_status": quote["quote_status"],
        },
    )

    return {
        "message": "Quote approved successfully",
        "quote_id": quote_id,
        "quote_status": quote["quote_status"],
        "approved_by": quote["approved_by"],
        "approved_at": quote["approved_at"],
        "authenticated_user": current_user.email,
        "authenticated_role": current_user.role,
        "erp_status": quote["erp_payload"]["status"],
        "audit_trail": quote["audit_trail"],
    }


@app.post("/quotes/{quote_id}/reject")
def reject_quote_endpoint(
    quote_id: str,
    request: QuoteRejectionRequest,
    current_user=Depends(
        require_roles(
            "manager",
            "admin",
        )
    ),
):
    quote = reject_quote(
        quote_id=quote_id,
        reviewed_by=request.reviewed_by,
        reason=request.reason,
    )

    if quote is None:
        raise HTTPException(
            status_code=404,
            detail=f"Quote not found: {quote_id}",
        )

    record_audit_event(
        actor_email=current_user.email,
        actor_role=current_user.role,
        action="QUOTE_REJECTED",
        entity_type="QUOTE",
        entity_id=quote_id,
        status="SUCCESS",
        details={
            "rejected_by": quote["rejected_by"],
            "reason": quote["rejection_reason"],
        },
    )

    return {
        "message": "Quote rejected successfully",
        "quote_id": quote_id,
        "quote_status": quote["quote_status"],
        "rejected_by": quote["rejected_by"],
        "rejected_at": quote["rejected_at"],
        "rejection_reason": quote["rejection_reason"],
        "authenticated_user": current_user.email,
        "authenticated_role": current_user.role,
        "erp_status": quote["erp_payload"]["status"],
        "audit_trail": quote["audit_trail"],
    }


@app.get("/quotes/{quote_id}/pdf")
def download_quote_pdf(
    quote_id: str,
    current_user=Depends(get_current_user),
):
    quote = get_quote(quote_id)

    if quote is None:
        raise HTTPException(
            status_code=404,
            detail=f"Quote not found: {quote_id}",
        )

    if (
        current_user.role == "sales_rep"
        and quote.get("created_by") != current_user.email
    ):
        raise HTTPException(
            status_code=404,
            detail=f"Quote not found: {quote_id}",
        )

    if quote.get("quote_status") not in {
        "APPROVED",
        "CONVERTED_TO_ORDER",
    }:
        raise HTTPException(
            status_code=400,
            detail=(
                "Quote must be approved "
                "before generating a PDF"
            ),
        )

    pdf_path = generate_quote_pdf(quote)

    record_audit_event(
        actor_email=current_user.email,
        actor_role=current_user.role,
        action="QUOTE_PDF_GENERATED",
        entity_type="QUOTE",
        entity_id=quote_id,
        status="SUCCESS",
    )

    return FileResponse(
        path=str(pdf_path),
        media_type="application/pdf",
        filename=f"{quote_id}.pdf",
    )


@app.get("/quotes/{quote_id}/excel")
def download_quote_excel(
    quote_id: str,
    current_user=Depends(get_current_user),
):
    quote = get_quote(quote_id)

    if quote is None:
        raise HTTPException(
            status_code=404,
            detail=f"Quote not found: {quote_id}",
        )

    if (
        current_user.role == "sales_rep"
        and quote.get("created_by") != current_user.email
    ):
        raise HTTPException(
            status_code=404,
            detail=f"Quote not found: {quote_id}",
        )

    if quote.get("quote_status") not in {
        "APPROVED",
        "CONVERTED_TO_ORDER",
    }:
        raise HTTPException(
            status_code=400,
            detail=(
                "Quote must be approved "
                "before generating an Excel export"
            ),
        )

    excel_path = generate_quote_excel(quote)

    record_audit_event(
        actor_email=current_user.email,
        actor_role=current_user.role,
        action="QUOTE_EXCEL_GENERATED",
        entity_type="QUOTE",
        entity_id=quote_id,
        status="SUCCESS",
    )

    return FileResponse(
        path=str(excel_path),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        filename=f"{quote_id}.xlsx",
    )


@app.post("/quotes/{quote_id}/create-order")
def create_order_endpoint(
    quote_id: str,
    current_user=Depends(
        require_roles(
            "manager",
            "admin",
        )
    ),
):
    quote = get_quote(quote_id)

    if quote is None:
        raise HTTPException(
            status_code=404,
            detail=f"Quote not found: {quote_id}",
        )

    try:
        sales_order = create_sales_order(quote)

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        ) from error

    updated_quote = get_quote(quote_id)

    record_audit_event(
        actor_email=current_user.email,
        actor_role=current_user.role,
        action="SALES_ORDER_CREATED",
        entity_type="SALES_ORDER",
        entity_id=sales_order["sales_order_id"],
        status="SUCCESS",
        details={
            "source_quote_id": quote_id,
            "order_total": sales_order["order_total"],
        },
    )

    return {
        "message": "Sales order created successfully",
        "sales_order": sales_order,
        "created_by": current_user.email,
        "created_by_role": current_user.role,
        "quote_status": updated_quote["quote_status"],
        "erp_status": updated_quote[
            "erp_payload"
        ]["status"],
        "audit_trail": updated_quote["audit_trail"],
    }


@app.get("/orders/{order_id}")
def retrieve_sales_order(
    order_id: str,
    current_user=Depends(get_current_user),
):
    sales_order = get_sales_order(order_id)

    if sales_order is None:
        raise HTTPException(
            status_code=404,
            detail=f"Sales order not found: {order_id}",
        )

    return sales_order