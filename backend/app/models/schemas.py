from pydantic import BaseModel, Field
from typing import List, Optional


class RFQRequest(BaseModel):
    rfq_text: str


class RFQUploadResponse(BaseModel):
    filename: str
    rfq_text: str
    character_count: int
    suggested_customer_id: Optional[str] = None
    suggested_customer_name: Optional[str] = None
    suggested_customer_match_score: Optional[float] = None
    is_new_customer: Optional[bool] = None


class ExtractedLineItem(BaseModel):
    description_raw: str
    quantity: float
    uom_raw: Optional[str] = None
    customer_part_number: Optional[str] = None
    requirements: Optional[str] = None
    confidence: Optional[str] = None
    needs_review: Optional[bool] = None
    extraction_method: Optional[str] = None


class RFQExtractionResponse(BaseModel):
    line_count: int
    lines: List[ExtractedLineItem]


class MatchLinesRequest(BaseModel):
    lines: List[ExtractedLineItem]


class MatchedLineItem(BaseModel):
    description_raw: str
    quantity: float
    uom_raw: Optional[str] = None
    matched_sku: str
    matched_product_name: str
    matched_category: str
    match_score: float
    match_confidence: str


class MatchLinesResponse(BaseModel):
    match_count: int
    matched_lines: List[MatchedLineItem]


class PriceQuoteRequest(BaseModel):
    customer_id: str
    matched_lines: List[MatchedLineItem]


class PricedLineItem(BaseModel):
    description_raw: str
    quantity: float
    uom_raw: Optional[str] = None
    sku: str
    product_name: str
    category: str
    base_cost: float
    list_price: float
    unit_price: float
    line_total: float
    margin_pct: float
    pricing_rule_applied: str
    risk_flag: bool
    risk_reason: Optional[str] = None


class PriceQuoteResponse(BaseModel):
    customer_id: str
    customer_name: str
    price_class: str
    line_count: int
    subtotal: float
    estimated_margin_pct: float
    risk_count: int
    priced_lines: List[PricedLineItem]


class ProcessRFQRequest(BaseModel):
    customer_id: str
    rfq_text: str


class ProcessRFQResponse(BaseModel):
    customer_id: str
    customer_name: str
    price_class: str
    extracted_line_count: int
    matched_line_count: int
    quote_subtotal: float
    estimated_margin_pct: float
    risk_count: int
    extracted_lines: List[ExtractedLineItem]
    matched_lines: List[MatchedLineItem]
    priced_lines: List[PricedLineItem]


class QuoteApprovalRequest(BaseModel):
    reviewed_by: str


class QuoteRejectionRequest(BaseModel):
    reviewed_by: str
    reason: str


class UserRegisterRequest(BaseModel):
    email: str
    full_name: str
    password: str
    role: str = "sales_rep"


class UserLoginRequest(BaseModel):
    email: str
    password: str


class UserResponse(BaseModel):
    id: int
    email: str
    full_name: str
    role: str
    is_active: bool


class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    expires_in_minutes: int


class CurrentUserResponse(BaseModel):
    email: str
    full_name: str
    role: str


class CopilotMessage(BaseModel):
    role: str
    content: str


class CopilotRequest(BaseModel):
    message: str
    quote_id: Optional[str] = None
    history: List[CopilotMessage] = Field(default_factory=list)


class CopilotUsage(BaseModel):
    input_tokens: Optional[int] = None
    output_tokens: Optional[int] = None
    total_tokens: Optional[int] = None


class CopilotResponse(BaseModel):
    answer: str
    quote_id: Optional[str] = None
    model: str
    usage: CopilotUsage
    grounded: bool
    disclaimer: str
