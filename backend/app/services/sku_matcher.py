from rapidfuzz import fuzz


def _build_search_text(product: dict) -> str:
    return " ".join([
        str(product.get("sku", "")),
        str(product.get("product_name", "")),
        str(product.get("category", "")),
        str(product.get("description", "")),
        str(product.get("brand", "")),
    ]).lower()


def _confidence_label(score: float) -> str:
    if score >= 85:
        return "high"
    if score >= 65:
        return "medium"
    return "low"


MINIMUM_MATCH_SCORE = 55


def match_line_to_catalog(line: dict, catalog: list[dict]) -> dict:
    query = str(line["description_raw"]).lower()

    best_product = None
    best_score = -1

    for product in catalog:
        search_text = _build_search_text(product)

        score = max(
            fuzz.token_set_ratio(query, search_text),
            fuzz.partial_ratio(query, search_text),
            fuzz.WRatio(query, search_text)
        )

        if score > best_score:
            best_score = score
            best_product = product

    if best_product is None or best_score < MINIMUM_MATCH_SCORE:
        return {
            "description_raw": line["description_raw"],
            "quantity": line.get("quantity"),
            "uom_raw": line.get("uom_raw"),
            "matched_sku": None,
            "matched_product_name": None,
            "matched_category": None,
            "match_score": round(float(best_score), 2) if best_product else 0.0,
            "match_confidence": "unmatched"
        }

    return {
        "description_raw": line["description_raw"],
        "quantity": line.get("quantity"),
        "uom_raw": line.get("uom_raw"),
        "matched_sku": best_product["sku"],
        "matched_product_name": best_product["product_name"],
        "matched_category": best_product["category"],
        "match_score": round(float(best_score), 2),
        "match_confidence": _confidence_label(float(best_score))
    }


def match_lines_to_catalog(lines: list[dict], catalog: list[dict]) -> list[dict]:
    return [match_line_to_catalog(line, catalog) for line in lines]
