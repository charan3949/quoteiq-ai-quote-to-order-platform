import re


def extract_rfq_lines(rfq_text: str):
    extracted_lines = []

    for line in rfq_text.splitlines():
        cleaned = line.strip()

        if not cleaned:
            continue

        match = re.match(
            r"^(?P<quantity>\d+(?:\.\d+)?)\s+(?P<uom>\w+)?\s*(?P<description>.+)$",
            cleaned,
            re.IGNORECASE
        )

        if match:
            extracted_lines.append({
                "description_raw": match.group("description").strip(),
                "quantity": float(match.group("quantity")),
                "uom_raw": match.group("uom")
            })

    return extracted_lines