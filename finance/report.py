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
from .receipt import MONTHS_PT, format_brl


def _build_report_styles():
    styles = getSampleStyleSheet()
    return {
        "header": ParagraphStyle(
            "gen_header",
            parent=styles["Title"],
            fontSize=14,
            spaceAfter=2,
            alignment=1,
        ),
        "sub": ParagraphStyle(
            "gen_sub",
            parent=styles["Normal"],
            fontSize=8,
            alignment=1,
            textColor=colors.grey,
            spaceAfter=1,
        ),
        "title": ParagraphStyle(
            "gen_title",
            parent=styles["Heading2"],
            fontSize=12,
            alignment=1,
            spaceAfter=4,
        ),
        "filter": ParagraphStyle(
            "gen_filters",
            parent=styles["Normal"],
            fontSize=9,
            alignment=1,
            textColor=colors.HexColor("#555555"),
            spaceAfter=6,
        ),
        "section": ParagraphStyle(
            "gen_section",
            parent=styles["Heading3"],
            fontSize=11,
            spaceAfter=8,
        ),
        "item": ParagraphStyle(
            "gen_item",
            parent=styles["Normal"],
            fontSize=10,
            leading=14,
            spaceBefore=2,
            spaceAfter=2,
        ),
        "total": ParagraphStyle(
            "gen_total",
            parent=styles["Normal"],
            fontSize=11,
            spaceBefore=4,
        ),
        "footer": ParagraphStyle(
            "gen_footer",
            parent=styles["Normal"],
            fontSize=8,
            textColor=colors.grey,
            alignment=2,
        ),
    }


def _build_header_elements(report_styles):
    return [
        Paragraph(
            "AGÊNCIA MISSIONÁRIA DE AMPARO AOS EXCLUÍDOS",
            report_styles["header"],
        ),
        Paragraph(
            "CNPJ: 55.934.659/0001-07 &nbsp;|&nbsp; "
            "AG. 3128-3 &nbsp;|&nbsp; C/C. 109.277-4 &nbsp;|&nbsp; "
            "Banco do Brasil",
            report_styles["sub"],
        ),
        Spacer(1, 0.3 * cm),
        Paragraph("RELATÓRIO GERAL", report_styles["title"]),
    ]


def _build_expense_groups(queryset):
    expense_qs = queryset.filter(type=TransactionType.EXPENSE).select_related(
        "category", "adoption__mission_field"
    )

    groups = OrderedDict()
    for transaction in expense_qs.order_by("date"):
        group_name = _get_mission_field_label(transaction)
        if group_name not in groups:
            groups[group_name] = {
                "total": Decimal("0"),
                "descriptions": [],
            }
        groups[group_name]["total"] += transaction.amount
        desc = transaction.description.strip()
        if desc and desc not in groups[group_name]["descriptions"]:
            groups[group_name]["descriptions"].append(desc)

    return groups


def _build_expense_table(groups, item_style):
    data = []
    for index, (group_name, group_data) in enumerate(groups.items(), 1):
        label = f"<b>{index}) {group_name.upper()}</b>"
        if group_data["descriptions"]:
            details = ", ".join(group_data["descriptions"])
            label += f" ({details})"
        label += f" - <b>{format_brl(group_data['total'])}</b>"
        data.append([Paragraph(label, item_style)])

    if not data:
        return [Paragraph("Nenhuma despesa encontrada.", item_style)]

    table = Table(data, colWidths=[None])
    table.setStyle(
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
    return [table]


def _build_footer(report_styles):
    today = date.today()
    footer_text = (
        f"Relatório gerado em {today.day:02d} de "
        f"{MONTHS_PT[today.month]} de {today.year}"
    )
    return Paragraph(footer_text, report_styles["footer"])


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

    report_styles = _build_report_styles()
    story = _build_header_elements(report_styles)

    if filters_description:
        story.append(Paragraph(filters_description, report_styles["filter"]))

    story.append(Spacer(1, 0.4 * cm))
    story.append(Paragraph("INVESTIMENTOS (DESPESAS)", report_styles["section"]))

    groups = _build_expense_groups(queryset)
    story.extend(_build_expense_table(groups, report_styles["item"]))

    story.append(Spacer(1, 0.5 * cm))

    period_label = _build_period_label(queryset)
    story.append(
        Paragraph(
            f"<b>TOTAL DE INVESTIMENTOS {period_label} - {format_brl(expense)}</b>",
            report_styles["total"],
        )
    )

    story.append(Spacer(1, 1 * cm))
    story.append(_build_footer(report_styles))

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
