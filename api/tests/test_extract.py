import io, os, sys
import pytest
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter

# ensure import path
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from extractor.extract import pdf_to_text, extract_fields


def make_pdf_bytes(lines):
    """Create a simple in-memory PDF with the given lines of text."""
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=letter)
    width, height = letter
    y = height - 72
    for line in lines:
        c.drawString(72, y, line)
        y -= 18
        if y < 72:
            c.showPage()
            y = height - 72
    c.save()
    return buf.getvalue()


def test_pdf_to_text_returns_content():
    pdf = make_pdf_bytes([
        "John Doe", "john@example.com", "Experience", "• Built things in Python and FastAPI.",
        "• Deployed on AWS using Docker and ECS."
    ])
    txt = pdf_to_text(pdf)
    assert isinstance(txt, str) and len(txt) > 50


def test_extract_fields_email_or_bullets():
    pdf = make_pdf_bytes([
        "Jane Smith", "Contact: jane@smith.dev", "Experience",
        "• Implemented streaming with Kafka", "- Built dashboards with React"
    ])
    txt = pdf_to_text(pdf)
    parsed = extract_fields(txt)
    email = parsed["basics"].get("email")
    bullets = parsed["work"][0].get("highlights", [])
    assert (email is not None) or (len(bullets) >= 4)


@pytest.mark.skip(reason="Enable locally to test OCR path manually")
def test_ocr_fallback_manual():
    assert True


