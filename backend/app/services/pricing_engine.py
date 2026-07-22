import math


def _is_blank(value) -> bool:
    if value is None:
        return True

    if isinstance(value, float) and math.isnan(value):
        return True

    if str(value).strip() == "":
        return True

    if str(value).strip().lower() == "nan":
        return True

    return False


def _clean(value):
    if _is_blank(value):
        return None

    return str(value).strip()


def _safe_float(value, default=0.0) -> float:
    if _is_blank(value):
        return default

    return float(value)


def _find_customer(
    customer_id: str,
    customers: list[dict]
) -> dict:
    for customer in customers:
        if _clean(customer.get("customer_id")) == customer_id:
            return customer

    raise ValueError(f"Customer not found: {customer_id}")


def _find_product(
    sku: str,
    catalog: list[dict]
) -> dict:
    for product in catalog:
        if _clean(product.get("sku")) == sku:
            return product

    raise ValueError(f"Product not found: {sku}")


def _matches_rule_value(
    rule_value,
    target_value
) -> bool:
    cleaned_rule_value = _clean(rule_value)

    if cleaned_rule_value is None:
        return True

    return cleaned_rule_value == str(target_value)


def _find_applicable_price_rule(
    customer: dict,
    product: dict,
    price_rules: list[dict]
) -> dict | None:
    customer_id = _clean(customer.get("customer_id"))
    price_class = _clean(customer.get("price_class"))
    sku = _clean(product.get("sku"))
    category = _clean(product.get("category"))

    candidates = []

    for rule in price_rules:
        if not _matches_rule_value(
            rule.get("customer_id"),
            customer_id
        ):
            continue

        if not _matches_rule_value(
            rule.get("price_class"),
            price_class
        ):
            continue

        if not _matches_rule_value(
            rule.get("sku"),
            sku
        ):
            continue

        if not _matches_rule_value(
            rule.get("category"),
            category
        ):
            continue

        candidates.append(rule)

    if not candidates:
        return None

    candidates.sort(
        key=lambda rule: int(
            _safe_float(
                rule.get("priority"),
                999
            )
        )
    )

    return candidates[0]


def _apply_price_rule(
    list_price: float,
    rule: dict | None
) -> tuple[float, str]:
    if rule is None:
        return list_price, "list_price"

    rule_type = _clean(rule.get("rule_type"))
    rule_value = _safe_float(rule.get("rule_value"))
    rule_id = _clean(rule.get("rule_id")) or "unknown_rule"

    if rule_type == "fixed_price":
        return (
            rule_value,
            f"fixed_price:{rule_id}"
        )

    if rule_type == "discount_pct":
        unit_price = list_price * (
            1 - rule_value / 100
        )

        return (
            unit_price,
            f"discount_pct:{rule_id}"
        )

    return list_price, "list_price"


def _find_margin_policy(
    customer: dict,
    product: dict,
    margin_policies: list[dict]
) -> dict | None:
    price_class = _clean(
        customer.get("price_class")
    )

    category = _clean(
        product.get("category")
    )

    for policy in margin_policies:
        policy_category = _clean(
            policy.get("category")
        )

        policy_price_class = _clean(
            policy.get("price_class")
        )

        if (
            policy_category == category
            and policy_price_class == price_class
        ):
            return policy

    return None


def _calculate_margin_pct(
    unit_price: float,
    base_cost: float
) -> float:
    if unit_price <= 0:
        return 0.0

    return (
        (unit_price - base_cost)
        / unit_price
    ) * 100


def price_quote(
    customer_id: str,
    matched_lines: list[dict],
    catalog: list[dict],
    customers: list[dict],
    price_rules: list[dict],
    margin_policies: list[dict],
) -> dict:
    customer = _find_customer(
        customer_id,
        customers
    )

    priced_lines = []
    subtotal = 0.0
    total_revenue = 0.0
    total_cost = 0.0
    risk_count = 0

    for line in matched_lines:
        quantity = _safe_float(
            line.get("quantity")
        )

        if line.get("matched_sku") is None:
            risk_count += 1

            priced_lines.append({
                "description_raw": line["description_raw"],
                "quantity": quantity,
                "uom_raw": line.get("uom_raw"),
                "sku": None,
                "product_name": "UNMATCHED - manual review required",
                "category": None,
                "base_cost": 0.0,
                "list_price": 0.0,
                "unit_price": 0.0,
                "line_total": 0.0,
                "margin_pct": 0.0,
                "pricing_rule_applied": "unmatched",
                "risk_flag": True,
                "risk_reason": (
                    "No confident catalog match was found for this "
                    "line. A team member must manually select the "
                    "correct SKU before this line can be priced."
                )
            })

            continue

        product = _find_product(
            line["matched_sku"],
            catalog
        )

        base_cost = _safe_float(
            product.get("base_cost")
        )

        list_price = _safe_float(
            product.get("list_price")
        )

        rule = _find_applicable_price_rule(
            customer,
            product,
            price_rules
        )

        unit_price, rule_label = _apply_price_rule(
            list_price,
            rule
        )

        line_total = unit_price * quantity
        line_cost = base_cost * quantity

        margin_pct = _calculate_margin_pct(
            unit_price,
            base_cost
        )

        policy = _find_margin_policy(
            customer,
            product,
            margin_policies
        )

        risk_flag = False
        risk_reason = None

        if policy:
            floor_margin_pct = _safe_float(
                policy.get("floor_margin_pct")
            )

            if margin_pct < floor_margin_pct:
                risk_flag = True

                risk_reason = (
                    f"Margin {margin_pct:.2f}% is below "
                    f"floor {floor_margin_pct:.2f}% for "
                    f"{_clean(product.get('category'))} / "
                    f"{_clean(customer.get('price_class'))}"
                )

        if line.get("match_confidence") != "high":
            risk_flag = True
            risk_reason = (
                "Low or medium SKU match confidence "
                "requires human review"
            )

        if risk_flag:
            risk_count += 1

        priced_lines.append({
            "description_raw": line["description_raw"],
            "quantity": quantity,
            "uom_raw": line.get("uom_raw"),
            "sku": _clean(product.get("sku")),
            "product_name": _clean(
                product.get("product_name")
            ),
            "category": _clean(
                product.get("category")
            ),
            "base_cost": round(base_cost, 2),
            "list_price": round(list_price, 2),
            "unit_price": round(unit_price, 2),
            "line_total": round(line_total, 2),
            "margin_pct": round(margin_pct, 2),
            "pricing_rule_applied": rule_label,
            "risk_flag": risk_flag,
            "risk_reason": risk_reason
        })

        subtotal += line_total
        total_revenue += line_total
        total_cost += line_cost

    estimated_margin_pct = 0.0

    if total_revenue > 0:
        estimated_margin_pct = (
            (total_revenue - total_cost)
            / total_revenue
        ) * 100

    return {
        "customer_id": _clean(
            customer.get("customer_id")
        ),
        "customer_name": _clean(
            customer.get("customer_name")
        ),
        "price_class": _clean(
            customer.get("price_class")
        ),
        "line_count": len(priced_lines),
        "subtotal": round(subtotal, 2),
        "estimated_margin_pct": round(
            estimated_margin_pct,
            2
        ),
        "risk_count": risk_count,
        "priced_lines": priced_lines
    }
