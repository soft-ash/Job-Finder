import os
import fitz  # PyMuPDF
from core.config import logger

def extract_cv_text(pdf_path: str) -> str:
    """Extracts all text from a PDF file using PyMuPDF."""
    if not os.path.exists(pdf_path):
        logger.error(f"CV not found at {pdf_path}. Please place your cv.pdf in the project directory.")
        return ""
    try:
        doc = fitz.open(pdf_path)
        text = ""
        for page in doc:
            text += page.get_text()
        doc.close()
        return text.strip()
    except Exception as e:
        logger.error(f"Failed to extract CV text: {e}")
        return ""
