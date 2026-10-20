import os
import fitz
from datetime import datetime, timezone

def test_pdf_generation():
    doc = fitz.open()
    page = doc.new_page(width=595.28, height=841.89)
    
    # Title Page test
    page.draw_rect(fitz.Rect(30, 30, 565, 811), color=(0.06, 0.15, 0.32), width=1.5)
    page.insert_text((50, 100), "INTELLIRESEARCH ACADEMIC RESEARCH REPORT", fontsize=10, fontname="hebo", color=(0.12, 0.32, 0.58))
    page.insert_text((50, 140), "Plant Disease Detection and Classification Using AI", fontsize=16, fontname="hebo", color=(0.06, 0.15, 0.32))
    
    pdf_bytes = doc.tobytes()
    print(f"Generated PDF bytes length: {len(pdf_bytes)}")
    assert len(pdf_bytes) > 500
    print("PyMuPDF basic check passed!")

if __name__ == "__main__":
    test_pdf_generation()
