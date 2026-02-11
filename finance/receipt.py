import io

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib.utils import simpleSplit
from reportlab.pdfgen import canvas

MONTHS_PT = {
    1: "janeiro",
    2: "fevereiro",
    3: "março",
    4: "abril",
    5: "maio",
    6: "junho",
    7: "julho",
    8: "agosto",
    9: "setembro",
    10: "outubro",
    11: "novembro",
    12: "dezembro",
}

_UNITS = [
    "",
    "um",
    "dois",
    "três",
    "quatro",
    "cinco",
    "seis",
    "sete",
    "oito",
    "nove",
    "dez",
    "onze",
    "doze",
    "treze",
    "quatorze",
    "quinze",
    "dezesseis",
    "dezessete",
    "dezoito",
    "dezenove",
]

_TENS = [
    "",
    "",
    "vinte",
    "trinta",
    "quarenta",
    "cinquenta",
    "sessenta",
    "setenta",
    "oitenta",
    "noventa",
]

_HUNDREDS = [
    "",
    "cento",
    "duzentos",
    "trezentos",
    "quatrocentos",
    "quinhentos",
    "seiscentos",
    "setecentos",
    "oitocentos",
    "novecentos",
]


def _int_to_words(number):
    """Convert integer 0-999999 to Portuguese words."""
    if number == 0:
        return "zero"
    if number == 100:
        return "cem"

    parts = []
    if number >= 1000:
        thousands = number // 1000
        number %= 1000
        if thousands == 1:
            parts.append("mil")
        else:
            parts.append(f"{_int_to_words(thousands)} mil")

    if number >= 100:
        parts.append(_HUNDREDS[number // 100])
        number %= 100

    if number >= 20:
        parts.append(_TENS[number // 10])
        number %= 10

    if number > 0:
        parts.append(_UNITS[number])

    return " e ".join(parts)


def amount_to_words(amount):
    """Convert a Decimal amount to Portuguese currency words."""
    reais = int(amount)
    centavos = int(round((amount - reais) * 100))

    parts = []
    if reais > 0:
        word = _int_to_words(reais)
        word = word[0].upper() + word[1:]
        parts.append(f'{word} {"real" if reais == 1 else "reais"}')

    if centavos > 0:
        word = _int_to_words(centavos)
        if not parts:
            word = word[0].upper() + word[1:]
        parts.append(f'{word} {"centavo" if centavos == 1 else "centavos"}')

    return " e ".join(parts) if parts else "Zero reais"


def format_brl(value):
    return f"R$ {value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def _draw_header(pdf_canvas, center, cursor_y, left_margin, right_margin):
    pdf_canvas.setFont("Helvetica-Bold", 13)
    pdf_canvas.drawCentredString(
        center, cursor_y, "AGÊNCIA MISSIONÁRIA DE AMPARO AOS EXCLUÍDOS"
    )
    cursor_y -= 0.6 * cm

    pdf_canvas.setFont("Helvetica", 9)
    pdf_canvas.drawCentredString(
        center,
        cursor_y,
        "CNPJ: 55.934.659/0001-07   |   PIX: 55.934.659/0001-07",
    )
    cursor_y -= 0.45 * cm
    pdf_canvas.drawCentredString(
        center,
        cursor_y,
        "AG. 3128-3   |   C/C. 109.277-4   |   Banco do Brasil",
    )
    cursor_y -= 0.8 * cm

    pdf_canvas.setLineWidth(0.8)
    pdf_canvas.line(left_margin, cursor_y, right_margin, cursor_y)
    cursor_y -= 1 * cm

    return cursor_y


def _draw_body(pdf_canvas, transaction, cursor_y, left_margin, right_margin):
    content_width = right_margin - left_margin

    receipt_no = f"R{transaction.pk:05d}"
    formatted = format_brl(transaction.amount)

    pdf_canvas.setFont("Helvetica-Bold", 12)
    pdf_canvas.drawString(left_margin, cursor_y, f"RECIBO Nº {receipt_no}")
    pdf_canvas.drawRightString(right_margin, cursor_y, formatted)
    cursor_y -= 1.2 * cm

    words = amount_to_words(transaction.amount)
    investor = transaction.adoption.investor.name if transaction.adoption else None

    body = f"Eu, Antônio Delson C. de Jesus, recebi {formatted} ({words})"
    if investor:
        body += f" do irmão {investor}"
    body += " como oferta para Missões e Evangelismo desta agência"
    if transaction.description:
        body += f" (ref. {transaction.description})"
    body += ". Que o Senhor o abençoe e o recompense grandemente."

    pdf_canvas.setFont("Helvetica", 11)
    lines = simpleSplit(body, "Helvetica", 11, content_width)
    for line in lines:
        pdf_canvas.drawString(left_margin, cursor_y, line)
        cursor_y -= 0.55 * cm

    return cursor_y


def _draw_date_and_signature(pdf_canvas, transaction, cursor_y, center, right_margin):
    cursor_y -= 1.5 * cm

    transaction_date = transaction.date
    date_str = (
        f"FSA, {transaction_date.day:02d} de "
        f"{MONTHS_PT[transaction_date.month]} de {transaction_date.year}"
    )
    pdf_canvas.drawRightString(right_margin, cursor_y, date_str)

    cursor_y -= 3 * cm

    pdf_canvas.line(center - 4 * cm, cursor_y, center + 4 * cm, cursor_y)
    cursor_y -= 0.5 * cm
    pdf_canvas.setFont("Helvetica-Bold", 10)
    pdf_canvas.drawCentredString(center, cursor_y, "Antônio Delson C. de Jesus")
    cursor_y -= 0.45 * cm
    pdf_canvas.setFont("Helvetica", 9)
    pdf_canvas.drawCentredString(center, cursor_y, "Presidente da AMAE")


def generate_receipt_pdf(transaction):
    buffer = io.BytesIO()
    width, height = A4
    pdf_canvas = canvas.Canvas(buffer, pagesize=A4)

    left_margin = 2.5 * cm
    right_margin = width - 2.5 * cm
    center = width / 2

    cursor_y = height - 3 * cm
    cursor_y = _draw_header(pdf_canvas, center, cursor_y, left_margin, right_margin)
    cursor_y = _draw_body(pdf_canvas, transaction, cursor_y, left_margin, right_margin)
    _draw_date_and_signature(pdf_canvas, transaction, cursor_y, center, right_margin)

    pdf_canvas.save()
    buffer.seek(0)
    return buffer
