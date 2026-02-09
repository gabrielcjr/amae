import io
from collections import OrderedDict
from datetime import date
from decimal import Decimal

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from .models import TransactionType
from .receipt import MONTHS_PT, _fmt_brl


def generate_general_report_pdf(queryset, expense, filters_description=""):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=2 * cm,
        rightMargin=2 * cm,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
    )

    styles = getSampleStyleSheet()
    story = []

    # --- Header ---
    header_style = ParagraphStyle(
        "gen_header",
        parent=styles["Title"],
        fontSize=14,
        spaceAfter=2,
        alignment=1,
    )
    sub_style = ParagraphStyle(
        "gen_sub",
        parent=styles["Normal"],
        fontSize=8,
        alignment=1,
        textColor=colors.grey,
        spaceAfter=1,
    )

    story.append(Paragraph("AGÊNCIA MISSIONÁRIA DE AMPARO AOS EXCLUÍDOS", header_style))
    story.append(
        Paragraph(
            "CNPJ: 55.934.659/0001-07 &nbsp;|&nbsp; "
            "AG. 3128-3 &nbsp;|&nbsp; C/C. 109.277-4 &nbsp;|&nbsp; "
            "Banco do Brasil",
            sub_style,
        )
    )
    story.append(Spacer(1, 0.3 * cm))

    # --- Title ---
    title_style = ParagraphStyle(
        "gen_title",
        parent=styles["Heading2"],
        fontSize=12,
        alignment=1,
        spaceAfter=4,
    )
    story.append(Paragraph("RELATÓRIO GERAL", title_style))

    if filters_description:
        filter_style = ParagraphStyle(
            "gen_filters",
            parent=styles["Normal"],
            fontSize=9,
            alignment=1,
            textColor=colors.HexColor("#555555"),
            spaceAfter=6,
        )
        story.append(Paragraph(filters_description, filter_style))

    story.append(Spacer(1, 0.4 * cm))

    # --- Expense items grouped by category ---
    section_style = ParagraphStyle(
        "gen_section",
        parent=styles["Heading3"],
        fontSize=11,
        spaceAfter=8,
    )
    story.append(Paragraph("INVESTIMENTOS (DESPESAS)", section_style))

    expense_qs = queryset.filter(type=TransactionType.EXPENSE).select_related(
        "category", "adoption__mission_field"
    )

    # Group by mission field name (via adoption → missionary → mission_fields)
    groups = OrderedDict()
    for tx in expense_qs.order_by("date"):
        group_name = _get_mission_field_label(tx)
        if group_name not in groups:
            groups[group_name] = {
                "total": Decimal("0"),
                "descriptions": [],
            }
        groups[group_name]["total"] += tx.amount
        desc = tx.description.strip()
        if desc and desc not in groups[group_name]["descriptions"]:
            groups[group_name]["descriptions"].append(desc)

    item_style = ParagraphStyle(
        "gen_item",
        parent=styles["Normal"],
        fontSize=10,
        leading=14,
        spaceBefore=2,
        spaceAfter=2,
    )

    # Numbered expense items
    data = []
    for i, (group_name, info) in enumerate(groups.items(), 1):
        label = f"<b>{i}) {group_name.upper()}</b>"
        if info["descriptions"]:
            details = ", ".join(info["descriptions"])
            label += f" ({details})"
        label += f" - <b>{_fmt_brl(info['total'])}</b>"
        data.append([Paragraph(label, item_style)])

    if data:
        item_table = Table(data, colWidths=[None])
        item_table.setStyle(
            TableStyle(
                [
                    ("TOPPADDING", (0, 0), (-1, -1), 4),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                    ("LEFTPADDING", (0, 0), (-1, -1), 8),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                    (
                        "ROWBACKGROUNDS",
                        (0, 0),
                        (-1, -1),
                        [colors.white, colors.HexColor("#f8f9fa")],
                    ),
                ]
            )
        )
        story.append(item_table)
    else:
        story.append(Paragraph("Nenhuma despesa encontrada.", item_style))

    story.append(Spacer(1, 0.5 * cm))

    # --- Grand total ---
    total_style = ParagraphStyle(
        "gen_total",
        parent=styles["Normal"],
        fontSize=11,
        spaceBefore=4,
    )

    # Build period label from filters or use current month
    period_label = _build_period_label(queryset)

    story.append(
        Paragraph(
            f"<b>TOTAL DE INVESTIMENTOS {period_label}" f" - {_fmt_brl(expense)}</b>",
            total_style,
        )
    )

    # --- Footer ---
    story.append(Spacer(1, 1 * cm))
    today = date.today()
    footer_text = (
        f"Relatório gerado em {today.day:02d} de "
        f"{MONTHS_PT[today.month]} de {today.year}"
    )
    footer_style = ParagraphStyle(
        "gen_footer",
        parent=styles["Normal"],
        fontSize=8,
        textColor=colors.grey,
        alignment=2,
    )
    story.append(Paragraph(footer_text, footer_style))

    doc.build(story)
    buffer.seek(0)
    return buffer


def _get_mission_field_label(transaction):
    """Derive a group label: category name + country from adoption's mission field."""
    category = transaction.category.name
    if transaction.adoption and transaction.adoption.mission_field:
        return f"{category} {transaction.adoption.mission_field.get_country_display()}"
    return category


def _build_period_label(queryset):
    """Build a period label like 'EM DEZEMBRO/2025' from the queryset."""
    months = queryset.values_list("reference_month", flat=True).distinct()
    years = queryset.values_list("reference_year", flat=True).distinct()
    month_list = sorted(set(months))
    year_list = sorted(set(years))

    if len(month_list) == 1 and len(year_list) == 1:
        month_name = MONTHS_PT[month_list[0]].upper()
        return f"EM {month_name}/{year_list[0]}"
    elif len(year_list) == 1:
        return f"EM {year_list[0]}"
    return ""
