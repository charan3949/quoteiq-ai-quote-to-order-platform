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

export type ActiveView = "dashboard" | "rfq" | "audit";