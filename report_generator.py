from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_CENTER

def generate_pdf(messages, words, media, links):

    doc = SimpleDocTemplate("chat_report.pdf")

    style = ParagraphStyle(name="Title", fontSize=20, leading=30, alignment=TA_CENTER)

    elements = []
    elements.append(Paragraph("WhatsApp Chat Analysis Report", style))
    elements.append(Spacer(1,20))

    data = [
        ["Total Messages", messages],
        ["Total Words", words],
        ["Media Shared", media],
        ["Links Shared", links]
    ]

    table = Table(data)
    elements.append(table)

    doc.build(elements)
    return "chat_report.pdf"
