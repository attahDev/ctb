"""Generates a simple, print-ready PDF certificate. Pure-Python (reportlab),
no system dependencies like wkhtmltopdf — matches the "nothing too heavy"
approach used everywhere else in this project."""

import io

from reportlab.lib.colors import HexColor
from reportlab.lib.pagesizes import landscape, letter
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas

NAVY = HexColor("#0a0f1c")
GOLD = HexColor("#f5a623")
MUTED = HexColor("#5c6578")


def render_certificate_pdf(recipient_name: str, title: str, issued_date: str) -> bytes:
    buffer = io.BytesIO()
    page_size = landscape(letter)
    width, height = page_size
    c = canvas.Canvas(buffer, pagesize=page_size)

    # Border
    c.setStrokeColor(GOLD)
    c.setLineWidth(3)
    c.rect(0.4 * inch, 0.4 * inch, width - 0.8 * inch, height - 0.8 * inch)

    c.setStrokeColor(NAVY)
    c.setLineWidth(0.75)
    c.rect(0.55 * inch, 0.55 * inch, width - 1.1 * inch, height - 1.1 * inch)

    c.setFillColor(NAVY)
    c.setFont("Helvetica-Bold", 14)
    c.drawCentredString(width / 2, height - 1.3 * inch, "GLORY TIME CHRISTIAN CENTER")

    c.setFillColor(MUTED)
    c.setFont("Helvetica", 11)
    c.drawCentredString(width / 2, height - 1.6 * inch, "Certificate of Completion")

    c.setFillColor(NAVY)
    c.setFont("Helvetica-Bold", 30)
    c.drawCentredString(width / 2, height / 2 + 0.3 * inch, recipient_name)

    c.setFillColor(MUTED)
    c.setFont("Helvetica", 13)
    c.drawCentredString(width / 2, height / 2 - 0.25 * inch, "has successfully completed")

    c.setFillColor(NAVY)
    c.setFont("Helvetica-Bold", 18)
    c.drawCentredString(width / 2, height / 2 - 0.65 * inch, title)

    c.setFillColor(MUTED)
    c.setFont("Helvetica", 10)
    c.drawCentredString(width / 2, 1.1 * inch, f"Issued {issued_date}")

    c.showPage()
    c.save()
    return buffer.getvalue()
