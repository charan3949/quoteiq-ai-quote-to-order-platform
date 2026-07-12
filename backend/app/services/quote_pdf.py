from pathlib import Path
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    KeepTogether,
)


BASE_DIR = Path(__file__).resolve().parents[3]
OUTPUT_DIR = BASE_DIR / "generated_quotes"


def _money(value: float) -> str:
    return f"${float(value):,.2f}"


def _safe_text(value) -> str:
    if value is None:
        return ""
    return escape(str(value))


def generate_quote_pdf(quote: dict) -> Path:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    quote_id = quote["quote_id"]
    output_path = OUTPUT_DIR / f"{quote_id}.pdf"

    document = SimpleDocTemplate(
        str(output_path),
        pagesize=LETTER,
        rightMargin=0.55 * inch,
        leftMargin=0.55 * inch,
        topMargin=0.55 * inch,
        bottomMargin=0.55 * inch,
        title=f"Quote {quote_id}",
        author="QuoteIQ"
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "QuoteTitle",
        parent=styles["Title"],
        fontSize=22,
        leading=26,
        alignment=TA_LEFT,
        spaceAfter=4
    )

    company_style = ParagraphStyle(
        "CompanyName",
        parent=styles["Heading2"],
        fontSize=13,
        leading=16,
        spaceAfter=2
    )

    label_style = ParagraphStyle(
        "Label",
        parent=styles["Normal"],
        fontSize=8,
        leading=10,
        textColor=colors.HexColor("#5B6472")
    )

    value_style = ParagraphStyle(
        "Value",
        parent=styles["Normal"],
        fontSize=10,
        leading=13
    )

    small_style = ParagraphStyle(
        "Small",
        parent=styles["Normal"],
        fontSize=8,
        leading=11,
        textColor=colors.HexColor("#5B6472")
    )

    right_value_style = ParagraphStyle(
        "RightValue",
        parent=value_style,
        alignment=TA_RIGHT
    )

    story = []

    header_data = [
        [
            Paragraph("QuoteIQ", title_style),
            Paragraph(
                f"<b>QUOTE</b><br/>{_safe_text(quote_id)}",
                right_value_style
            )
        ]
    ]

    header_table = Table(
        header_data,
        colWidths=[4.7 * inch, 2.0 * inch]
    )

    header_table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LINEBELOW", (0, 0), (-1, -1), 1.5, colors.HexColor("#1E293B")),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10)
    ]))

    story.append(header_table)
    story.append(Spacer(1, 12))

    customer_data = [
        [
            Paragraph("PREPARED FOR", label_style),
            Paragraph("QUOTE STATUS", label_style),
            Paragraph("CONFIDENCE", label_style)
        ],
        [
            Paragraph(
                f"<b>{_safe_text(quote['customer_name'])}</b><br/>"
                f"Customer ID: {_safe_text(quote['customer_id'])}<br/>"
                f"Price class: {_safe_text(quote['price_class'])}",
                value_style
            ),
            Paragraph(
                f"<b>{_safe_text(quote['quote_status'])}</b>",
                value_style
            ),
            Paragraph(
                f"<b>{quote['quote_confidence']:.0f}%</b>",
                value_style
            )
        ]
    ]

    customer_table = Table(
        customer_data,
        colWidths=[3.7 * inch, 1.8 * inch, 1.2 * inch]
    )

    customer_table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#F1F5F9")),
        ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7)
    ]))

    story.append(customer_table)
    story.append(Spacer(1, 18))

    story.append(Paragraph("Quoted Materials", company_style))
    story.append(Spacer(1, 5))

    item_data = [
        [
            Paragraph("<b>SKU</b>", small_style),
            Paragraph("<b>Description</b>", small_style),
            Paragraph("<b>Qty</b>", small_style),
            Paragraph("<b>UOM</b>", small_style),
            Paragraph("<b>Unit Price</b>", small_style),
            Paragraph("<b>Total</b>", small_style)
        ]
    ]

    for line in quote["priced_lines"]:
        item_data.append([
            Paragraph(_safe_text(line["sku"]), small_style),
            Paragraph(_safe_text(line["product_name"]), small_style),
            Paragraph(str(line["quantity"]), small_style),
            Paragraph(_safe_text(line.get("uom_raw")), small_style),
            Paragraph(_money(line["unit_price"]), small_style),
            Paragraph(_money(line["line_total"]), small_style)
        ])

    items_table = Table(
        item_data,
        repeatRows=1,
        colWidths=[
            1.25 * inch,
            2.35 * inch,
            0.5 * inch,
            0.55 * inch,
            0.85 * inch,
            0.9 * inch
        ]
    )

    items_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1E293B")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN", (2, 1), (-1, -1), "RIGHT"),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#CBD5E1")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [
            colors.white,
            colors.HexColor("#F8FAFC")
        ]),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7)
    ]))

    story.append(items_table)
    story.append(Spacer(1, 12))

    summary_data = [
        [
            "",
            Paragraph("Subtotal", right_value_style),
            Paragraph(
                f"<b>{_money(quote['quote_subtotal'])}</b>",
                right_value_style
            )
        ]
    ]

    summary_table = Table(
        summary_data,
        colWidths=[4.7 * inch, 1.0 * inch, 1.0 * inch]
    )

    summary_table.setStyle(TableStyle([
        ("LINEABOVE", (1, 0), (-1, 0), 1, colors.HexColor("#1E293B")),
        ("TOPPADDING", (0, 0), (-1, -1), 8)
    ]))

    story.append(summary_table)
    story.append(Spacer(1, 18))

    notes = [
        Paragraph("Quote Details", company_style),
        Paragraph(
            f"Estimated gross margin: "
            f"<b>{quote['estimated_margin_pct']:.2f}%</b>",
            value_style
        ),
        Paragraph(
            f"Review required: "
            f"<b>{'Yes' if quote['review_required'] else 'No'}</b>",
            value_style
        ),
        Paragraph(
            "This quote was prepared using QuoteIQ's RFQ extraction, "
            "catalog matching, customer pricing, margin validation and "
            "human approval workflow.",
            small_style
        )
    ]

    story.append(KeepTogether(notes))
    story.append(Spacer(1, 18))

    story.append(Paragraph(
        "Thank you for the opportunity to provide this quote.",
        value_style
    ))

    document.build(story)

    return output_path