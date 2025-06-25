# core/pdf_to_txt.py
import fitz  # PyMuPDF
import re
from typing import Optional, List

def extract_text_from_pdf(pdf_bytes: bytes) -> Optional[str]:
    """Extracts all text content from a PDF file provided as bytes."""
    try:
        pdf_document = fitz.open(stream=pdf_bytes, filetype="pdf")
        full_text = ""
        for page in pdf_document:
            full_text += page.get_text("text")
        return full_text
    except Exception as e:
        print(f"Error processing PDF file: {e}")
        return None

def text_to_sections(text: Optional[str]) -> List[str]:
    """
    Splits a block of text into a list of sections based on Roman numerals.

    This is more robust as it splits the document into its semantic sections,
    which will be used for analysis.

    Args:
        text: The input string to be processed.

    Returns:
        A list of strings, where each string is a full section (title + content).
    """
    if not text:
        return []

    # Use a positive lookahead `(?=...)` to split the text BEFORE each line
    # that starts with a Roman numeral, keeping the delimiter as part of the next split.
    # `(?m)` flag enables multiline matching for `^`.
    pattern = r'(?m)(?=^[IVXLCDM]+\.)'
    
    sections = re.split(pattern, text)

    # The first element of the split might be an empty string if the text starts
    # with the pattern. We filter this out, and also strip whitespace from each section.
    cleaned_sections = [section.strip() for section in sections if section.strip()]
    
    return cleaned_sections