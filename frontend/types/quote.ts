export type PricedLine = {
  description_raw: string;
  quantity: number;
  uom_raw: string | null;
  sku: string;
  product_name: string;
  category: string;
  base_cost: number;
  list_price: number;
  unit_price: number;
  line_total: number;
  margin_pct: number;
  pricing_rule_applied: string;
  risk_flag: boolean;
  risk_reason: string | null;
};

export type Quote = {
  quote_id: string;
  quote_status: string;
  customer_id: string;
  customer_name: string;
  price_class: string;
  quote_subtotal: number;
  estimated_margin_pct: number;
  risk_count: number;
  quote_confidence: number;
  extracted_line_count: number;
  matched_line_count: number;
  priced_lines: PricedLine[];
  review_required?: boolean;
  unresolved_line_count?: number;
  pricing_status_message?: string | null;
  created_by?: string | null;
  created_at?: string | null;
  updated_at?: string | null;
  approved_by?: string | null;
  approved_at?: string | null;
  rejected_by?: string | null;
  rejected_at?: string | null;
  rejection_reason?: string | null;
  sales_order_id?: string | null;
};

export type QuoteListResponse = {
  count: number;
  total: number;
  skip: number;
  limit: number;
  quotes: Quote[];
};

export type AuditLog = {
  id: number;
  timestamp: string;
  actor_email: string;
  actor_role: string;
  action: string;
  entity_type: string;
  entity_id: string | null;
  status: string;
  details: string | null;
  request_id: string | null;
};

export type ActiveView = "dashboard" | "analytics" | "quotes" | "rfq" | "customers" | "erp" | "audit" | "revenue" | "sales" | "copilot";

export type DashboardSummary = {
  total_quotes: number;
  pending_quotes: number;
  approved_quotes: number;
  rejected_quotes: number;
  converted_quotes: number;
  revenue: number;
  conversion_rate_pct: number;
  avg_approval_time_hours: number | null;
  avg_quote_value: number;
};

export type TrendPoint = {
  month: string;
  quotes: number;
  revenue: number;
  converted: number;
};

export type TopCustomer = {
  customer_id: string;
  customer_name: string;
  quote_count: number;
  revenue: number;
  approved_count: number;
  approval_rate_pct: number;
};

export type RepPerformance = {
  sales_rep: string;
  quote_count: number;
  revenue: number;
  approved_count: number;
  avg_margin_pct: number;
  conversion_rate_pct: number;
  avg_approval_time_hours: number | null;
};

export type PendingQuoteSummary = {
  quote_id: string;
  customer_name: string;
  quote_subtotal: number;
  risk_count: number;
  created_by: string | null;
  age_hours: number | null;
};

export type Bottlenecks = {
  pending_count: number;
  revenue_at_risk: number;
  oldest_pending: PendingQuoteSummary[];
};

export type CustomerPortfolio = {
  customer_id: string;
  customer_name: string;
  price_class: string;
  branch_id: string;
  credit_status: string;
  quote_count: number;
  approved_count: number;
  revenue: number;
  pipeline: number;
  approval_rate_pct: number;
};

export type EnterpriseOrder = {
  sales_order_id: string;
  source_quote_id: string;
  customer_id: string;
  customer_name: string;
  target_erp: string;
  order_status: string;
  order_total: number;
  line_count: number;
  created_at: string | null;
};

export type QuoteIntelligenceData = {
  quote_id: string;
  recommendation: string;
  risk_level: string;
  confidence_pct: number;
  reasons: string[];
  timeline: Array<{ event: string; timestamp: string | null; details?: string }>;
  line_explanations: unknown[];
  status: string;
};
