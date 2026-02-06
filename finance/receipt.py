import io

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib.utils import simpleSplit
from reportlab.pdfgen import canvas

MONTHS_PT = {
    1: 'janeiro', 2: 'fevereiro', 3: 'março', 4: 'abril',
    5: 'maio', 6: 'junho', 7: 'julho', 8: 'agosto',
    9: 'setembro', 10: 'outubro', 11: 'novembro', 12: 'dezembro',
}

_UNITS = [
    '', 'um', 'dois', 'três', 'quatro', 'cinco', 'seis', 'sete', 'oito', 'nove',
    'dez', 'onze', 'doze', 'treze', 'quatorze', 'quinze',
    'dezesseis', 'dezessete', 'dezoito', 'dezenove',
]

_TENS = ['', '', 'vinte', 'trinta', 'quarenta', 'cinquenta',
         'sessenta', 'setenta', 'oitenta', 'noventa']

_HUNDREDS = ['', 'cento', 'duzentos', 'trezentos', 'quatrocentos', 'quinhentos',
             'seiscentos', 'setecentos', 'oitocentos', 'novecentos']


def _int_to_words(n):
    """Convert integer 0-999999 to Portuguese words."""
    if n == 0:
        return 'zero'
    if n == 100:
        return 'cem'

    parts = []
    if n >= 1000:
        thousands = n // 1000
        n %= 1000
        if thousands == 1:
            parts.append('mil')
        else:
            parts.append(f'{_int_to_words(thousands)} mil')

    if n >= 100:
        parts.append(_HUNDREDS[n // 100])
        n %= 100

    if n >= 20:
        parts.append(_TENS[n // 10])
        n %= 10

    if n > 0:
        parts.append(_UNITS[n])

    return ' e '.join(parts)


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

    return ' e '.join(parts) if parts else 'Zero reais'


def _fmt_brl(value):
    return f'R$ {value:,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.')


def generate_receipt_pdf(transaction):
    buffer = io.BytesIO()
    width, height = A4
    c = canvas.Canvas(buffer, pagesize=A4)

    left_margin = 2.5 * cm
    right_margin = width - 2.5 * cm
    content_width = right_margin - left_margin
    center = width / 2

    y = height - 3 * cm

    # --- Header ---
    c.setFont('Helvetica-Bold', 13)
    c.drawCentredString(center, y, 'AGÊNCIA MISSIONÁRIA DE AMPARO AOS EXCLUÍDOS')
    y -= 0.6 * cm

    c.setFont('Helvetica', 9)
    c.drawCentredString(center, y, 'CNPJ: 55.934.659/0001-07   |   PIX: 55.934.659/0001-07')
    y -= 0.45 * cm
    c.drawCentredString(center, y, 'AG. 3128-3   |   C/C. 109.277-4   |   Banco do Brasil')
    y -= 0.8 * cm

    # Horizontal line
    c.setLineWidth(0.8)
    c.line(left_margin, y, right_margin, y)
    y -= 1 * cm

    # --- Receipt number and value ---
    receipt_no = f'R{transaction.pk:05d}'
    formatted = _fmt_brl(transaction.amount)

    c.setFont('Helvetica-Bold', 12)
    c.drawString(left_margin, y, f'RECIBO Nº {receipt_no}')
    c.drawRightString(right_margin, y, formatted)
    y -= 1.2 * cm

    # --- Body text ---
    words = amount_to_words(transaction.amount)
    church = transaction.adoption.church.name if transaction.adoption else None

    body = f'Eu, Antônio Delson C. de Jesus, recebi {formatted} ({words})'
    if church:
        body += f' do irmão {church}'
    body += ' como oferta para Missões e Evangelismo desta agência'
    if transaction.description:
        body += f' (ref. {transaction.description})'
    body += '. Que o Senhor o abençoe e o recompense grandemente.'

    c.setFont('Helvetica', 11)
    lines = simpleSplit(body, 'Helvetica', 11, content_width)
    for line in lines:
        c.drawString(left_margin, y, line)
        y -= 0.55 * cm

    y -= 1.5 * cm

    # --- Date ---
    d = transaction.date
    date_str = f'FSA, {d.day:02d} de {MONTHS_PT[d.month]} de {d.year}'
    c.drawRightString(right_margin, y, date_str)

    y -= 3 * cm

    # --- Signature ---
    c.line(center - 4 * cm, y, center + 4 * cm, y)
    y -= 0.5 * cm
    c.setFont('Helvetica-Bold', 10)
    c.drawCentredString(center, y, 'Antônio Delson C. de Jesus')
    y -= 0.45 * cm
    c.setFont('Helvetica', 9)
    c.drawCentredString(center, y, 'Presidente da AMAE')

    c.save()
    buffer.seek(0)
    return buffer
