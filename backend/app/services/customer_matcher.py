from rapidfuzz import fuzz

import csv
import re
from pathlib import Path

MINIMUM_CUSTOMER_MATCH_SCORE = 80

CUSTOMERS_CSV_PATH = (
    Path(__file__).resolve().parents[3] / "data" / "customers.csv"
)

# Matches common "label: Company Name" patterns seen in real RFQs,
# e.g. "Customer: Desert Ridge Builders", "Buyer: Elena Martinez"
# (buyer is a person, not a company, so we deliberately exclude
# "buyer"/"contact"/"attn" — those are usually a person's name, not
# the company we want to record as the customer).
_LABELED_NAME_PATTERN = re.compile(
    r"^\s*(?:customer|company|client|bill\s*to)\s*:\s*(.+)$",
    re.IGNORECASE | re.MULTILINE,
)

# Matches a standalone, mostly-uppercase line near the top of a
# document that looks like a company header, e.g.
# "NORTHRIDGE INDUSTRIAL SYSTEMS"
_UPPERCASE_HEADER_PATTERN = re.compile(
    r"^[A-Z][A-Z0-9&.,'\- ]{4,60}$"
)


def suggest_customer(rfq_text: str, customers: list[dict]) -> dict | None:
    """
    Looks for a known customer's name anywhere in the RFQ text and
    suggests it if found with high confidence. Returns None if no
    confident match is found — callers should treat that as "let the
    user pick manually," not as an error.
    """
    text_lower = rfq_text.lower()

    best_customer = None
    best_score = -1.0

    for customer in customers:
        customer_name = str(customer.get("customer_name", "")).strip()

        if not customer_name:
            continue

        score = fuzz.partial_ratio(customer_name.lower(), text_lower)

        if score > best_score:
            best_score = score
            best_customer = customer

    if best_customer is None or best_score < MINIMUM_CUSTOMER_MATCH_SCORE:
        return None

    return {
        "customer_id": best_customer.get("customer_id"),
        "customer_name": best_customer.get("customer_name"),
        "match_score": round(float(best_score), 2),
    }


def extract_candidate_company_name(rfq_text: str) -> str | None:
    """
    Best-effort, heuristic extraction of a company name from RFQ
    text when no existing customer matched. This is intentionally
    conservative — it only returns a name when there's a clear
    signal (a "Customer:"-style label, or an all-caps header line),
    and returns None otherwise rather than guessing at arbitrary
    text. A None result means "let the human decide," which is the
    safe default for anything ambiguous.
    """
    labeled_match = _LABELED_NAME_PATTERN.search(rfq_text)
    if labeled_match:
        candidate = labeled_match.group(1).strip()
        # Guard against accidentally capturing a full sentence if the
        # regex over-matched (e.g. a "Customer:" line with trailing
        # commentary) — a real company name is short.
        if 2 <= len(candidate) <= 80:
            return candidate

    for line in rfq_text.splitlines()[:15]:
        stripped = line.strip()
        if _UPPERCASE_HEADER_PATTERN.match(stripped):
            return stripped.title()

    return None


def _generate_next_customer_id(customers: list[dict]) -> str:
    existing_numbers = []

    for customer in customers:
        customer_id = str(customer.get("customer_id", ""))
        match = re.match(r"CUST-(\d+)$", customer_id)
        if match:
            existing_numbers.append(int(match.group(1)))

    next_number = (max(existing_numbers) + 1) if existing_numbers else 1001

    return f"CUST-{next_number}"


def create_new_customer(
    customer_name: str,
    customers: list[dict],
) -> dict:
    """
    Appends a new customer row to customers.csv with a conservative
    default price class, and returns the new record. This is a
    demo-appropriate way to persist new customers discovered from
    RFQ text — a production system would write to a real database
    with proper validation and deduplication, not a flat CSV file.
    """
    new_customer_id = _generate_next_customer_id(customers)

    new_row = {
        "customer_id": new_customer_id,
        "customer_name": customer_name,
        "price_class": "RETAIL",
        "branch_id": "PHX01",
        "credit_status": "PENDING_REVIEW",
    }

    file_exists = CUSTOMERS_CSV_PATH.exists()

    # Guard against a missing trailing newline on the existing file —
    # without this, appending would glue the new row onto the end of
    # the last existing line instead of starting a new one, silently
    # corrupting the CSV (this happened during testing; worth keeping
    # this check permanently since a hand-edited CSV could easily lack
    # a trailing newline again in the future).
    if file_exists:
        with open(CUSTOMERS_CSV_PATH, "rb") as f:
            f.seek(-1, 2)
            last_byte = f.read(1)
        needs_newline = last_byte not in (b"\n", b"")
    else:
        needs_newline = False

    with open(CUSTOMERS_CSV_PATH, "a", newline="", encoding="utf-8") as f:
        if needs_newline:
            f.write("\n")

        writer = csv.DictWriter(
            f,
            fieldnames=[
                "customer_id",
                "customer_name",
                "price_class",
                "branch_id",
                "credit_status",
            ],
        )
        if not file_exists:
            writer.writeheader()
        writer.writerow(new_row)

    return new_row


def suggest_or_create_customer(
    rfq_text: str,
    customers: list[dict],
) -> dict:
    """
    Full pipeline: try to match an existing customer first. If none
    matches confidently, try to extract a company name from the text
    and auto-create a new customer record. If neither succeeds,
    return a result indicating manual selection is required.
    """
    existing_match = suggest_customer(rfq_text, customers)

    if existing_match is not None:
        return {
            **existing_match,
            "is_new_customer": False,
        }

    candidate_name = extract_candidate_company_name(rfq_text)

    if candidate_name is None:
        return {
            "customer_id": None,
            "customer_name": None,
            "match_score": None,
            "is_new_customer": False,
        }

    new_customer = create_new_customer(candidate_name, customers)

    return {
        "customer_id": new_customer["customer_id"],
        "customer_name": new_customer["customer_name"],
        "match_score": None,
        "is_new_customer": True,
    }