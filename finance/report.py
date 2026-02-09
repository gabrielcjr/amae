import io
from collections import OrderedDict
from datetime import date
from decimal import Decimal

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from .models import TransactionType
from .receipt import MONTHS_PT, _fmt_brl


def generate_report_pdf(queryset, income, expense, balance, filters_description=""):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=landscape(A4),
        leftMargin=1.5 * cm,
        rightMargin=1.5 * cm,
        topMargin=1.5 * cm,
        bottomMargin=1.5 * cm,
    )

    styles = getSampleStyleSheet()
    story = []

    # --- Header ---
    header_style = ParagraphStyle(
        "header",
        parent=styles["Title"],
        fontSize=14,
        spaceAfter=2,
        alignment=1,
    )
    sub_style = ParagraphStyle(
        "sub",
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
            "AG. 3128-3 &nbsp;|&nbsp; C/C. 109.277-4 &nbsp;|&nbsp; Banco do Brasil",
            sub_style,
        )
    )
    story.append(Spacer(1, 0.3 * cm))

    # --- Title ---
    title_style = ParagraphStyle(
        "report_title",
        parent=styles["Heading2"],
        fontSize=12,
        alignment=1,
        spaceAfter=4,
    )
    story.append(Paragraph("RELATÓRIO FINANCEIRO", title_style))

    if filters_description:
        filter_style = ParagraphStyle(
            "filters",
            parent=styles["Normal"],
            fontSize=9,
            alignment=1,
            textColor=colors.HexColor("#555555"),
            spaceAfter=6,
        )
        story.append(Paragraph(filters_description, filter_style))

    story.append(Spacer(1, 0.3 * cm))

    # --- Summary ---
    balance_color = "#28a745" if balance >= 0 else "#dc3545"
    summary_data = [
        [
            Paragraph(
                f'<b>Receitas:</b> <font color="#28a745">{_fmt_brl(income)}</font>',
                styles["Normal"],
            ),
            Paragraph(
                f'<b>Despesas:</b> <font color="#dc3545">{_fmt_brl(expense)}</font>',
                styles["Normal"],
            ),
            Paragraph(
                f'<b>Saldo:</b> <font color="{balance_color}">'
                f"{_fmt_brl(balance)}</font>",
                styles["Normal"],
            ),
        ]
    ]
    summary_table = Table(summary_data, colWidths=[None, None, None])
    summary_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f8f9fa")),
                ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#dee2e6")),
                ("TOPPADDING", (0, 0), (-1, -1), 8),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                ("LEFTPADDING", (0, 0), (-1, -1), 12),
                ("RIGHTPADDING", (0, 0), (-1, -1), 12),
            ]
        )
    )
    story.append(summary_table)
    story.append(Spacer(1, 0.4 * cm))

    # --- Transaction table ---
    header_row = [
        "Data",
        "Tipo",
        "Categoria",
        "Descrição",
        "Igreja",
        "Missionário",
        "Ref.",
        "Valor",
    ]

    cell_style = ParagraphStyle("cell", parent=styles["Normal"], fontSize=8, leading=10)
    header_para_style = ParagraphStyle(
        "header_cell",
        parent=styles["Normal"],
        fontSize=8,
        leading=10,
        textColor=colors.white,
    )

    data = [[Paragraph(h, header_para_style) for h in header_row]]

    transactions = queryset.select_related(
        "category", "adoption__church", "adoption__missionary"
    )
    for tx in transactions:
        church = tx.adoption.church.name if tx.adoption else "-"
        missionary = tx.adoption.missionary.name if tx.adoption else "-"
        sign = "+" if tx.type == TransactionType.INCOME else "-"
        amount_str = (
            f"{sign} R$ {tx.amount:,.2f}".replace(",", "X")
            .replace(".", ",")
            .replace("X", ".")
        )
        ref = f"{tx.reference_month:02d}/{tx.reference_year}"

        data.append(
            [
                Paragraph(tx.date.strftime("%d/%m/%Y"), cell_style),
                Paragraph(tx.get_type_display(), cell_style),
                Paragraph(str(tx.category), cell_style),
                Paragraph(tx.description[:50], cell_style),
                Paragraph(church, cell_style),
                Paragraph(missionary, cell_style),
                Paragraph(ref, cell_style),
                Paragraph(amount_str, cell_style),
            ]
        )

    col_widths = [
        2.0 * cm,  # Data
        1.8 * cm,  # Tipo
        3.0 * cm,  # Categoria
        5.5 * cm,  # Descrição
        4.0 * cm,  # Igreja
        4.0 * cm,  # Missionário
        2.0 * cm,  # Ref.
        3.0 * cm,  # Valor
    ]

    table = Table(data, colWidths=col_widths, repeatRows=1)
    table.setStyle(
        TableStyle(
            [
                # Header
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#343a40")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTSIZE", (0, 0), (-1, 0), 8),
                # Body
                ("FONTSIZE", (0, 1), (-1, -1), 8),
                (
                    "ROWBACKGROUNDS",
                    (0, 1),
                    (-1, -1),
                    [colors.white, colors.HexColor("#f8f9fa")],
                ),
                # Grid
                ("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#dee2e6")),
                # Padding
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ("LEFTPADDING", (0, 0), (-1, -1), 4),
                ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                # Right-align amount column
                ("ALIGN", (-1, 0), (-1, -1), "RIGHT"),
            ]
        )
    )
    story.append(table)

    # --- Footer ---
    story.append(Spacer(1, 0.5 * cm))
    today = date.today()
    footer_text = (
        f"Relatório gerado em {today.day:02d} de "
        f"{MONTHS_PT[today.month]} de {today.year}"
    )
    footer_style = ParagraphStyle(
        "footer",
        parent=styles["Normal"],
        fontSize=8,
        textColor=colors.grey,
        alignment=2,
    )
    story.append(Paragraph(footer_text, footer_style))

    doc.build(story)
    buffer.seek(0)
    return buffer


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
